# This script is to store results in dynamodb after scraping
# Secrets are being fetched from secret manager

import json
import datetime
import time
import os
import dateutil.parser
import logging
import math
import boto3
import requests
from urllib.parse import quote
from botocore.exceptions import ClientError

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
    secret = json.loads(get_secret_value_response['SecretString'])['Api_Key']
    return secret


def lambda_handler(event, context):
    key = get_secret()
    cuisines = ["Chinese", "Italian", "Indian", "Mexican", "French", "Japanese", "American", "Thai", "Cuban", "Greek", "Korean"]
    unique_restaurant=[]

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    
    for cuisine in cuisines:
        print(f"Storing Cuisine Restaurants: {cuisine}")
        for offset in range(0, 200, 50):
            print(f"Parsing Offset: {offset}")
            url = f"https://api.yelp.com/v3/businesses/search?location=NYC&term={cuisine}%20restaurants&categories=&sort_by=best_match&limit=50&offset={offset}"
            headers = {
                "accept": "application/json",
                "Authorization": f"BEARER {key}"
            }
            response = requests.get(url, headers=headers)
            businesses = json.loads(response.text)["businesses"]
            for restaurants in businesses:
                print(restaurants)
                if(restaurants['id'] not in unique_restaurant):
                    unique_restaurant.append(restaurants['id'])
                    restaurant={}
                    ts = time.time_ns()
                    restaurant["insertedAtTimestamp"] = ts
                    restaurant["BusinessId"]=restaurants['id']
                    restaurant["Name"]=restaurants['name']
                    restaurant["Cuisine"] = cuisine
                    if('location' in restaurants):
                        restaurant['Address'] = restaurants['location']['display_address']
                    if('coordinates' in restaurants):
                        restaurant["Coordinates"] = {"Latitude":str(restaurants["coordinates"]["latitude"]), "Longitude": str(restaurants["coordinates"]["longitude"])}
                    if('rating' in restaurants):
                        restaurant["rating"] = str(restaurants["rating"])
                    table.put_item(Item=restaurant)
                else:
                    continue
    return
    
    