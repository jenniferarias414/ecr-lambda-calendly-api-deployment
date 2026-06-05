# Docker, ECR, and Lambda Container Notes

These notes explain the Docker/ECR/Lambda part of the project in a more detailed study format.

This was the core deployment pattern:

```text
Python code
    ↓
Dockerfile
    ↓
Docker image
    ↓
Amazon ECR
    ↓
AWS Lambda container function
```

## Why This Project Uses Docker

A basic Lambda function can run Python code directly, but this project uses a container image.

The reason is that the application needs a full packaged runtime that includes:

- the Python code
- Python dependencies
- Lambda runtime support
- deployment instructions
- a consistent environment for AWS Lambda

The project dependencies were listed in `requirements.txt`:

```text
boto3==1.34.75
pandas==2.2.3
requests==2.31.0
awslambdaric==2.0.2
```

The important idea:

```text
Docker packages the application and dependencies together.
```

## Dockerfile

The Dockerfile is the set of instructions used to build the image.

Project Dockerfile:

```dockerfile
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.9

WORKDIR /var/task

COPY lambda_function.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/var/lang/bin/python3.9", "-m", "awslambdaric"]
CMD ["lambda_function.lambda_handler"]
```

## What Each Dockerfile Line Means

### Base Image

```dockerfile
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.9
```

This starts from an AWS-provided Lambda Python base image.

That means the image already has the basic Lambda runtime structure needed to run Python in Lambda.

The image was built for:

```text
linux/amd64
```

That matched the Lambda function architecture:

```text
x86_64
```

### Working Directory

```dockerfile
WORKDIR /var/task
```

`/var/task` is the normal location where Lambda expects application code inside the container.

### Copy Code Into the Image

```dockerfile
COPY lambda_function.py .
COPY requirements.txt .
```

These lines copy the Lambda code and dependency file into the image.

### Install Dependencies

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

This installs the required Python packages into the image.

The main packages used were:

| Package | Purpose |
|---|---|
| `requests` | Calls the Calendly API |
| `pandas` | Creates DataFrames and CSV output |
| `boto3` | Calls AWS services such as S3 and Secrets Manager |
| `awslambdaric` | Lambda runtime interface client used by the container |

### Entry Point

```dockerfile
ENTRYPOINT ["/var/lang/bin/python3.9", "-m", "awslambdaric"]
```

This tells the container to start using the AWS Lambda Runtime Interface Client.

### Command

```dockerfile
CMD ["lambda_function.lambda_handler"]
```

This tells Lambda which handler function to run.

In this project:

```text
File: lambda_function.py
Function: lambda_handler
```

So the handler is:

```text
lambda_function.lambda_handler
```

## Docker Image vs. Container

These terms are easy to mix up.

### Docker Image

A Docker image is the packaged application.

It includes:

- code
- dependencies
- runtime setup
- instructions for how to start

A helpful way to think about it:

```text
Docker image = packaged version of the app
```

### Container

A container is a running instance of the image.

A helpful way to think about it:

```text
Container = image while it is running
```

In this project, Lambda runs the container from the image stored in ECR.

## Why Amazon ECR Is Needed

ECR means Elastic Container Registry.

It is AWS storage for Docker container images.

Lambda cannot run an image that only exists on the local laptop. The image needs to be somewhere AWS can access.

That is why the workflow is:

```text
Build image locally
    ↓
Push image to ECR
    ↓
Create Lambda from ECR image URI
```

## ECR Image URI

The ECR image URI identifies the exact image Lambda should use.

The pattern is:

```text
account-id.dkr.ecr.region.amazonaws.com/repository-name:tag
```

For this project, the ECR repository was:

```text
calendly-api-lambda
```

The image tag was:

```text
latest
```

The public documentation and screenshots should avoid exposing account-level details where possible, but the format is useful to understand.

## Build Command

The working build command used Docker Buildx:

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  --load \
  -t calendly-api-lambda:latest \
  .
