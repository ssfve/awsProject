"""
This handler import a document in S3 bucket to an Opensearch Cluster after
invoked by S3 notification.
"""
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json
import os
import logging
import urllib.parse
from pypdf import PdfReader
from io import BytesIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

host = os.environ[
    'OSENDPOINT']  # Need to remove https in env var For example, my-test-domain.us-east-1.es.amazonaws.com
region = os.environ['AWSREGION']  # e.g. us-west-1

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

s3_client = boto3.client("s3")

os_client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)


def index_doc(doc, filename, filePath):
    document = {
        'attachment': {'content': doc},
        'filePath': filePath
    }

    try:
        response = os_client.index(
            index="searchbot",
            body=document,
            id=filename
        )
        print(f"Indexing document {filename}.")
        return response
    except Exception as e:
        logger.info(f"Fail to index document {filename} because of {e}")
        return str(e)


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    filePath = "https://s3.us-east-1.amazonaws.com/" + bucket + "/" + key
    try:

        file_content = s3_client.get_object(Bucket=bucket, Key=key)
        reader = PdfReader(BytesIO(file_content["Body"].read()))
        page = reader.pages[0]
        document = page.extract_text()
        print(f"DOCUMENT CONTENT======")
        print(document)

        index_doc(document, key, filePath)

    except Exception as e:
        logger.info(e)
        logger.info('Error parsing pdf file {} from bucket {}.'.format(key, bucket))
        raise e


