import os
import time
import boto3
from boto3 import client, resource
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeDeserializer
from random import randint
from datetime import date

db_source = os.environ.get("db_source")
print(db_source)


session = boto3.Session(region_name='us-east-1')
client = session.client('dynamodb')
resource = session.resource('dynamodb')

acctTable = resource.Table('accounts')
transTable = resource.Table('deposits_transactions')



def getAccountDetailsByAcctId(acc_id):

    response = acctTable.query(TableName='accounts',
            KeyConditionExpression=Key('acc_id').eq(acc_id)
    )
    print(response)
    return response


def updateAcctBalance(acc_id, balance):
    response = acctTable.update_item(
        Key = {
            'acc_id': acc_id
        },
        AttributeUpdates={
            'balance': {
                'Value'  : balance,
                'Action' : 'PUT' # # available options -> DELETE(delete), PUT(set), ADD(increment)
            }
        },
        ReturnValues = "UPDATED_NEW"  # returns the new updated values
    )
    return response

def insertTransactions(acc_id,trans_message,amount):
    session = boto3.Session(region_name='us-east-1')
    resource1 = session.resource("dynamodb")
    tTable = resource1.Table('deposits_transactions')
    response = tTable.put_item(Item = {"trans_id": randint(0,10000), "acc_id": int(acc_id), "trans_message": trans_message, "last_updated_date": str(date.today()), "amount" : int(amount)})   
    if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
        return {
            'msg': 'Add transaction successful',
        }
    return { 
        'msg': 'error occurred',
        'response': response
    }

def getTransactions(acc_id,number):
    response = transTable.query( TableName='deposits_transactions',
            KeyConditionExpression=Key('acc_id').eq(acc_id),
            Limit=int(number),
            ScanIndexForward=True)

    return response
    

def transactionUpdate(src_data,trg_data,src_balance,trg_balance,amount):
    response = client.transact_write_items(
                TransactItems=[
                    {
                        'Update': {
                            'TableName': 'accounts',
                            'Key': {
                                'acc_id': {'N': str(trg_data['acc_id'])},
                            },
                            'ExpressionAttributeNames': {
                                '#balance': "balance"
                            },
                            'ExpressionAttributeValues': {
                                ':balance': {'N': str(trg_balance)},
                            },
                            'UpdateExpression': "SET #balance = :balance" 
                        }
                    },
                    {                                            
                        'Update': {
                            'TableName': 'accounts',
                            'Key': {
                                'acc_id': {'N': str(src_data['acc_id'])},
                            },
                            'ExpressionAttributeNames': {
                                '#balance': "balance"
                            },
                            'ExpressionAttributeValues': {
                                ':balance': {'N': str(src_balance)},
                            },
                            'UpdateExpression': "SET #balance = :balance" 
                        }
                    }
                ]
    )
    return response
