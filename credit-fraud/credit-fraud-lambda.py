import json
import os
import boto3
import base64
from datetime import datetime
import uuid

# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
sagemaker_client = boto3.client('runtime.sagemaker')
dynamodb_client = boto3.client('dynamodb')


def put_item(score, payload):
    response = dynamodb_client.put_item(
        TableName='Fraud',
        Item={
            "id": {
                "S": str(uuid.uuid1())
            },
            "datetime": {
                "S": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            },
            "score": {
                "N": str(score)
            },
            "raw_transaction": {
                "S": str(payload)
            }
        }
    )


def lambda_handler(event, context):
    for record in event['Records']:
        # Kinesis data is base64 encoded so decode here
        payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')

        response = sagemaker_client.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                                    ContentType='text/csv',
                                                    Body=payload)

        result = json.loads(response['Body'].read().decode())
        score = result['predictions'][0]['score']
        predicted_label = result['predictions'][0]['predicted_label']

        if predicted_label == 1:
            put_item(score, payload)
            print('This looks like a fraud...' + ' Score: ' + str(score))

    return 'Successfully processed {} transactions.'.format(len(event['Records']))
