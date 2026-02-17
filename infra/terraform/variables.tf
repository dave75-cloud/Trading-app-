variable "create_secrets" {
  type    = bool
  default = true
}
variable "region" {
  type    = string
  default = "ap-southeast-2"
}

variable "project" {
  type    = string
  default = "gbpusd-signal"
}

variable "vpc_id" {
  type = string
}

variable "public_subnets" {
  type = list(string)
}

variable "private_subnets" {
  type = list(string)
}

variable "ecs_security_group" {
  type = string
}

variable "alb_security_group" {
  type = string
}

variable "api_image" {
  type = string
}

variable "broker_image" {
  type = string
}

variable "dashboard_image" {
  type = string
}

# Secrets are sourced from AWS Secrets Manager at runtime (recommended).
variable "db_url_secret_arn" {
  type = string
}

variable "polygon_api_key_secret_arn" {
  type    = string
  default = ""
}

variable "slack_webhook_url_secret_arn" {
  type    = string
  default = ""
}

variable "signal_cron" {
  type    = string
  default = "rate(30 minutes)"
}

variable "alarm_email" {
  type    = string
  default = ""
}

variable "enable_alb_access_logs" {
  type    = bool
  default = true
}

variable "alb_access_logs_bucket" {
  type    = string
  default = ""
}
