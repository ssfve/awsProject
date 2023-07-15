## The CIO has instructed the cyber security team to migrate to serverless, highly decoupled ##
## environment. Although the AWS Lambda function below operates in a serverless compute environment ##
## It is trying to accomplish too much. Migrate the below code to stand alone steps of a state machine ##
## were possible. ##

import json
import boto3
import logging
import sys
import time

from botocore.exceptions import ClientError
import time
import os
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')
sts_client = boto3.client('sts')
macie_client = boto3.client('macie2')


##Main handler function that is invoked by Step function Invoke Lambda.
def lambda_handler(event, context):
    logger.info(event)

    # The ingress bucket is the staging bucket were all digital assets that need to be protected are sent.
    ingress_bucket = os.environ['ingress_bucket']

    # Any findings reported by Amazon Macie or if corruption is detected are kept in the analytics bucket for forensic analysis.
    analytics_bucket = os.environ['analytics_bucket']

    # If the digital asset is deemed safe, it is written to a vault that is configured for WORM.
    vault_bucket = os.environ['vault_bucket']

    file_name = event['object']

    state_message = main(ingress_bucket, analytics_bucket, vault_bucket, file_name)

    return {
        'statusCode': 200,
        'body': state_message
    }


##each of the below method calls should be converted into a step in a step machine.
def main(ingress_bucket, analytics_bucket, vault_bucket, file_name):
    print('in main')
    response = {}

    # copies the file from ingress zone to analytics zone
    copyFile(ingress_bucket, file_name, analytics_bucket)

    hasFindings = False
    mockTest = False

    # runs a local test to check for data integrity
    integrity = check_data_integrity(analytics_bucket, file_name)
    if not integrity:
        logging.info('Aborting backup. File is corrupted')
        response['Status'] = "INTEGRITY_FAIL"
        response['JobId'] = "null"
        response['AnalyticsBucket'] = analytics_bucket
        return response

    if not mockTest:
        # creates a classification job to classify the new file
        account_id = sts_client.get_caller_identity()['Account']
        custom_data_identifiers = list_custom_data_identifiers()
        job_result = create_classification_job(analytics_bucket, account_id, custom_data_identifiers, file_name)
        job_id = job_result['jobId']

        # waits until the classification job finishes
        job_result = wait_for_job(job_id)

    if job_result == 'FINDINGS':
        # logging.info('Aborting backup: found High priority findings')
        print('Aborting backup: found High priority findings')
        response['Status'] = "HAS_FINDINGS"
        response['JobId'] = job_id
        response['AnalyticsBucket'] = analytics_bucket
        return response
    elif job_result == 'CANCELLED':
        print('Aborting backup: Macie job cancelled')
        response['Status'] = "JOB_CANCELLED"
        response['JobId'] = job_id
        response['AnalyticsBucket'] = analytics_bucket
        return response

    # copy the file from analytics zone to vault zone
    copyFile(analytics_bucket, file_name, vault_bucket)

    print('Backup sucessfull.')
    response['Status'] = "VAULT_COPY"
    response['JobId'] = job_id
    response['AnalyticsBucket'] = analytics_bucket
    return response


def copyFile(source_bucket, file_name, destination_bucket):
    print('In copyFile')
    copy_source = {
        'Bucket': source_bucket,
        'Key': file_name
    }
    try:
        result = s3.meta.client.copy(copy_source, destination_bucket, file_name)
        print('File ' + file_name + ' copied from ' + source_bucket + ' to ' + destination_bucket)
    except Exception as e:
        print('Error copying file in copyFile')
        print(e)


def check_data_integrity(analytics_bucket, file_name):
    print('In check_data_integrity')
    try:
        df = pd.read_fwf('s3://' + analytics_bucket + '/' + file_name)
        return True
    except Exception as e:
        print('Data integrity error:')
        print(e)
    return False


def list_custom_data_identifiers():
    print('list_custom_data_identifiers')
    """Returns a list of all custom data identifier ids"""
    custom_data_identifiers = []
    try:
        response = macie_client.list_custom_data_identifiers()
        for item in response['items']:
            custom_data_identifiers.append(item['id'])
        return custom_data_identifiers
    except ClientError as e:
        logging.error(e)
        sys.exit(e)


def create_classification_job(data_bucket, account_id, custom_data_identifiers, file_name):
    print('create_classification_job')
    unique_id = "CheckData_" + file_name + str(int(time.time()))
    """Create 1x Macie classification job"""
    try:
        response = macie_client.create_classification_job(
            customDataIdentifierIds=custom_data_identifiers,
            description='Check new data (1x)',
            jobType='ONE_TIME',
            initialRun=True,
            clientToken=unique_id,
            name=unique_id,
            s3JobDefinition={
                'bucketDefinitions': [
                    {
                        'accountId': account_id,
                        'buckets': [
                            data_bucket
                        ]
                    }
                ],
                'scoping': {
                    'includes': {
                        'and': [
                            {
                                'simpleScopeTerm': {
                                    'comparator': 'STARTS_WITH',
                                    'key': 'OBJECT_KEY',
                                    'values': [
                                        file_name,
                                    ]
                                }
                            },
                        ]
                    }
                }
            }
        )
        # logging.debug(f'Response: {response}')
        return response
    except ClientError as e:
        logging.error(e)
        sys.exit(e)


def wait_for_job(job_id):
    print('wait_for_job')

    """waits until the macie job finishes"""
    running = True
    sleepTime = 60  # seconds
    jobStatus = None
    while (running):
        response = macie_client.describe_classification_job(
            jobId=job_id
        )
        if (response['jobStatus'] != 'COMPLETE' and response['jobStatus'] != 'CANCELLED'):
            print(response['jobStatus'])
            print('Still running... sleeping for ' + str(sleepTime))
            time.sleep(sleepTime)
        else:
            jobStatus = response['jobStatus']
            running = False

    if jobStatus == 'COMPLETE':
        hasFindings = look_for_high_priority_findings(job_id)
        if hasFindings:
            return 'FINDINGS'
        else:
            return 'NO_FINDINGS'
    else:
        print('Macie job was CANCELLED')
        return 'CANCELLED'


def look_for_high_priority_findings(job_id):
    print('look_for_high_priority_findings')
    """returns true if a high priority finding is found for the file"""
    findingsSearch = macie_client.list_findings(
        findingCriteria={
            'criterion': {
                'classificationDetails.jobId': {
                    'eq': [
                        job_id,
                    ]
                }
            }
        },
        maxResults=50
    )
    findingIdsList = findingsSearch['findingIds']

    if len(findingIdsList) > 0:
        findingsDict = macie_client.get_findings(
            findingIds=findingIdsList
        )
        findingsList = findingsDict['findings']
        for finding in findingsList:
            print(finding['severity']['description'])
            if (finding['severity']['description'] == 'High'):
                print('Found High priority issue.')
                return True

    return False
