# AltWallet Checkout Agent Terraform Module
# This module deploys the AltWallet Checkout Agent infrastructure

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Configuration
resource "aws_vpc" "main" {
  count = var.create_vpc ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = var.create_vpc ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-igw"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = var.create_vpc ? length(var.public_subnet_cidrs) : 0

  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-subnet-${count.index + 1}"
    Type = "Public"
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = var.create_vpc ? length(var.private_subnet_cidrs) : 0

  vpc_id            = aws_vpc.main[0].id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-subnet-${count.index + 1}"
    Type = "Private"
  })
}

# NAT Gateways
resource "aws_eip" "nat" {
  count = var.create_vpc && var.enable_nat_gateway ? length(var.public_subnet_cidrs) : 0

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-eip-${count.index + 1}"
  })
}

resource "aws_nat_gateway" "main" {
  count = var.create_vpc && var.enable_nat_gateway ? length(var.public_subnet_cidrs) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-gateway-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  count = var.create_vpc ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-rt"
  })
}

resource "aws_route_table" "private" {
  count = var.create_vpc && var.enable_nat_gateway ? length(var.private_subnet_cidrs) : 0

  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-rt-${count.index + 1}"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = var.create_vpc ? length(var.public_subnet_cidrs) : 0

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "private" {
  count = var.create_vpc && var.enable_nat_gateway ? length(var.private_subnet_cidrs) : 0

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Groups
resource "aws_security_group" "alb" {
  count = var.create_alb ? 1 : 0

  name_prefix = "${var.name_prefix}-alb-"
  vpc_id      = var.vpc_id != "" ? var.vpc_id : aws_vpc.main[0].id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "ecs" {
  count = var.create_ecs ? 1 : 0

  name_prefix = "${var.name_prefix}-ecs-"
  vpc_id      = var.vpc_id != "" ? var.vpc_id : aws_vpc.main[0].id

  ingress {
    description     = "Application Port"
    from_port       = var.application_port
    to_port         = var.application_port
    protocol        = "tcp"
    security_groups = var.create_alb ? [aws_security_group.alb[0].id] : []
  }

  ingress {
    description     = "Metrics Port"
    from_port       = var.metrics_port
    to_port         = var.metrics_port
    protocol        = "tcp"
    security_groups = var.create_alb ? [aws_security_group.alb[0].id] : []
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-ecs-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "rds" {
  count = var.create_rds ? 1 : 0

  name_prefix = "${var.name_prefix}-rds-"
  vpc_id      = var.vpc_id != "" ? var.vpc_id : aws_vpc.main[0].id

  ingress {
    description     = "PostgreSQL"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.create_ecs ? [aws_security_group.ecs[0].id] : []
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rds-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "elasticache" {
  count = var.create_elasticache ? 1 : 0

  name_prefix = "${var.name_prefix}-elasticache-"
  vpc_id      = var.vpc_id != "" ? var.vpc_id : aws_vpc.main[0].id

  ingress {
    description     = "Redis"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.create_ecs ? [aws_security_group.ecs[0].id] : []
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-elasticache-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  count = var.create_alb ? 1 : 0

  name               = "${var.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = var.vpc_id != "" ? var.public_subnet_ids : aws_subnet.public[*].id

  enable_deletion_protection = var.alb_deletion_protection

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb"
  })
}

resource "aws_lb_target_group" "main" {
  count = var.create_alb ? 1 : 0

  name        = "${var.name_prefix}-tg"
  port        = var.application_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id != "" ? var.vpc_id : aws_vpc.main[0].id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-tg"
  })
}

resource "aws_lb_listener" "http" {
  count = var.create_alb ? 1 : 0

  load_balancer_arn = aws_lb.main[0].arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  count = var.create_alb && var.certificate_arn != "" ? 1 : 0

  load_balancer_arn = aws_lb.main[0].arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main[0].arn
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  count = var.create_ecs ? 1 : 0

  name = "${var.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cluster"
  })
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  count = var.create_ecs ? 1 : 0

  cluster_name = aws_ecs_cluster.main[0].name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  count = var.create_ecs ? 1 : 0

  family                   = "${var.name_prefix}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution[0].arn
  task_role_arn            = aws_iam_role.ecs_task[0].arn

  container_definitions = jsonencode([
    {
      name  = var.container_name
      image = "${var.container_image}:${var.container_tag}"
      
      portMappings = [
        {
          containerPort = var.application_port
          protocol      = "tcp"
        },
        {
          containerPort = var.metrics_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "LOG_LEVEL"
          value = var.log_level
        },
        {
          name  = "LOG_FORMAT"
          value = "json"
        },
        {
          name  = "PORT"
          value = tostring(var.application_port)
        },
        {
          name  = "HOST"
          value = "0.0.0.0"
        },
        {
          name  = "ENABLE_METRICS"
          value = "true"
        },
        {
          name  = "METRICS_PORT"
          value = tostring(var.metrics_port)
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.database_url[0].arn
        },
        {
          name      = "REDIS_URL"
          valueFrom = aws_secretsmanager_secret.redis_url[0].arn
        },
        {
          name      = "API_KEY"
          valueFrom = aws_secretsmanager_secret.api_key[0].arn
        },
        {
          name      = "JWT_SECRET"
          valueFrom = aws_secretsmanager_secret.jwt_secret[0].arn
        },
        {
          name      = "ENCRYPTION_KEY"
          valueFrom = aws_secretsmanager_secret.encryption_key[0].arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.main[0].name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.application_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-task"
  })
}

# ECS Service
resource "aws_ecs_service" "main" {
  count = var.create_ecs ? 1 : 0

  name            = "${var.name_prefix}-service"
  cluster         = aws_ecs_cluster.main[0].id
  task_definition = aws_ecs_task_definition.main[0].arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs[0].id]
    subnets          = var.vpc_id != "" ? var.private_subnet_ids : aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.create_alb ? aws_lb_target_group.main[0].arn : null
    container_name   = var.container_name
    container_port   = var.application_port
  }

  depends_on = [
    aws_lb_listener.https,
    aws_iam_role_policy_attachment.ecs_execution
  ]

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-service"
  })
}

# RDS Database
resource "aws_db_subnet_group" "main" {
  count = var.create_rds ? 1 : 0

  name       = "${var.name_prefix}-db-subnet-group"
  subnet_ids = var.vpc_id != "" ? var.private_subnet_ids : aws_subnet.private[*].id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-subnet-group"
  })
}

