variable "aws_region" {
  type    = string
  default = "ap-south-1"
}
variable "project_name" {
  type    = string
  default = "northstar-lms"
}
variable "ssh_allowed_cidr" {
  type        = string
  description = "Trusted public IPv4 CIDR allowed to SSH, e.g. 203.0.113.10/32. Never use 0.0.0.0/0."
}
variable "ssh_public_key" {
  type        = string
  description = "OpenSSH public key installed as the EC2 key pair. Keep the private key outside the repository."
}
variable "app_repo_url" {
  type        = string
  description = "HTTPS clone URL of the public GitHub repository."
}
variable "db_password" {
  type      = string
  sensitive = true
}
variable "instance_type" {
  type    = string
  default = "t3.small"
}
variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}
variable "db_name" {
  type    = string
  default = "northstar"
}
variable "db_username" {
  type    = string
  default = "lmsapp"
}
variable "secret_key" {
  type      = string
  sensitive = true
}
variable "log_retention_days" {
  type    = number
  default = 30
}
