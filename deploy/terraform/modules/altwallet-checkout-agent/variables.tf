# AltWallet Checkout Agent Terraform Module Variables

# General Configuration
variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "altwallet-checkout-agent"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "AltWallet"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

# VPC Configuration
variable "create_vpc" {
  description = "Whether to create a new VPC"
  type        = bool
  default     = true
}

variable "vpc_id" {
  description = "ID of existing VPC to use (if not creating new VPC)"
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "public_subnet_ids" {
  description = "IDs of existing public subnets (if not creating new VPC)"
  type        = list(string)
  default     = []
}

variable "private_subnet_ids" {
  description = "IDs of existing private subnets (if not creating new VPC)"
  type        = list(string)
  default     = []
}

variable "enable_nat_gateway" {
  description = "Whether to enable NAT Gateway"
  type        = bool
  default     = true
}

# Application Load Balancer Configuration
variable "create_alb" {
  description = "Whether to create Application Load Balancer"
  type        = bool
  default     = true
}

variable "certificate_arn" {
  description = "ARN of SSL certificate for HTTPS"
  type        = string
  default     = ""
}

variable "alb_deletion_protection" {
  description = "Enable deletion protection for ALB"
  type        = bool
  default     = false
}

# ECS Configuration
variable "create_ecs" {
  description = "Whether to create ECS resources"
  type        = bool
  default     = true
}

variable "container_name" {
  description = "Name of the container"
  type        = string
  default     = "altwallet-checkout-agent"
}

variable "container_image" {
  description = "Container image repository"
  type        = string
  default     = "altwallet/checkout-agent"
}

variable "container_tag" {
  description = "Container image tag"
  type        = string
  default     = "1.0.0"
}

variable "application_port" {
  description = "Application port"
  type        = number
  default     = 8000
}

variable "metrics_port" {
  description = "Metrics port"
  type        = number
  default     = 9090
}

variable "task_cpu" {
  description = "CPU units for ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Memory for ECS task in MiB"
  type        = number
  default     = 2048
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "enable_container_insights" {
  description = "Enable ECS Container Insights"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARN", "ERROR"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARN, ERROR."
  }
}

variable "log_retention_in_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# RDS Configuration
variable "create_rds" {
  description = "Whether to create RDS database"
  type        = bool
  default     = true
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_database_name" {
  description = "RDS database name"
  type        = string
  default     = "altwallet"
}

variable "rds_username" {
  description = "RDS master username"
  type        = string
  default     = "altwallet"
}

variable "rds_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "rds_backup_retention_period" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 7
}

variable "rds_backup_window" {
  description = "RDS backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "rds_maintenance_window" {
  description = "RDS maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "rds_skip_final_snapshot" {
  description = "Skip final snapshot when deleting RDS"
  type        = bool
  default     = false
}

variable "rds_deletion_protection" {
  description = "Enable deletion protection for RDS"
  type        = bool
  default     = true
}

variable "rds_performance_insights_enabled" {
  description = "Enable Performance Insights for RDS"
  type        = bool
  default     = true
}

variable "rds_monitoring_interval" {
  description = "RDS monitoring interval in seconds (0 to disable)"
  type        = number
  default     = 60
}

# ElastiCache Configuration
variable "create_elasticache" {
  description = "Whether to create ElastiCache Redis"
  type        = bool
  default     = true
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "elasticache_parameter_group_name" {
  description = "ElastiCache parameter group name"
  type        = string
  default     = "default.redis7"
}

variable "elasticache_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}

variable "elasticache_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "elasticache_transit_encryption_enabled" {
  description = "Enable transit encryption for ElastiCache"
  type        = bool
  default     = true
}

variable "elasticache_snapshot_retention_limit" {
  description = "ElastiCache snapshot retention limit in days"
  type        = number
  default     = 5
}

variable "elasticache_snapshot_window" {
  description = "ElastiCache snapshot window"
  type        = string
  default     = "03:00-05:00"
}

# Secrets Configuration
variable "create_secrets" {
  description = "Whether to create Secrets Manager secrets"
  type        = bool
  default     = true
}

variable "database_url" {
  description = "External database URL (if not creating RDS)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "redis_url" {
  description = "External Redis URL (if not creating ElastiCache)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "api_key" {
  description = "API key for the application"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret for the application"
  type        = string
  sensitive   = true
}

variable "encryption_key" {
  description = "Encryption key for the application"
  type        = string
  sensitive   = true
}

# Auto Scaling Configuration
variable "enable_autoscaling" {
  description = "Enable ECS service auto scaling"
  type        = bool
  default     = false
}

variable "min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 10
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

variable "target_memory_utilization" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80
}

# Monitoring Configuration
variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  type        = string
  default     = ""
}

# Backup Configuration
variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = false
}

variable "backup_schedule" {
  description = "Backup schedule (cron expression)"
  type        = string
  default     = "0 2 * * *"
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

# Security Configuration
variable "enable_waf" {
  description = "Enable AWS WAF for ALB"
  type        = bool
  default     = false
}

variable "waf_web_acl_arn" {
  description = "ARN of WAF Web ACL to associate with ALB"
  type        = string
  default     = ""
}

# Cost Optimization
variable "enable_spot_instances" {
  description = "Enable Fargate Spot for cost optimization"
  type        = bool
  default     = false
}

variable "spot_percentage" {
  description = "Percentage of tasks to run on Fargate Spot"
  type        = number
  default     = 50
  validation {
    condition     = var.spot_percentage >= 0 && var.spot_percentage <= 100
    error_message = "Spot percentage must be between 0 and 100."
  }
}
