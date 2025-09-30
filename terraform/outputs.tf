# ===== Terraform Outputs Configuration =====
# Voice RAG System Infrastructure Outputs
# Expose key infrastructure information for external use

# ===== Network Outputs =====
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnets
}

output "database_subnets" {
  description = "IDs of the database subnets"
  value       = module.vpc.database_subnets
}

# ===== Load Balancer Outputs =====
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "backend_target_group_arn" {
  description = "ARN of the backend target group"
  value       = aws_lb_target_group.backend.arn
}

output "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  value       = aws_lb_target_group.frontend.arn
}

# ===== Application URLs =====
output "application_url" {
  description = "Primary application URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"
}

output "backend_api_url" {
  description = "Backend API URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}/api" : "http://${aws_lb.main.dns_name}/api"
}

output "api_documentation_url" {
  description = "API documentation URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}/docs" : "http://${aws_lb.main.dns_name}/docs"
}

# ===== ECS Outputs =====
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "backend_service_arn" {
  description = "ARN of the backend ECS service"
  value       = aws_ecs_service.backend.id
}

output "frontend_service_arn" {
  description = "ARN of the frontend ECS service"
  value       = aws_ecs_service.frontend.id
}

# ===== Database Outputs =====
output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "database_username" {
  description = "Database master username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "database_connection_string" {
  description = "Database connection string (without password)"
  value       = "postgresql://${aws_db_instance.main.username}:PASSWORD@${aws_db_instance.main.endpoint}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
  sensitive   = true
}

# ===== Cache Outputs =====
output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_connection_string" {
  description = "Redis connection string (without auth token)"
  value       = "redis://:AUTH_TOKEN@${aws_elasticache_replication_group.main.primary_endpoint_address}:${aws_elasticache_replication_group.main.port}"
  sensitive   = true
}

# ===== S3 Bucket Outputs =====
output "vector_store_bucket_name" {
  description = "Name of the vector store S3 bucket"
  value       = aws_s3_bucket.vector_store.bucket
}

output "vector_store_bucket_arn" {
  description = "ARN of the vector store S3 bucket"
  value       = aws_s3_bucket.vector_store.arn
}

output "uploads_bucket_name" {
  description = "Name of the uploads S3 bucket"
  value       = aws_s3_bucket.uploads.bucket
}

output "uploads_bucket_arn" {
  description = "ARN of the uploads S3 bucket"
  value       = aws_s3_bucket.uploads.arn
}

output "backups_bucket_name" {
  description = "Name of the backups S3 bucket"
  value       = aws_s3_bucket.backups.bucket
}

output "backups_bucket_arn" {
  description = "ARN of the backups S3 bucket"
  value       = aws_s3_bucket.backups.arn
}

# ===== Security Outputs =====
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS tasks security group"
  value       = aws_security_group.ecs_tasks.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = aws_security_group.redis.id
}

# ===== IAM Outputs =====
output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

# ===== Secrets Manager Outputs =====
output "db_password_secret_arn" {
  description = "ARN of the database password secret"
  value       = aws_secretsmanager_secret.db_password.arn
  sensitive   = true
}

output "redis_auth_token_secret_arn" {
  description = "ARN of the Redis auth token secret"
  value       = aws_secretsmanager_secret.redis_auth_token.arn
  sensitive   = true
}

output "app_secrets_arn" {
  description = "ARN of the application secrets"
  value       = aws_secretsmanager_secret.app_secrets.arn
  sensitive   = true
}

# ===== CloudWatch Outputs =====
output "ecs_log_group_name" {
  description = "Name of the ECS CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "backend_log_group_name" {
  description = "Name of the backend CloudWatch log group"
  value       = aws_cloudwatch_log_group.backend.name
}

output "frontend_log_group_name" {
  description = "Name of the frontend CloudWatch log group"
  value       = aws_cloudwatch_log_group.frontend.name
}

# ===== Monitoring Outputs =====
output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${local.name_prefix}-dashboard"
}

output "monitoring_alarms" {
  description = "List of monitoring alarm names"
  value = [
    aws_cloudwatch_metric_alarm.backend_cpu_high.alarm_name,
    aws_cloudwatch_metric_alarm.frontend_cpu_high.alarm_name,
    aws_cloudwatch_metric_alarm.alb_target_response_time.alarm_name,
    aws_cloudwatch_metric_alarm.rds_cpu_high.alarm_name,
    aws_cloudwatch_metric_alarm.rds_connections_high.alarm_name
  ]
}

