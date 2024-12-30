#!/usr/bin/env python3

import json
import boto3

def create_cloudwatch_client(credentials_file):
    """
    Reads AWS credentials from a JSON file and creates a CloudWatch client.

    Args:
        credentials_file (str): Path to the JSON file containing the credentials.

    Returns:
        boto3.client: A CloudWatch client object.
    """

    with open(credentials_file, 'r') as f:
        credentials = json.load(f)

    access_key = credentials['accessKey']
    secret_key = credentials['secret']

    cloudwatch = boto3.client(
        'cloudwatch',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='il-central-1'  # Replace with your desired region
    )

    return cloudwatch



def main():

    cloudwatch  = create_cloudwatch_client("./aws-credentials.json")
    

    # Publish metric to CloudWatch
    response = cloudwatch.put_metric_data(
        Namespace='TestMetric',  # Choose a namespace for your metrics
        MetricData=[
            {
                'MetricName': 'Testing',
                'Dimensions': [
                    {'Name': 'SensorID', 'Value': 'sensor1'}  # Add dimensions if needed
                ],
                'Value': 150.9,
                'Unit': 'Count/Second'  # Or specify a unit like 'Count', 'Seconds', etc.
            },
        ]
    )


if __name__ == "__main__":
  main()