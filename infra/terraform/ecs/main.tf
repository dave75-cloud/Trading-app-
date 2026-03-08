╷
│ Error: Duplicate local value definition
│ 
│   on ecs/main.tf line 102, in locals:
│  102:   api_secrets = concat(
│  103:     [{ name = "DB_URL", valueFrom = var.db_url_secret_arn }],
│  104:     var.polygon_api_key_secret_arn != "" ? [{ name = "POLYGON_API_KEY", valueFrom = var.polygon_api_key_secret_arn }] : []
│  105:   )
│ 
│ A local value named "api_secrets" was already defined at
│ ecs/main.tf:10,3-29,4. Local value names must be unique within a module.
╵

╷
│ Error: Duplicate local value definition
│ 
│   on ecs/main.tf line 107, in locals:
│  107:   runner_secrets = concat(
│  108:     [{ name = "DB_URL", valueFrom = var.db_url_secret_arn }],
│  109:     var.polygon_api_key_secret_arn != "" ? [{ name = "POLYGON_API_KEY", valueFrom = var.polygon_api_key_secret_arn }] : [],
│  110:     var.slack_webhook_url_secret_arn != "" ? [{ name = "SLACK_WEBHOOK_URL", valueFrom = var.slack_webhook_url_secret_arn }] : []
│  111:   )
│ 
│ A local value named "runner_secrets" was already defined at
│ ecs/main.tf:31,3-37. Local value names must be unique within a module.
╵

╷
│ Error: Duplicate resource "aws_ecs_cluster" configuration
│ 
│   on ecs/main.tf line 114:
│  114: resource "aws_ecs_cluster" "this" {
│ 
│ A aws_ecs_cluster resource named "this" was already declared at
│ ecs/main.tf:34,1-34. Resource names must be unique per type in each module.
╵

╷
│ Error: Duplicate resource "aws_iam_role" configuration
│ 
│   on ecs/main.tf line 119:
│  119: resource "aws_iam_role" "task_execution" {
│ 
│ A aws_iam_role resource named "task_execution" was already declared at
│ ecs/main.tf:39,1-41. Resource names must be unique per type in each module.
╵

╷
│ Error: Duplicate resource "aws_iam_role_policy_attachment" configuration
│ 
│   on ecs/main.tf line 131:
│  131: resource "aws_iam_role_policy_attachment" "task_execution" {
│ 
│ A aws_iam_role_policy_attachment resource named "task_execution" was
│ already declared at ecs/main.tf:51,1-59. Resource names must be unique per
│ type in each module.
╵

╷
│ Error: Duplicate resource "aws_iam_role" configuration
│ 
│   on ecs/main.tf line 136:
│  136: resource "aws_iam_role" "task" {
│ 
│ A aws_iam_role resource named "task" was already declared at
│ ecs/main.tf:56,1-31. Resource names must be unique per type in each module.
╵

╷
│ Error: Duplicate resource "aws_iam_role_policy" configuration
│ 
│   on ecs/main.tf line 149:
│  149: resource "aws_iam_role_policy" "task" {
│ 
│ A aws_iam_role_policy resource named "task" was already declared at
│ ecs/main.tf:68,1-38. Resource names must be unique per type in each module.
╵

╷
│ Error: Argument or block definition required
│ 
│   on ecs/main.tf line 212:
│  212:       {
│ 
│ An argument or block definition is required here.
╵

Error: Terraform exited with code 1.
Error: Process completed with exit code 1.
