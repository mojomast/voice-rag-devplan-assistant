# ===== ECS Task Definitions and Services =====
# Voice RAG System Container Orchestration
# Defines ECS tasks, services, and auto-scaling configuration

# ===== Task Definitions =====
resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name_prefix}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = var.backend_image

      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENV"
          value = var.environment
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "DATABASE_URL"
          value = "postgresql://${var.db_username}:PLACEHOLDER@${aws_db_instance.main.endpoint}:${aws_db_instance.main.port}/${var.db_name}"
        },
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_replication_group.main.primary_endpoint_address}:${aws_elasticache_replication_group.main.port}"
        },
        {
          name  = "VECTOR_STORE_BUCKET"
          value = aws_s3_bucket.vector_store.bucket
        },
        {
          name  = "UPLOADS_BUCKET"
          value = aws_s3_bucket.uploads.bucket
        },
        {
          name  = "BACKUPS_BUCKET"
          value = aws_s3_bucket.backups.bucket
        },
        {
          name  = "LOG_LEVEL"
          value = var.environment == "production" ? "INFO" : "DEBUG"
        },
        {
          name  = "CORS_ORIGINS"
          value = var.domain_name != "" ? "https://${var.domain_name}" : "*"
        }
      ]

      secrets = [
        {
          name      = "DATABASE_PASSWORD"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        },
        {
          name      = "REDIS_AUTH_TOKEN"
          valueFrom = aws_secretsmanager_secret.redis_auth_token.arn
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:OPENAI_API_KEY::"
        },
        {
          name      = "REQUESTY_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:REQUESTY_API_KEY::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      # Resource limits
      ulimits = [
        {
          name      = "nofile"
          softLimit = 65536
          hardLimit = 65536
        }
      ]
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "frontend"
      image = var.frontend_image

      essential = true

      portMappings = [
        {
          containerPort = 8501
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENV"
          value = var.environment
        },
        {
          name  = "BACKEND_URL"
          value = "http://localhost:8000"
        },
        {
          name  = "STREAMLIT_SERVER_PORT"
          value = "8501"
        },
        {
          name  = "STREAMLIT_SERVER_ADDRESS"
          value = "0.0.0.0"
        },
        {
          name  = "STREAMLIT_SERVER_HEADLESS"
          value = "true"
        },
        {
          name  = "STREAMLIT_BROWSER_GATHER_USAGE_STATS"
          value = "false"
        },
        {
          name  = "STREAMLIT_SERVER_ENABLE_CORS"
          value = "true"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:8501/_stcore/health || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 90
      }

      # Resource limits
      ulimits = [
        {
          name      = "nofile"
          softLimit = 32768
          hardLimit = 32768
        }
      ]
    }
  ])

  tags = local.common_tags
}

# ===== ECS Services =====
resource "aws_ecs_service" "backend" {
  name            = "${local.name_prefix}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  platform_version = "LATEST"

  # Use Fargate Spot for cost optimization in non-production
  capacity_provider_strategy {
    capacity_provider = var.environment == "production" ? "FARGATE" : (var.use_spot_instances ? "FARGATE_SPOT" : "FARGATE")
    weight            = 100
    base              = var.backend_desired_count
  }

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = module.vpc.private_subnets
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  # Enable service discovery
  service_registries {
    registry_arn = aws_service_discovery_service.backend.arn
  }

  # Deployment configuration
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100

    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  # Enable execute command for debugging
  enable_execute_command = var.environment != "production"

  # Health check grace period
  health_check_grace_period_seconds = 300

  depends_on = [aws_lb_listener.main]

  tags = local.common_tags

  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  platform_version = "LATEST"

  # Use Fargate Spot for cost optimization in non-production
  capacity_provider_strategy {
    capacity_provider = var.environment == "production" ? "FARGATE" : (var.use_spot_instances ? "FARGATE_SPOT" : "FARGATE")
    weight            = 100
    base              = var.frontend_desired_count
  }

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = module.vpc.private_subnets
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 8501
  }

  # Enable service discovery
  service_registries {
    registry_arn = aws_service_discovery_service.frontend.arn
  }

  # Deployment configuration
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100

    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  # Enable execute command for debugging
  enable_execute_command = var.environment != "production"

  # Health check grace period
  health_check_grace_period_seconds = 300

  depends_on = [aws_lb_listener.main]

  tags = local.common_tags

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# ===== Service Discovery =====
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${local.name_prefix}.local"
  description = "Private DNS namespace for ${local.name_prefix}"
  vpc         = module.vpc.vpc_id

  tags = local.common_tags
}

