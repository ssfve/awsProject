#!/usr/bin/env python

import random

import mysql.connector
from mysql.connector import Error
from faker import Faker
from faker.providers import bank, currency

Faker.seed(20000)

fake = Faker()
fake.add_provider(currency)
fake.add_provider(bank)


create_table_sql = """
CREATE TABLE `lending_table` (
  `customer_id` int(11) NOT NULL AUTO_INCREMENT,
  `loan_type` varchar(20) NOT NULL,
  `loan_id` varchar(20) NOT NULL,
  `payment` varchar(20) NOT NULL,
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
"""

db_host = "CLUSTER_ENDPOINT"
db_name = "lending"
db_user = "admin"
db_pass = "Lab1234!"

try:
    conn = mysql.connector.connect(host=db_host, database = db_name,
                                   user=db_user, password=db_pass)

    if conn.is_connected():
        cursor = conn.cursor()

        try:
            cursor.execute(create_table_sql)
            print("Table created")
        except Exception as e:
            print("Error creating table", e)
        row = {}
        n = 0

        while True:
            n += 1
            row = [fake.random_element(elements=('Conventional', 'Fixed-Rate', 'Adjustable-Rate', 'FHA', 'USDA', 'VA', 'Jumbo')), fake.bban(), round(random.uniform(500, 10000), 2)]

            cursor.execute(' \
                INSERT INTO `lending_table` (loan_type, loan_id, payment) \
                VALUES ("%s", "%s", "%s"); \
                ' % (row[0], row[1], row[2]))

            if n % 100 == 0:
                print("iteration %s" % n)
                conn.commit()
except Error as e :
    print ("error", e)
    pass
except Exception as e:
    print ("Unknown error %s", e)
finally:
    #closing database connection.
    if(conn and conn.is_connected()):
        conn.commit()
        cursor.close()
        conn.close()