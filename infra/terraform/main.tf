terraform {
  required_version = ">= 1.6.0"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
}
provider "aws" { region = var.region }

# ---- KMS (optional) for Secrets Manager encryption-at-rest ----
data "aws_caller_identity" "current" {}

resource "aws_kms_key" "secrets" {
  count                   = var.create_kms_key && var.kms_key_arn == "" ? 1 : 0
  description             = "${var.project} secrets"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "secrets" {
  count         = var.create_kms_key && var.kms_key_arn == "" ? 1 : 0
  name          = "alias/${var.project}-secrets"
  target_key_id = aws_kms_key.secrets[0].key_id
}

locals {
  effective_kms_key_id = var.kms_key_arn != "" ? var.kms_key_arn : (length(aws_kms_key.secrets) > 0 ? aws_kms_key.secrets[0].arn : null)
}


# ---- Secrets Manager (recommended for runtime secrets) ----
# If you supply *_secret_arn variables and set create_secrets=false, Terraform will not create secrets.

resource "aws_secretsmanager_secret" "db_url" {
  count = var.create_secrets && var.db_url_secret_arn == "" ? 1 : 0
  name  = "${var.project}/db_url"
}

resource "aws_secretsmanager_secret_version" "db_url" {
  count         = var.create_secrets && var.db_url_secret_arn == "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.db_url[0].id
  secret_string = module.rds.db_url
}

resource "aws_secretsmanager_secret" "polygon_api_key" {
  count = var.create_secrets && var.polygon_api_key_secret_arn == "" && var.polygon_api_key != "" ? 1 : 0
  name  = "${var.project}/polygon_api_key"
}

resource "aws_secretsmanager_secret_version" "polygon_api_key" {
  count         = var.create_secrets && var.polygon_api_key_secret_arn == "" && var.polygon_api_key != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.polygon_api_key[0].id
  secret_string = var.polygon_api_key
}

resource "aws_secretsmanager_secret" "slack_webhook_url" {
  count = var.create_secrets && var.slack_webhook_url_secret_arn == "" && var.slack_webhook_url != "" ? 1 : 0
  name  = "${var.project}/slack_webhook_url"
}

resource "aws_secretsmanager_secret_version" "slack_webhook_url" {
  count         = var.create_secrets && var.slack_webhook_url_secret_arn == "" && var.slack_webhook_url != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.slack_webhook_url[0].id
  secret_string = var.slack_webhook_url
}

locals {
  effective_db_url_secret_arn = var.db_url_secret_arn != "" ? var.db_url_secret_arn : aws_secretsmanager_secret.db_url[0].arn

effective_polygon_api_key_secret_arn = var.polygon_api_key_secret_arn != "" ? var.polygon_api_key_secret_arn : (length(aws_secretsmanager_secret.polygon_api_key) > 0 ? aws_secretsmanager_secret.polygon_api_key[0].arn : "")


  effective_slack_webhook_url_secret_arn = var.slack_webhook_url_secret_arn != "" ? var.slack_webhook_url_secret_arn :
    (length(aws_secretsmanager_secret.slack_webhook_url) > 0 ? aws_secretsmanager_secret.slack_webhook_url[0].arn : "")
}

# ---- ALB access logs (optional but recommended) ----
resource "aws_s3_bucket" "alb_logs" {
  count  = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0
  bucket = "${var.project}-alb-logs-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_ownership_controls" "alb_logs" {
  count  = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id
  rule { object_ownership = "BucketOwnerEnforced" }
}

resource "aws_s3_bucket_public_access_block" "alb_logs" {
  count  = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "alb_logs" {
  count = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0

  statement {
    sid     = "AWSALBLogDeliveryWrite"
    effect  = "Allow"
    actions = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.alb_logs[0].arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }

  statement {
    sid     = "AWSALBLogDeliveryAclCheck"
    effect  = "Allow"
    actions = ["s3:GetBucketAcl", "s3:ListBucket"]
    resources = [aws_s3_bucket.alb_logs[0].arn]

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "alb_logs" {
  count  = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id
  policy = data.aws_iam_policy_document.alb_logs[0].json
}

locals {
  effective_alb_logs_bucket = var.alb_access_logs_bucket != "" ? var.alb_access_logs_bucket :
    (length(aws_s3_bucket.alb_logs) > 0 ? aws_s3_bucket.alb_logs[0].bucket : "")
}

module "s3" {
  source  = "./s3"
  project = var.project
}
module "rds" {
  source = "./rds"
  project = var.project
  vpc_id = var.vpc_id
  private_subnets = var.private_subnets
  ecs_security_group_id = var.ecs_security_group
  db_username = var.db_username
  db_password = var.db_password
  db_instance_class = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  alarms_topic_arn = module.ecs.alarms_topic_arn
}

module "ecs" {
  source = "./ecs"
  region = var.region
  project = var.project
  vpc_id = var.vpc_id
  public_subnets = var.public_subnets
  private_subnets = var.private_subnets
  ecs_security_group = var.ecs_security_group
  alb_security_group = var.alb_security_group
  api_image = var.api_image
  broker_image = var.broker_image
  dashboard_image = var.dashboard_image != "" ? var.dashboard_image : var.api_image
  signal_cron = var.signal_cron
}
