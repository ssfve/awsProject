import json
import boto3
import os
import json

s3 = boto3.resource('s3')
glue = boto3.client('glue')

workflow = os.environ['WORKFLOW_NAME']


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))

    try:
        start_glue_workflow = glue.start_workflow_run(
            Name=workflow
        )
        print('Started glue workflow ID {} '.format(start_glue_workflow['RunId']))

    except Exception as e:
        print(e)
        raise e