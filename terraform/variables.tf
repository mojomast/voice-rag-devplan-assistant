# ===== Terraform Variables Configuration =====
# Voice RAG System Infrastructure Variables
# Define all configurable parameters for the deployment

# ===== Project Configuration =====
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "voice-rag"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.project_name))
    error_message = "Project name must start with a letter, contain only lowercase letters, numbers, and hyphens, and end with a letter or number."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "voice-rag-team"
}

# ===== AWS Configuration =====
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.aws_region))
    error_message = "AWS region must be a valid region identifier."
  }
}

# ===== Network Configuration =====
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

# ===== Database Configuration =====
variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "voiceragdb"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_name))
    error_message = "Database name must start with a letter and contain only alphanumeric characters and underscores."
  }
}

variable "db_username" {
  description = "PostgreSQL database username"
  type        = string
  default     = "voiceraguser"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_username))
    error_message = "Database username must start with a letter and contain only alphanumeric characters and underscores."
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"

  validation {
    condition     = can(regex("^db\\.[a-z0-9]+\\.[a-z0-9]+$", var.db_instance_class))
    error_message = "Database instance class must be a valid RDS instance type."
  }
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 1000
    error_message = "Database allocated storage must be between 20 and 1000 GB."
  }
}

variable "db_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 100

  validation {
    condition     = var.db_max_allocated_storage >= var.db_allocated_storage
    error_message = "Database max allocated storage must be greater than or equal to allocated storage."
  }
}

# ===== Cache Configuration =====
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"

  validation {
    condition     = can(regex("^cache\\.[a-z0-9]+\\.[a-z0-9]+$", var.redis_node_type))
    error_message = "Redis node type must be a valid ElastiCache instance type."
  }
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in the Redis cluster"
  type        = number
  default     = 1

  validation {
    condition     = var.redis_num_cache_nodes >= 1 && var.redis_num_cache_nodes <= 6
    error_message = "Number of Redis cache nodes must be between 1 and 6."
  }
}

# ===== ECS Configuration =====
variable "backend_cpu" {
  description = "CPU units for backend container (1 vCPU = 1024 CPU units)"
  type        = number
  default     = 512

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.backend_cpu)
    error_message = "Backend CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "backend_memory" {
  description = "Memory for backend container in MB"
  type        = number
  default     = 1024

  validation {
    condition     = var.backend_memory >= 512 && var.backend_memory <= 8192
    error_message = "Backend memory must be between 512 and 8192 MB."
  }
}

variable "frontend_cpu" {
  description = "CPU units for frontend container (1 vCPU = 1024 CPU units)"
  type        = number
  default     = 256

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.frontend_cpu)
    error_message = "Frontend CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "frontend_memory" {
  description = "Memory for frontend container in MB"
  type        = number
  default     = 512

  validation {
    condition     = var.frontend_memory >= 256 && var.frontend_memory <= 4096
    error_message = "Frontend memory must be between 256 and 4096 MB."
  }
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 1

  validation {
    condition     = var.backend_desired_count >= 1 && var.backend_desired_count <= 10
    error_message = "Backend desired count must be between 1 and 10."
  }
}

variable "frontend_desired_count" {
  description = "Desired number of frontend tasks"
  type        = number
  default     = 1

  validation {
    condition     = var.frontend_desired_count >= 1 && var.frontend_desired_count <= 10
    error_message = "Frontend desired count must be between 1 and 10."
  }
}

# ===== Auto Scaling Configuration =====
variable "backend_max_capacity" {
  description = "Maximum number of backend tasks for auto scaling"
  type        = number
  default     = 5

  validation {
    condition     = var.backend_max_capacity >= var.backend_desired_count
    error_message = "Backend max capacity must be greater than or equal to desired count."
  }
}

variable "frontend_max_capacity" {
  description = "Maximum number of frontend tasks for auto scaling"
  type        = number
  default     = 3

  validation {
    condition     = var.frontend_max_capacity >= var.frontend_desired_count
    error_message = "Frontend max capacity must be greater than or equal to desired count."
  }
}

variable "auto_scaling_target_cpu" {
  description = "Target CPU utilization percentage for auto scaling"
  type        = number
  default     = 70

  validation {
    condition     = var.auto_scaling_target_cpu >= 10 && var.auto_scaling_target_cpu <= 90
    error_message = "Auto scaling target CPU must be between 10 and 90 percent."
  }
}

# ===== Container Images =====
variable "backend_image" {
  description = "Docker image for backend container"
  type        = string
  default     = "voice-rag-backend:latest"
}

variable "frontend_image" {
  description = "Docker image for frontend container"
  type        = string
  default     = "voice-rag-frontend:latest"
}

# ===== API Keys and Secrets =====
variable "openai_api_key" {
  description = "OpenAI API key for language model access"
  type        = string
  sensitive   = true
  default     = ""

  validation {
    condition     = length(var.openai_api_key) == 0 || can(regex("^sk-[a-zA-Z0-9]{48}$", var.openai_api_key))
    error_message = "OpenAI API key must be empty or follow the format 'sk-' followed by 48 alphanumeric characters."
  }
}

variable "requesty_api_key" {
  description = "Requesty.ai API key for intelligent routing"
  type        = string
  sensitive   = true
  default     = ""
}

# ===== Logging Configuration =====
variable "log_retention_days" {
  description = "CloudWatch logs retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be one of the valid CloudWatch retention periods."
  }
}

# ===== Monitoring Configuration =====
variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = false
}

variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring for RDS (production only)"
  type        = bool
  default     = false
}

# ===== Security Configuration =====
variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = false
}

variable "enable_backup_retention" {
  description = "Enable backup retention for databases"
  type        = bool
  default     = true
}

# ===== Cost Optimization =====
variable "use_spot_instances" {
  description = "Use Fargate Spot instances for cost optimization (non-production)"
  type        = bool
  default     = false
}

variable "enable_cost_allocation_tags" {
  description = "Enable detailed cost allocation tags"
  type        = bool
  default     = true
}

# ===== Domain and SSL Configuration =====
variable "domain_name" {
  description = "Custom domain name for the application"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}

# ===== Backup Configuration =====
variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_period >= 0 && var.backup_retention_period <= 35
    error_message = "Backup retention period must be between 0 and 35 days."
  }
}

# ===== Performance Configuration =====
variable "enable_performance_insights" {
  description = "Enable Performance Insights for RDS"
  type        = bool
  default     = false
}

variable "performance_insights_retention_period" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([7, 731], var.performance_insights_retention_period)
    error_message = "Performance Insights retention period must be 7 or 731 days."
  }
}

# ===== Feature Flags =====
variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment for RDS (production recommended)"
  type        = bool
  default     = false
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for audit logging"
  type        = bool
  default     = false
}

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = false
}

# ===== Advanced Configuration =====
variable "custom_tags" {
  description = "Additional custom tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]

  validation {
    condition     = alltrue([for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))])
    error_message = "All CIDR blocks must be valid IPv4 CIDR notation."
  }
}