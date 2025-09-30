# ===== Main Terraform Configuration =====
# Voice RAG System Infrastructure
# Supports AWS deployment with ECS, RDS, ElastiCache, and monitoring

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  # Backend configuration - uncomment and configure for production
  # backend "s3" {
  #   bucket = "voice-rag-terraform-state"
  #   key    = "infrastructure/terraform.tfstate"
  #   region = "us-west-2"
  #   encrypt = true
  #   dynamodb_table = "voice-rag-terraform-locks"
  # }
}

# ===== Provider Configuration =====
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
    }
  }
}

# ===== Data Sources =====
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# ===== Local Values =====
locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # Subnet configuration
  vpc_cidr = var.vpc_cidr
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)

  private_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 1),
    cidrsubnet(local.vpc_cidr, 8, 2),
    cidrsubnet(local.vpc_cidr, 8, 3)
  ]

  public_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 101),
    cidrsubnet(local.vpc_cidr, 8, 102),
    cidrsubnet(local.vpc_cidr, 8, 103)
  ]

  database_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 201),
    cidrsubnet(local.vpc_cidr, 8, 202),
    cidrsubnet(local.vpc_cidr, 8, 203)
  ]

  # Common tags
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ===== Random Password Generation =====
resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "random_password" "redis_auth_token" {
  length  = 32
  special = false
}

# ===== VPC and Networking =====
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.name_prefix}-vpc"
  cidr = local.vpc_cidr

  azs              = local.azs
  private_subnets  = local.private_subnets
  public_subnets   = local.public_subnets
  database_subnets = local.database_subnets

  enable_nat_gateway = true
  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support = true

  # Database subnet group
  create_database_subnet_group = true
  create_database_subnet_route_table = true

  tags = local.common_tags
}

# ===== Security Groups =====
resource "aws_security_group" "alb" {
  name_prefix = "${local.name_prefix}-alb"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
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

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb-sg"
  })
}

resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${local.name_prefix}-ecs-tasks"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecs-tasks-sg"
  })
}

resource "aws_security_group" "rds" {
  name_prefix = "${local.name_prefix}-rds"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rds-sg"
  })
}

resource "aws_security_group" "redis" {
  name_prefix = "${local.name_prefix}-redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-sg"
  })
}

# ===== Application Load Balancer =====
resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = var.environment == "production" ? true : false

  tags = local.common_tags
}

resource "aws_lb_target_group" "backend" {
  name     = "${local.name_prefix}-backend-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id
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

  tags = local.common_tags
}

resource "aws_lb_target_group" "frontend" {
  name     = "${local.name_prefix}-frontend-tg"
  port     = 8501
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/_stcore/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = local.common_tags
}

resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "backend_api" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/docs", "/health", "/metrics", "/analytics/*", "/voice/*", "/documents/*", "/query/*", "/usage/*", "/performance/*"]
    }
  }
}

# ===== ECS Cluster =====
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"

      log_configuration {
        cloud_watch_encryption_enabled = true
        cloud_watch_log_group_name     = aws_cloudwatch_log_group.ecs.name
      }
    }
  }

  tags = local.common_tags
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = var.environment == "production" ? "FARGATE" : "FARGATE_SPOT"
  }
}

# ===== CloudWatch Log Groups =====
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name_prefix}/backend"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.name_prefix}/frontend"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# ===== RDS PostgreSQL Database =====
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = module.vpc.database_subnets

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

resource "aws_db_instance" "main" {
  identifier = "${local.name_prefix}-db"

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = var.environment == "production" ? 7 : 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = var.environment != "production"
  deletion_protection = var.environment == "production"

  # Performance Insights
  performance_insights_enabled = var.environment == "production"
  performance_insights_retention_period = var.environment == "production" ? 7 : 0

  # Monitoring
  monitoring_interval = var.environment == "production" ? 60 : 0
  monitoring_role_arn = var.environment == "production" ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  tags = local.common_tags
}

# ===== ElastiCache Redis =====
resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name_prefix}-cache-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = local.common_tags
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id         = "${local.name_prefix}-redis"
  description                  = "Redis cluster for ${local.name_prefix}"

  port                         = 6379
  parameter_group_name         = "default.redis7"
  node_type                    = var.redis_node_type
  num_cache_clusters           = var.redis_num_cache_nodes

  engine_version               = "7.0"

  subnet_group_name            = aws_elasticache_subnet_group.main.name
  security_group_ids           = [aws_security_group.redis.id]

  at_rest_encryption_enabled   = true
  transit_encryption_enabled   = true
  auth_token                   = random_password.redis_auth_token.result

  snapshot_retention_limit     = var.environment == "production" ? 5 : 0
  snapshot_window              = "03:00-05:00"

  tags = local.common_tags
}

# ===== IAM Roles and Policies =====
resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name_prefix}-ecs-task-execution"

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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task"

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

  tags = local.common_tags
}

# Enhanced monitoring role for RDS
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.environment == "production" ? 1 : 0

  name = "${local.name_prefix}-rds-monitoring"

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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count = var.environment == "production" ? 1 : 0

  role       = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ===== S3 Buckets =====
resource "aws_s3_bucket" "vector_store" {
  bucket = "${local.name_prefix}-vector-store-${random_id.bucket_suffix.hex}"

  tags = local.common_tags
}

resource "aws_s3_bucket" "uploads" {
  bucket = "${local.name_prefix}-uploads-${random_id.bucket_suffix.hex}"

  tags = local.common_tags
}

resource "aws_s3_bucket" "backups" {
  bucket = "${local.name_prefix}-backups-${random_id.bucket_suffix.hex}"

  tags = local.common_tags
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 bucket configurations
resource "aws_s3_bucket_versioning" "vector_store" {
  bucket = aws_s3_bucket.vector_store.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "vector_store" {
  bucket = aws_s3_bucket.vector_store.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ===== Secrets Manager =====
resource "aws_secretsmanager_secret" "db_password" {
  name = "${local.name_prefix}-db-password"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

resource "aws_secretsmanager_secret" "redis_auth_token" {
  name = "${local.name_prefix}-redis-auth-token"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id     = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = random_password.redis_auth_token.result
}

resource "aws_secretsmanager_secret" "app_secrets" {
  name = "${local.name_prefix}-app-secrets"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    OPENAI_API_KEY    = var.openai_api_key
    REQUESTY_API_KEY  = var.requesty_api_key
  })
}