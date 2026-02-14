#!/usr/bin/env bash
set -euo pipefail

echo "Terraform init/validate/plan (NO APPLY)"
terraform init
terraform fmt -check
terraform validate

echo ""
echo "Now run terraform plan with your variables. Example:"
echo "  terraform plan -var='api_image=...:latest' -var='dashboard_image=...:latest' -var='broker_image=ignored' -var='vpc_id=vpc-...' -var='public_subnets=["subnet-...","subnet-..."]' -var='private_subnets=["subnet-...","subnet-..."]' -var='ecs_security_group=sg-...' -var='alb_security_group=sg-...'"
