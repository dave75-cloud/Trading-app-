

output "alarms_topic_arn" { value = aws_sns_topic.alarms.arn }
output "alb_dns_name" { value = aws_lb.alb.dns_name }
