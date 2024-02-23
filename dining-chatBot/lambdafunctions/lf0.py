import json
import boto3
from datetime import datetime
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

def get_address(event):
    add=""
    for x in event['Item']['Address']['L']:
        for k,v in x.items():
            add+=v+' '
    add=add.strip()
    return add

def get_cuisine_email(event,sessionId):
    print(event)
    for x in event['Items']:
        if(x['sessionId']['S']==sessionId):
            return [x['cuisine']['S'],x['email']['S']]
    

def lambda_handler(event, context):
    print(event)
    print(context)
    messageBody = json.loads(event['body'])
    
    #check if user already came
    sessionId=messageBody['messages'][0]['id']
    dynamo_client = boto3.client('dynamodb')
    response = dynamo_client.scan(
        TableName='sessionTable',
        AttributesToGet=['sessionId','cuisine','email']
        )
    print(response)


    #check if this session exists in dynamodb table
    if(response['Count']==0):
        print("count=0")
        message_content=messageBody['messages'][0]['unstructured']['text']
        print(message_content)
        lex_client = boto3.client('lexv2-runtime')
        response1 = lex_client.recognize_text(
            botId="AIXXHL1YYP",
            botAliasId="8C735HSJOG",
            localeId="en_US",
            sessionId=messageBody['messages'][0]['id'],
            text=messageBody['messages'][0]['unstructured']['text']
            )
        print("1")
        print(response1)
        messages = []
        for msg in response1["messages"]:
            message = {
                'type': "unstructured",
                'unstructured': {
                    'id': messageBody['messages'][0]['id'],
                    'text': msg["content"],
                    'timestamp': (datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
                }
            }
            messages.append(message)
        print(messages)
        d={"messages":messages}
        return {
            'statusCode': 200,
            'headers':{
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin' : "*",
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(d)
        }
    else:
        print("Session exists!")
        session_list=[]
        for x in response['Items']:
            print(x)
            session_list.append(x['sessionId']['S'])
        print(session_list)
        if(sessionId in session_list):
            cuisine,email = get_cuisine_email(response,sessionId)
            query ={
                "query": {
                    "function_score": {
                      "query": {
                        "match": {
                          "cuisine": cuisine
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
            response1 = requests.get(host, auth=aws_auth, headers=headers, data=json.dumps(query))
            elastic_results = dict(json.loads(response1.text))
            # get restaurant id from elaticsearch results 
            res_id = []
            for x in elastic_results['hits']['hits']:
                res_id.append(x['_id'])
        
            body = f"""Hi,\nThank You for using our service. Please find below suggested retaurants based on your preferences:"""
            
            z=1
            for id in res_id:
                response2 = dynamo_client.get_item(
                    TableName = 'yelp-restaurants',
                    Key ={
                        'BusinessId':{
                            'S':id
                            },
                    })
                body+=f"""\n{z}. Name: {response2['Item']['Name']['S']}
Address: {get_address(response2)}
Rating: {response2['Item']['rating']['S']}\n"""
                z+=1
            
            body+= "\n Thank you and enjoy!"
            
            # send email using SES
            ses_client = boto3.client('ses')
            subject = "DiningBot : Restaurant Suggestions"
            message = {"Subject":{"Data":subject}, "Body": {"Text": {"Data": body}}}
            response3 = ses_client.send_email(Source = "rohanchopra96@yahoo.com",
                                            Destination = {"ToAddresses": [email]},
                                            Message = message)
            messages=[]
            message = {
                'type': "unstructured",
                'unstructured': {
                    'id': sessionId,
                    'text': "Hi, welcome back! We have sent suggestions to your registered email. Thanks and Enjoy!",
                    'timestamp': (datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
                }
            }
            messages.append(message)
            d={"messages":messages}
            return {
                'statusCode': 200,
                'headers':{
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin' : "*",
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(d)
            }
        else:
            print("2")
            message_content=messageBody['messages'][0]['unstructured']['text']
            print(message_content)
            lex_client = boto3.client('lexv2-runtime')
            response4 = lex_client.recognize_text(
                botId="AIXXHL1YYP",
                botAliasId="8C735HSJOG",
                localeId="en_US",
                sessionId=messageBody['messages'][0]['id'],
                text=messageBody['messages'][0]['unstructured']['text']
                )
            messages = []
            for msg in response4["messages"]:
                message = {
                    'type': "unstructured",
                    'unstructured': {
                        'id': messageBody['messages'][0]['id'],
                        'text': msg["content"],
                        'timestamp': (datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
                    }
                }
                messages.append(message)
            print(messages)
            d={"messages":messages}
            return {
                'statusCode': 200,
                'headers':{
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin' : "*",
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(d)
            }   
        
        
