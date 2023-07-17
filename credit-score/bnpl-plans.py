import json
import boto3
import requests
import urllib.parse
import os
from boto3.dynamodb.conditions import Key, Attr
from aws_requests_auth.aws_auth import AWSRequestsAuth

table_name = os.environ['TABLE_NAME']
endpoint = os.environ['ENDPOINT']

dynamodb_resource = boto3.resource('dynamodb')
table = dynamodb_resource.Table(table_name)

credentials = boto3.Session().get_credentials()
auth = AWSRequestsAuth(
    aws_access_key=credentials.access_key,
    aws_secret_access_key=credentials.secret_key,
    aws_token=credentials.token,
    aws_host=urllib.parse.urlparse(endpoint).netloc,
    aws_region="us-east-1",
    aws_service="execute-api"
)


def lambda_handler(event, context):
    # get customerId from path
    customer_id = event['pathParameters']['customer_id']

    # call credit api to verify if customer credit score allows BNPL
    response = requests.get(
        url=endpoint + '/' + customer_id,
        auth=auth,
    )

    if (response.status_code == 200):
        score = int(response.json()['score'])
        if (score < 500):
            print('score < 500...')
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': '{"message": "Insufficient credit score. There are no BNPL options available."}'
            }

        response = table.scan(
            FilterExpression=Attr('end_date').eq('null')
        )

        print('found installments...')
        print(response['Items'])
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(response['Items'])
        }
    else:
        print('error...')
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': '{"message": "Error trying to get BNPL options."}'
        }