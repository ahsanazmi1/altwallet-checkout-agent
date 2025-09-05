# AltWallet Checkout Agent Terraform Module Outputs

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = var.create_vpc ? aws_vpc.main[0].cidr_block : null
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = var.create_vpc ? aws_subnet.public[*].id : var.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = var.create_vpc ? aws_subnet.private[*].id : var.private_subnet_ids
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = var.create_vpc ? aws_internet_gateway.main[0].id : null
}

output "nat_gateway_ids" {
  description = "IDs of the NAT Gateways"
  value       = var.create_vpc && var.enable_nat_gateway ? aws_nat_gateway.main[*].id : []
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = var.create_alb ? aws_security_group.alb[0].id : null
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = var.create_ecs ? aws_security_group.ecs[0].id : null
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = var.create_rds ? aws_security_group.rds[0].id : null
}

output "elasticache_security_group_id" {
  description = "ID of the ElastiCache security group"
  value       = var.create_elasticache ? aws_security_group.elasticache[0].id : null
}

# Application Load Balancer Outputs
output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = var.create_alb ? aws_lb.main[0].arn : null
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = var.create_alb ? aws_lb.main[0].dns_name : null
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = var.create_alb ? aws_lb.main[0].zone_id : null
}

output "alb_target_group_arn" {
  description = "ARN of the ALB target group"
  value       = var.create_alb ? aws_lb_target_group.main[0].arn : null
}

output "alb_https_listener_arn" {
  description = "ARN of the HTTPS listener"
  value       = var.create_alb && var.certificate_arn != "" ? aws_lb_listener.https[0].arn : null
}

# ECS Outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = var.create_ecs ? aws_ecs_cluster.main[0].id : null
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = var.create_ecs ? aws_ecs_cluster.main[0].arn : null
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = var.create_ecs ? aws_ecs_cluster.main[0].name : null
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = var.create_ecs ? aws_ecs_task_definition.main[0].arn : null
}

output "ecs_task_definition_family" {
  description = "Family of the ECS task definition"
  value       = var.create_ecs ? aws_ecs_task_definition.main[0].family : null
}

output "ecs_task_definition_revision" {
  description = "Revision of the ECS task definition"
  value       = var.create_ecs ? aws_ecs_task_definition.main[0].revision : null
}

output "ecs_service_id" {
  description = "ID of the ECS service"
  value       = var.create_ecs ? aws_ecs_service.main[0].id : null
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = var.create_ecs ? aws_ecs_service.main[0].name : null
}

# RDS Outputs
output "rds_instance_id" {
  description = "ID of the RDS instance"
  value       = var.create_rds ? aws_db_instance.main[0].id : null
}

output "rds_instance_arn" {
  description = "ARN of the RDS instance"
  value       = var.create_rds ? aws_db_instance.main[0].arn : null
}

output "rds_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = var.create_rds ? aws_db_instance.main[0].endpoint : null
}

output "rds_instance_hosted_zone_id" {
  description = "RDS instance hosted zone ID"
  value       = var.create_rds ? aws_db_instance.main[0].hosted_zone_id : null
}

output "rds_instance_port" {
  description = "RDS instance port"
  value       = var.create_rds ? aws_db_instance.main[0].port : null
}

output "rds_instance_username" {
  description = "RDS instance master username"
  value       = var.create_rds ? aws_db_instance.main[0].username : null
}

output "rds_instance_database_name" {
  description = "RDS instance database name"
  value       = var.create_rds ? aws_db_instance.main[0].db_name : null
}

# ElastiCache Outputs
output "elasticache_replication_group_id" {
  description = "ID of the ElastiCache replication group"
  value       = var.create_elasticache ? aws_elasticache_replication_group.main[0].id : null
}

output "elasticache_replication_group_arn" {
  description = "ARN of the ElastiCache replication group"
  value       = var.create_elasticache ? aws_elasticache_replication_group.main[0].arn : null
}

output "elasticache_primary_endpoint" {
  description = "ElastiCache primary endpoint"
  value       = var.create_elasticache ? aws_elasticache_replication_group.main[0].primary_endpoint_address : null
}

