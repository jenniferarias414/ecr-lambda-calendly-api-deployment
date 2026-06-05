# Service-by-Service Study Notes

These notes explain each service and tool used in the ECR Lambda Calendly API Deployment project.

The main project flow was:

```text
Local Python code
    ↓
Docker image
    ↓
Amazon ECR
    ↓
AWS Lambda
    ↓
Secrets Manager
    ↓
Calendly API
    ↓
pandas processing
    ↓
Amazon S3
    ↓
CloudWatch Logs
```

## Local Python Code

The project started with Python code in `lambda_function.py`.

The code did several jobs:

- Read configuration from Lambda environment variables
- Retrieve the Calendly API token from Secrets Manager
- Call the Calendly API with `requests`
- Convert API response data into pandas DataFrames
- Create a metrics CSV
- Upload CSV output to S3
- Write logs for validation

The main function was:

```text
lambda_function.lambda_handler
```

That is the function AWS Lambda runs when the container is invoked.

## requirements.txt

The `requirements.txt` file listed the Python packages installed into the Docker image.

```text
boto3==1.34.75
pandas==2.2.3
requests==2.31.0
awslambdaric==2.0.2
```

| Package | Purpose |
|---|---|
| `boto3` | Allows Python to call AWS services |
| `pandas` | Creates tabular data and CSV output |
| `requests` | Calls the Calendly API |
| `awslambdaric` | Lets the container work with the Lambda runtime |

This is one of the main reasons Docker was useful. The image carried these dependencies with the code.

## Docker Desktop

Docker Desktop was used to build the container image locally.

A Docker image packages:

- application code
- dependencies
- runtime setup
- startup command

In this project, Docker turned the Python workflow into a Lambda-compatible image.

Important idea:

```text
Docker image = packaged application
Container = running copy of that image
```

## Dockerfile

The Dockerfile told Docker how to build the image.

The Dockerfile used an AWS Lambda Python base image:

```text
public.ecr.aws/lambda/python:3.9
```

That base image already includes Lambda runtime structure for Python.

The Dockerfile then:

1. Set the working directory to `/var/task`
2. Copied `lambda_function.py`
3. Copied `requirements.txt`
4. Installed Python dependencies
5. Set the Lambda handler to `lambda_function.lambda_handler`

## Docker Buildx

Docker Buildx was used to rebuild the image with Lambda-compatible settings.

The working command used:

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  --load \
  -t calendly-api-lambda:latest \
  .
```

Important flags:

| Flag | Meaning |
|---|---|
| `--platform linux/amd64` | Builds the image for Lambda x86_64 architecture |
| `--provenance=false` | Avoids image metadata that Lambda rejected |
| `--sbom=false` | Avoids extra metadata for this small project build |
| `--load` | Loads the built image into local Docker |
| `-t` | Tags the image name and version |

## Amazon ECR

Amazon ECR means Elastic Container Registry.

ECR stores Docker images in AWS.

Lambda cannot run an image that only exists on the laptop. The image must be pushed to a registry that Lambda can access.

Project ECR repository:

```text
calendly-api-lambda
```

Image tag:

```text
latest
```

The ECR flow was:

```text
Build image locally
    ↓
Tag image with ECR URI
    ↓
Push image to ECR
    ↓
Lambda uses ECR image URI
```

## AWS Lambda

AWS Lambda ran the containerized application.

Instead of using a zip file, this Lambda used:

```text
Package type: Image
```

That means Lambda ran from the Docker image stored in ECR.

Project Lambda function:

```text
calendly-api-container-lambda
```

Lambda configuration:

| Setting | Value |
|---|---|
| Package type | Image |
| Architecture | x86_64 |
| Timeout | 120 seconds |
| Memory | 1024 MB |

The timeout and memory were increased because the function used a container image, external API calls, pandas, Secrets Manager, and S3 upload.

## Lambda Environment Variables

Lambda environment variables were used for project configuration.

| Variable | Purpose |
|---|---|
| `S3_BUCKET_NAME` | Name of the S3 output bucket |
| `S3_FOLDER_PATH` | Folder-like prefix for output files |
| `CALENDLY_SECRET_NAME` | Name of the Secrets Manager secret |

The actual Calendly API token was not stored in the Lambda environment variables.

Only the secret name was stored there.

## AWS Secrets Manager

Secrets Manager stored the Calendly API token.

Project secret name:

```text
calendly-api-token
```

The secret contained a JSON value with this key:

```text
calendly-api-key
```

The Lambda code retrieved the secret at runtime using boto3:

```text
Lambda reads secret name
    ↓
