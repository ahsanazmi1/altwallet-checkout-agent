# AltWallet Checkout Agent - Terraform Outputs

# Application URLs
output "application_url" {
  description = "URL of the application"
  value       = module.altwallet_checkout_agent.application_url
}

output "application_url_http" {
  description = "HTTP URL of the application"
  value       = module.altwallet_checkout_agent.application_url_http
}

output "health_check_url" {
  description = "Health check endpoint URL"
  value       = module.altwallet_checkout_agent.health_check_url
}

output "metrics_url" {
  description = "Metrics endpoint URL"
  value       = module.altwallet_checkout_agent.metrics_url
}

# Load Balancer Information
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.altwallet_checkout_agent.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = module.altwallet_checkout_agent.alb_zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.altwallet_checkout_agent.alb_arn
}

# ECS Information
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.altwallet_checkout_agent.ecs_cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.altwallet_checkout_agent.ecs_cluster_arn
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.altwallet_checkout_agent.ecs_service_name
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = module.altwallet_checkout_agent.ecs_task_definition_arn
}

# Database Information
output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.altwallet_checkout_agent.database_endpoint
}

output "database_port" {
  description = "RDS instance port"
  value       = module.altwallet_checkout_agent.rds_instance_port
}

output "database_name" {
  description = "RDS instance database name"
  value       = module.altwallet_checkout_agent.rds_instance_database_name
}

# Redis Information
output "redis_endpoint" {
  description = "ElastiCache primary endpoint"
  value       = module.altwallet_checkout_agent.redis_endpoint
}

output "redis_reader_endpoint" {
  description = "ElastiCache reader endpoint"
  value       = module.altwallet_checkout_agent.elasticache_reader_endpoint
}

output "redis_port" {
  description = "ElastiCache port"
  value       = 6379
}

# VPC Information
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.altwallet_checkout_agent.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.altwallet_checkout_agent.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.altwallet_checkout_agent.private_subnet_ids
}

# Security Groups
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = module.altwallet_checkout_agent.alb_security_group_id
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = module.altwallet_checkout_agent.ecs_security_group_id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = module.altwallet_checkout_agent.rds_security_group_id
}

output "elasticache_security_group_id" {
  description = "ID of the ElastiCache security group"
  value       = module.altwallet_checkout_agent.elasticache_security_group_id
}

# Secrets Manager
output "secrets_manager_database_url_arn" {
  description = "ARN of the database URL secret"
  value       = module.altwallet_checkout_agent.secrets_manager_database_url_arn
}

output "secrets_manager_redis_url_arn" {
  description = "ARN of the Redis URL secret"
  value       = module.altwallet_checkout_agent.secrets_manager_redis_url_arn
}

output "secrets_manager_api_key_arn" {
  description = "ARN of the API key secret"
  value       = module.altwallet_checkout_agent.secrets_manager_api_key_arn
}

# CloudWatch
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.altwallet_checkout_agent.cloudwatch_log_group_name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = module.altwallet_checkout_agent.cloudwatch_log_group_arn
}

# SSL Certificate
output "ssl_certificate_arn" {
  description = "ARN of the SSL certificate"
  value       = var.create_ssl_certificate ? aws_acm_certificate_validation.main[0].certificate_arn : null
}

# Route53
output "route53_zone_id" {
  description = "ID of the Route53 hosted zone"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : null
}

output "route53_name_servers" {
  description = "Name servers of the Route53 hosted zone"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].name_servers : null
}

# SNS
output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = var.create_sns_topic ? aws_sns_topic.alerts[0].arn : null
}

# WAF
output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].arn : null
}

# Backup
output "backup_vault_arn" {
  description = "ARN of the backup vault"
  value       = var.enable_backup ? aws_backup_vault.main[0].arn : null
}

output "backup_plan_arn" {
  description = "ARN of the backup plan"
  value       = var.enable_backup ? aws_backup_plan.main[0].arn : null
}

# Resource Summary
output "resource_summary" {
  description = "Summary of created resources"
  value       = module.altwallet_checkout_agent.resource_summary
}

# Connection Information (Sensitive)
output "database_connection_info" {
  description = "Database connection information"
  value       = module.altwallet_checkout_agent.database_connection_info
  sensitive   = true
}

output "redis_connection_info" {
  description = "Redis connection information"
  value       = module.altwallet_checkout_agent.redis_connection_info
  sensitive   = true
}

# Deployment Information
output "deployment_info" {
  description = "Deployment information"
  value = {
    environment        = var.environment
    region            = var.aws_region
    application_url   = module.altwallet_checkout_agent.application_url
    health_check_url  = module.altwallet_checkout_agent.health_check_url
    metrics_url       = module.altwallet_checkout_agent.metrics_url
    ecs_cluster_name  = module.altwallet_checkout_agent.ecs_cluster_name
    database_endpoint = module.altwallet_checkout_agent.database_endpoint
    redis_endpoint    = module.altwallet_checkout_agent.redis_endpoint
  }
}
