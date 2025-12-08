# Terraform configuration for testing IaC scanning
terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Security-focused AWS provider configuration
provider "aws" {
  region = "us-east-1"
  
  # Assume role for better security
  assume_role {
    role_arn = "arn:aws:iam::123456789012:role/TerraformRole"
  }
  
  # Enable secure defaults
  default_tags {
    tags = {
      Environment = "production"
      ManagedBy   = "Terraform"
      Project     = "DevSecOps"
    }
  }
}

# Secure S3 bucket for logs
resource "aws_s3_bucket" "security_logs" {
  bucket = "devsecops-security-logs-2024"
  
  tags = {
    Name        = "Security Logs"
    Environment = "Production"
  }
}

resource "aws_s3_bucket_acl" "security_logs_acl" {
  bucket = aws_s3_bucket.security_logs.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "security_logs_versioning" {
  bucket = aws_s3_bucket.security_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "security_logs_encryption" {
  bucket = aws_s3_bucket.security_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "security_logs_block" {
  bucket = aws_s3_bucket.security_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Security group with minimum permissions
resource "aws_security_group" "app_security" {
  name        = "devsecops-app-sg"
  description = "Security group for DevSecOps application"
  vpc_id      = "vpc-12345678"

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP for redirect"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "devsecops-app-security-group"
  }
}
