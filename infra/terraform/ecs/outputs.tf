output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "cluster_arn" {
  value = aws_ecs_cluster.this.arn
}

output "alb_dns_name" {
  value = aws_lb.alb.dns_name
}

output "alb_arn" {
  value = aws_lb.alb.arn
}

output "alb_listener_arn" {
  value = aws_lb_listener.http.arn
}

output "api_target_group_arn" {
  value = aws_lb_target_group.api.arn
}

output "dashboard_target_group_arn" {
  value = aws_lb_target_group.dashboard.arn
}

output "api_service_name" {
  value = aws_ecs_service.api.name
}

output "dashboard_service_name" {
  value = aws_ecs_service.dashboard.name
}

output "alarms_topic_arn" {
  value = aws_sns_topic.alarms.arn
}

