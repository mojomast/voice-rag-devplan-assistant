# ===== CloudWatch Monitoring and Alerting =====
# Voice RAG System Comprehensive Monitoring Infrastructure
# Includes dashboards, alarms, metrics, and alerting

# ===== CloudWatch Dashboard =====
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", aws_ecs_service.backend.name, "ClusterName", aws_ecs_cluster.main.name],
            [".", "MemoryUtilization", ".", ".", ".", "."],
            ["AWS/ECS", "CPUUtilization", "ServiceName", aws_ecs_service.frontend.name, "ClusterName", aws_ecs_cluster.main.name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ECS Service Resources"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.main.arn_suffix],
            [".", "RequestCount", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.main.id],
            [".", "DatabaseConnections", ".", "."],
            [".", "FreeableMemory", ".", "."],
            [".", "FreeStorageSpace", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "RDS Database Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", "${aws_elasticache_replication_group.main.replication_group_id}-001"],
            [".", "NetworkBytesIn", ".", "."],
            [".", "NetworkBytesOut", ".", "."],
            [".", "CurrConnections", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ElastiCache Redis Metrics"
          period  = 300
        }
      }
    ]
  })

  tags = local.common_tags
}

# ===== CloudWatch Alarms =====
resource "aws_cloudwatch_metric_alarm" "backend_cpu_high" {
  alarm_name          = "${local.name_prefix}-backend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors backend CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ServiceName = aws_ecs_service.backend.name
    ClusterName = aws_ecs_cluster.main.name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "backend_memory_high" {
  alarm_name          = "${local.name_prefix}-backend-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "120"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors backend memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ServiceName = aws_ecs_service.backend.name
    ClusterName = aws_ecs_cluster.main.name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "frontend_cpu_high" {
  alarm_name          = "${local.name_prefix}-frontend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors frontend CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ServiceName = aws_ecs_service.frontend.name
    ClusterName = aws_ecs_cluster.main.name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "alb_target_response_time" {
  alarm_name          = "${local.name_prefix}-alb-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "120"
  statistic           = "Average"
  threshold           = "5"
  alarm_description   = "This metric monitors ALB target response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${local.name_prefix}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors ALB 5XX errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  alarm_name          = "${local.name_prefix}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "120"
  statistic           = "Average"
  threshold           = "40"
  alarm_description   = "This metric monitors RDS connection count"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_freeable_memory_low" {
  alarm_name          = "${local.name_prefix}-rds-memory-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeableMemory"
  namespace           = "AWS/RDS"
  period              = "120"
  statistic           = "Average"
  threshold           = "100000000"  # 100MB in bytes
  alarm_description   = "This metric monitors RDS available memory"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  alarm_name          = "${local.name_prefix}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors Redis CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = "${aws_elasticache_replication_group.main.replication_group_id}-001"
  }

  tags = local.common_tags
}

# ===== SNS Topic for Alerts =====
resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"

  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count     = var.environment == "production" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "alerts@voicerag.com"  # Replace with actual email
}

# ===== CloudWatch Log Insights Queries =====
resource "aws_cloudwatch_query_definition" "error_analysis" {
  name = "${local.name_prefix}-error-analysis"

  log_group_names = [
    aws_cloudwatch_log_group.backend.name,
    aws_cloudwatch_log_group.frontend.name
  ]

  query_string = <<EOF
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
EOF
}

resource "aws_cloudwatch_query_definition" "performance_analysis" {
  name = "${local.name_prefix}-performance-analysis"

  log_group_names = [
    aws_cloudwatch_log_group.backend.name
  ]

  query_string = <<EOF
fields @timestamp, @message
| filter @message like /response_time/
| stats avg(response_time) by bin(5m)
| sort @timestamp desc
EOF
}

resource "aws_cloudwatch_query_definition" "user_activity" {
  name = "${local.name_prefix}-user-activity"

  log_group_names = [
    aws_cloudwatch_log_group.backend.name
  ]

  query_string = <<EOF
fields @timestamp, @message
| filter @message like /user_id/
| stats count() by user_id
| sort count desc
| limit 50
EOF
}

# ===== CloudWatch Composite Alarms =====
resource "aws_cloudwatch_composite_alarm" "service_health" {
  alarm_name        = "${local.name_prefix}-service-health"
  alarm_description = "Composite alarm for overall service health"

  alarm_rule = "ALARM(${aws_cloudwatch_metric_alarm.backend_cpu_high.alarm_name}) OR ALARM(${aws_cloudwatch_metric_alarm.backend_memory_high.alarm_name}) OR ALARM(${aws_cloudwatch_metric_alarm.alb_5xx_errors.alarm_name})"

  actions_enabled = true
  alarm_actions   = [aws_sns_topic.alerts.arn]

  tags = local.common_tags
}

# ===== Custom CloudWatch Metrics =====
resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "${local.name_prefix}-error-count"
  log_group_name = aws_cloudwatch_log_group.backend.name
  pattern        = "ERROR"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "VoiceRAG/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "query_latency" {
  name           = "${local.name_prefix}-query-latency"
  log_group_name = aws_cloudwatch_log_group.backend.name
  pattern        = "[timestamp, request_id, level=\"INFO\", message=\"Query processed\", latency_ms]"

  metric_transformation {
    name      = "QueryLatency"
    namespace = "VoiceRAG/Performance"
    value     = "$latency_ms"
    unit      = "Milliseconds"
  }
}

