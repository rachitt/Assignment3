import json
import boto3
import os
import logging
import uuid
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
lex = boto3.client('lexv2-runtime')

# Environment variables
elasticsearch_endpoint = os.environ['ELASTICSEARCH_ENDPOINT']
master_username = os.environ['MASTER_USERNAME']
master_password = os.environ['MASTER_PASSWORD']
bot_alias_id = os.environ['BOT_ALIAS_ID']
bot_id = os.environ['BOT_ID']

# Initialize OpenSearch client
opensearch_client = OpenSearch(
    hosts=[{'host': elasticsearch_endpoint, 'port': 443}],
    http_auth=HTTPBasicAuth(master_username, master_password),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

def clean_data(query):
    word_list = query.split(" ")
    w_list = [word for word in word_list if word not in ["and", "or", ","]]
    return w_list

def get_labels(query):
    try:
        session_id = str(uuid.uuid4())
        response = lex.recognize_text(
            botAliasId=bot_alias_id,
            botId=bot_id,
            sessionId=session_id,
            localeId='en_US',
            text=query
        )
        print(response)
        interpreted_value = response["interpretations"][0]["intent"]["slots"]["SearchKeyword"]["value"]["interpretedValue"]
        labels = clean_data(interpreted_value)
        return labels
    except Exception as e:
        logger.error(f"Error getting labels from Lex: {e}")
        return []

def query_index(keys):
    try:
        index = 'data'
        query = {
            "size": 100,
            "query": {
                "multi_match": {
                    "query": keys,
                }
            }
        }
        response = opensearch_client.search(
            index=index,
            body=query
        )
        image_list = [photo['_source']['objectKey'] for photo in response['hits']['hits']]
        return image_list
    except Exception as e:
        logger.error(f"Error querying OpenSearch index: {e}")
        return []

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        query = event.get("queryStringParameters", {}).get('q', '')
        if not query:
            raise ValueError("Query parameter 'q' is missing")

        label_list = get_labels(query)
        logger.info(f"Labels extracted: {label_list}")
        
        image_array = []
        for label in label_list:
            image_array.extend(query_index(label))
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({"keys": image_array})
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({"error": "Internal Server Error"})
        }