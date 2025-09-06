# Auto Scaling Configuration for AltWallet Checkout Agent

# Application Auto Scaling Target
resource "aws_appautoscaling_target" "ecs_target" {
  count = var.create_ecs && var.enable_autoscaling ? 1 : 0

  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main[0].name}/${aws_ecs_service.main[0].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  depends_on = [aws_ecs_service.main]
}

# CPU-based Auto Scaling Policy
resource "aws_appautoscaling_policy" "ecs_cpu_policy" {
  count = var.create_ecs && var.enable_autoscaling ? 1 : 0

  name               = "${var.name_prefix}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.target_cpu_utilization
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

# Memory-based Auto Scaling Policy
resource "aws_appautoscaling_policy" "ecs_memory_policy" {
  count = var.create_ecs && var.enable_autoscaling ? 1 : 0

  name               = "${var.name_prefix}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = var.target_memory_utilization
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

# Custom Metric Auto Scaling Policy (Request Count)
resource "aws_appautoscaling_policy" "ecs_request_count_policy" {
  count = var.create_ecs && var.enable_autoscaling ? 1 : 0

  name               = "${var.name_prefix}-request-count-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "RequestCount"
      namespace   = "AWS/ApplicationELB"
      statistic   = "Average"
      dimensions = {
        TargetGroup  = aws_lb_target_group.main[0].arn_suffix
        LoadBalancer = aws_lb.main[0].arn_suffix
      }
    }
    target_value       = 1000  # Target 1000 requests per minute per task
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

# Scheduled Scaling (Optional)
resource "aws_appautoscaling_scheduled_action" "scale_up" {
  count = var.create_ecs && var.enable_autoscaling ? 1 : 0

  name               = "${var.name_prefix}-scale-up"
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  schedule           = "cron(0 8 * * MON-FRI)"  # 8 AM weekdays
  timezone           = "UTC"

  scalable_target_action {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }
}

resource "aws_appautoscaling_scheduled_action" "scale_down" {
  count = var.create_ecs && var.enable_autoscaling ? 1 : 0

  name               = "${var.name_prefix}-scale-down"
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  schedule           = "cron(0 18 * * MON-FRI)"  # 6 PM weekdays
  timezone           = "UTC"

  scalable_target_action {
    min_capacity = 1
    max_capacity = var.max_capacity
  }
}

# CloudWatch Alarms for Auto Scaling
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  count = var.create_ecs && var.enable_autoscaling && var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    ServiceName = aws_ecs_service.main[0].name
    ClusterName = aws_ecs_cluster.main[0].name
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-high-cpu"
  })
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  count = var.create_ecs && var.enable_autoscaling && var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS memory utilization"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    ServiceName = aws_ecs_service.main[0].name
    ClusterName = aws_ecs_cluster.main[0].name
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-high-memory"
  })
}

resource "aws_cloudwatch_metric_alarm" "high_request_count" {
  count = var.create_ecs && var.enable_autoscaling && var.enable_cloudwatch_alarms && var.create_alb ? 1 : 0

  alarm_name          = "${var.name_prefix}-high-request-count"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "RequestCount"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"
  alarm_description   = "This metric monitors ALB request count"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    TargetGroup  = aws_lb_target_group.main[0].arn_suffix
    LoadBalancer = aws_lb.main[0].arn_suffix
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-high-request-count"
  })
}

resource "aws_cloudwatch_metric_alarm" "high_response_time" {
  count = var.create_ecs && var.enable_autoscaling && var.enable_cloudwatch_alarms && var.create_alb ? 1 : 0

  alarm_name          = "${var.name_prefix}-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "2"
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    TargetGroup  = aws_lb_target_group.main[0].arn_suffix
    LoadBalancer = aws_lb.main[0].arn_suffix
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-high-response-time"
  })
}

# Service Health Alarms
resource "aws_cloudwatch_metric_alarm" "service_unhealthy" {
  count = var.create_ecs && var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-service-unhealthy"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "RunningTaskCount"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors ECS service health"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    ServiceName = aws_ecs_service.main[0].name
    ClusterName = aws_ecs_cluster.main[0].name
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-service-unhealthy"
  })
}

# Database Alarms
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  count = var.create_rds && var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-database-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main[0].id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-cpu"
  })
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  count = var.create_rds && var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-database-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS database connections"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main[0].id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-connections"
  })
}

# Redis Alarms
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  count = var.create_elasticache && var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-redis-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ElastiCache CPU utilization"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.main[0].id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis-cpu"
  })
}

resource "aws_cloudwatch_metric_alarm" "redis_connections" {
  count = var.create_elasticache && var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-redis-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CurrConnections"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "100"
  alarm_description   = "This metric monitors ElastiCache connections"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.main[0].id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis-connections"
  })
}
