import os, boto3, logging

# AWS Lambda Function Logging in Python - More info: https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Boto3 - Rekognition Client
# More Info: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/comprehend.html
comprehend_client = boto3.client('comprehend')


def lambda_handler(event, context):
    logger.info(event)
    sentiment = comprehend_client.detect_sentiment(Text=event['content'], LanguageCode='en')['Sentiment']
    return {'sentiment': sentiment}
