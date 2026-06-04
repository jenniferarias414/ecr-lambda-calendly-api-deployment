import os
import json
import boto3
import pandas as pd
import requests
import datetime
from io import StringIO
import logging


# Configure logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Environment variables configured on the Lambda function
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
S3_FOLDER_PATH = os.getenv("S3_FOLDER_PATH", "calendly/")
SECRET_NAME = os.environ["CALENDLY_SECRET_NAME"]
REGION_NAME = os.getenv("AWS_REGION", "us-east-2")


# AWS clients
secrets_client = boto3.client("secretsmanager", region_name=REGION_NAME)
s3_client = boto3.client("s3")


def get_timestamp():
    """Create a timestamp used in S3 output file names."""
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def get_calendly_api_key():
    """Fetch the Calendly API key from AWS Secrets Manager."""
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response["SecretString"])

        api_key = secret.get("calendly-api-key")

        if not api_key:
            raise ValueError("Secret does not contain key: calendly-api-key")

        return api_key

    except Exception as e:
        logger.error(f"Error fetching Calendly API key from Secrets Manager: {e}")
        raise


def upload_to_s3(df, s3_path):
    """Upload a pandas DataFrame to S3 as a CSV file."""
    if df.empty:
        logger.info(f"No data to upload for {s3_path}")
        return

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_path,
        Body=csv_buffer.getvalue(),
    )

    logger.info(f"Uploaded file to s3://{S3_BUCKET_NAME}/{s3_path}")


def get_calendly_org_uri(api_key):
    """Call Calendly users/me endpoint and return the organization URI."""
    url = "https://api.calendly.com/users/me"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url=url, headers=headers, timeout=30)

    if response.status_code == 200:
        org_uri = response.json().get("resource", {}).get("current_organization", "")
        logger.info("Successfully retrieved Calendly organization URI")
        return org_uri

    logger.error(
        f"Error fetching Calendly organization URI: "
        f"{response.status_code}, {response.text}"
    )
    return None


def get_event_types(api_key, org_uri):
    """Fetch Calendly event type URIs for the organization."""
    url = f"https://api.calendly.com/event_types?organization={org_uri}"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url=url, headers=headers, timeout=30)

    if response.status_code == 200:
        event_types = response.json().get("collection", [])
        logger.info(f"Retrieved {len(event_types)} Calendly event type(s)")
        return [event["uri"] for event in event_types]

    logger.error(f"Error fetching event types: {response.status_code}, {response.text}")
    return []


def fetch_calendly_scheduled_calls(api_key):
    """Fetch scheduled Calendly events and return them as a DataFrame."""
    org_uri = get_calendly_org_uri(api_key)

    if not org_uri:
        logger.error("Failed to retrieve Calendly organization URI. Cannot proceed.")
        return pd.DataFrame()

    event_types = get_event_types(api_key, org_uri)

    if not event_types:
        logger.warning("No event types found. Returning empty scheduled calls DataFrame.")
        return pd.DataFrame()

    all_events = []

    for event_type in event_types:
        url = (
            "https://api.calendly.com/scheduled_events"
            f"?event_type={event_type}&organization={org_uri}"
        )
        headers = {"Authorization": f"Bearer {api_key}"}

        response = requests.get(url=url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()

            for event in data.get("collection", []):
                all_events.append(
                    {
                        "event_id": event.get("uri", ""),
                        "event_type": event.get("event_type", ""),
                        "start_time": event.get("start_time", ""),
                        "end_time": event.get("end_time", ""),
                        "status": event.get("status", "N/A"),
                        "location_type": event.get("location", {}).get("type", "N/A"),
                    }
                )
        else:
            logger.error(
                f"Error fetching events for event type {event_type}: "
                f"{response.status_code}, {response.text}"
            )

    logger.info(f"Fetched {len(all_events)} scheduled Calendly event(s)")
    return pd.DataFrame(all_events)


def calculate_metrics(calendly_df, timestamp):
    """Calculate basic metrics from the Calendly scheduled events DataFrame."""
    total_scheduled_calls = len(calendly_df)

    completed_calls = 0
    if not calendly_df.empty and "status" in calendly_df.columns:
        completed_calls = calendly_df[calendly_df["status"] == "completed"].shape[0]

    completed_calls_percentage = (
        (completed_calls / total_scheduled_calls) * 100
        if total_scheduled_calls > 0
        else 0
    )

    metrics_data = {
        "timestamp": [timestamp],
        "total_scheduled_calls": [total_scheduled_calls],
        "completed_calls": [completed_calls],
        "completed_calls_percentage": [round(completed_calls_percentage, 2)],
    }

    return pd.DataFrame(metrics_data)


def lambda_handler(event, context):
    """Lambda entry point."""
    logger.info("Lambda execution started")

    try:
        timestamp = get_timestamp()

        calendly_path = (
            f"{S3_FOLDER_PATH}calendly_scheduled_calls_{timestamp}.csv"
        )
        metrics_path = f"{S3_FOLDER_PATH}campaign_metrics_{timestamp}.csv"

        api_key = get_calendly_api_key()

        calendly_df = fetch_calendly_scheduled_calls(api_key)
        upload_to_s3(calendly_df, calendly_path)

        metrics_df = calculate_metrics(calendly_df, timestamp)
        upload_to_s3(metrics_df, metrics_path)

        logger.info("Lambda execution completed successfully")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Lambda execution completed successfully",
                    "scheduled_calls_path": calendly_path,
                    "metrics_path": metrics_path,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error during Lambda execution: {e}")

        return {
            "statusCode": 500,
            "body": json.dumps(f"Lambda execution failed: {e}"),
        }
