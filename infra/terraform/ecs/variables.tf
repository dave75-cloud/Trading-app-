variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnets" {
  type = list(string)

  validation {
    condition     = length(var.public_subnets) >= 2
    error_message = "public_subnets must contain at least two subnet IDs."
  }
}

variable "private_subnets" {
  type = list(string)

  validation {
    condition     = length(var.private_subnets) >= 2
    error_message = "private_subnets must contain at least two subnet IDs."
  }
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