```

### What the Build Flags Mean

| Flag | Meaning |
|---|---|
| `--platform linux/amd64` | Builds the image for the architecture used by the Lambda function |
| `--provenance=false` | Disables provenance metadata that caused Lambda image compatibility issues |
| `--sbom=false` | Disables SBOM metadata for this build |
| `--load` | Loads the built image into local Docker images |
| `-t calendly-api-lambda:latest` | Tags the local image name and version |
| `.` | Uses the current folder as the Docker build context |

## Why `--provenance=false` Was Needed

The first Lambda create attempt failed with:

```text
The image manifest, config or layer media type for the source image is not supported.
```

This meant Lambda could see the image in ECR, but the image metadata/manifest format was not acceptable for Lambda.

The fix was to rebuild with:

```text
--provenance=false
```

and:

```text
--sbom=false
```

Then the image was loaded locally, tagged, and pushed again.

## Tagging the Image

After the image was built locally, it was tagged with the ECR URI.

Pattern:

```bash
docker tag calendly-api-lambda:latest "$ECR_URI"
```

Tagging tells Docker:

```text
This local image should also be known by this ECR repository path.
```

## Pushing the Image

After tagging, the image was pushed to ECR:

```bash
docker push "$ECR_URI"
```

That uploaded the image layers to AWS.

The ECR console then showed the image with:

```text
Tag: latest
```

## Why Direct Buildx Push Failed

A direct Buildx push failed with:

```text
403 Forbidden
```

The failed pattern was:

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t "$ECR_URI" \
  --push \
  .
```

The workaround was:

```text
Build locally with --load
Tag the image
Push with normal docker push
```

That worked.

## Lambda Container Function

The Lambda function was created using:

```text
Package type: Image
```

That means Lambda used an ECR image instead of a zip deployment package.

The function used:

```text
Architecture: x86_64
Memory: 1024 MB
Timeout: 120 seconds
```

The memory and timeout were increased because the function uses:

- external API calls
- pandas
- Secrets Manager
- S3 upload
- container image startup time

## Lambda Environment Variables

The Lambda function used environment variables for configuration:

| Variable | Purpose |
|---|---|
| `S3_BUCKET_NAME` | Tells Lambda where to write CSV output |
| `S3_FOLDER_PATH` | Tells Lambda what S3 prefix to use |
| `CALENDLY_SECRET_NAME` | Tells Lambda which Secrets Manager secret to read |

The Calendly token itself was not stored in the environment variables.

Only the secret name was stored there.

## Secrets Manager Flow

The code uses this flow:

```text
Lambda reads CALENDLY_SECRET_NAME
    ↓
boto3 calls Secrets Manager
    ↓
Secrets Manager returns the token
    ↓
Lambda uses token in Calendly API header
```

The token is passed to Calendly as a Bearer token:

```text
Authorization: Bearer <token>
```

The code should not print this token.

## S3 Output Flow

After the API call and metrics processing, Lambda writes CSV output to S3.

The code uses:

```python
s3_client.put_object(
    Bucket=S3_BUCKET_NAME,
    Key=s3_path,
    Body=csv_buffer.getvalue()
)
```

In this project, the final output was a metrics CSV:

```text
calendly/campaign_metrics_2026-06-04_12-18-15.csv
```

The scheduled-events CSV was skipped because the personal Calendly account had no scheduled events available through the API at test time.

## CloudWatch Validation

CloudWatch Logs confirmed the Lambda runtime behavior.

Important log messages included:

```text
Lambda execution started
Successfully retrieved Calendly organization URI
Retrieved 1 Calendly event type(s)
Fetched 0 scheduled Calendly event(s)
No data to upload for calendly/calendly_scheduled_calls...
Uploaded file to s3://...
Lambda execution completed successfully
```

This confirmed that the function ran successfully, even though there were no scheduled events to extract.

## Main Takeaway

This project demonstrates how a local Python API workflow can be packaged and deployed as a Lambda container function.

The important pattern is:

```text
Docker packages the app.
ECR stores the image.
Lambda runs the image.
Secrets Manager protects the token.
S3 stores the output.
CloudWatch shows what happened.
```
