# AltWallet Checkout Agent - Example Terraform Configuration
# This is an example configuration for deploying the AltWallet Checkout Agent

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "AltWallet"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# VPC Configuration (if creating new VPC)
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  count = var.create_vpc ? 1 : 0

  name = "${local.name_prefix}-vpc"
  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnets  = var.public_subnet_cidrs
  private_subnets = var.private_subnet_cidrs

  enable_nat_gateway = true
  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    Type = "Public"
  }

  private_subnet_tags = {
    Type = "Private"
  }

  tags = local.common_tags
}

# SSL Certificate (if using HTTPS)
resource "aws_acm_certificate" "main" {
  count = var.create_ssl_certificate ? 1 : 0

  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = var.subject_alternative_names

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ssl-cert"
  })
}

# SSL Certificate Validation
resource "aws_acm_certificate_validation" "main" {
  count = var.create_ssl_certificate ? 1 : 0

  certificate_arn         = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]

  timeouts {
    create = "5m"
  }
}

# Route53 Hosted Zone (if creating DNS)
resource "aws_route53_zone" "main" {
  count = var.create_route53_zone ? 1 : 0

  name = var.domain_name

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-hosted-zone"
  })
}

# Route53 Records for SSL Certificate Validation
resource "aws_route53_record" "cert_validation" {
  for_each = var.create_ssl_certificate ? {
    for dvo in aws_acm_certificate.main[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : var.route53_zone_id
}

# Route53 A Record for ALB
resource "aws_route53_record" "main" {
  count = var.create_route53_zone || var.route53_zone_id != "" ? 1 : 0

  zone_id = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : var.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = module.altwallet_checkout_agent.alb_dns_name
    zone_id                = module.altwallet_checkout_agent.alb_zone_id
    evaluate_target_health = true
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  count = var.create_sns_topic ? 1 : 0

  name = "${local.name_prefix}-alerts"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alerts"
  })
}

# SNS Topic Subscription
resource "aws_sns_topic_subscription" "alerts" {
  count = var.create_sns_topic && var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# AltWallet Checkout Agent Module
module "altwallet_checkout_agent" {
  source = "./modules/altwallet-checkout-agent"

  # General Configuration
  name_prefix = local.name_prefix
  environment = var.environment
  region      = var.aws_region
  tags        = local.common_tags

  # VPC Configuration
  create_vpc              = var.create_vpc
  vpc_id                  = var.create_vpc ? null : var.vpc_id
  vpc_cidr                = var.vpc_cidr
  public_subnet_cidrs     = var.public_subnet_cidrs
  private_subnet_cidrs    = var.private_subnet_cidrs
  public_subnet_ids       = var.create_vpc ? null : var.public_subnet_ids
  private_subnet_ids      = var.create_vpc ? null : var.private_subnet_ids
  enable_nat_gateway      = true

  # Application Load Balancer Configuration
  create_alb              = true
  certificate_arn         = var.create_ssl_certificate ? aws_acm_certificate_validation.main[0].certificate_arn : var.certificate_arn
  alb_deletion_protection = var.environment == "prod"

  # ECS Configuration
  create_ecs                    = true
  container_name                = "altwallet-checkout-agent"
  container_image               = var.container_image
  container_tag                 = var.container_tag
  application_port              = 8000
  metrics_port                  = 9090
  task_cpu                      = var.task_cpu
  task_memory                   = var.task_memory
  desired_count                 = var.desired_count
  enable_container_insights     = true
  log_level                     = var.log_level
  log_retention_in_days         = var.log_retention_in_days

  # RDS Configuration
  create_rds                        = var.create_rds
  rds_engine_version                = var.rds_engine_version
  rds_instance_class                = var.rds_instance_class
  rds_allocated_storage             = var.rds_allocated_storage
  rds_max_allocated_storage         = var.rds_max_allocated_storage
  rds_database_name                 = var.rds_database_name
  rds_username                      = var.rds_username
  rds_password                      = var.rds_password
  rds_backup_retention_period       = var.rds_backup_retention_period
  rds_backup_window                 = var.rds_backup_window
  rds_maintenance_window            = var.rds_maintenance_window
  rds_skip_final_snapshot           = var.environment != "prod"
  rds_deletion_protection           = var.environment == "prod"
  rds_performance_insights_enabled  = true
  rds_monitoring_interval           = 60

  # ElastiCache Configuration
  create_elasticache                    = var.create_elasticache
  elasticache_node_type                 = var.elasticache_node_type
  elasticache_parameter_group_name      = var.elasticache_parameter_group_name
  elasticache_num_cache_nodes           = var.elasticache_num_cache_nodes
  elasticache_engine_version            = var.elasticache_engine_version
  elasticache_transit_encryption_enabled = true
  elasticache_snapshot_retention_limit  = var.elasticache_snapshot_retention_limit
  elasticache_snapshot_window           = var.elasticache_snapshot_window

  # Secrets Configuration
  create_secrets = true
  database_url   = var.database_url
  redis_url      = var.redis_url
  api_key        = var.api_key
  jwt_secret     = var.jwt_secret
  encryption_key = var.encryption_key

  # Auto Scaling Configuration
  enable_autoscaling           = var.enable_autoscaling
  min_capacity                 = var.min_capacity
  max_capacity                 = var.max_capacity
  target_cpu_utilization       = var.target_cpu_utilization
  target_memory_utilization    = var.target_memory_utilization

  # Monitoring Configuration
  enable_cloudwatch_alarms = true
  alarm_sns_topic_arn      = var.create_sns_topic ? aws_sns_topic.alerts[0].arn : var.alarm_sns_topic_arn

  # Backup Configuration
  enable_backup         = var.enable_backup
  backup_schedule       = var.backup_schedule
  backup_retention_days = var.backup_retention_days

  # Security Configuration
  enable_waf        = var.enable_waf
  waf_web_acl_arn   = var.waf_web_acl_arn

  # Cost Optimization
  enable_spot_instances = var.enable_spot_instances
  spot_percentage      = var.spot_percentage

  depends_on = [
    aws_acm_certificate_validation.main
  ]
}

# WAF Web ACL (if enabled)
resource "aws_wafv2_web_acl" "main" {
  count = var.enable_waf ? 1 : 0

  name  = "${local.name_prefix}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "KnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLiRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}WAFMetric"
    sampled_requests_enabled   = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-waf"
  })
}

