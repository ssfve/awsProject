#!/bin/bash

date
echo "Args: $@"
env
echo "This is my simple test job!."
echo "jobId: $AWS_BATCH_JOB_ID"
python3 --version
python3 hello.py >> batch.log
python3 batch_processor.py --InputFile $1 --BucketName $2 --OutputFolder $3 >> batch.log
date
aws s3 sync . s3://$2/logs/
echo "bye bye!!"


