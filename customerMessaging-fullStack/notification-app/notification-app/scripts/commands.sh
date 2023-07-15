## Config update for backend application 
sudo yum -y install jq
cd ~/environment/notification-app/backend
export BUCKET_NAME=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'resource-bucket')].Name" --output text)
sed -Ei "s|<BUCKET_NAME>|${BUCKET_NAME}|g" samconfig.toml
export AWS_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r '.region')
sed -Ei "s|<AWS_REGION>|${AWS_REGION}|g" samconfig.toml
export LAMBDA_ROLE_ARN=$(aws iam  list-roles --query "Roles[?contains(RoleName, 'LambdaDeploymentRole')].Arn" --output text)
sed -Ei "s|<LAMBDA_ROLE_ARN>|${LAMBDA_ROLE_ARN}|g" samconfig.toml
export SQS_ROLE_ARN=$(aws iam  list-roles --query "Roles[?contains(RoleName, 'SQSRole')].Arn" --output text)
sed -Ei "s|<SQS_ROLE_ARN>|${SQS_ROLE_ARN}|g" samconfig.toml
export STEP_FUNCTIONS_ROLE_ARN=$(aws iam  list-roles --query "Roles[?contains(RoleName, 'StepFunctionsRole')].Arn" --output text)
sed -Ei "s|<STEP_FUNCTIONS_ROLE_ARN>|${STEP_FUNCTIONS_ROLE_ARN}|g" samconfig.toml

## Config update for frontend application
cd ~/environment/notification-app/frontend/src
export API_GATEWAY_ID=$(aws apigateway get-rest-apis --query 'items[?name==`MLNApp`].id' --output text)  
export AWS_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r '.region')
sed -Ei "s|<AWS_REGION>|${AWS_REGION}|g" aws-exports.js
export API_GATEWAY_URL=https://${API_GATEWAY_ID}.execute-api.${AWS_REGION}.amazonaws.com/dev 
sed -Ei "s|<API_GATEWAY_URL>|${API_GATEWAY_URL}|g" aws-exports.js
export COGNITO_USER_POOL_ID=$(aws cognito-idp list-user-pools --query "UserPools[?contains(Name, 'MultiNotificationUserPool')].Id"  --max-results 1 --output text)
sed -Ei "s|<COGNITO_USER_POOL_ID>|${COGNITO_USER_POOL_ID}|g" aws-exports.js
export APP_CLIENT_ID=$(aws cognito-idp list-user-pool-clients --user-pool-id ${COGNITO_USER_POOL_ID}  --query "UserPoolClients[?contains(ClientName, 'MultiNotificationAppClient')].ClientId"  --output text)
sed -Ei "s|<APP_CLIENT_ID>|${APP_CLIENT_ID}|g" aws-exports.js
cd ..

## Upload app.zip to S3
export BUCKET_NAME=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'resource-bucket')].Name" --output text)
aws s3 cp app.zip s3://${BUCKET_NAME}



