#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import random
from datetime import datetime
import json
import boto3
import base64
from random import randrange
from datetime import timedelta

from kafka import KafkaProducer

batch_no = 0
batch_max = 1000000
batch_size = 500
stream_name = 'stock-stream'
records = []
order_types = ['buy', 'sell']
categories = ['amount', 'price', 'limited', 'stop']
statuses = ['pending', 'open', 'complete', 'canceled', 'rejected']

msk = boto3.client("kafka")

def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)

def print_time_stamp(batch_no):
    curDTObj = datetime.now()
    timeStr = curDTObj.strftime("%Y/%m/%d %H:%M:%S")
    print(f"{timeStr} - Batch Number: {batch_no}")

stocks_df = pd.read_csv('data/stocks.csv')
stocks_lst = stocks_df.values.tolist()
random.seed()

for _ in range(1, batch_max):
    ticker = stocks_lst[random.randint(0,len(stocks_lst)-1)][0] 
    order_class = 'stocks'
    order_type = order_types[random.randint(0,1)]
    category = categories[random.randint(0,3)]
    amount = random.randint(1,500)
    executed = amount
    price = round(random.uniform(10.12, 480.47), 2)
    status = statuses[random.randint(0,4)]
    investor_id = random.randint(1,10000000)

    d1 = datetime.strptime('1/1/2010 12:00 AM', '%m/%d/%Y %I:%M %p')
    d2 = datetime.now()
    rdate = random_date(d1, d2)

    order_date = rdate.strftime("%Y-%m-%d")
    order_time = rdate.strftime("%H:%M:%S")
 
    cluster_arn = "INSERT_CLUSTER_ARN"
    
    response = msk.get_bootstrap_brokers(
            ClusterArn=cluster_arn
        )

    producer = KafkaProducer(security_protocol="PLAINTEXT",bootstrap_servers=response["BootstrapBrokerString"],value_serializer=lambda x: x.encode("utf-8"))

    data = json.dumps({
        "ticker" : ticker,
        "order_class" : order_class,
        "order_type" : order_type,
        "category" : category,
        "amount" : amount,
        "executed" : executed,
        "price" : price,
        "status" : status,
        "investor_id" : investor_id,
        "order_date" : order_date,
        "order_time" : order_time
    })

    producer.send("stock_transactions", value=data)

    print_time_stamp(batch_no)

    batch_no = batch_no + 1
