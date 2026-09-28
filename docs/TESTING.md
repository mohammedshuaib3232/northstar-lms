# Test plan and results

| Check | Expected result | Result |
|---|---|---|
| Python source parse | No syntax errors | Passed (AST parse) |
| Home page render | HTTP 200 with hero and empty course state | Passed in GitHub Actions |
| Student registration | Account created, password hashed, session established | Passed in GitHub Actions |
| Admin course creation | Authorized admin creates unique course code | Passed in GitHub Actions |
| Course view | Student can view published course page | Passed in GitHub Actions |
| Authorization | Student receives HTTP 403 on `/admin` | Passed in GitHub Actions |
| Invalid login | Wrong password rejected with generic response | Passed in GitHub Actions |
| Terraform format/validate/plan | Infrastructure configuration parses and proposed resources are visible | Not run (Terraform CLI and AWS target not available) |
| S3 upload and signed download | File stored privately and short-lived URL returned | Requires AWS credentials; not run locally |
| RDS connectivity and CloudWatch streaming | App connects and container logs arrive | Requires AWS deployment; not run locally |

The included pytest suite targets core flows with an isolated SQLite database. GitHub Actions completed successfully on the main branch: dependencies installed, Python compilation passed, and all four pytest cases passed. It was not run locally in this environment. Cloud behavior remains pending because no AWS resources were provisioned.
