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

module "s3" {
  source  = "./s3"
  project = var.project
}

module "rds" {
  source = "./rds"

  project               = var.project
  vpc_id                = var.vpc_id
  private_subnets       = var.private_subnets
  ecs_security_group_id = var.ecs_security_group

  db_username          = var.db_username
  db_password          = var.db_password
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
}

module "ecs" {
  source = "./ecs"

  project          = var.project
  region           = var.region
  vpc_id           = var.vpc_id
  public_subnets   = var.public_subnets
  private_subnets  = var.private_subnets

  ecs_security_group = var.ecs_security_group
  alb_security_group = var.alb_security_group

  api_image       = var.api_image
  broker_image    = var.broker_image
  dashboard_image = var.dashboard_image != "" ? var.dashboard_image : var.api_image

  db_url_secret_arn             = var.db_url_secret_arn
  polygon_api_key_secret_arn    = var.polygon_api_key_secret_arn
  slack_webhook_url_secret_arn  = var.slack_webhook_url_secret_arn

  signal_cron = var.signal_cron
  alarm_email = var.alarm_email
}

output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}
