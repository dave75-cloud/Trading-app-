variable "region" {
  type    = string
  default = "***"
}
variable "project"               { type = string  default = "gbpusd-signal" }
variable "vpc_id"                { type = string }
variable "public_subnets"        { type = list(string) }
variable "private_subnets"       { type = list(string) }
variable "ecs_security_group"    { type = string }
variable "alb_security_group"    { type = string }
variable "api_image"             { type = string }
variable "broker_image"          { type = string }
variable "dashboard_image"       { type = string  default = "" }
variable "db_username"           { type = string  default = "signal_user" }
variable "db_password"           { type = string  default = "ChangeMe123!" }
variable "db_instance_class"     { type = string  default = "db.t4g.micro" }
variable "db_allocated_storage"  { type = number  default = 20 }

# ---- Secrets handling ----
# Recommended: provide existing Secrets Manager ARNs below and set create_secrets=false.
variable "create_secrets" { type = bool default = true }

variable "db_url_secret_arn" {
  type    = string
  default = ""
}

variable "polygon_api_key_secret_arn" {
  type    = string
  default = ""
}

variable "slack_webhook_url_secret_arn" {
  type    = string
  default = ""
}

# If you are creating secrets via TF (not recommended for mature setups), provide values here:
variable "polygon_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "slack_webhook_url" {
  type      = string
  default   = ""
  sensitive = true
}

variable "signal_cron" {
  type    = string
  default = "rate(30 minutes)"
}

# Optional: subscribe an email address to alarm notifications.
variable "alarm_email" {
  type    = string
  default = ""
}

# --- Hardening / Ops ---
variable "create_kms_key"          { type = bool   default = true }
variable "kms_key_arn"             { type = string default = "" } # optional existing CMK ARN for Secrets Manager
variable "enable_alb_access_logs"  { type = bool   default = true }
variable "alb_access_logs_bucket"  { type = string default = "" } # optional existing bucket name; if empty and enable=true TF creates one
