import json
import boto3
import time
import csv

STREAM_NAME = "TransactionsStream"
kinesis_client = boto3.client('kinesis')
filename = 'creditcard_csv.csv'

with open(filename, 'r') as csvfile:
    # open the csv file
    datareader = csv.reader(csvfile)
    cont = 0

    # iterate over the csv lines
    for row in datareader:
        # remove last column
        row.pop()
        # ignores header - row 0
        if cont > 0:
            # replace unwanted characters
            str_row = str(row).replace("'", "").replace("[", "").replace("]", "").replace(" ", "")
            # print(str_row)
            print('sending transaction #' + str(cont))
            print(str_row)

            # send the record to Kinesis Streams in csv format...
            kinesis_client.put_record(
                StreamName=STREAM_NAME,
                Data=str_row,
                PartitionKey="partitionkey")

        # stop after sending 10 transactions
        cont = cont + 1
        if cont > 1000:
            break