# AltWallet Checkout Agent - Terraform Variables

# General Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "altwallet-checkout-agent"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
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

# SSL Certificate Configuration
variable "create_ssl_certificate" {
  description = "Whether to create SSL certificate"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "subject_alternative_names" {
  description = "Subject alternative names for SSL certificate"
  type        = list(string)
  default     = []
}

variable "certificate_arn" {
  description = "ARN of existing SSL certificate"
  type        = string
  default     = ""
}

# Route53 Configuration
variable "create_route53_zone" {
  description = "Whether to create Route53 hosted zone"
  type        = bool
  default     = false
}

variable "route53_zone_id" {
  description = "ID of existing Route53 hosted zone"
  type        = string
  default     = ""
}

# Container Configuration
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
variable "create_sns_topic" {
  description = "Whether to create SNS topic for alerts"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

variable "alarm_sns_topic_arn" {
  description = "ARN of existing SNS topic for alarms"
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
