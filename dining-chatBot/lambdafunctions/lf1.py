import json
import datetime
import time
import os
import dateutil.parser
import logging
import math
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


cities=["New york","Boston"]
cuisines=["American","Chinese","Cuban","Greek","Indian","Italian","Japanese","Korean","Mexican","Thai","Vietnamese"]

# -------------------- DELEGATE -----------------------------

def delegate(event,slots):
    print("inside delegate")
    response= {
        "sessionState":{
            "sessionAttributes":event['sessionState']['sessionAttributes'] if event['sessionState']['sessionAttributes'] is not None else {},
            "dialogAction":{
                "type":"Delegate"
            },
            "intent":{
                "name":event['sessionState']['intent']['name'],
                "slots":slots,
                "state":"ReadyForFulfillment"
            }
        }
    }
    print(response)
    return response

# -------------------- Date Format Check Function -----------------------------
def check_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except:
        return False

# -------------------- Time Format Check Function -----------------------------
def check_time(time):
    try:
        dateutil.parser.parse(time)
        return True
    except:
        return False

# -------------------- Slot Validation Helper Function -----------------------------
def validate(flag,slot,message):
    if(not flag):
        return {
            "isValid":flag,
            "slot":slot,
            "message":message
        }

# -------------------- Slot Validate Function -----------------------------
def validateSlots(slots):
    logger.debug(f"Validating Slots")
    
    location=slots['Location'] if slots['Location'] is None else slots['Location']['value']['originalValue'].capitalize()
    cuisine=slots['Cuisine'] if slots['Cuisine'] is None else slots['Cuisine']['value']['originalValue'].capitalize()
    dining_date=slots['Date'] if slots['Date'] is None else slots['Date']['value']['originalValue']
    dining_time=slots['Time'] if slots['Time'] is None else dateutil.parser.parse(slots['Time']['value']['originalValue'])
    noOfPeople=slots['People'] if slots['People'] is None else int(slots['People']['value']['originalValue'])
    email=slots['Email'] if slots['Email'] is None else slots['Email']['value']['originalValue']
    
    if(location is None):
        return validate(False,'Location',"May I know the city in which you are looking for restaurants?")
    if(location is not None and location not in cities):
        return validate(False,'Location',f"Sorry, currently we do not operate in {location}. Kindly select from [{", ".join(cities)}].")
    
    if(cuisine is None):
        return validate(False,'Cuisine',"What kind of cuisine would you like to have?")
    if(cuisine is not None and cuisine not in cuisines):
        return validate(False,'Cuisine',f"Sorry, currently we do not serve {cuisine}. Kindly select from [{", ".join(cuisines)}].")
    
    if(dining_date is None):
        return validate(False,'Date',"For which date would you like to make the reservation?")
    if(not check_date(dining_date)):
        return validate(False,"Date",f"Sorry, Im not able to understand thr format of date. Kindly enter in YYYY-MM-DD format.")
    
    if(dining_time is None):
        return validate(False,'Time',"At what time you will be arriving?")
    if(dining_time is not None):
        print(dining_time)
        print(type(dining_time))
        if(not check_time(str(dining_time))):
            return validate(False, 'Time', 'I am sorry that it is not a valid time. Please enter a valid time in HH:MM format.')
    
    if(noOfPeople is None):
        return validate(False,'People',"How many people ?")
    if(noOfPeople is not None):
        if(int(noOfPeople)<1):
            return validate(False,'People',"Sorry, atleast 1 person is required for restaurant suggestions!")
    
    if(email is None):
        return validate(False,'Email',"May I have your email to which confirmation will be sent?")
    if(email is not None):
        if('@' not in email):
            return validate(False,'Email',"Kindly enter a valid email.")
    return {"isValid":True}
    
            
# -------------------- Greeting Intent  -----------------------------
def greeting(event):
    logger.debug(f"Greeting Intent Called!")
    
    response= {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": event['sessionState']['intent']['name'],
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Hi, How may I help you?"
            }
        ]
    }
    return response

