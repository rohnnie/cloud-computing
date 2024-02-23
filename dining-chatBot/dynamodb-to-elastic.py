# This script is to store indexes in elasticsearch from dynamodb
# Secrets are being fetched from the secret manager

import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import requests
from botocore.exceptions import ClientError

credentials = boto3.Session().get_credentials()

def get_secret():

    secret_name = "Yelp_api_key"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    secret_key = json.loads(get_secret_value_response['SecretString'])['secret_key']
    access_key = json.loads(get_secret_value_response['SecretString'])['access_key']
    return [access_key,secret_key]


def lambda_handler(event, context):
    client=boto3.client('dynamodb')
    response= client.scan(
        TableName='yelp-restaurants',
        AttributesToGet=[
            'BusinessId',
            'Cuisine'])
    
    restaurant_list=[]
    
    for item in response['Items']:
        rId=item['BusinessId']['S']
        rCuisine=item['Cuisine']['S']
        d={'id':rId, 'cuisine':rCuisine}
        restaurant_list.append(d)
    
    headers = {'Content-Type': 'application/json'}
    access_key,secret_key=get_secret()
    region = "us-east-1"
    service = "es"
    aws_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,session_token=credentials.token)
    
    
    for d in restaurant_list:
        host = f"https://search-restaurants-qie66x24l3j73av6o6353ipzcq.us-east-1.es.amazonaws.com/restaurants/_doc/{d['id']}"
        data = {
            'cuisine': d['cuisine']
        }
        response = requests.put(host, auth=aws_auth, headers=headers, data=json.dumps(data))
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
