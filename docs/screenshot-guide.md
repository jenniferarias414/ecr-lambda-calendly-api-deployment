# Screenshot Guide

This guide explains the screenshots captured during the ECR Lambda Calendly API Deployment project.

The screenshots are organized into two folders:

```text
screenshots/full-walkthrough/
screenshots/selected-for-readme/
```

## Screenshot Folders

| Folder | Purpose |
|---|---|
| `screenshots/full-walkthrough/` | Full project build record, including setup, troubleshooting, validation, and cleanup |
| `screenshots/selected-for-readme/` | Smaller set of screenshots used in the main README |

## Full Walkthrough Screenshots

| Screenshot | What It Shows |
|---|---|
| `01-local-project-files.png` | Local project files in VS Code / terminal before deployment |
| `02-s3-output-bucket-created.png` | S3 output bucket created for Lambda CSV output |
| `03-secrets-manager-calendly-secret-created.png` | Calendly API token stored in Secrets Manager without exposing the value |
| `04-lambda-iam-role-created.png` | Lambda execution role created with required permissions |
| `05-ecr-repository-created.png` | Amazon ECR repository created for the Docker image |
| `06-docker-build-success.png` | Docker image built locally for Lambda deployment |
| `07a-buildx-direct-push-403-error.png` | Buildx direct push error captured for troubleshooting notes |
| `07b-ecr-image-pushed.png` | Terminal evidence that the image was pushed to ECR |
| `07c-ecr-image-pushed.png` | AWS ECR console showing the `latest` image tag |
| `08-lambda-created-from-ecr-image.png` | Lambda function created from the ECR image URI |
| `09-lambda-environment-variables-configured.png` | Lambda environment variables configured for S3 and Secrets Manager |
| `10-lambda-test-success.png` | Lambda test event returned a successful response |
| `11-s3-output-files-created.png` | Metrics CSV output appeared in the S3 bucket |
| `12-s3-metrics-csv-preview.png` | Metrics CSV preview showing output contents |
| `13-cloudwatch-logs-success.png` | CloudWatch logs showing successful Lambda execution |
| `14-cleanup-confirmation.png` | Cleanup validation after AWS resources were deleted |

## Selected README Screenshots

The selected screenshots focus on the strongest project evidence.

| Screenshot | Why It Was Selected |
|---|---|
| `02-s3-output-bucket-created.png` | Shows the target storage layer for generated CSV output |
| `03-secrets-manager-calendly-secret-created.png` | Shows secure token storage without exposing the token value |
| `04-lambda-iam-role-created.png` | Shows the Lambda runtime permission layer |
| `06-docker-build-success.png` | Shows that the local Docker image build completed |
| `07-ecr-image-pushed.png` | Shows that the image was pushed to Amazon ECR |
| `08-lambda-created-from-ecr-image.png` | Shows Lambda using the ECR image |
| `09-lambda-environment-variables-configured.png` | Shows runtime configuration without exposing secrets |
| `10-lambda-test-success.png` | Shows Lambda execution succeeded |
| `11-s3-output-files-created.png` | Shows output was written to S3 |
| `12-s3-metrics-csv-preview.png` | Shows the generated metrics CSV contents |
| `13-cloudwatch-logs-success.png` | Shows runtime logs for validation |
| `14-cleanup-confirmation.png` | Shows resources were cleaned up after validation |

## Notes on Sensitive Information

Screenshots should avoid exposing sensitive values.

Do not show:

- Calendly API token
- AWS access keys
- secret values
- private credentials
- internal work account details

Some screenshots may show resource names, ARNs, or image URIs. Those are not passwords or access keys, but public-facing screenshots should still be cropped or blurred when full account-level details are not needed.

## Screenshot Use in the Final README

The main README uses selected screenshots to prove the core project flow:

```text
Docker build
    ↓
ECR image push
    ↓
Lambda from container image
    ↓
Lambda test success
    ↓
S3 output
    ↓
CloudWatch logs
```

The troubleshooting screenshot for the Buildx direct push error is kept in the full walkthrough folder, but it is not part of the main README screenshot set.

## Main Takeaway

The screenshot set proves that the project was built and validated end to end:

1. Required AWS resources were created.
2. The Docker image was built locally.
3. The image was pushed to ECR.
4. Lambda was created from the ECR image.
5. Lambda retrieved its secret configuration and ran successfully.
6. Output was written to S3.
7. CloudWatch logs confirmed execution.
8. AWS resources were cleaned up after validation.
