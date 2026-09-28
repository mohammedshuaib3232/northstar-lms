# Security controls

| Area | Implemented control | Follow-up for production |
|---|---|---|
| Authentication | Werkzeug password hashing, Flask-Login, no public admin signup | Add MFA/SSO and centralized account lifecycle |
| Authorization | Admin-only management routes; student routes require login where appropriate | Review course enrollment rules and object-level permissions |
| Web requests | Flask-WTF CSRF tokens; HttpOnly and SameSite cookies | Enable TLS and `SESSION_COOKIE_SECURE=true`; add CSP/HSTS at the proxy |
| Uploads | Extension allowlist, generated storage keys, 50 MiB request cap | Add malware scanning, quotas, and content inspection |
| Object storage | Private S3 bucket, public access block, server-side encryption, signed downloads | Add lifecycle policies and retention/legal controls |
| Database | RDS encryption, seven-day backup retention, DB SG allows only app SG | Use Secrets Manager, maintenance windows, PITR drills, and private subnets |
| Compute | IMDSv2 required, encrypted root volume, app runs as non-root in container | Place behind ALB, remove public SSH, patch AMI, harden Docker host |
| IAM | Instance role with bucket-scoped object access and log-write permissions | Split read/write and deployment roles; review IAM Access Analyzer findings |
| Monitoring | Docker stdout/stderr to CloudWatch Logs; EC2/RDS dashboard and metric alarms | Add alarm notification routing and audit trails |

## IAM policy shape

The EC2 role can list the single materials bucket, read/write objects only under that bucket, and create/append streams only in the LMS CloudWatch log group. It has no broad administrator policy and no long-lived AWS keys are stored in the app container.

## Known demo limitations

The HTTP endpoint is for a classroom demo only. The request/session login throttle is per signed browser session and is not a robust distributed rate limiter. A production deployment should use server-side throttling (for example, a shared Redis-backed limiter), TLS, secure cookies, managed secrets, S3 lifecycle and malware controls, and centralized alerting.
