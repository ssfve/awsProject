# Creating a Lambda package with runtime dependencies
# https://docs.aws.amazon.com/lambda/latest/dg/python-package-create.html#python-package-create-with-dependency
from datetime import datetime
import boto3
import os
import base64
import json

dynamodb = boto3.client('dynamodb')
output_table = os.environ.get('OUTPUT_TABLE_NAME')


def handler(event, context):
    # Response will be a list of records.

    response = {
        "records": []
    }

    for record in event['records']:
        try:
            dynamodb.put_item(TableName=output_table,
                              Item={
                                  'timestamp': {
                                      'S': str(datetime.now())
                                  },
                                  'value': {
                                      'S': base64.b64decode(record.get('data')).decode('utf-8')
                                  }
                              })
            response['records'].append({
                'recordId': record.get('recordId'),
                'result': 'Ok'
            })
        except:
            response['records'].append({
                'recordId': record.get('recordId'),
                'result': 'DeliveryFailed'
            })

    return response


#-- Approximate distinct count  - Counts the number of distinct items in a stream using HyperLogLog.
#-- Returns the approximate number of distinct items in a specified column over a tumbling window.
#-- Note that when there are less or equal to 10,000 items in the window, the function returns exact count.
#CREATE OR REPLACE STREAM DESTINATION_SQL_STREAM (NUMBER_OF_DISTINCT_ITEMS BIGINT);
#CREATE OR REPLACE PUMP "STREAM_PUMP" AS INSERT INTO "DESTINATION_SQL_STREAM"
#SELECT STREAM NUMBER_OF_DISTINCT_ITEMS FROM TABLE(COUNT_DISTINCT_ITEMS_TUMBLING(
#  CURSOR(SELECT STREAM * FROM "SOURCE_SQL_STREAM_001"),
#  'COL1', -- name of column in single quotes
#  60 -- tumbling window size in seconds
#  )
#);
