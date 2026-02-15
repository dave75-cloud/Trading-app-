locals {
  api_paths = [
    "/health",
    "/signals/*",
    "/backtest/*",
    "/docs",
    "/openapi.json",
  ]

  api_secrets = concat(
    [{ name = "DB_URL", valueFrom = var.db_url_secret_arn }],
    var.polygon_api_key_secret_arn != "" ? [{ name = "POLYGON_API_KEY", valueFrom = var.polygon_api_key_secret_arn }] : []
  )

  runner_secrets = concat(
    [{ name = "DB_URL", valueFrom = var.db_url_secret_arn }],
    var.polygon_api_key_secret_arn != "" ? [{ name = "POLYGON_API_KEY", valueFrom = var.polygon_api_key_secret_arn }] : [],
    var.slack_webhook_url_secret_arn != "" ? [{ name = "SLACK_WEBHOOK_URL", valueFrom = var.slack_webhook_url_secret_arn }] : []
  )
}

resource "aws_ecs_cluster" "this" {
  name = "${var.project}-cluster"
}

# ---- IAM (execution + task) ----
resource "aws_iam_role" "task_execution" {
  name = "${var.project}-ecsTaskExecutionRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name = "${var.project}-taskRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

# If you later move secrets to Secrets Manager/SSM, add explicit permissions here.
resource "aws_iam_role_policy" "task" {
  name = "${var.project}-taskRoleInline"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # App logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.api.arn}:*",
          "${aws_cloudwatch_log_group.dashboard.arn}:*",
          "${aws_cloudwatch_log_group.runner.arn}:*"
        ]
      },

      # Runtime secrets (Secrets Manager)
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = compact([
          var.db_url_secret_arn,
          var.polygon_api_key_secret_arn,
          var.slack_webhook_url_secret_arn
        ])
      },

      # If the Secrets Manager secrets use a customer-managed KMS key, allow decrypt.
      {
        Effect = "Allow"
        Action = ["kms:Decrypt"]
        Resource = "*"
      }
    ]
  })
}

# ---- Logs ----
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project}/api"
  retention_in_days = 14
}
resource "aws_cloudwatch_log_group" "dashboard" {
  name              = "/ecs/${var.project}/dashboard"
  retention_in_days = 14
}
resource "aws_cloudwatch_log_group" "runner" {
  name              = "/ecs/${var.project}/runner"
  retention_in_days = 14
}

# ---- ALB ----
resource "aws_lb" "alb" {

dynamic "access_logs" {
  for_each = var.enable_alb_access_logs && var.alb_access_logs_bucket != "" ? [1] : []
  content {
    bucket  = var.alb_access_logs_bucket
    enabled = true
    prefix  = "${var.project}/alb"
  }
}
  name               = "${var.project}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group]
  subnets            = var.public_subnets
}

resource "aws_lb_target_group" "api" {
  name        = "${var.project}-api-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check { path = "/health" }
}

resource "aws_lb_target_group" "dashboard" {
  name        = "${var.project}-dash-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check { path = "/" }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  # Default to dashboard.
default_action {
  type             = "forward"
  target_group_arn = aws_lb_target_group.dashboard.arn
}
}

resource "aws_lb_listener_rule" "api_paths" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
  condition {
    path_pattern { values = local.api_paths }
  }
}

