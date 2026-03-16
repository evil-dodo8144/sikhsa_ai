provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "scaledown-tutor-vpc"
  }
}

# Subnets
resource "aws_subnet" "public" {
  count = 2
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.${count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "scaledown-tutor-public-${count.index}"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "scaledown-tutor-cluster"
}

# RDS Instance
resource "aws_db_instance" "postgres" {
  identifier = "scaledown-tutor-db"
  engine = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  
  db_name = "tutordb"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name = aws_db_subnet_group.main.name
  
  skip_final_snapshot = true
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id = "scaledown-tutor-cache"
  engine = "redis"
  node_type = "cache.t3.micro"
  num_cache_nodes = 1
  parameter_group_name = "default.redis7"
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
}