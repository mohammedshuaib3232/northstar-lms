# Deployment guide

## Local development

Follow the quick start in `README.md`. For a production-like local database, install PostgreSQL and set `DATABASE_URL=postgresql+psycopg://...`. Use `STORAGE_BACKEND=local` locally; S3 is enabled by the EC2 instance role in AWS.

## AWS deployment with Terraform

The Terraform configuration provisions a VPC, EC2 application host, RDS PostgreSQL, private S3 bucket with versioning and default encryption, an EC2 instance profile with scoped S3/CloudWatch permissions, security groups, and a CloudWatch Logs group. It expects a public GitHub repository for first boot.

1. Create an AWS account and install AWS CLI v2 and Terraform 1.6+ on your workstation. Configure a non-root IAM identity with permissions to create the resources in `infra/terraform/`.
2. Create a GitHub repository and push this directory's contents. Set `app_repo_url` to its HTTPS clone URL.
3. From `infra/terraform/`, copy `terraform.tfvars.example` to `terraform.tfvars`. Set `ssh_allowed_cidr` to a trusted public IPv4 `/32`, update the repository URL, and provide an OpenSSH public key as `ssh_public_key`. Keep the matching private key outside the repository.
4. Set sensitive values in your shell rather than committing them. Generate long random values for `TF_VAR_db_password` and `TF_VAR_secret_key`; keep Terraform state encrypted and private because it can contain credentials and user data.
5. Run `terraform init`, `terraform fmt -recursive`, `terraform validate`, and `terraform plan`. Review the plan and estimated charges. Then run `terraform apply` to create the resources.
6. Wait for EC2 user data to finish and visit the `application_url` output. The assignment demo uses HTTP. For production, front the instance with an HTTPS Application Load Balancer and ACM certificate, configure secure cookies, and allow only the load balancer security group to reach the app.
7. Initialize the schema and create the initial administrator over SSH:

   ```bash
   sudo docker exec -u 10001 northstar-lms flask --app run.py init-db
   sudo docker exec -u 10001 -it northstar-lms flask --app run.py create-admin
   ```

   The CLI prompts for the administrator email and password. Admin signup is not available to the public.
8. Review `/northstar-lms/application` in CloudWatch Logs and the `northstar-lms-operations` dashboard. Terraform creates alarms for EC2 status checks, sustained CPU, low RDS free storage, and high database connections. Add notification actions to an SNS topic you own, enable billing alerts, and validate a restore from an RDS backup.

## GitHub CI and deployment

The CI workflow runs compile checks and pytest on pushes and pull requests. To enable automated EC2 deployment, configure repository secrets `EC2_HOST` (instance DNS/IP), `EC2_USER` (`ec2-user`), and `EC2_SSH_KEY` (a deploy-only private key whose matching public key is installed for that user). The deploy workflow runs tests, then connects to the instance, pulls `main`, rebuilds the image, and restarts the container.

Terraform installs the supplied public key on EC2; store the matching private key only as the GitHub `EC2_SSH_KEY` secret. Restrict SSH ingress to a trusted static runner or use AWS Systems Manager Session Manager for production. GitHub-hosted runner IP ranges change, so a static trusted runner is preferred.

## Rollback and teardown

For an application rollback, redeploy a known Git commit and rebuild the image. For a database rollback, use RDS point-in-time recovery and validate the restored instance before cutover. `terraform destroy` removes the demo infrastructure and database; copy needed submissions first. Bucket versioning can retain object versions, and deletion protection is disabled for this educational stack.

## Cost and production notes

EC2, RDS, S3, CloudWatch, and data transfer can incur charges. Select a region and sizes appropriate to the assignment and delete demo resources after submission. The sample has a single EC2 app and no load balancer, so it is not highly available. The demo uses public EC2 HTTP ingress. For production, use TLS, a load balancer, a private app subnet, private RDS subnets, NAT or VPC endpoints, secrets management, health checks, least-privilege operations, managed schema migrations, and tested backups.
