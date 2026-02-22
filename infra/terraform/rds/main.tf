resource "aws_db_subnet_group" "this" {
  name       = "${var.project}-db-subnets"
  subnet_ids = var.private_subnets
}
resource "aws_security_group" "db" {
  name   = "${var.project}-db-sg"
  vpc_id = var.vpc_id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }
egress {
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}
}
resource "aws_db_instance" "postgres" {
  identifier              = "${var.project}-db"
  engine                  = "postgres"
  engine_version          = "15"
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  db_name                 = "signals"
  username                = var.db_username
  password                = var.db_password
  publicly_accessible     = false
  skip_final_snapshot     = true
  vpc_security_group_ids  = [aws_security_group.db.id]
  db_subnet_group_name    = aws_db_subnet_group.this.name
}
  35	output "db_endpoint" { value = aws_db_instance.postgres.address }
    36	output "db_port" { value = aws_db_instance.postgres.port }
    37	output "db_name" { value = aws_db_instance.postgres.db_name }
    38	
    39	output "db_url" {
    40	  value     = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
    41	  sensitive = true
    42	}
    43	
    44	# ---- RDS alarms (optional) ----
    45	resource "aws_cloudwatch_metric_alarm" "db_cpu_high" {
    46	  count               = var.alarms_topic_arn != "" ? 1 : 0
    47	  alarm_name          = "${var.project}-db-cpu-high"
    48	  alarm_description   = "RDS CPU utilization is high."
    49	  namespace           = "AWS/RDS"
    50	  metric_name         = "CPUUtilization"
    51	  statistic           = "Average"
    52	  period              = 300
    53	  evaluation_periods  = 2
    54	  threshold           = 80
    55	  comparison_operator = "GreaterThanOrEqualToThreshold"
    56	  treat_missing_data  = "notBreaching"
    57	dimensions = { DBInstanceIdentifier = aws_db_instance.postgres.id }
    58	  alarm_actions = [var.alarms_topic_arn]
    59	}
    60	
    61	resource "aws_cloudwatch_metric_alarm" "db_free_storage_low" {
    62	  count               = var.alarms_topic_arn != "" ? 1 : 0
    63	  alarm_name          = "${var.project}-db-free-storage-low"
    64	  alarm_description   = "RDS free storage is low."
    65	  namespace           = "AWS/RDS"
    66	  metric_name         = "FreeStorageSpace"
    67	  statistic           = "Average"
    68	  period              = 300
    69	  evaluation_periods  = 1
    70	  threshold           = 10737418240 # 10 GiB
    71	  comparison_operator = "LessThanOrEqualToThreshold"
    72	  treat_missing_data  = "notBreaching"
    73	dimensions = { DBInstanceIdentifier = aws_db_instance.postgres.id }
    74	  alarm_actions = [var.alarms_topic_arn]
    75	}
    76	
    77	resource "aws_cloudwatch_metric_alarm" "db_freeable_memory_low" {
    78	  count               = var.alarms_topic_arn != "" ? 1 : 0
    79	  alarm_name          = "${var.project}-db-freeable-memory-low"
    80	  alarm_description   = "RDS freeable memory is low."
    81	  namespace           = "AWS/RDS"
    82	  metric_name         = "FreeableMemory"
    83	  statistic           = "Average"
    84	  period              = 300
    85	  evaluation_periods  = 1
    86	  threshold           = 268435456 # 256 MiB
    87	  comparison_operator = "LessThanOrEqualToThreshold"
    88	  treat_missing_data  = "notBreaching"
    89	dimensions = { DBInstanceIdentifier = aws_db_instance.postgres.id }
    90	  alarm_actions = [var.alarms_topic_arn]
    91	}
