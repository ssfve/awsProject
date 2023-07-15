import datetime
import time
import boto3
import requests
import json
import os
import logging

bucket_in = os.environ.get('BUCKET_IN')
bucket_out = os.environ.get('BUCKET_OUT')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def transcribe_file(job_name, file_uri, transcribe_client):
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='mp3',
        LanguageCode='en-US'
    )

    max_tries = 60
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']
        if job_status in ['COMPLETED', 'FAILED']:
            logger.info(f"Job {job_name} is {job_status}.")
            if job_status == 'COMPLETED':
                logger.info(
                    f"Download the transcript from\n"
                    f"\t{job['TranscriptionJob']['Transcript']['TranscriptFileUri']}.")

                transcript_simple = requests.get(
                    job['TranscriptionJob']['Transcript']['TranscriptFileUri']).json()
                logger.info(f"Transcript for job {transcript_simple['jobName']}:")
                logger.info(transcript_simple['results']['transcripts'][0]['transcript'])

                # Upload the file
                s3_client = boto3.client('s3')
                json_object = json.dumps(transcript_simple['results']['transcripts'][0]['transcript'])
                with open('/tmp/' + 'output.txt', 'w') as outfile:
                    json.dump(json_object, outfile)
                response = s3_client.upload_file('/tmp/' + 'output.txt', bucket_out, 'transcribeoutput.txt')
                logger.info(response)
            break
        else:
            logger.info(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)


def lambda_handler(event, context):
    file_object = event['Records'][0]['s3']['object']['key']
    job_name = "sentiment-" + str(datetime.datetime.today().strftime('%Y-%m-%d-%S'))

    transcribe_client = boto3.client('transcribe')

    file_uri = f"s3://{bucket_in}/{file_object}"
    logger.info(file_uri)
    transcribe_file(job_name, file_uri, transcribe_client)
