# Cost Control and Cleanup

This project used AWS resources that can create ongoing cost if they are left active after testing. Cleanup was completed after validation.

## Cost-Control Goal

The goal was to build and validate the workflow, capture evidence, then remove the resources that were no longer needed.

The project followed this pattern:

```text
Build → Test → Validate → Screenshot → Clean up
```

## Resources Created

| Resource | Purpose | Cleanup Needed |
|---|---|---|
| AWS Lambda function | Ran the containerized Calendly API workflow | Yes |
| Amazon ECR repository | Stored the Lambda Docker image | Yes |
| ECR image | Container image used by Lambda | Yes |
| Amazon S3 bucket | Stored generated CSV output | Yes |
| S3 CSV files | Output from the Lambda run | Yes |
| AWS Secrets Manager secret | Stored the Calendly API token | Yes |
| IAM role | Gave Lambda runtime permissions | Yes |
| IAM inline policy | Allowed Lambda to read secret and write to S3 | Yes |
| CloudWatch log group | Stored Lambda execution logs | Yes |
| Local Docker image | Stored image on local laptop | Optional |

## Cleanup Order Used

The cleanup order matters because some resources depend on others.

### 1. Delete Lambda Function

The Lambda function was deleted first because it depended on the ECR image, IAM role, Secrets Manager secret, S3 bucket, and CloudWatch logs.

```bash
aws lambda delete-function \
  --function-name calendly-api-container-lambda \
  --region us-east-2 \
  --profile retail-poc
```

### 2. Delete ECR Repository and Image

The ECR repository was deleted with `--force` so the image inside the repository was also removed.

```bash
aws ecr delete-repository \
  --repository-name calendly-api-lambda \
  --region us-east-2 \
  --profile retail-poc \
  --force
```

### 3. Empty and Delete S3 Bucket

S3 buckets must be empty before they can be deleted.

```bash
aws s3 rm s3://calendly-api-output-jenny-9b2373 \
  --recursive \
  --profile retail-poc

aws s3 rb s3://calendly-api-output-jenny-9b2373 \
  --profile retail-poc
```

### 4. Delete Secrets Manager Secret

The Calendly token secret was deleted after Lambda was no longer running.

```bash
aws secretsmanager delete-secret \
  --secret-id calendly-api-token \
  --force-delete-without-recovery \
  --region us-east-2 \
  --profile retail-poc
```

`--force-delete-without-recovery` permanently deletes the secret instead of keeping it in a recovery window.

### 5. Delete IAM Role Policy and Role

The inline policy was removed first, then the AWS-managed Lambda logging policy was detached, then the role was deleted.

```bash
aws iam delete-role-policy \
  --role-name calendly-api-lambda-role \
  --policy-name calendly-api-lambda-s3-secrets-policy \
  --profile retail-poc

aws iam detach-role-policy \
  --role-name calendly-api-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --profile retail-poc

aws iam delete-role \
  --role-name calendly-api-lambda-role \
  --profile retail-poc
```

### 6. Delete CloudWatch Log Group

The CloudWatch log group was deleted after screenshots were captured.

```bash
aws logs delete-log-group \
  --log-group-name /aws/lambda/calendly-api-container-lambda \
  --region us-east-2 \
  --profile retail-poc
```

### 7. Remove Local Docker Image

This step only affects the local laptop. It does not delete anything from AWS.

```bash
docker image rm calendly-api-lambda:latest || true
```

## Cleanup Validation

After deletion, AWS CLI checks were run to confirm the main resources were no longer available.

```bash
aws lambda get-function \
  --function-name calendly-api-container-lambda \
  --region us-east-2 \
  --profile retail-poc || true

aws ecr describe-repositories \
  --repository-names calendly-api-lambda \
  --region us-east-2 \
  --profile retail-poc || true

aws s3 ls s3://calendly-api-output-jenny-9b2373 \
  --profile retail-poc || true

aws secretsmanager describe-secret \
  --secret-id calendly-api-token \
  --region us-east-2 \
  --profile retail-poc || true

aws iam get-role \
  --role-name calendly-api-lambda-role \
  --profile retail-poc || true
```

Expected cleanup validation messages included:

```text
Function not found
Repository does not exist
Bucket does not exist
Secrets Manager can't find the specified secret
Role not found
```

These errors were expected because they confirmed the resources had been removed.

## Cost Notes by Service

### Lambda

Lambda is usually low-cost for small tests, but it should still be deleted after the project is complete so it cannot be invoked later by mistake.

### ECR

ECR stores container images. Images are charged based on storage, so the repository and image were removed after validation.

### S3

S3 charges for storage and requests. The output bucket was emptied and deleted after screenshots were captured.

### Secrets Manager

Secrets Manager can create ongoing monthly charges per secret. The Calendly token secret was deleted after Lambda testing was complete.

### CloudWatch Logs

CloudWatch log storage can create small ongoing costs. The log group was deleted after successful execution evidence was captured.

### IAM

IAM roles and policies do not directly create compute/storage cost, but unused permissions should still be cleaned up.

## Final Cleanup Result

The project resources were removed after validation. The final cleanup screenshot confirms that the major AWS resources were no longer found.

Screenshot:

```text
screenshots/full-walkthrough/14-cleanup-confirmation.png
```