resource "aws_cloudwatch_log_metric_filter" "document_uploads" {
  name           = "${local.name_prefix}-document-uploads"
  log_group_name = aws_cloudwatch_log_group.backend.name
  pattern        = "Document uploaded successfully"

  metric_transformation {
    name      = "DocumentUploads"
    namespace = "VoiceRAG/Usage"
    value     = "1"
  }
}

# ===== CloudWatch Alarms for Custom Metrics =====
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${local.name_prefix}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ErrorCount"
  namespace           = "VoiceRAG/Application"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "High error rate detected"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "high_query_latency" {
  alarm_name          = "${local.name_prefix}-high-query-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "QueryLatency"
  namespace           = "VoiceRAG/Performance"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000"  # 5 seconds
  alarm_description   = "High query latency detected"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = local.common_tags
}

# ===== CloudWatch Events for Automated Responses =====
resource "aws_cloudwatch_event_rule" "ecs_task_failure" {
  name        = "${local.name_prefix}-ecs-task-failure"
  description = "Capture ECS task failures"

  event_pattern = jsonencode({
    source        = ["aws.ecs"]
    detail-type   = ["ECS Task State Change"]
    detail = {
      lastStatus = ["STOPPED"]
      stopCode   = ["TaskFailedToStart", "EssentialContainerExited"]
      clusterArn = [aws_ecs_cluster.main.arn]
    }
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "task_failure_notification" {
  rule      = aws_cloudwatch_event_rule.ecs_task_failure.name
  target_id = "TaskFailureNotification"
  arn       = aws_sns_topic.alerts.arn
}

# ===== Performance Insights for RDS =====
resource "aws_cloudwatch_metric_alarm" "rds_db_load_high" {
  count               = var.enable_performance_insights ? 1 : 0
  alarm_name          = "${local.name_prefix}-rds-db-load-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DBLoad"
  namespace           = "AWS/RDS"
  period              = "120"
  statistic           = "Average"
  threshold           = "2"
  alarm_description   = "High database load detected"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = local.common_tags
}

# ===== Cost Monitoring =====
resource "aws_cloudwatch_metric_alarm" "estimated_charges" {
  count               = var.environment == "production" ? 1 : 0
  alarm_name          = "${local.name_prefix}-estimated-charges"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "86400"  # 24 hours
  statistic           = "Maximum"
  threshold           = "200"  # $200 threshold
  alarm_description   = "AWS charges exceed threshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    Currency = "USD"
  }

  tags = local.common_tags
}

# ===== CloudWatch Synthetics for Uptime Monitoring =====
resource "aws_synthetics_canary" "endpoint_health" {
  count                = var.environment == "production" ? 1 : 0
  name                 = "${local.name_prefix}-endpoint-health"
  artifact_s3_location = "s3://${aws_s3_bucket.monitoring[0].bucket}/canary-artifacts/"
  execution_role_arn   = aws_iam_role.synthetics_execution[0].arn
  handler              = "apiCanaryBlueprint.handler"
  zip_file             = "apiCanaryBlueprint.zip"
  runtime_version      = "syn-nodejs-puppeteer-3.9"

  schedule {
    expression = "rate(5 minutes)"
  }

  run_config {
    timeout_in_seconds    = 60
    memory_in_mb         = 960
    active_tracing       = false
  }

  success_retention_period = 2
  failure_retention_period = 14

  tags = local.common_tags
}

# ===== S3 Bucket for Monitoring Data =====
resource "aws_s3_bucket" "monitoring" {
  count  = var.environment == "production" ? 1 : 0
  bucket = "${local.name_prefix}-monitoring-${random_id.bucket_suffix.hex}"

  tags = local.common_tags
}

# ===== IAM Role for Synthetics =====
resource "aws_iam_role" "synthetics_execution" {
  count = var.environment == "production" ? 1 : 0
  name  = "${local.name_prefix}-synthetics-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "synthetics_execution" {
  count      = var.environment == "production" ? 1 : 0
  role       = aws_iam_role.synthetics_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchSyntheticsExecutionRolePolicy"
}

# ===== AWS X-Ray Tracing =====
resource "aws_xray_sampling_rule" "voice_rag_sampling" {
  rule_name      = "${local.name_prefix}-sampling"
  priority       = 9000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.1
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"

  tags = local.common_tags
}