terraform {

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

# ------------------------------------------------------------
# Optional KMS key (only created if create_kms_key = true
# and no kms_key_arn is supplied)
# ------------------------------------------------------------

resource "aws_kms_key" "secrets" {
  count                   = var.create_kms_key && var.kms_key_arn == "" ? 1 : 0
  description             = "${var.project} secrets"
  deletion_window_in_days = 7
  enable_key_rotation     = false
}

resource "aws_kms_alias" "secrets" {
  count         = var.create_kms_key && var.kms_key_arn == "" ? 1 : 0
  name          = "alias/${var.project}-secrets"
  target_key_id = aws_kms_key.secrets[0].key_id
}

locals {
  effective_kms_key_arn = var.kms_key_arn != "" ? var.kms_key_arn : (
    length(aws_kms_key.secrets) > 0 ? aws_kms_key.secrets[0].arn : ""
  )
}

# ------------------------------------------------------------
# Optional runtime secrets
# ------------------------------------------------------------

resource "aws_secretsmanager_secret" "db_url" {
  count      = var.create_secrets && var.db_url_secret_arn == "" ? 1 : 0
  name       = "${var.project}/db_url"
  kms_key_id = local.effective_kms_key_arn != "" ? local.effective_kms_key_arn : null
}

resource "aws_secretsmanager_secret_version" "db_url" {
  count        = var.create_secrets && var.db_url_secret_arn == "" ? 1 : 0
  secret_id    = aws_secretsmanager_secret.db_url[0].id
  secret_string = "postgres://${var.db_username}:${var.db_password}@placeholder:5432/signals"
}

locals {
  effective_db_url_secret_arn = var.db_url_secret_arn != "" ? var.db_url_secret_arn : (
    length(aws_secretsmanager_secret.db_url) > 0 ? aws_secretsmanager_secret.db_url[0].arn : ""
  )
}

# ------------------------------------------------------------
# ALB access logs bucket (optional)
# ------------------------------------------------------------

resource "aws_s3_bucket" "alb_logs" {
  count  = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0
  bucket = "${var.project}-alb-logs-${data.aws_caller_identity.current.account_id}"
}

# ------------------------------------------------------------
# Modules
# ------------------------------------------------------------

module "s3" {
  source  = "./s3"
  project = var.project
}

module "rds" {
  source              = "./rds"
  project             = var.project
  vpc_id              = var.vpc_id
  private_subnets     = var.private_subnets
  ecs_security_group  = var.ecs_security_group
  db_instance_class   = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_username         = var.db_username
  db_password         = var.db_password
}

module "ecs" {
  source                     = "./ecs"
  project                    = var.project
  region                     = var.region
  vpc_id                     = var.vpc_id
  public_subnets             = var.public_subnets
  private_subnets            = var.private_subnets
  ecs_security_group         = var.ecs_security_group
  alb_security_group         = var.alb_security_group
  api_image                  = var.api_image
  broker_image               = var.broker_image
  dashboard_image            = var.dashboard_image
  db_url_secret_arn          = local.effective_db_url_secret_arn
  polygon_api_key_secret_arn = var.polygon_api_key_secret_arn
  slack_webhook_url_secret_arn = var.slack_webhook_url_secret_arn
  signal_cron                = var.signal_cron
}
