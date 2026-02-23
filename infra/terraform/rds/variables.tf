variable "project" { type = string }

variable "vpc_id" { type = string }

variable "private_subnets" {
  type = list(string)
}

variable "ecs_security_group_id" {
  type = string
}

variable "db_username" {
  type    = string
  default = "app"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "alarms_topic_arn" {
  type    = string
  default = ""
}
