#!/bin/bash

# This script creates a docker image of the apps and uploads the image to Amazon ECR.
source ~/.bash_profile

echo "Creating an ECR image for the deposit application"

cd /home/ec2-user/environment/deposit-app

# Create an ECR image for the deposit application
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker build -t deposit-app-$ACCOUNT_ID .
docker tag deposit-app-$ACCOUNT_ID:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/deposit-app-$ACCOUNT_ID:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/deposit-app-$ACCOUNT_ID:latest

echo "Creating an ECR image for the mortgage application"

cd /home/ec2-user/environment/mortgage-app

# Create an ECR image for the mortgage application
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker build -t mortgage-app-$ACCOUNT_ID .
docker tag mortgage-app-$ACCOUNT_ID:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mortgage-app-$ACCOUNT_ID:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mortgage-app-$ACCOUNT_ID:latest