# ---- Task Definitions ----
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.api_image
      essential = true
      portMappings = [{ containerPort = 8080, hostPort = 8080 }]
      environment = [
        { name = "MODEL_REGISTRY", value = "/models_registry/gbpusd" },
        { name = "DATA_DIR",       value = "/data/market_candles" },
        { name = "SYMBOL",         value = "GBPUSD" },
        # DB_URL and POLYGON_API_KEY are injected via Secrets Manager
      ]
      secrets = local.api_secrets
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "dashboard" {
  family                   = "${var.project}-dashboard"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "dashboard"
      image     = var.dashboard_image
      essential = true
      portMappings = [{ containerPort = 8501, hostPort = 8501 }]
      command = [
        "streamlit",
        "run",
        "services/dashboard/app.py",
        "--server.address=0.0.0.0",
        "--server.port=8501"
      ]
      # Server-side calls to the API should go via the public ALB so routing rules apply.
      environment = [
        { name = "API_BASE_URL", value = "http://${aws_lb.alb.dns_name}" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.dashboard.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "runner" {
  family                   = "${var.project}-runner"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "runner"
      image     = var.api_image
      essential = true
      command   = ["python", "cli/signal_report.py"]
      environment = [
        { name = "MODEL_REGISTRY", value = "/models_registry/gbpusd" },
        { name = "DATA_DIR",       value = "/data/market_candles" },
        { name = "SYMBOL",         value = "GBPUSD" },
        # DB_URL and POLYGON_API_KEY are injected via Secrets Manager
      ]
      secrets = local.api_secrets
      ]
logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.runner.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

# ---- Services ----
resource "aws_ecs_service" "api" {
  name            = "${var.project}-api-svc"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [var.ecs_security_group]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8080
  }
}

resource "aws_ecs_service" "dashboard" {
  name            = "${var.project}-dashboard-svc"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.dashboard.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [var.ecs_security_group]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.dashboard.arn
    container_name   = "dashboard"
    container_port   = 8501
  }
}

# ---- Scheduled run (EventBridge) ----
resource "aws_iam_role" "events" {
  name = "${var.project}-eventsRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "events.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "events" {
  name = "${var.project}-eventsRoleInline"
  role = aws_iam_role.events.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["ecs:RunTask"]
        Resource = [aws_ecs_task_definition.runner.arn]
      },
      {
        Effect = "Allow"
        Action = ["iam:PassRole"]
        Resource = [aws_iam_role.task_execution.arn, aws_iam_role.task.arn]
      }
    ]
  })
}

resource "aws_cloudwatch_event_rule" "signal" {
  name                = "${var.project}-signal"
  schedule_expression = var.signal_cron
}

resource "aws_cloudwatch_event_target" "signal" {
  rule      = aws_cloudwatch_event_rule.signal.name
  target_id = "run-signal"
  arn       = aws_ecs_cluster.this.arn
  role_arn  = aws_iam_role.events.arn

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.runner.arn
    launch_type         = "FARGATE"
    platform_version    = "LATEST"

    network_configuration {
      subnets          = var.private_subnets
      security_groups  = [var.ecs_security_group]
      assign_public_ip = false
    }
  }
}


# ---- Alarms (CloudWatch + SNS) ----
resource "aws_sns_topic" "alarms" {
  name = "${var.project}-alarms"
}

resource "aws_sns_topic_subscription" "alarm_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# ALB 5xx from the load balancer
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.project}-alb-5xx"
  alarm_description   = "ALB is returning 5xx responses."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_ELB_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    LoadBalancer = aws_lb.alb.arn_suffix
  }
  alarm_actions = [aws_sns_topic.alarms.arn]
}

# ECS service CPU and memory
resource "aws_cloudwatch_metric_alarm" "api_cpu_high" {
  alarm_name          = "${var.project}-api-cpu-high"
  alarm_description   = "API service CPU utilization is high."
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    ClusterName = aws_ecs_cluster.this.name
    ServiceName = aws_ecs_service.api.name
  }
  alarm_actions = [aws_sns_topic.alarms.arn]
}

resource "aws_cloudwatch_metric_alarm" "api_mem_high" {
  alarm_name          = "${var.project}-api-mem-high"
  alarm_description   = "API service memory utilization is high."
  namespace           = "AWS/ECS"
  metric_name         = "MemoryUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    ClusterName = aws_ecs_cluster.this.name
    ServiceName = aws_ecs_service.api.name
  }
  alarm_actions = [aws_sns_topic.alarms.arn]
}

# Log-based alarm for ERROR lines in API logs
resource "aws_cloudwatch_log_metric_filter" "api_errors" {
  name           = "${var.project}-api-errors"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = ""ERROR""

  metric_transformation {
    name      = "${var.project}-api-error-count"
    namespace = "${var.project}/logs"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_error_logs" {
  alarm_name          = "${var.project}-api-error-logs"
  alarm_description   = "API is logging ERROR lines."
  namespace           = aws_cloudwatch_log_metric_filter.api_errors.metric_transformation[0].namespace
  metric_name         = aws_cloudwatch_log_metric_filter.api_errors.metric_transformation[0].name
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
}

output "alb_dns_name" {
  value = aws_lb.alb.dns_name
}

output "alarms_topic_arn" {
  value = aws_sns_topic.alarms.arn
}