resource "aws_service_discovery_service" "backend" {
  name = "backend"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 60
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_grace_period_seconds = 300

  tags = local.common_tags
}

resource "aws_service_discovery_service" "frontend" {
  name = "frontend"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 60
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_grace_period_seconds = 300

  tags = local.common_tags
}

# ===== Auto Scaling =====
resource "aws_appautoscaling_target" "backend" {
  max_capacity       = var.backend_max_capacity
  min_capacity       = var.backend_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = local.common_tags
}

resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = var.frontend_max_capacity
  min_capacity       = var.frontend_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = local.common_tags
}

# ===== Auto Scaling Policies =====
resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${local.name_prefix}-backend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.auto_scaling_target_cpu
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

resource "aws_appautoscaling_policy" "backend_memory" {
  name               = "${local.name_prefix}-backend-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

resource "aws_appautoscaling_policy" "frontend_cpu" {
  name               = "${local.name_prefix}-frontend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.auto_scaling_target_cpu
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

# ===== ECS Task IAM Policy for S3 and Secrets =====
resource "aws_iam_policy" "ecs_task_policy" {
  name = "${local.name_prefix}-ecs-task-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.vector_store.arn,
          "${aws_s3_bucket.vector_store.arn}/*",
          aws_s3_bucket.uploads.arn,
          "${aws_s3_bucket.uploads.arn}/*",
          aws_s3_bucket.backups.arn,
          "${aws_s3_bucket.backups.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn,
          aws_secretsmanager_secret.redis_auth_token.arn,
          aws_secretsmanager_secret.app_secrets.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_policy" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_task_policy.arn
}

# ===== Scheduled Tasks =====
resource "aws_ecs_task_definition" "maintenance" {
  family                   = "${local.name_prefix}-maintenance"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "maintenance"
      image = var.backend_image

      essential = true

      command = ["python", "-m", "backend.maintenance.cleanup"]

      environment = [
        {
          name  = "ENV"
          value = var.environment
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "VECTOR_STORE_BUCKET"
          value = aws_s3_bucket.vector_store.bucket
        },
        {
          name  = "UPLOADS_BUCKET"
          value = aws_s3_bucket.uploads.bucket
        },
        {
          name  = "BACKUPS_BUCKET"
          value = aws_s3_bucket.backups.bucket
        }
      ]

      secrets = [
        {
          name      = "DATABASE_PASSWORD"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "maintenance"
        }
      }
    }
  ])

  tags = local.common_tags
}

# ===== CloudWatch Events for Scheduled Tasks =====
resource "aws_cloudwatch_event_rule" "maintenance_schedule" {
  name                = "${local.name_prefix}-maintenance"
  description         = "Run maintenance tasks daily"
  schedule_expression = "cron(0 2 * * ? *)"  # Run at 2 AM UTC daily

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "maintenance_target" {
  rule      = aws_cloudwatch_event_rule.maintenance_schedule.name
  target_id = "MaintenanceTarget"
  arn       = aws_ecs_cluster.main.arn
  role_arn  = aws_iam_role.events_task_execution.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.maintenance.arn
    launch_type         = "FARGATE"
    platform_version    = "LATEST"

    network_configuration {
      security_groups  = [aws_security_group.ecs_tasks.id]
      subnets          = module.vpc.private_subnets
      assign_public_ip = false
    }
  }
}

# ===== IAM Role for CloudWatch Events =====
resource "aws_iam_role" "events_task_execution" {
  name = "${local.name_prefix}-events-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "events_task_execution" {
  name = "${local.name_prefix}-events-task-execution"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask"
        ]
        Resource = aws_ecs_task_definition.maintenance.arn
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.ecs_task_execution.arn,
          aws_iam_role.ecs_task.arn
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "events_task_execution" {
  role       = aws_iam_role.events_task_execution.name
  policy_arn = aws_iam_policy.events_task_execution.arn
}