#!/bin/bash

# This script installs aws load balancer controller add-on.

# Create bash_profile file.
echo "export CLUSTER_NAME=banking-app-cluster" | tee -a ~/.bash_profile
source ~/.bash_profile

# Create an IAM OIDC identity provider for the cluster 
eksctl utils associate-iam-oidc-provider --cluster $CLUSTER_NAME --approve --region $AWS_REGION

# Create a folder for alb installation
mkdir /home/ec2-user/environment/install-alb-add-on
cd /home/ec2-user/environment/install-alb-add-on/

# Create an IAM role. Create a Kubernetes service account named aws-load-balancer-controller in the kube-system namespace 
# for the AWS Load Balancer Controller and annotate the Kubernetes service account with the name of the IAM role.
eksctl create iamserviceaccount \
  --cluster=$CLUSTER_NAME \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name "AmazonEKSLoadBalancerControllerRole" \
  --attach-policy-arn=arn:aws:iam::$ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --override-existing-serviceaccounts

#Install cert-manager
kubectl apply \
    --validate=false \
    -f https://github.com/jetstack/cert-manager/releases/download/v1.5.4/cert-manager.yaml

# Wait 10 seconds for cert-manager to get installed.
sleep 10

#Download the controller specification.
curl -Lo v2_4_4_full.yaml https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.4.4/v2_4_4_full.yaml

# Remove the ServiceAccount section in the manifest. 
sed -i.bak -e '480,488d' ./v2_4_4_full.yaml

# Replace your-cluster-name in the Deployment spec section of the file with the name of the cluster by replacing my-cluster with the name of the cluster.
sed -i.bak -e "s|your-cluster-name|$CLUSTER_NAME|" ./v2_4_4_full.yaml

# Apply the file
kubectl apply -f v2_4_4_full.yaml

# Download the IngressClass and IngressClassParams manifest to the cluster.
curl -Lo v2_4_4_ingclass.yaml https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.4.4/v2_4_4_ingclass.yaml

# Apply the manifest to your cluster.
kubectl apply -f v2_4_4_ingclass.yaml

# Return back to /home/ec2-user/environment
cd /home/ec2-user/environment