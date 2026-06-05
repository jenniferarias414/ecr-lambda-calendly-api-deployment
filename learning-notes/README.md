# Learning Notes

This folder contains study-focused notes for the ECR Lambda Calendly API Deployment project.

The main README gives the project summary, architecture, screenshots, and final outcome. These learning notes go deeper into the concepts behind the project: Docker images, Amazon ECR, Lambda container deployment, Secrets Manager, IAM permissions, S3 output, and CloudWatch validation.

## Notes in This Folder

| File | Purpose |
|---|---|
| `docker-ecr-lambda-notes.md` | Explains Docker, images, containers, ECR, Lambda container images, and the build/push/deploy flow |
| `service-by-service-notes.md` | Explains each AWS service and local tool used in the project |
| `api-and-secrets-notes.md` | Explains the Calendly API call pattern, Bearer token auth, and Secrets Manager usage |

## Main Project Flow

```text
Local Python code
    ↓
Dockerfile + requirements.txt
    ↓
Docker image built locally
    ↓
Amazon ECR repository
    ↓
AWS Lambda container function
    ↓
Calendly API
    ↓
pandas metrics processing
    ↓
Amazon S3 CSV output
    ↓
CloudWatch Logs validation
```

## Why This Project Uses Docker

A regular Lambda function can run simple Python code, but this project uses dependencies like:

```text
requests
pandas
boto3
awslambdaric
```

Docker packages the code, dependencies, and runtime setup together into one image.

That image can then be pushed to Amazon ECR and used by Lambda.

## Why This Project Uses ECR

Amazon ECR is the AWS container image registry.

Lambda cannot run a Docker image that only exists locally on a laptop. The image needs to be stored in a place AWS Lambda can access.

For this project:

```text
Docker image on laptop
    ↓
Pushed to Amazon ECR
    ↓
Lambda created from ECR image URI
```

## Why This Project Uses Secrets Manager

The Calendly API requires an access token.

Instead of hardcoding the token in the Python code, the token was stored in AWS Secrets Manager.

Lambda used this environment variable:

```text
CALENDLY_SECRET_NAME=calendly-api-token
```

Then the code retrieved the token at runtime using boto3.

## Why This Project Uses S3

The Lambda function writes API output to S3 as CSV files.

During validation, the Calendly account had no scheduled events available through the API, so the scheduled-events extract was empty and skipped. The metrics CSV still uploaded successfully.

Final S3 output example:

```text
calendly/campaign_metrics_2026-06-04_12-18-15.csv
```

## Why This Project Uses CloudWatch

CloudWatch Logs confirmed what happened when Lambda ran.

The logs showed that Lambda:

- Started successfully
- Retrieved the Calendly organization URI
- Retrieved one Calendly event type
- Found zero scheduled events
- Skipped the empty scheduled-events CSV
- Uploaded the metrics CSV to S3
- Completed successfully

## Main Concepts to Review

| Concept | Where It Appears |
|---|---|
| Docker image | Local build step |
| Container image registry | Amazon ECR |
| Lambda container deployment | Lambda function created from ECR image URI |
| External API call | Calendly API requests |
| Secret storage | AWS Secrets Manager |
| Runtime permissions | IAM Lambda execution role |
| CSV output | Amazon S3 |
| Execution logs | CloudWatch Logs |
| Cleanup | Lambda, ECR, S3, Secrets Manager, IAM, CloudWatch |

## Main Takeaway

This project demonstrates how a local Python API workflow can be packaged as a container image and deployed to AWS Lambda.

The important pattern is:

```text
Build the code locally
Package it with Docker
Store the image in ECR
Run it with Lambda
Keep secrets in Secrets Manager
Write output to S3
Validate with CloudWatch
Clean up resources
```
