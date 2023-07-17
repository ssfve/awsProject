import boto3

from kafka import KafkaConsumer
from json import loads

msk = boto3.client("kafka")
dynamodb = boto3.client('dynamodb')

count = 0
output_table = "stock_transactions_table"

cluster_arn = "arn:aws:kafka:us-east-1:575523709134:cluster/retail-stock-cluster/287a34dc-5fb4-4ab2-8422-73eb3c1e6a27-3"

response = msk.get_bootstrap_brokers(
    ClusterArn=cluster_arn
)

consumer = KafkaConsumer(
    'stock_transactions',
    bootstrap_servers=response["BootstrapBrokerString"],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='my-group',
    value_deserializer=lambda x: loads(x.decode('utf-8')))

for message in consumer:
    value = message.value
    count = count + 1

    dynamodb.put_item(TableName=output_table,
                      Item={
                          'investor_id': {
                              'N': str(value['investor_id'])
                          },
                          'ticker': {
                              'S': value['ticker']
                          },
                          'order_class': {
                              'S': value['order_class']
                          },
                          'order_type': {
                              'S': value['order_type']
                          },
                          'category': {
                              'S': value['category']
                          },
                          'amount': {
                              'S': str(value['amount'])
                          },
                          'executed': {
                              'S': str(value['executed'])
                          },
                          'price': {
                              'S': str(value['price'])
                          },
                          'status': {
                              'S': value['status']
                          },
                          'order_date': {
                              'S': value['order_date']
                          },
                          'order_time': {
                              'S': value['order_time']
                          }
                      })

    print('Item ' + str(count) + ' added to database')