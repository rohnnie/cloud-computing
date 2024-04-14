import json
import boto3
import requests
import base64
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    try:
        s3_client = boto3.client('s3')
        rekognition_client = boto3.client('rekognition')
        
        s3_bucket = event['Records'][0]['s3']['bucket']['name']
        s3_object_key = event['Records'][0]['s3']['object']['key']
        print(s3_bucket,s3_object_key)
        
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_object_key)
        encodedImage = response['Body'].read()
    
        decodedImage = base64.b64decode(encodedImage)
        
        labels=[]
        #read the image file
        response = rekognition_client.detect_labels(Image={'Bytes': decodedImage})
        for label in response['Labels']:
            if label['Confidence']>=75 and label['Name'] not in labels:
                labels.append(label['Name'])
        
        #Print labels
        print(labels)
        
        photo_metadata = s3_client.head_object(Bucket=s3_bucket, Key = s3_object_key)
        #Print Photo Metadata
        print(photo_metadata)
        
    
        created_timestamp = photo_metadata['LastModified'].isoformat()
        if 'customlabels' in photo_metadata['Metadata']:
            custom_labels = photo_metadata['Metadata']['customlabels'].split(',')
            for label in custom_labels:
                if(label not in labels):
                    labels.append(label)
        
        json_object = {
            "objectKey": s3_object_key,
            "bucket": s3_bucket,
            "createdTimestamp": created_timestamp,
            "labels": labels
        }
        
        print(json_object)
        
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
        print(secret_key, access_key)
        
        auth = (secret_key, access_key) 
        headers = {'Content-Type': 'application/json'}
        indexName = "photos"
        host = "https://search-photos-xwvikqbuzcosailtzkcs2f5aua.us-east-1.es.amazonaws.com"
        url = f"{host}/{indexName}/_doc/{s3_object_key}"
        response = requests.post(url, data=json.dumps(json_object), auth=auth, headers=headers)
        
        print(response)
        print("Response status code:", response.status_code)
        print("Response headers:", response.headers)
        print("Response content:", response.content.decode('utf-8'))
    except ClientError as e:
        raise e
    
    print("index-photos lambda finished successfully")
    return {
        'statusCode': 200,
        'body': labels
    }
