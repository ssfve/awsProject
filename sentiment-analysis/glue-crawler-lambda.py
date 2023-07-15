import json
import boto3
import logging
import os
import time

crawler_name = os.environ.get('CRAWLER_NAME')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    glue_client = boto3.client('glue')

    try:
        glue_response = glue_client.start_crawler(
            Name=crawler_name
        )
    except glue_client.exceptions.CrawlerRunningException:
        logger.info("Crawler already running..wait for it to stop and then try again " + crawler_name)
        return False
    except glue_client.exceptions.EntityNotFoundException:
        logger.info("Crawler name provided does not exist " + crawler_name)
        return False

    logger.info(glue_response)

    crawler_response = glue_client.get_crawler(
        Name=crawler_name
    )

    crawler_status = crawler_response['Crawler']['State']

    while crawler_status == "RUNNING":
        logger.info("Crawler is still running sleep for 30 " + crawler_name)
        crawler_response = glue_client.get_crawler(
            Name=crawler_name
        )
        crawler_status = crawler_response['Crawler']['State']
        time.sleep(30)

    return True