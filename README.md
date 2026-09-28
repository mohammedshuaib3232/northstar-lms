# Cloud-Based Learning Management System

A small, deployable LMS reference implementation for the assignment brief. Students can register, browse courses, download learning materials, submit assignments, and view announcements. Administrators can create courses, publish materials and assignments, review submissions, and post announcements.

## Stack

- Python 3.11, Flask, Flask-Login, Flask-WTF, SQLAlchemy
- SQLite for local development; PostgreSQL for production
- AWS S3 for uploaded course files (local file storage for development)
- AWS EC2, RDS PostgreSQL, VPC security groups, IAM instance profile, CloudWatch Logs, dashboard, and alarms
- GitHub Actions for automated test and compile checks

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; on macOS/Linux use: cp .env.example .env
flask --app run.py init-db
flask --app run.py create-admin
flask --app run.py run --debug
```

The admin command prompts for an email and password if they are not set in `ADMIN_EMAIL` and `ADMIN_PASSWORD`. Open http://127.0.0.1:5000. Create a student account using the registration page.

## Configuration

Copy `.env.example` to `.env`. Use a long random `SECRET_KEY`. `DATABASE_URL` accepts SQLAlchemy URLs such as `sqlite:///lms.db` or `postgresql+psycopg://user:password@host:5432/lms`. Set `STORAGE_BACKEND=s3`, `S3_BUCKET`, and `AWS_REGION` to use S3. In AWS, the EC2 instance role grants access; do not put AWS access keys in the app environment.

## Features and security

- Werkzeug password hashing, role checks, CSRF protection, secure session cookie defaults, and basic session-scoped login throttling.
- Upload allowlist (PDF, common office documents, text, images, and video), size cap, generated object names, and S3 private objects with short-lived signed download URLs.
- Admin bootstrap is a CLI action and does not expose public admin registration.
- Configure TLS at a reverse proxy or load balancer before internet production use. Restrict SSH in Terraform to a trusted CIDR. Back up PostgreSQL and S3 according to your retention policy.

## AWS deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) and `infra/terraform/`. The Terraform plan creates a VPC, public application subnet, private PostgreSQL RDS instance, S3 bucket, EC2 instance profile, CloudWatch log group, and security groups. It installs Docker and runs the app container on EC2. The app endpoint is HTTP for assignment/demo use; add an HTTPS load balancer and ACM certificate before production.

Do not commit `.env`, SSH keys, database passwords, or AWS credentials. The Terraform database password is supplied at apply time and stored in Terraform state, so protect the state backend. For a real deployment, use a remote encrypted state backend and rotate credentials.

## Submission visuals

![Northstar LMS AWS architecture](docs/architecture.svg)

`docs/screenshots/` contains three explicitly labeled static interface previews. They are not live browser captures; recapture the screens after running the app before submitting if your instructor requires runtime screenshots.

## Repository map

```text
app/                 Flask application, models, routes, templates, static assets
infra/terraform/     AWS infrastructure as code
docs/                Architecture and screenshots
tests/               Pytest fixtures and application tests
.github/workflows/   GitHub Actions CI and EC2 deployment workflow
Northstar_LMS_Project_Report.pdf
                     13-page assignment report
Northstar_LMS_Source.zip
                     Portable copy of the complete source package
```

## Verification

Run `python -m pytest -q` and `python -m compileall -q app run.py`. GitHub Actions runs both checks on pushes and pull requests. `docs/screenshots/` currently contains labeled static interface previews; replace them with live browser captures after starting the app. Terraform deployment and AWS service checks require your AWS account and are not run by CI.

## License

Educational project. Review dependencies and security settings before adapting for production.
