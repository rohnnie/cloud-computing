import json
import boto3
import requests
import uuid

lex_client = boto3.client('lexv2-runtime')

def getSlots(response):
    #pass the query to lex bot to get slots
    query = lex_client.recognize_text(
        botId='GNKAHWIHNB',
        botAliasId='KEROZ4WURY',
        localeId="en_US",
        sessionId=str(uuid.uuid4()),
        text=response
    )
    print("Input Query by User", query)
    event=query['interpretations'][0]['intent']['slots']
    if event['type2'] is None:
        type2=None
    else:
        type2=event['type2']['value']['originalValue']
    type1=event['type1']['value']['originalValue']
    return type1,type2

def getSecret():
    #Fetch Secrets from secret manager
    session = boto3.session.Session()
    client = session.client(
        service_name = 'secretsmanager',
        region_name = "us-east-1"
    )

    get_secret_value_response = client.get_secret_value(
        SecretId = "opensearchCredentials"
    )

    secret_key = json.loads(get_secret_value_response['SecretString'])['username']
    access_key = json.loads(get_secret_value_response['SecretString'])['password']
    return secret_key, access_key

def get_image_path(labels):
    
    host = "https://search-photos-xwvikqbuzcosailtzkcs2f5aua.us-east-1.es.amazonaws.com"
    username, passowrd = getSecret()
    headers = {'Content-Type': 'application/json'}

    img_paths=[]
    for i in labels:
        path = host + '/_search?q=labels:'+i
        print(path)
        response = requests.get(path, headers=headers,
                                auth=(username, passowrd))
        print("Elasticsearch Response:", response)
        d = json.loads(response.text)
        print(d)
        total_finds = d['hits']['total']['value']
        for j in range(0, total_finds):
            bucket = d["hits"]["hits"][j]["_source"]["bucket"]
            file_name = d["hits"]["hits"][j]["_source"]["objectKey"]
            print(bucket)
            print(file_name)
            img_path = 'https://s3.amazonaws.com/' + bucket + '/' + file_name
            img_paths.append(img_path)
    print(img_paths)
    return img_paths

def lambda_handler(event, context):
    print(event)
    response = event["queryStringParameters"]["q"]
    slot1,slot2 = getSlots(response)
    if slot2==None:
        labels=[slot1]
    else:
        labels= [slot1,slot2]
    
    img_paths = get_image_path(labels)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'imagePaths': img_paths,
            'userQuery': response,
            'labels': labels,
        }),
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin' : "*",
            'Access-Control-Allow-Methods': 'OPTIONS,GET'
        },
        "isBase64Encoded": False
    }