output "elasticache_reader_endpoint" {
  description = "ElastiCache reader endpoint"
  value       = var.create_elasticache ? aws_elasticache_replication_group.main[0].reader_endpoint_address : null
}

output "elasticache_configuration_endpoint" {
  description = "ElastiCache configuration endpoint"
  value       = var.create_elasticache ? aws_elasticache_replication_group.main[0].configuration_endpoint_address : null
}

# CloudWatch Outputs
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = var.create_ecs ? aws_cloudwatch_log_group.main[0].name : null
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = var.create_ecs ? aws_cloudwatch_log_group.main[0].arn : null
}

# Secrets Manager Outputs
output "secrets_manager_database_url_arn" {
  description = "ARN of the database URL secret"
  value       = var.create_secrets ? aws_secretsmanager_secret.database_url[0].arn : null
}

output "secrets_manager_redis_url_arn" {
  description = "ARN of the Redis URL secret"
  value       = var.create_secrets ? aws_secretsmanager_secret.redis_url[0].arn : null
}

output "secrets_manager_api_key_arn" {
  description = "ARN of the API key secret"
  value       = var.create_secrets ? aws_secretsmanager_secret.api_key[0].arn : null
}

output "secrets_manager_jwt_secret_arn" {
  description = "ARN of the JWT secret"
  value       = var.create_secrets ? aws_secretsmanager_secret.jwt_secret[0].arn : null
}

output "secrets_manager_encryption_key_arn" {
  description = "ARN of the encryption key secret"
  value       = var.create_secrets ? aws_secretsmanager_secret.encryption_key[0].arn : null
}

# IAM Role Outputs
output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = var.create_ecs ? aws_iam_role.ecs_execution[0].arn : null
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = var.create_ecs ? aws_iam_role.ecs_task[0].arn : null
}

# Application URLs
output "application_url" {
  description = "URL of the application"
  value       = var.create_alb ? "https://${aws_lb.main[0].dns_name}" : null
}

output "application_url_http" {
  description = "HTTP URL of the application"
  value       = var.create_alb ? "http://${aws_lb.main[0].dns_name}" : null
}

# Health Check Endpoints
output "health_check_url" {
  description = "Health check endpoint URL"
  value       = var.create_alb ? "https://${aws_lb.main[0].dns_name}/health" : null
}

output "metrics_url" {
  description = "Metrics endpoint URL"
  value       = var.create_alb ? "https://${aws_lb.main[0].dns_name}/metrics" : null
}

# Connection Information
output "database_connection_info" {
  description = "Database connection information"
  value = var.create_rds ? {
    endpoint = aws_db_instance.main[0].endpoint
    port     = aws_db_instance.main[0].port
    database = aws_db_instance.main[0].db_name
    username = aws_db_instance.main[0].username
  } : null
  sensitive = true
}

output "redis_connection_info" {
  description = "Redis connection information"
  value = var.create_elasticache ? {
    primary_endpoint = aws_elasticache_replication_group.main[0].primary_endpoint_address
    reader_endpoint  = aws_elasticache_replication_group.main[0].reader_endpoint_address
    port             = aws_elasticache_replication_group.main[0].port
  } : null
  sensitive = true
}

# Resource Summary
output "resource_summary" {
  description = "Summary of created resources"
  value = {
    vpc_created           = var.create_vpc
    alb_created           = var.create_alb
    ecs_created           = var.create_ecs
    rds_created           = var.create_rds
    elasticache_created   = var.create_elasticache
    secrets_created       = var.create_secrets
    application_url       = var.create_alb ? "https://${aws_lb.main[0].dns_name}" : null
    ecs_cluster_name      = var.create_ecs ? aws_ecs_cluster.main[0].name : null
    database_endpoint     = var.create_rds ? aws_db_instance.main[0].endpoint : null
    redis_endpoint        = var.create_elasticache ? aws_elasticache_replication_group.main[0].primary_endpoint_address : null
  }
}
