output "application_url" { value = "http://${aws_instance.app.public_dns}" }
output "instance_public_ip" { value = aws_instance.app.public_ip }
output "materials_bucket" { value = aws_s3_bucket.materials.id }
output "database_endpoint" { value = aws_db_instance.lms.address }
output "cloudwatch_log_group" { value = aws_cloudwatch_log_group.app.name }
output "cloudwatch_dashboard" { value = aws_cloudwatch_dashboard.lms.dashboard_name }
