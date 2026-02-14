variable "project"           { type = string }
variable "vpc_id"            { type = string }
variable "private_subnets"   { type = list(string) }
variable "ecs_security_group_id" { type = string }
variable "db_username"       { type = string }
variable "db_password"       { type = string }
variable "db_instance_class" { type = string }
variable "db_allocated_storage" { type = number }

variable "alarms_topic_arn" { type = string default = "" }
