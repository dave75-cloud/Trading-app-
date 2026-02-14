# Terraform — Signal Dashboard Deployment (AWS)

Resources:
- S3 bucket (optional data bucket)
- RDS Postgres (signal history)
- ECS Fargate cluster + services:
  - inference API (FastAPI)
  - dashboard (Streamlit)
  - scheduled runner (EventBridge → ECS RunTask)
- Public ALB with path-based routing (dashboard default; API paths forwarded)

## Usage
See `variables.tf` for required inputs (VPC, subnets, SGs, images).

### Plan (no apply)
```bash
terraform init
terraform fmt -check
terraform validate

# Provide your built image URIs and networking inputs:
terraform plan \
  -var='api_image=...ecr...:api' \
  -var='dashboard_image=...ecr...:api' \
  -var='broker_image=...ignored' \
  -var='vpc_id=vpc-...' \
  -var='public_subnets=["subnet-...","subnet-..."]' \
  -var='private_subnets=["subnet-...","subnet-..."]' \
  -var='ecs_security_group=sg-...' \
  -var='alb_security_group=sg-...' \
  -var='polygon_api_key=...optional...' \
  -var='slack_webhook_url=...optional...' \
  -var='signal_cron=rate(30 minutes)'
```

### Migration
After RDS exists and DB_URL is known:
```bash
export DB_PATH=./data/app.db
export DB_URL='postgresql://...'
python cli/migrate_sqlite_to_postgres.py
```


## Secrets Manager (recommended)
This stack injects runtime secrets into ECS tasks via **AWS Secrets Manager** (not plain environment variables).

You have two options:

### Option A (recommended): manage secrets outside Terraform
1) Create these Secrets Manager secrets (string values):
- `${project}/db_url` (e.g. `postgresql://user:pass@host:5432/signals`)
- `${project}/polygon_api_key` (optional)
- `${project}/slack_webhook_url` (optional)

2) Plan/apply with:
- `-var='create_secrets=false'`
- `-var='db_url_secret_arn=arn:aws:secretsmanager:...:secret:...'`
- (optional) `-var='polygon_api_key_secret_arn=...'`
- (optional) `-var='slack_webhook_url_secret_arn=...'`

### Option B: let Terraform create secrets (convenience, not ideal long-term)
Pass `polygon_api_key` / `slack_webhook_url` values and keep `create_secrets=true`.
Note: secret values will still be stored in Terraform state, so prefer Option A for production.

## Alarms
The ECS module creates:
- ALB 5xx alarm
- API CPU and memory alarms
- API log-based alarm for lines matching `"ERROR"`
All alarms publish to an SNS topic output `alarms_topic_arn`.

Optionally set `-var='alarm_email=you@example.com'` to create an email subscription (you must confirm the subscription email).

## Plain-English: what all this does

- **ECS/Fargate**: runs your API + dashboard containers (serverless containers).
- **ALB (load balancer)**: gives you one public URL and routes `/signals/*` etc to the API.
- **RDS Postgres**: stores signal history (so you can chart and evaluate).
- **Secrets Manager**: stores passwords/API keys so they are not hard-coded.
- **KMS key**: encrypts those secrets with your own AWS-managed encryption key (safer default).
- **Access logs**: the load balancer writes request logs to S3 so you can debug "who hit what".
- **Alarms**: CloudWatch watches for errors/5xx/high CPU and emails you.

You don't need to understand the AWS internals to use it: you mainly do **plan**, then (when happy) **apply**.
