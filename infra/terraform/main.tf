locals {
  name = var.project_name
  tags = { Project = local.name, ManagedBy = "Terraform" }
}
resource "aws_vpc" "lms" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = merge(local.tags, { Name = "${local.name}-vpc" })
}
resource "aws_internet_gateway" "lms" {
  vpc_id = aws_vpc.lms.id
  tags   = local.tags
}
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.lms.id
  cidr_block              = count.index == 0 ? "10.42.1.0/24" : "10.42.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags                    = merge(local.tags, { Name = "${local.name}-public-${count.index + 1}" })
}
resource "aws_subnet" "private" {
  count                   = 2
  vpc_id                  = aws_vpc.lms.id
  cidr_block              = count.index == 0 ? "10.42.11.0/24" : "10.42.12.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = false
  tags                    = merge(local.tags, { Name = "${local.name}-private-${count.index + 1}" })
}
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.lms.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lms.id
  }
  tags = local.tags
}
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
resource "aws_security_group" "app" {
  name        = "${local.name}-app"
  description = "Web application and restricted administration ingress"
  vpc_id      = aws_vpc.lms.id
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = local.tags
}
resource "aws_security_group" "db" {
  name        = "${local.name}-db"
  description = "PostgreSQL access only from application instance"
  vpc_id      = aws_vpc.lms.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = local.tags
}
resource "aws_key_pair" "deploy" {
  key_name   = "${local.name}-deploy"
  public_key = var.ssh_public_key
  tags       = local.tags
}
resource "aws_db_subnet_group" "lms" {
  name       = "${local.name}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
  tags       = local.tags
}
resource "aws_db_instance" "lms" {
  identifier                 = "${local.name}-postgres"
  engine                     = "postgres"
  instance_class             = var.db_instance_class
  allocated_storage          = 20
  max_allocated_storage      = 100
  storage_type               = "gp3"
  storage_encrypted          = true
  db_name                    = var.db_name
  username                   = var.db_username
  password                   = var.db_password
  db_subnet_group_name       = aws_db_subnet_group.lms.name
  vpc_security_group_ids     = [aws_security_group.db.id]
  publicly_accessible        = false
  backup_retention_period    = 7
  auto_minor_version_upgrade = true
  deletion_protection        = false
  skip_final_snapshot        = true
  tags                       = local.tags
}
resource "aws_s3_bucket" "materials" {
  bucket_prefix = "${local.name}-materials-"
  tags          = local.tags
}
resource "aws_s3_bucket_public_access_block" "materials" {
  bucket                  = aws_s3_bucket.materials.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "materials" {
  bucket = aws_s3_bucket.materials.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_versioning" "materials" {
  bucket = aws_s3_bucket.materials.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_iam_role" "ec2" {
  name = "${local.name}-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
  tags = local.tags
}
resource "aws_iam_role_policy" "ec2" {
  name = "${local.name}-s3-logs"
  role = aws_iam_role.ec2.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:PutObject", "s3:GetObject", "s3:AbortMultipartUpload"], Resource = "${aws_s3_bucket.materials.arn}/*" },
      { Effect = "Allow", Action = ["s3:ListBucket"], Resource = aws_s3_bucket.materials.arn },
      { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"], Resource = "${aws_cloudwatch_log_group.app.arn}:*" }
    ]
  })
}
resource "aws_iam_instance_profile" "ec2" {
  name = "${local.name}-instance-profile"
  role = aws_iam_role.ec2.name
}
resource "aws_cloudwatch_log_group" "app" {
  name              = "/${local.name}/application"
  retention_in_days = var.log_retention_days
  tags              = local.tags
}
resource "aws_instance" "app" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  key_name                    = aws_key_pair.deploy.key_name
  associate_public_ip_address = true
  metadata_options {
    http_tokens                 = "required"
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 2
  }
  root_block_device {
    encrypted   = true
    volume_size = 16
    volume_type = "gp3"
  }
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    app_repo_url = var.app_repo_url
    db_url       = "postgresql+psycopg://${var.db_username}:${urlencode(var.db_password)}@${aws_db_instance.lms.address}:${aws_db_instance.lms.port}/${var.db_name}"
    secret_key   = var.secret_key
    aws_region   = var.aws_region
    s3_bucket    = aws_s3_bucket.materials.id
    log_group    = aws_cloudwatch_log_group.app.name
  })
  user_data_replace_on_change = true
  depends_on                   = [aws_db_instance.lms, aws_iam_role_policy.ec2]
  tags                         = merge(local.tags, { Name = "${local.name}-app" })
}
resource "aws_cloudwatch_metric_alarm" "ec2_status" {
  alarm_name          = "${local.name}-ec2-status-check"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 1
  dimensions          = { InstanceId = aws_instance.app.id }
  alarm_description  = "EC2 instance status check failure"
  tags                = local.tags
}
resource "aws_cloudwatch_metric_alarm" "ec2_cpu" {
  alarm_name          = "${local.name}-ec2-cpu-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  dimensions          = { InstanceId = aws_instance.app.id }
  alarm_description  = "EC2 average CPU at or above 80 percent for ten minutes"
  tags                = local.tags
}
resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${local.name}-rds-free-storage-low"
  comparison_operator = "LessThanThreshold"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 5368709120
  dimensions          = { DBInstanceIdentifier = aws_db_instance.lms.id }
  alarm_description  = "RDS free storage below 5 GiB"
  tags                = local.tags
}
resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "${local.name}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 30
  dimensions          = { DBInstanceIdentifier = aws_db_instance.lms.id }
  alarm_description  = "RDS database connections above 30"
  tags                = local.tags
}
resource "aws_cloudwatch_dashboard" "lms" {
  dashboard_name = "${local.name}-operations"
  dashboard_body = jsonencode({
    widgets = [
      { type = "metric", x = 0, y = 0, width = 12, height = 6, properties = { title = "EC2 CPU utilization", region = var.aws_region, stat = "Average", period = 300, metrics = [["AWS/EC2", "CPUUtilization", "InstanceId", aws_instance.app.id]] } },
      { type = "metric", x = 12, y = 0, width = 12, height = 6, properties = { title = "EC2 status checks", region = var.aws_region, stat = "Maximum", period = 60, metrics = [["AWS/EC2", "StatusCheckFailed", "InstanceId", aws_instance.app.id]] } },
      { type = "metric", x = 0, y = 6, width = 12, height = 6, properties = { title = "RDS free storage", region = var.aws_region, stat = "Average", period = 300, metrics = [["AWS/RDS", "FreeStorageSpace", "DBInstanceIdentifier", aws_db_instance.lms.id]] } },
      { type = "metric", x = 12, y = 6, width = 12, height = 6, properties = { title = "RDS connections", region = var.aws_region, stat = "Maximum", period = 300, metrics = [["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", aws_db_instance.lms.id]] } }
    ]
  })
}