boto3 calls Secrets Manager
    ↓
Secrets Manager returns API token
    ↓
Lambda uses token for Calendly API call
```

This avoided hardcoding the token in source code.

## Calendly API

The Calendly API was the external data source for the project.

The code called:

```text
https://api.calendly.com/users/me
```

That endpoint returned information about the authenticated Calendly user, including the current organization URI.

Then the code used the organization URI to get event types.

Then it checked scheduled events for those event types.

Main API flow:

```text
Get current user
    ↓
Get organization URI
    ↓
Get event types
    ↓
Get scheduled events
    ↓
Build DataFrames
```

## Bearer Token Authentication

The Calendly API used Bearer token authentication.

The request header looked like this conceptually:

```text
Authorization: Bearer <Calendly API token>
```

The token proves the request is allowed to access the Calendly account.

Important safety rule:

```text
The token should not be committed, printed, logged, or shown in screenshots.
```

## pandas

pandas was used to create DataFrames.

The scheduled events response was converted into tabular data.

The metrics output was also created as a DataFrame.

Metrics included:

- timestamp
- total scheduled calls
- completed calls
- completed calls percentage

The metrics DataFrame was converted to CSV before uploading to S3.

## Amazon S3

S3 stored the Lambda output files.

Project output bucket:

```text
calendly-api-output-jenny-9b2373
```

Output prefix:

```text
calendly/
```

Final output example:

```text
calendly/campaign_metrics_2026-06-04_12-18-15.csv
```

The function used `put_object` to write CSV content to S3.

Conceptually:

```text
pandas DataFrame
    ↓
CSV string
    ↓
s3_client.put_object()
    ↓
S3 output file
```

## IAM

IAM controlled permissions for the Lambda function.

The Lambda execution role was:

```text
calendly-api-lambda-role
```

Lambda needed permission to:

- write logs to CloudWatch
- read the Calendly token from Secrets Manager
- write CSV files to S3
- list the S3 output bucket

The project used:

- AWS-managed `AWSLambdaBasicExecutionRole`
- a project-specific inline policy for Secrets Manager and S3 access

A helpful IAM question:

```text
Which service is trying to do what action on which resource?
```

Examples:

```text
Lambda is trying to GetSecretValue from Secrets Manager.
Lambda is trying to PutObject into S3.
Lambda is trying to PutLogEvents into CloudWatch Logs.
```

## CloudWatch Logs

CloudWatch Logs captured Lambda runtime output.

The logs confirmed that Lambda:

- started successfully
- retrieved the Calendly organization URI
- retrieved one event type
- found zero scheduled events
- skipped the empty scheduled-events CSV
- uploaded the metrics CSV to S3
- completed successfully

CloudWatch was important because the function ran inside AWS, not directly in the local terminal.

## AWS CLI

AWS CLI was used to create, configure, validate, and delete AWS resources.

Examples of AWS CLI tasks:

- create S3 bucket
- create Secrets Manager secret
- create IAM role and policy
- create ECR repository
- describe ECR images
- create Lambda function
- invoke Lambda
- check S3 output
- read CloudWatch logs
- delete resources during cleanup

## VS Code

VS Code was used to manage the local project files.

Important files included:

```text
Dockerfile
lambda_function.py
requirements.txt
commands-project.sh
README.md
docs/
learning-notes/
screenshots/
```

VS Code was useful for checking the repo structure and editing project documentation.

## Terminal

The terminal was used for AWS CLI and Docker commands.

This project depended heavily on terminal commands because the workflow included:

- setting environment variables
- building Docker images
- tagging images
- pushing images
- invoking Lambda
- checking S3 output
- validating cleanup

## How the Services Worked Together

The services worked together like this:

```text
Docker packages the Python app.
ECR stores the Docker image.
Lambda runs the image.
Secrets Manager provides the API token.
Calendly API returns event data.
pandas creates metrics.
S3 stores CSV output.
CloudWatch records execution logs.
IAM allows each service interaction.
```

## Main Takeaway

This project used multiple AWS services, but each service had a clear responsibility.

| Service / Tool | Main Responsibility |
|---|---|
| Docker | Package code and dependencies |
| ECR | Store container image |
| Lambda | Run the containerized workflow |
| Secrets Manager | Store the API token |
| Calendly API | Provide event data |
| pandas | Create CSV-ready metrics |
| S3 | Store output files |
| CloudWatch | Show runtime logs |
| IAM | Control permissions |
| AWS CLI | Build, deploy, validate, and clean up |

The project is a compact example of how a local Python API script can become a cloud-deployed, containerized Lambda workflow.