# ===== Auto Scaling Outputs =====
output "backend_autoscaling_group_arn" {
  description = "ARN of the backend auto scaling target"
  value       = aws_appautoscaling_target.backend.id
}

output "frontend_autoscaling_group_arn" {
  description = "ARN of the frontend auto scaling target"
  value       = aws_appautoscaling_target.frontend.id
}

# ===== Environment Information =====
output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "deployment_timestamp" {
  description = "Timestamp of the deployment"
  value       = timestamp()
}

# ===== Connection Information =====
output "connection_info" {
  description = "Complete connection information for the deployment"
  value = {
    application_url       = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"
    api_url              = var.domain_name != "" ? "https://${var.domain_name}/api" : "http://${aws_lb.main.dns_name}/api"
    docs_url             = var.domain_name != "" ? "https://${var.domain_name}/docs" : "http://${aws_lb.main.dns_name}/docs"
    health_check_url     = var.domain_name != "" ? "https://${var.domain_name}/health" : "http://${aws_lb.main.dns_name}/health"
    metrics_url          = var.domain_name != "" ? "https://${var.domain_name}/metrics" : "http://${aws_lb.main.dns_name}/metrics"
    analytics_url        = var.domain_name != "" ? "https://${var.domain_name}/analytics" : "http://${aws_lb.main.dns_name}/analytics"
  }
  sensitive = false
}

# ===== Resource Tags =====
output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# ===== Cost Information =====
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (approximate)"
  value = {
    note = "These are rough estimates based on current AWS pricing and may vary"
    ecs_fargate = var.environment == "production" ? "~$50-100/month" : "~$20-40/month"
    rds = var.db_instance_class == "db.t3.micro" ? "~$15-25/month" : "~$30-60/month"
    elasticache = var.redis_node_type == "cache.t3.micro" ? "~$12-18/month" : "~$25-40/month"
    alb = "~$20-25/month"
    s3 = "~$5-15/month (varies with usage)"
    secrets_manager = "~$2-5/month"
    cloudwatch = "~$5-15/month"
    total_estimate = var.environment == "production" ? "$120-250/month" : "$80-150/month"
  }
}

# ===== Backup Information =====
output "backup_information" {
  description = "Backup and disaster recovery information"
  value = {
    rds_backups = {
      retention_period = aws_db_instance.main.backup_retention_period
      backup_window = aws_db_instance.main.backup_window
      maintenance_window = aws_db_instance.main.maintenance_window
    }
    redis_snapshots = {
      retention_limit = aws_elasticache_replication_group.main.snapshot_retention_limit
      snapshot_window = aws_elasticache_replication_group.main.snapshot_window
    }
    s3_versioning = {
      vector_store = "enabled"
      uploads = "enabled"
      backups = "enabled"
    }
  }
}

# ===== Security Information =====
output "security_summary" {
  description = "Security configuration summary"
  value = {
    encryption = {
      rds_encrypted = aws_db_instance.main.storage_encrypted
      redis_at_rest = aws_elasticache_replication_group.main.at_rest_encryption_enabled
      redis_in_transit = aws_elasticache_replication_group.main.transit_encryption_enabled
      s3_encryption = "AES256"
    }
    network = {
      vpc_isolated = true
      private_subnets = true
      security_groups = "restrictive"
    }
    secrets = {
      secrets_manager = "enabled"
      random_passwords = true
    }
  }
}

# ===== Quick Start Guide =====
output "quick_start_guide" {
  description = "Quick start commands and information"
  value = {
    deploy_commands = [
      "terraform init",
      "terraform plan -var-file=environments/${var.environment}.tfvars",
      "terraform apply -var-file=environments/${var.environment}.tfvars"
    ]
    post_deployment = [
      "Update DNS records to point to: ${aws_lb.main.dns_name}",
      "Configure SSL certificate if using custom domain",
      "Set up monitoring alerts",
      "Configure backup schedules",
      "Test application endpoints"
    ]
    health_checks = [
      "curl ${var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"}/health",
      "Check ECS service status in AWS console",
      "Monitor CloudWatch logs for errors"
    ]
  }
}