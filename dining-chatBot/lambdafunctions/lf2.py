import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import requests
from botocore.exceptions import ClientError

credentials = boto3.Session().get_credentials()
dynamo_client = boto3.client('dynamodb')

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

def get_address(event):
    add=""
    for x in event['Item']['Address']['L']:
        for k,v in x.items():
            add+=v+' '
    add=add.strip()
    return add


def lambda_handler(event, context):
    sqs = boto3.client('sqs')
    response = sqs.get_queue_url(QueueName='SQ1')
    queue_url = response['QueueUrl']
    print(queue_url)
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    receipt_handle=response['Messages'][0]['ReceiptHandle']
    print(f"Message is : {response}")
    
    location = response['Messages'][0]['MessageAttributes']['Location']['StringValue']
    cuisine = response['Messages'][0]['MessageAttributes']['Cuisine']['StringValue']
    date =  response['Messages'][0]['MessageAttributes']['Date']['StringValue']
    time = response['Messages'][0]['MessageAttributes']['Time']['StringValue']
    poeple = response['Messages'][0]['MessageAttributes']['People']['StringValue']
    email =  response['Messages'][0]['MessageAttributes']['Email']['StringValue']
    sessionId = response['Messages'][0]['MessageAttributes']['sessionId']['StringValue']
    
    #insert sessionId and cuisine in session table for that session id
    response1=dynamo_client.put_item(
            TableName='sessionTable',
            Item={
                'sessionId':{
                    'S':sessionId
                },
                'cuisine':{
                    'S':cuisine
                },
                'email':{
                    'S':email
                }
            })
    query ={
        "query": {
            "function_score": {
              "query": {
                "match": {
                  "cuisine": "Indian"
                }
              },
              "random_score": {
                "seed": sessionId
              }
            }
          },
          "size": 10,
    }
    host = f"https://search-restaurants-qie66x24l3j73av6o6353ipzcq.us-east-1.es.amazonaws.com/restaurants/_search"
    headers = {'Content-Type': 'application/json'}
    access_key,secret_key=get_secret()
    region = "us-east-1"
    service = "es"
    aws_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,session_token=credentials.token)
    response = requests.get(host, auth=aws_auth, headers=headers, data=json.dumps(query))
    elastic_results = dict(json.loads(response.text))
    # get restaurant id from elaticsearch results 
    res_id = []
    for x in elastic_results['hits']['hits']:
        res_id.append(x['_id'])

    body = f"""Hi,\nThank You for using our service. Please find below suggested retaurants based on your preferces for {cuisine.capitalize()} cuisine in {location.capitalize()} for {poeple} people:\n"""

    #Extract data from dynamo db now
    z=1
    for id in res_id:
        response2 = dynamo_client.get_item(
            TableName = 'yelp-restaurants',
            Key ={
                'BusinessId':{
                    'S':id
                    },
            })
        body+=f"""\n{z}. Name: {response2['Item']['Name']['S']}\n
Address: {get_address(response2)}\n
Rating: {response2['Item']['rating']['S']}\n\n"""
        z+=1
    body+= "\n Thank you and enjoy!"
    
    # send email using SES
    ses_client = boto3.client('ses')
    subject = "DiningBot : Restaurant Suggestions"
    message = {"Subject":{"Data":subject}, "Body": {"Text": {"Data": body}}}
    response3 = ses_client.send_email(Source = "rohanchopra96@yahoo.com",
                                    Destination = {"ToAddresses": [email]},
                                    Message = message)
    
    #delete the message after extracting so that the user doesnt get spammed with same emails
    response4 = sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
        )
    return

    
    