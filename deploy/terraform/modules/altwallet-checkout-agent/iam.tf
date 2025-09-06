# IAM Roles and Policies for AltWallet Checkout Agent

# Data sources
data "aws_region" "current" {}

# ECS Execution Role
resource "aws_iam_role" "ecs_execution" {
  count = var.create_ecs ? 1 : 0

  name = "${var.name_prefix}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-ecs-execution-role"
  })
}

# ECS Execution Role Policy
resource "aws_iam_role_policy_attachment" "ecs_execution" {
  count = var.create_ecs ? 1 : 0

  role       = aws_iam_role.ecs_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Execution Role Policy for Secrets Manager
resource "aws_iam_role_policy" "ecs_execution_secrets" {
  count = var.create_ecs && var.create_secrets ? 1 : 0

  name = "${var.name_prefix}-ecs-execution-secrets-policy"
  role = aws_iam_role.ecs_execution[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.database_url[0].arn,
          aws_secretsmanager_secret.redis_url[0].arn,
          aws_secretsmanager_secret.api_key[0].arn,
          aws_secretsmanager_secret.jwt_secret[0].arn,
          aws_secretsmanager_secret.encryption_key[0].arn
        ]
      }
    ]
  })
}

# ECS Task Role
resource "aws_iam_role" "ecs_task" {
  count = var.create_ecs ? 1 : 0

  name = "${var.name_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-ecs-task-role"
  })
}

# ECS Task Role Policy for CloudWatch Logs
resource "aws_iam_role_policy" "ecs_task_logs" {
  count = var.create_ecs ? 1 : 0

  name = "${var.name_prefix}-ecs-task-logs-policy"
  role = aws_iam_role.ecs_task[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.main[0].arn}:*"
        ]
      }
    ]
  })
}

# ECS Task Role Policy for Secrets Manager
resource "aws_iam_role_policy" "ecs_task_secrets" {
  count = var.create_ecs && var.create_secrets ? 1 : 0

  name = "${var.name_prefix}-ecs-task-secrets-policy"
  role = aws_iam_role.ecs_task[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.database_url[0].arn,
          aws_secretsmanager_secret.redis_url[0].arn,
          aws_secretsmanager_secret.api_key[0].arn,
          aws_secretsmanager_secret.jwt_secret[0].arn,
          aws_secretsmanager_secret.encryption_key[0].arn
        ]
      }
    ]
  })
}

# ECS Task Role Policy for RDS
resource "aws_iam_role_policy" "ecs_task_rds" {
  count = var.create_ecs && var.create_rds ? 1 : 0

  name = "${var.name_prefix}-ecs-task-rds-policy"
  role = aws_iam_role.ecs_task[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-db:connect"
        ]
        Resource = [
          "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_db_instance.main[0].id}/${var.rds_username}"
        ]
      }
    ]
  })
}

# ECS Task Role Policy for ElastiCache
resource "aws_iam_role_policy" "ecs_task_elasticache" {
  count = var.create_ecs && var.create_elasticache ? 1 : 0

  name = "${var.name_prefix}-ecs-task-elasticache-policy"
  role = aws_iam_role.ecs_task[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticache:DescribeCacheClusters",
          "elasticache:DescribeReplicationGroups"
        ]
        Resource = [
          aws_elasticache_replication_group.main[0].arn
        ]
      }
    ]
  })
}

# ECS Task Role Policy for X-Ray (if enabled)
resource "aws_iam_role_policy" "ecs_task_xray" {
  count = var.create_ecs ? 1 : 0

  name = "${var.name_prefix}-ecs-task-xray-policy"
  role = aws_iam_role.ecs_task[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

# RDS Enhanced Monitoring Role
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.create_rds && var.rds_monitoring_interval > 0 ? 1 : 0

  name = "${var.name_prefix}-rds-enhanced-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rds-enhanced-monitoring-role"
  })
}

# RDS Enhanced Monitoring Role Policy
resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count = var.create_rds && var.rds_monitoring_interval > 0 ? 1 : 0

  role       = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Auto Scaling Role
resource "aws_iam_role" "autoscaling" {
  count = var.create_ecs && var.enable_autoscaling ? 1 : 0

  name = "${var.name_prefix}-autoscaling-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "application-autoscaling.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-autoscaling-role"
  })
}

# Auto Scaling Role Policy
resource "aws_iam_role_policy_attachment" "autoscaling" {
  count = var.create_ecs && var.enable_autoscaling ? 1 : 0

  role       = aws_iam_role.autoscaling[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceAutoscaleRole"
}

# Backup Role (if backup is enabled)
resource "aws_iam_role" "backup" {
  count = var.enable_backup ? 1 : 0

  name = "${var.name_prefix}-backup-role"

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

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backup-role"
  })
}

# Backup Role Policy
resource "aws_iam_role_policy" "backup" {
  count = var.enable_backup ? 1 : 0

  name = "${var.name_prefix}-backup-policy"
  role = aws_iam_role.backup[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeClusters",
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:ListTasks",
          "ecs:DescribeTasks",
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "elasticache:DescribeReplicationGroups",
          "elasticache:DescribeCacheClusters",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      }
    ]
  })
}

# WAF Role (if WAF is enabled)
resource "aws_iam_role" "waf" {
  count = var.enable_waf ? 1 : 0

  name = "${var.name_prefix}-waf-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "wafv2.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-waf-role"
  })
}

# WAF Role Policy
resource "aws_iam_role_policy" "waf" {
  count = var.enable_waf ? 1 : 0

  name = "${var.name_prefix}-waf-policy"
  role = aws_iam_role.waf[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "wafv2:GetWebACL",
          "wafv2:GetWebACLForResource",
          "wafv2:AssociateWebACL",
          "wafv2:DisassociateWebACL",
          "wafv2:ListResourcesForWebACL"
        ]
        Resource = "*"
      }
    ]
  })
}