resource "aws_db_instance" "main" {
  count = var.create_rds ? 1 : 0

  identifier = "${var.name_prefix}-db"

  engine         = "postgres"
  engine_version = var.rds_engine_version
  instance_class = var.rds_instance_class

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.rds_database_name
  username = var.rds_username
  password = var.rds_password

  vpc_security_group_ids = [aws_security_group.rds[0].id]
  db_subnet_group_name   = aws_db_subnet_group.main[0].name

  backup_retention_period = var.rds_backup_retention_period
  backup_window          = var.rds_backup_window
  maintenance_window     = var.rds_maintenance_window

  skip_final_snapshot = var.rds_skip_final_snapshot
  deletion_protection = var.rds_deletion_protection

  performance_insights_enabled = var.rds_performance_insights_enabled
  monitoring_interval         = var.rds_monitoring_interval
  monitoring_role_arn         = var.rds_monitoring_interval > 0 ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db"
  })
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  count = var.create_elasticache ? 1 : 0

  name       = "${var.name_prefix}-cache-subnet-group"
  subnet_ids = var.vpc_id != "" ? var.private_subnet_ids : aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "main" {
  count = var.create_elasticache ? 1 : 0

  replication_group_id       = "${var.name_prefix}-redis"
  description                = "Redis cluster for AltWallet Checkout Agent"

  node_type                  = var.elasticache_node_type
  port                       = 6379
  parameter_group_name       = var.elasticache_parameter_group_name
  num_cache_clusters         = var.elasticache_num_cache_nodes

  engine_version             = var.elasticache_engine_version
  at_rest_encryption_enabled = true
  transit_encryption_enabled = var.elasticache_transit_encryption_enabled

  subnet_group_name  = aws_elasticache_subnet_group.main[0].name
  security_group_ids = [aws_security_group.elasticache[0].id]

  snapshot_retention_limit = var.elasticache_snapshot_retention_limit
  snapshot_window         = var.elasticache_snapshot_window

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis"
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  count = var.create_ecs ? 1 : 0

  name              = "/ecs/${var.name_prefix}"
  retention_in_days = var.log_retention_in_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-logs"
  })
}

# Secrets Manager
resource "aws_secretsmanager_secret" "database_url" {
  count = var.create_secrets ? 1 : 0

  name        = "${var.name_prefix}/database-url"
  description = "Database connection URL for AltWallet Checkout Agent"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-url"
  })
}

resource "aws_secretsmanager_secret_version" "database_url" {
  count = var.create_secrets ? 1 : 0

  secret_id = aws_secretsmanager_secret.database_url[0].id
  secret_string = jsonencode({
    url = var.create_rds ? "postgresql://${var.rds_username}:${var.rds_password}@${aws_db_instance.main[0].endpoint}/${var.rds_database_name}" : var.database_url
  })
}

resource "aws_secretsmanager_secret" "redis_url" {
  count = var.create_secrets ? 1 : 0

  name        = "${var.name_prefix}/redis-url"
  description = "Redis connection URL for AltWallet Checkout Agent"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis-url"
  })
}

resource "aws_secretsmanager_secret_version" "redis_url" {
  count = var.create_secrets ? 1 : 0

  secret_id = aws_secretsmanager_secret.redis_url[0].id
  secret_string = jsonencode({
    url = var.create_elasticache ? "redis://${aws_elasticache_replication_group.main[0].configuration_endpoint_address}:6379/0" : var.redis_url
  })
}

resource "aws_secretsmanager_secret" "api_key" {
  count = var.create_secrets ? 1 : 0

  name        = "${var.name_prefix}/api-key"
  description = "API key for AltWallet Checkout Agent"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-key"
  })
}

resource "aws_secretsmanager_secret_version" "api_key" {
  count = var.create_secrets ? 1 : 0

  secret_id     = aws_secretsmanager_secret.api_key[0].id
  secret_string = jsonencode({ key = var.api_key })
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  count = var.create_secrets ? 1 : 0

  name        = "${var.name_prefix}/jwt-secret"
  description = "JWT secret for AltWallet Checkout Agent"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-jwt-secret"
  })
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  count = var.create_secrets ? 1 : 0

  secret_id     = aws_secretsmanager_secret.jwt_secret[0].id
  secret_string = jsonencode({ secret = var.jwt_secret })
}

resource "aws_secretsmanager_secret" "encryption_key" {
  count = var.create_secrets ? 1 : 0

  name        = "${var.name_prefix}/encryption-key"
  description = "Encryption key for AltWallet Checkout Agent"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-encryption-key"
  })
}

resource "aws_secretsmanager_secret_version" "encryption_key" {
  count = var.create_secrets ? 1 : 0

  secret_id     = aws_secretsmanager_secret.encryption_key[0].id
  secret_string = jsonencode({ key = var.encryption_key })
}
