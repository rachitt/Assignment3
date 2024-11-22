import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')

# Environment variables
elasticsearch_endpoint = os.environ['ELASTICSEARCH_ENDPOINT']
master_username = os.environ['MASTER_USERNAME']
master_password = os.environ['MASTER_PASSWORD']

# Initialize OpenSearch client
opensearch_client = OpenSearch(
    hosts=[{'host': elasticsearch_endpoint, 'port': 443}],
    http_auth=HTTPBasicAuth(master_username, master_password),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

def get_labels_from_rekognition(bucket_name, object_key):
    try:
        response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': object_key
                }
            }
        )
        return [entry['Name'] for entry in response['Labels']]
    except Exception as e:
        logger.error(f"Error detecting labels: {e}")
        return []

def get_custom_labels_from_s3(bucket_name, object_key):
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        if 'x-amz-meta-customlabels' in response['Metadata']:
            return response['Metadata']['x-amz-meta-customlabels'].split(',')
        return []
    except Exception as e:
        logger.error(f"Error retrieving S3 metadata: {e}")
        return []

def index_document(object_key, bucket_name, event_time, labels):
    document = {
        'objectKey': object_key,
        'bucket': bucket_name,
        'createdTimestamp': event_time,
        'labels': labels
    }
    try:
        opensearch_client.index(
            index='data',
            id=object_key,
            body=document
        )
    except Exception as e:
        logger.error(f"Error indexing document: {e}")

def lambda_handler(event, context):
    logger.info('Lambda function invoked')
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        event_time = record['eventTime']

        labels = get_labels_from_rekognition(bucket_name, object_key)
        custom_labels = get_custom_labels_from_s3(bucket_name, object_key)
        labels.extend(custom_labels)

        index_document(object_key, bucket_name, event_time, labels)
    logger.info('Lambda function completed')