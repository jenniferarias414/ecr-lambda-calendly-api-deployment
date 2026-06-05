# Project Status

## Final Status

Complete.

The project was built, tested, validated, screenshotted, and cleaned up.

## Project Summary

This project deployed a Python Calendly API workflow as an AWS Lambda container image.

The workflow used Docker to package the Python code and dependencies, Amazon ECR to store the image, AWS Lambda to run the containerized function, AWS Secrets Manager to store the Calendly API token, Amazon S3 to store generated CSV output, and CloudWatch Logs to validate execution.

## Final Architecture

```text
Calendly API
    ↓
AWS Lambda container function
    ↓
AWS Secrets Manager
    ↓
Python requests + pandas processing
    ↓
Amazon S3 CSV output
    ↓
Amazon CloudWatch Logs
```

## What Was Built

- Local Python project using the provided Calendly Lambda source files
- Cleaned `lambda_function.py` to avoid logging sensitive token values
- Docker image for the Lambda runtime
- Amazon ECR repository for storing the image
- S3 bucket for output CSV files
- Secrets Manager secret for the Calendly API token
- IAM role for Lambda execution
- Lambda function created from the ECR image URI
- Lambda environment variables for bucket, folder path, and secret name
- CloudWatch log validation
- Cleanup process for cost control

## AWS Region

The project was built in:

```text
us-east-2
```

## AWS Profile Used

The personal AWS CLI profile used for this project was:

```text
retail-poc
```

The work AWS profile was not used.

## Main Resource Names

| Resource | Name |
|---|---|
| ECR repository | `calendly-api-lambda` |
| Lambda function | `calendly-api-container-lambda` |
| Lambda IAM role | `calendly-api-lambda-role` |
| Secrets Manager secret | `calendly-api-token` |
| S3 output bucket | `calendly-api-output-jenny-9b2373` |
| S3 output prefix | `calendly/` |

## Local Tools Used

| Tool | Purpose |
|---|---|
| VS Code | Edited project files and organized repo structure |
| Terminal | Ran AWS CLI, Docker, and validation commands |
| AWS CLI | Created and validated AWS resources |
| Docker Desktop | Built the Lambda container image locally |
| Docker Buildx | Rebuilt the image with Lambda-compatible settings |
| AWS Console | Verified resources and captured screenshots |

## Code Changes Made

The downloaded source code was adjusted before deployment.

Key cleanup:

- Removed direct token printing so the Calendly token would not be written to CloudWatch Logs
- Required `S3_BUCKET_NAME` and `CALENDLY_SECRET_NAME` from Lambda environment variables
- Used Secrets Manager for the API token instead of hardcoding it
- Added request timeouts for external API calls
- Improved logging while avoiding secret exposure
- Generated timestamps inside the Lambda handler
- Preserved the overall project behavior from the provided source

## Docker Image Build

The image was built for:

```text
linux/amd64
```

The Lambda function was configured for:

```text
x86_64
```

This matched the Lambda runtime architecture. Docker Desktop showed an AMD64 warning locally because the Mac can run Apple Silicon/ARM workloads, but the project image needed to be compatible with the Lambda configuration.

## ECR Deployment

The Docker image was pushed to Amazon ECR with the tag:

```text
latest
```

The ECR repository showed the pushed image in the AWS Console.

## Lambda Deployment

The Lambda function was created using:

```text
Package type: Image
Architecture: x86_64
Memory: 1024 MB
Timeout: 120 seconds
```

Environment variables configured:

| Variable | Value |
|---|---|
| `S3_BUCKET_NAME` | S3 output bucket |
| `S3_FOLDER_PATH` | `calendly/` |
| `CALENDLY_SECRET_NAME` | `calendly-api-token` |

## Validation Results

The Lambda test returned a successful response:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Lambda execution completed successfully\"}"
}
```

The function successfully:

- Started from the ECR container image
- Retrieved the Calendly API token from Secrets Manager
- Called the Calendly API
- Retrieved the Calendly organization URI
- Retrieved one Calendly event type
- Found zero scheduled events in the personal Calendly account
- Created a metrics CSV
- Uploaded the metrics CSV to S3
- Wrote successful execution logs to CloudWatch

## S3 Output

The final S3 output included:

```text
calendly/campaign_metrics_2026-06-04_12-18-15.csv
```

The scheduled calls extract was skipped because there were no scheduled Calendly events available in the personal Calendly account at test time.

The metrics CSV preview showed:

```csv
timestamp,total_scheduled_calls,completed_calls,completed_calls_percentage
2026-06-04_12-18-15,0,0,0
```

## Troubleshooting Encountered

### ECR direct Buildx push returned 403

A direct Buildx push failed with:

```text
403 Forbidden
```

The fix was to build locally with `--load`, then use a normal `docker push`.

### Lambda rejected the first image manifest

The first Lambda create attempt returned:

```text
The image manifest, config or layer media type for the source image is not supported.
```

The fix was to rebuild the image using:

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  --load \
  -t calendly-api-lambda:latest \
  .
```

Then the image was tagged and pushed to ECR again.

## Cleanup Completed

The following resources were deleted after validation:

- Lambda function
- ECR repository and image
- S3 output bucket and CSV output
- Secrets Manager secret
- Lambda IAM role and inline policy
- CloudWatch log group
- Local Docker image

Cleanup was validated with AWS CLI commands showing the deleted resources were no longer found.

## Final Result

The project successfully demonstrated a containerized Lambda deployment pattern for a Python API workflow.

The final implementation used Docker, ECR, Lambda, Secrets Manager, S3, IAM, and CloudWatch together in a small end-to-end cloud deployment.