# -------------------- Dining Intent  -----------------------------
def dining(event):
    logger.debug(f"Dining Intent Called!")
    
    slots=event['sessionState']['intent']['slots']
    location=slots['Location'] if slots['Location'] is None else slots['Location']['value']['originalValue']
    cuisine=slots['Cuisine'] if slots['Cuisine'] is None else slots['Cuisine']['value']['originalValue']
    dining_date=slots['Date'] if slots['Date'] is None else slots['Date']['value']['originalValue']
    dining_time=slots['Time'] if slots['Time'] is None else slots['Time']['value']['originalValue']
    noOfPeople=slots['People'] if slots['People'] is None else slots['People']['value']['originalValue']
    email=slots['Email'] if slots['Email'] is None else slots['Email']['value']['originalValue']

    #check if the invocation if in progress
    if(event['invocationSource']=="DialogCodeHook"):
        #check if the input values are correct
        validate_result = validateSlots(event['sessionState']['intent']['slots'])
        print(validate_result)
        
        if(not validate_result["isValid"]):

            slots[validate_result['slot']]=None
            if(validate_result['message'] is None):
                response={
                    "sessionState":{
                        "sessionAttributes":event['sessionState']['sessionAttributes'] if event['sessionState']['sessionAttributes'] is not None else {},
                        "dialogAction":{
                            "slotToElicit":validate_result['slot'],
                            "type":"ElicitSlot"
                        },
                        "intent": {
                            "name": event['sessionState']['intent']['name'],
                            "slots": slots
                        }
                    }
                }
            else:
                response={
                    "sessionState":{
                        "sessionAttributes":event['sessionState']['sessionAttributes'] if event['sessionState']['sessionAttributes'] is not None else {},
                        "dialogAction":{
                            "slotToElicit":validate_result['slot'],
                            "type":"ElicitSlot"
                        },
                        "intent": {
                            "name": event['sessionState']['intent']['name'],
                            "slots": slots
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": validate_result["message"]
                        }
                    ]
                }
            return response
        return delegate(event,event['sessionState']['intent']['slots'])
    
    #When all slots have been filled
    elif(event['invocationSource']=='FulfillmentCodeHook'):
        sqs_client = boto3.client('sqs')
        sqs_url = sqs_client.get_queue_url(QueueName="SQ1")
        sqs_url = sqs_url['QueueUrl']
        print(sqs_url)
        print(location,cuisine,dining_date,dining_time,noOfPeople,email)
        
        response=sqs_client.send_message(
            QueueUrl=sqs_url,
            MessageAttributes={
                'Location': {
                    'DataType': 'String',
                    'StringValue': location
                },
                'Cuisine': {
                    'DataType': 'String',
                    'StringValue': cuisine
                },
                'Date': {
                    'DataType': 'String',
                    'StringValue': dining_date
                },
                'Time': {
                    'DataType': 'String',
                    'StringValue': dining_time
                },
                'People': {
                    'DataType': 'Number',
                    'StringValue': str(noOfPeople)
                },
                'Email': {
                    'DataType': 'String',
                    'StringValue': email
                },
                'sessionId':{
                    'DataType':'String',
                    'StringValue': event['sessionId']
                }
            },
            MessageBody = f"User input for restaurant suggestions with session id {event['sessionId']}"
            )
            
        #Close the intent
        response={
            "sessionState":{
                "sessionAttributes":event['sessionState']['sessionAttributes'] if event['sessionState']['sessionAttributes'] is not None else {},
                "dialogAction":{
                    "type":"Close"
                },
                "intent":{
                    "name":event['sessionState']['intent']['name'],
                    "slots":slots,
                    "state":"Fulfilled"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Thank you for using our service. A list of suggested restaurants will be sent to your mail shortly!"
                }
            ]
        }
        return response


# -------------------- Thank You Intent  -----------------------------
def thankYou(event):
    logger.debug(f"Thank You Intent Called!")
    response= {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": event['sessionState']['intent']['name'],
                "state": "Fulfilled"
            }
        }
        # "messages": [
        #     {
        #         "contentType": "PlainText",
        #         "content": "Happy to assist you! Bye."
        #     }
        # ]
    }
    return response


# -------------------- Determine Intent  -----------------------------
def detectIntent(event):
    logger.debug(f"Inside detectIntent function!")
    
    print(event)
    intent_name = event['sessionState']['intent']['name']
    if(intent_name=="greetingIntent"):
        return greeting(event)
    elif(intent_name=="thankYouIntent"):
        return thankYou(event)
    elif(intent_name=="diningIntent"):
        return dining(event)
    else:
        raise Exception('Intent with name ' + intent_name + ' not supported')
    
    

def lambda_handler(event, context):
    #Using new york time 
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    #Enabled logging
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return detectIntent(event)
    