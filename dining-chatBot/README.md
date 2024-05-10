
# Dining Concierge Chatbot

This repository contains the implementation of a Dining Concierge chatbot, which suggests restaurant options based on user preferences provided through conversation. The chatbot is built using serverless, microservice-driven architecture on AWS, incorporating services like Amazon Lex, API Gateway, Lambda, SQS, DynamoDB, SES, and ElasticSearch.

## Architecture Diagram

<img width="753" alt="Screenshot 2024-02-23 at 9 24 28 PM" src="https://github.com/rohnnie/cloud-computing/assets/46161834/abf37af5-c3bc-4def-ad70-1ec542ecd866">


## Assignment Overview

### Requirements
1. Frontend Development: Build and deploy the frontend of the application using AWS S3.
2. API Development: Setup the API using API Gateway and create Lambda functions to handle chat operations.
3. Chatbot Development: Create a Dining Concierge chatbot using Amazon Lex, with Lambda code hooks.
4. Integrate Lex Chatbot: Integrate the Lex chatbot into the API Lambda function.
5. Yelp API Integration: Collect restaurant data from Yelp API and store it in DynamoDB.
6. ElasticSearch Integration: Setup ElasticSearch instance to store restaurant data.
7. Suggestions Module: Build a Lambda function to process restaurant suggestions and send them via email.
8. Extra Credit: Implement state management for the chatbot application.

### Implementation Steps
1. Lambda Function LF0 Setup: Build a Lambda function (LF0) and connect it to API Gateway. This Lambda function will act as the entry point for the application.
2. Data Scraping and Migration: Use Lambda functions to scrape restaurant data from Yelp and store it in DynamoDB. Additionally, migrate this data to ElasticSearch for efficient search operations.
3. Session Handling and Lex Chatbot Integration:
Upon receiving a request, Lambda LF0 checks if the session is new or old.
If the session is new, LF0 triggers Lambda LF1 to interact with the Lex chatbot for responses. User information is stored in SQS.
An EventBridge rule is set up to trigger Lambda LF2 every minute. LF2 fetches data from ElasticSearch and DynamoDB based on session details and sends recommendations via email using SES. It also adds session details (session ID, cuisine, email) to a DynamoDB table called sessionTable.
If the session is old, LF0 retrieves session details from sessionTable, collects data from DynamoDB, and sends out an email directly.
4. Email Sending and Session Management:
LF2 sends restaurant recommendations to users via email using SES.
Session details such as session ID, cuisine, and email are stored in sessionTable for future reference.
5. Frontend: Access the frontend application hosted on the provided AWS S3 bucket URL.
6. Extra Credit - Cookies for Session Management:
Use cookies to store user data and check if the session is new or old. This enhances session management and provides a seamless user experience.

# Contributors
1. Rohan Chopra
2. Reet Nandy
