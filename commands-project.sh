# Project command reference
# AWS profile: retail-poc
# AWS region: us-east-2

export AWS_PROFILE=retail-poc
export AWS_REGION=us-east-2

ACCOUNT_ID=$(aws sts get-caller-identity \
  --profile "$AWS_PROFILE" \
  --query Account \
  --output text)

ECR_REPO_NAME=calendly-api-lambda
IMAGE_NAME=calendly-api-lambda
IMAGE_TAG=latest
ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG"

# Create ECR repository
aws ecr create-repository \
  --repository-name "$ECR_REPO_NAME" \
  --region "$AWS_REGION" \
  --profile "$AWS_PROFILE"

# Login Docker to ECR
aws ecr get-login-password \
  --region "$AWS_REGION" \
  --profile "$AWS_PROFILE" \
| docker login \
  --username AWS \
  --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Build Docker image for Lambda x86_64
docker build --platform linux/amd64 -t "$IMAGE_NAME" .

# Tag local image for ECR
docker tag "$IMAGE_NAME:latest" "$ECR_URI"

# Push image to ECR
docker push "$ECR_URI"
