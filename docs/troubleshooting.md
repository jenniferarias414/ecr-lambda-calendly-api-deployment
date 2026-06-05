# Troubleshooting Notes

This file documents the main issues encountered while building the ECR Lambda Calendly API deployment project and how they were resolved.

## Issue 1: Wrong AWS CLI Profile Name

### What Happened

An early command used this profile name:

```bash
scd1_lab
```

The AWS CLI returned:

```text
The config profile (scd1_lab) could not be found
```

### Cause

The actual profile name used a hyphen, not an underscore:

```bash
scd1-lab
```

### Resolution

Listed available profiles:

```bash
aws configure list-profiles
```

Then used the correct personal project profile:

```bash
retail-poc
```

### Lesson

AWS profile names must match exactly. A small typo in the profile name can make it look like AWS CLI is not configured, even when it is.

## Issue 2: ECR Authorization Failed with One AWS Profile

### What Happened

The `scd1-lab` profile returned this error when trying to authenticate Docker to ECR:

```text
not authorized to perform: ecr:GetAuthorizationToken
```

### Cause

The AWS user behind that profile did not have permission to request an ECR authorization token.

### Resolution

Tested available AWS profiles and found that the `retail-poc` profile had ECR access.

Profile used for the project:

```bash
export AWS_PROFILE=retail-poc
export AWS_REGION=us-east-2
```

### Lesson

`aws configure` only controls which AWS identity the terminal uses. IAM policies control what that identity is allowed to do.

In this project:

- AWS CLI profile = local identity used to create and deploy resources
- Lambda execution role = runtime identity used by Lambda when the function runs

Those are related but separate permission layers.

## Issue 3: Docker Build Warning for AMD64

### What Happened

Docker Desktop showed an AMD64 warning for the image.

### Cause

The image was built for:

```text
linux/amd64
```

The Lambda function was configured for:

```text
x86_64
```

On an Apple Silicon Mac, Docker Desktop may show a warning because running an AMD64 image locally can require emulation.

### Resolution

No code fix was needed. The image architecture matched the Lambda function architecture, so the warning was acceptable for this deployment.

### Lesson

Local Docker architecture and cloud runtime architecture both matter.

For this project:

```text
Docker image platform: linux/amd64
Lambda architecture: x86_64
```

That match was intentional.

## Issue 4: Lambda Rejected the First ECR Image

### What Happened

The first attempt to create Lambda from the ECR image returned:

```text
The image manifest, config or layer media type for the source image is not supported.
```

### Cause

The initial Docker build/push created an image manifest format that Lambda did not accept.

### Resolution

Rebuilt the image with Docker Buildx and disabled provenance/SBOM metadata:

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  --load \
  -t calendly-api-lambda:latest \
  .
```

Then tagged and pushed the rebuilt image to ECR:

```bash
docker tag calendly-api-lambda:latest "$ECR_URI"
docker push "$ECR_URI"
```

After that, Lambda accepted the ECR image.

### Lesson

A Docker image can exist in ECR and still be rejected by Lambda if the image manifest format is not compatible with Lambda container image requirements.

## Issue 5: Direct Buildx Push Returned 403 Forbidden

### What Happened

A direct Buildx build-and-push command failed with:

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

### Cause

The direct Buildx push path failed against ECR even though a normal Docker push worked.

### Resolution

Used a two-step approach:

1. Build locally with `--load`
2. Push with normal `docker push`

Working pattern:

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  --load \
  -t calendly-api-lambda:latest \
  .

docker tag calendly-api-lambda:latest "$ECR_URI"
docker push "$ECR_URI"
```

### Lesson

When direct Buildx push fails, building locally with `--load` and then using `docker push` can be a cleaner path.

## Issue 6: AWS CLI Output Opened in a Pager

### What Happened

Some AWS CLI output opened in a pager with a colon prompt at the bottom.

### Cause

The AWS CLI can send long output to a pager, depending on local configuration.

### Resolution

Exited the pager by pressing:

```text
q
```

Then disabled the pager for the current terminal session:

```bash
export AWS_PAGER=""
```

### Lesson

If the terminal looks stuck at a `:` prompt after an AWS CLI command, it may be inside the pager. Press `q` to exit.

## Issue 7: Scheduled Calls CSV Was Not Created

### What Happened

After the Lambda ran successfully, S3 showed only this output:

```text
calendly/campaign_metrics_2026-06-04_12-18-15.csv
```

The scheduled calls CSV was not created.

### Cause

The personal Calendly account had no scheduled events available through the API at test time.

The Lambda code skipped uploading empty DataFrames:

```python
if df.empty:
    logger.info(f"No data to upload for {s3_path}")
    return
```

### Resolution

No fix was needed. The metrics CSV was still created and uploaded successfully.

### Lesson

A missing scheduled-calls CSV does not automatically mean the Lambda failed. In this case, it meant the API returned zero scheduled events, so the function skipped the empty output file.

CloudWatch confirmed:

```text
Retrieved 1 Calendly event type(s)
Fetched 0 scheduled Calendly event(s)
No data to upload for calendly/calendly_scheduled_calls...
Uploaded file to s3://...
Lambda execution completed successfully
```

## Issue 8: Secrets Must Not Be Logged

### What Happened

The source code originally included direct printing of the API key.

### Risk

Printing a token would send it to CloudWatch Logs, which is not safe.

### Resolution

Removed direct token printing and kept only safe logging.

The token is retrieved from Secrets Manager at runtime, but the value is not printed.

### Lesson

Secrets should not be:

- hardcoded in source code
- committed to GitHub
- printed to terminal output
- printed to CloudWatch Logs
- shown in screenshots

## Final Troubleshooting Result

All issues were resolved.

The final deployment successfully:

- Built a Lambda-compatible Docker image
- Pushed the image to Amazon ECR
- Created a Lambda function from the ECR image URI
- Retrieved the Calendly API token from Secrets Manager
- Called the Calendly API
- Uploaded a metrics CSV to S3
- Logged successful execution in CloudWatch
- Removed AWS resources after validation
