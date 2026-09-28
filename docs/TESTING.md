# Test plan and results

| Check | Expected result | Result |
|---|---|---|
| Python source parse | No syntax errors | Passed (AST parse across 7 Python files) |
| Home page render | HTTP 200 with hero and empty course state | Test defined; not run (dependencies unavailable) |
| Student registration | Account created, password hashed, session established | Test defined; not run (dependencies unavailable) |
| Admin course creation | Authorized admin creates unique course code | Test defined; not run (dependencies unavailable) |
| Course view | Student can view published course page | Test defined; not run (dependencies unavailable) |
| Authorization | Student receives HTTP 403 on `/admin` | Test defined; not run (dependencies unavailable) |
| Invalid login | Wrong password rejected with generic response | Test defined; not run (dependencies unavailable) |
| Terraform format/validate/plan | Infrastructure configuration parses and proposed resources are visible | Not run (Terraform CLI and AWS target not available) |
| S3 upload and signed download | File stored privately and short-lived URL returned | Requires AWS credentials; not run locally |
| RDS connectivity and CloudWatch streaming | App connects and container logs arrive | Requires AWS deployment; not run locally |

The included pytest suite targets core flows with an isolated SQLite database. It was not run in this environment because dependency installation was denied. Cloud behavior remains pending because no AWS credentials or repository deployment target were provided.
