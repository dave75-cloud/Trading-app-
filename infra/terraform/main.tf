terraform {
  required_version = ">= 1.5.0"

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

# -------------------------------------------------------------------
# Optional: create runtime secrets in Secrets Manager
# If create_secrets=true AND the corresponding *_secret_arn is empty,
# Terraform creates the secret (and version) here.
# -------------------------------------------------------------------

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

  effective_polygon_api_key_secret_arn = var.polygon_api_key_secret_arn != "" ? var.polygon_api_key_secret_arn : (
    length(aws_secretsmanager_secret.polygon_api_key) > 0 ? aws_secretsmanager_secret.polygon_api_key[0].arn : ""
  )

  effective_slack_webhook_url_secret_arn = var.slack_webhook_url_secret_arn != "" ? var.slack_webhook_url_secret_arn : (
    length(aws_secretsmanager_secret.slack_webhook_url) > 0 ? aws_secretsmanager_secret.slack_webhook_url[0].arn : ""
  )
}

# -------------------------------------------------------------------
# Modules
# -------------------------------------------------------------------

module "s3" {
  source  = "./s3"
  project = var.project
}

module "rds" {
  source                = "./rds"
  project               = var.project
  vpc_id                = var.vpc_id
  private_subnets        = var.private_subnets
  ecs_security_group_id = var.ecs_security_group

  db_username          = var.db_username
  db_password          = var.db_password
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage

  # keep deterministic; don't depend on other module outputs existing
  alarms_topic_arn = ""
}

module "ecs" {
  source = "./ecs"

  region          = var.region
  project         = var.project
  vpc_id          = var.vpc_id
  public_subnets  = var.public_subnets
  private_subnets = var.private_subnets

  ecs_security_group = var.ecs_security_group
  alb_security_group = var.alb_security_group

  api_image       = var.api_image
  broker_image    = var.broker_image
  dashboard_image = var.dashboard_image != "" ? var.dashboard_image : var.api_image

  db_url_secret_arn = local.effective_db_url_secret_arn
  signal_cron       = var.signal_cron

  polygon_api_key_secret_arn   = local.effective_polygon_api_key_secret_arn
  slack_webhook_url_secret_arn = local.effective_slack_webhook_url_secret_arn
}

# -------------------------------------------------------------------
# Root outputs (handy for “where is it?” after apply)
# -------------------------------------------------------------------

output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "db_url_secret_arn" {
  value = local.effective_db_url_secret_arn
}

output "alb_dns_name" {
  value = try(module.ecs.alb_dns_name, "")
}

output "cluster_name" {
  value = try(module.ecs.cluster_name, "")
}
