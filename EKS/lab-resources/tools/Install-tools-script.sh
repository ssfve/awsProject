#!/bin/bash

sudo yum -y install jq gettext bash-completion moreutils

#Install AWS CLI V2 - You may need to restart terminal.
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update

# Reinitialize the terminal
reinit(){
  reset
  exec sudo --login --user "$USER" /bin/sh -c "cd '$PWD'; exec '$SHELL' -l"
}
aws --version
# Install and verify Kubectl - https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html

curl -o kubectl https://s3.us-west-2.amazonaws.com/amazon-eks/1.23.13/2022-10-31/bin/linux/amd64/kubectl
chmod +x ./kubectl
mkdir -p $HOME/bin && cp ./kubectl $HOME/bin/kubectl && export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc
kubectl version --short --client

#Enable kubectl bash_completion
kubectl completion bash >>  ~/.bash_completion
. /etc/profile.d/bash_completion.sh
. ~/.bash_completion

# Install and verify Eksctl - https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html

curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version

# Update credentials settings.
aws cloud9 update-environment  --environment-id $C9_PID --managed-credentials-action DISABLE
rm -vf ${HOME}/.aws/credentials

# Export environment variables

export ACCOUNT_ID=$(aws sts get-caller-identity --output text --query Account)
export AWS_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r '.region')
export AZS=($(aws ec2 describe-availability-zones --query 'AvailabilityZones[].ZoneName' --output text --region $AWS_REGION))

test -n "$AWS_REGION" && echo AWS_REGION is "$AWS_REGION" || echo AWS_REGION is not set

echo "export ACCOUNT_ID=${ACCOUNT_ID}" | tee -a ~/.bash_profile
echo "export AWS_REGION=${AWS_REGION}" | tee -a ~/.bash_profile
echo "export AZS=(${AZS[@]})" | tee -a ~/.bash_profile
aws configure set default.region ${AWS_REGION}
aws configure get default.region

# Update account id in deployment file.
sed -i.bak -e "s|your-account-id|$ACCOUNT_ID|" /home/ec2-user/environment/deployment-files/create-cluster.yaml
