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
  egress { from_port = 0, to_port = 0, protocol = "-1", cidr_blocks = ["0.0.0.0/0"] }
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
output "db_endpoint" { value = aws_db_instance.postgres.address }
output "db_port" { value = aws_db_instance.postgres.port }
output "db_name" { value = aws_db_instance.postgres.db_name }

output "db_url" {
  value     = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
  sensitive = true
}

# ---- RDS alarms (optional) ----
resource "aws_cloudwatch_metric_alarm" "db_cpu_high" {
  count               = var.alarms_topic_arn != "" ? 1 : 0
  alarm_name          = "${var.project}-db-cpu-high"
  alarm_description   = "RDS CPU utilization is high."
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = { DBInstanceIdentifier = aws_db_instance.this.id }
  alarm_actions = [var.alarms_topic_arn]
}

resource "aws_cloudwatch_metric_alarm" "db_free_storage_low" {
  count               = var.alarms_topic_arn != "" ? 1 : 0
  alarm_name          = "${var.project}-db-free-storage-low"
  alarm_description   = "RDS free storage is low."
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 1
  threshold           = 10737418240 # 10 GiB
  comparison_operator = "LessThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = { DBInstanceIdentifier = aws_db_instance.this.id }
  alarm_actions = [var.alarms_topic_arn]
}

resource "aws_cloudwatch_metric_alarm" "db_freeable_memory_low" {
  count               = var.alarms_topic_arn != "" ? 1 : 0
  alarm_name          = "${var.project}-db-freeable-memory-low"
  alarm_description   = "RDS freeable memory is low."
  namespace           = "AWS/RDS"
  metric_name         = "FreeableMemory"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 1
  threshold           = 268435456 # 256 MiB
  comparison_operator = "LessThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = { DBInstanceIdentifier = aws_db_instance.this.id }
  alarm_actions = [var.alarms_topic_arn]
}