# WAF Web ACL Association with ALB
resource "aws_wafv2_web_acl_association" "main" {
  count = var.enable_waf ? 1 : 0

  resource_arn = module.altwallet_checkout_agent.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.main[0].arn
}

# Backup Vault (if backup is enabled)
resource "aws_backup_vault" "main" {
  count = var.enable_backup ? 1 : 0

  name        = "${local.name_prefix}-backup-vault"
  kms_key_arn = aws_kms_key.backup[0].arn

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-backup-vault"
  })
}

# KMS Key for Backup
resource "aws_kms_key" "backup" {
  count = var.enable_backup ? 1 : 0

  description             = "KMS key for AltWallet Checkout Agent backup"
  deletion_window_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-backup-key"
  })
}

# KMS Key Alias for Backup
resource "aws_kms_alias" "backup" {
  count = var.enable_backup ? 1 : 0

  name          = "alias/${local.name_prefix}-backup"
  target_key_id = aws_kms_key.backup[0].key_id
}

# Backup Plan
resource "aws_backup_plan" "main" {
  count = var.enable_backup ? 1 : 0

  name = "${local.name_prefix}-backup-plan"

  rule {
    rule_name         = "daily_backup"
    target_vault_name = aws_backup_vault.main[0].name
    schedule          = var.backup_schedule

    lifecycle {
      cold_storage_after = 30
      delete_after       = 90
    }

    recovery_point_tags = local.common_tags
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-backup-plan"
  })
}

# Backup Selection
resource "aws_backup_selection" "main" {
  count = var.enable_backup ? 1 : 0

  iam_role_arn = aws_iam_role.backup[0].arn
  name         = "${local.name_prefix}-backup-selection"
  plan_id      = aws_backup_plan.main[0].id

  resources = [
    module.altwallet_checkout_agent.rds_instance_arn,
    module.altwallet_checkout_agent.elasticache_replication_group_arn
  ]
}

# Backup IAM Role
resource "aws_iam_role" "backup" {
  count = var.enable_backup ? 1 : 0

  name = "${local.name_prefix}-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-backup-role"
  })
}

# Backup IAM Role Policy
resource "aws_iam_role_policy_attachment" "backup" {
  count = var.enable_backup ? 1 : 0

  role       = aws_iam_role.backup[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}
