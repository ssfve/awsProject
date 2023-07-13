import boto3
from trp import Document
import json
from datetime import datetime
import uuid

# Amazon Textract and DynamoDB clients
textract_client = boto3.client('textract')
dynamodb_client = boto3.client('dynamodb')


def put_item(first_name, last_name, address, date_of_birth, phone, email, option):
    response = dynamodb_client.put_item(
        TableName='loan_application',
        Item={
            "id": {
                "S": str(uuid.uuid1())
            },
            "date_time": {
                "S": datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            },
            "first_name": {
                "S": first_name
            },
            "last_name": {
                "S": last_name
            },
            "address": {
                "S": address
            },
            "date_of_birth": {
                "S": date_of_birth
            },
            "phone": {
                "S": phone
            },
            "email": {
                "S": email
            },
            "option": {
                "S": option
            }
        }
    )


def get_field(key, page):
    field = page.form.getFieldByKey(key)
    value = ""
    if (field):
        value = str(field.value.text)
        return value
    return ""


def get_option(page, value):
    for field in page.form.fields:
        if (str(field.value.text) == value):
            return str(field.key.text)
    return ""


def lambda_handler(event, context):
    for record in event['Records']:
        payload = record["body"]
        json_object = json.loads(str(payload))
        for sub_record in json_object['Records']:
            s3BucketName = sub_record['s3']['bucket']['name']
            documentName = sub_record['s3']['object']['key']

            # Call Amazon Textract
            response = textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': s3BucketName,
                        'Name': documentName
                    }
                },
                FeatureTypes=["FORMS"])

            doc = Document(response)

            first_name, last_name, address, date_of_birth, phone, email = "", "", "", "", "", ""
            credit_cards, cash, consumer_credit, business, other, option = "", "", "", "", "", ""

            for page in doc.pages:
                option = get_option(page, "SELECTED")
                first_name = get_field("First Name:", page)
                last_name = get_field("Last Name:", page)
                address = get_field("Address:", page)
                date_of_birth = get_field("Date of Birth:", page)
                phone = get_field("Phone:", page)
                email = get_field("E-mail:", page)

                # Store results do DynamoDB
                put_item(first_name, last_name, address, date_of_birth, phone, email, option)

    return {
        'statusCode': 200,
        'body': json.dumps('OK!')
    }