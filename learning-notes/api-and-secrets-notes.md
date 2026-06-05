# API and Secrets Manager Notes

These notes explain the Calendly API and Secrets Manager parts of the project.

The main idea:

```text
Lambda needs a Calendly API token.
The token should not be stored in code.
Secrets Manager stores the token.
Lambda retrieves the token at runtime.
Lambda uses the token to call the Calendly API.
```

## Calendly API Purpose

The Calendly API was the external data source for this project.

The Lambda function called Calendly to retrieve information about:

- the authenticated Calendly user
- the user's current organization
- available event types
- scheduled events for those event types

The goal was to simulate a small API extraction workflow that could run in AWS Lambda.

## API Flow in the Code

The API flow looked like this:

```text
Get Calendly API token from Secrets Manager
    ↓
Call /users/me
    ↓
Get current organization URI
    ↓
Call /event_types
    ↓
Get event type URIs
    ↓
Call /scheduled_events
    ↓
Build event records
    ↓
Create metrics
    ↓
Upload CSV output to S3
```

## Bearer Token Authentication

The Calendly API uses Bearer token authentication.

That means the API request sends an authorization header like this:

```text
Authorization: Bearer <Calendly API token>
```

The token tells Calendly:

```text
This request is allowed to access this Calendly account.
```

The token should be protected like a password.

## Why the Token Should Not Be Hardcoded

Hardcoding a token means writing it directly into the Python file.

Example of what not to do:

```python
access_token = "real-token-value"
```

That is risky because the token could be:

- committed to GitHub
- copied into screenshots
- printed to terminal output
- logged in CloudWatch
- shared accidentally

The safer pattern is:

```text
Store token in Secrets Manager.
Store only the secret name in Lambda environment variables.
Retrieve the token at runtime.
```

## Secrets Manager

AWS Secrets Manager stores sensitive values such as API keys, database passwords, and access tokens.

In this project, Secrets Manager stored the Calendly API token.

Secret name:

```text
calendly-api-token
```

Secret JSON key:

```text
calendly-api-key
```

The secret value was stored as JSON:

```json
{
  "calendly-api-key": "token-value"
}
```

The actual token value should not be shown in documentation or screenshots.

## Lambda Environment Variable

Lambda did not store the token directly.

Instead, Lambda stored the secret name:

```text
CALENDLY_SECRET_NAME=calendly-api-token
```

That means the Lambda function knew which secret to ask for, but the actual token stayed in Secrets Manager.

## How Lambda Retrieved the Secret

The code used boto3 to create a Secrets Manager client:

```python
secrets_client = boto3.client("secretsmanager", region_name=REGION_NAME)
```

Then it called:

```python
response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
```

The response contained the secret string.

The code parsed the JSON:

```python
secret = json.loads(response["SecretString"])
api_key = secret.get("calendly-api-key")
```

Then the API key was used in the Calendly request header.

## Why IAM Was Needed for Secrets Manager

Lambda cannot automatically read secrets.

The Lambda execution role needed permission to call:

```text
secretsmanager:GetSecretValue
```

The project-specific IAM policy allowed Lambda to read only the Calendly secret.

Conceptually:

```text
Lambda role is allowed to read calendly-api-token.
Lambda role is not automatically allowed to read every secret.
```

That is a better pattern than giving Lambda broad secret access.

## Calendly `/users/me` Endpoint

The first Calendly endpoint called by the function was:

```text
https://api.calendly.com/users/me
```

This endpoint returns information about the authenticated Calendly user.

The code used it to find the current organization URI:

```python
org_uri = response.json().get("resource", {}).get("current_organization", "")
```

The organization URI was needed for the next API call.

## Calendly Event Types

After retrieving the organization URI, the function called the event types endpoint:

```text
https://api.calendly.com/event_types?organization=<organization_uri>
```

This returned the Calendly event types available for the organization.

The code collected each event type URI:

```python
return [event["uri"] for event in event_types]
```

Those event type URIs were used to look up scheduled events.

## Calendly Scheduled Events

For each event type, the function called scheduled events:

```text
https://api.calendly.com/scheduled_events?event_type=<event_type_uri>&organization=<organization_uri>
```

The code attempted to collect fields such as:

- event ID
- event type
- start time
- end time
- status
- location type

Those records were added to a list and converted into a pandas DataFrame.

## Why the Scheduled Calls File Was Empty

During project validation, the personal Calendly account had no scheduled events available through the API.

Because of that, the scheduled calls DataFrame was empty.

The upload function intentionally skipped empty DataFrames:

```python
if df.empty:
    logger.info(f"No data to upload for {s3_path}")
    return
```

That is why the scheduled calls CSV was not created in S3.

This was expected for the test data available at runtime.

## Metrics Output

Even though there were no scheduled calls, the function still created a metrics CSV.

The metrics included:

- timestamp
- total scheduled calls
- completed calls
- completed calls percentage

Example output:

```csv
timestamp,total_scheduled_calls,completed_calls,completed_calls_percentage
2026-06-04_12-18-15,0,0,0
```

This showed that the Lambda function completed the workflow and wrote output to S3.

## S3 Upload

The project used `put_object` to upload CSV output to S3.

The code converted a pandas DataFrame into CSV text:

```python
csv_buffer = StringIO()
df.to_csv(csv_buffer, index=False)
```

Then uploaded it:

```python
s3_client.put_object(
    Bucket=S3_BUCKET_NAME,
    Key=s3_path,
    Body=csv_buffer.getvalue()
)
```

The output path used:

```text
S3_BUCKET_NAME
S3_FOLDER_PATH
timestamped file name
```

Example:

```text
s3://calendly-api-output-jenny-9b2373/calendly/campaign_metrics_2026-06-04_12-18-15.csv
```

## Safe Logging

The source code was adjusted to avoid printing the API key.

The function logged useful runtime information such as:

- Lambda execution started
- Calendly organization URI was retrieved
- event types were retrieved
- scheduled events count
- file upload success
- Lambda execution completed successfully

It did not log the token value.

## What CloudWatch Confirmed

CloudWatch Logs confirmed the end-to-end API and output flow.

The logs showed:

```text
Lambda execution started
Successfully retrieved Calendly organization URI
Retrieved 1 Calendly event type(s)
Fetched 0 scheduled Calendly event(s)
No data to upload for calendly/calendly_scheduled_calls...
Uploaded file to s3://...
Lambda execution completed successfully
```

This means:

- the containerized Lambda started successfully
- the token was retrieved from Secrets Manager
- the Calendly API authentication worked
- the API returned event type data
- there were no scheduled events to extract
- the metrics CSV was uploaded to S3
- the function completed successfully

## Main Takeaway

The API and secret-handling pattern in this project was:

```text
Do not hardcode the token.
Store the token in Secrets Manager.
Give Lambda permission to read the secret.
Pass only the secret name as an environment variable.
Retrieve the token at runtime.
Use the token to call the external API.
Write output to S3.
Validate with CloudWatch Logs.
```

This is a useful pattern for API-based data extraction workflows because it keeps credentials separate from application code while still allowing the function to run automatically in AWS.
