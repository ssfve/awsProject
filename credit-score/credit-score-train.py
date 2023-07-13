ROLE = "sagemaker_session_role"
REGION = "us-east-1"
SOLUTION_NAME = "credit-score-automation"
SOLUTION_PREFIX = 'sagemaker-cq-lab'
BUCKET = "sagemaker-lab-bucket-196598475373-us-east-1" #Replace with the bucket name that you copied earlier.

import pandas as pd

df = pd.read_csv('CCR_data.csv')
print(df.shape)
df.head()

df["A"] = df["EBIT"]/df["TotalAssets"]
df["B"] = df["NetSales"]/df["TotalAssets"]
df["C"] = df["MktValueEquity"]/df["TotalLiabs"]
df["D"] = (df["CurrentAssets"]-df["CurrentLiabs"])/df["TotalAssets"]
df["E"] = df["RetainedEarnings"]/df["TotalAssets"]
df = df.drop(["TotalAssets","CurrentLiabs","TotalLiabs", "RetainedEarnings", "CurrentAssets",
              "NetSales", "EBIT", "MktValueEquity"], axis=1)
df.head()

df.to_csv("CCR_data_input.csv", index=False)
df.groupby('Rating').count()

rating_ratio = {"AAA": len(df[df["Rating"] == "AAA"])/len(df), "AA": len(df[df["Rating"] == "AA"])/len(df), "A": len(df[df["Rating"] == "A"])/len(df),
                "BBB": len(df[df["Rating"] == "BBB"])/len(df), "BB": len(df[df["Rating"] == "BB"])/len(df), "B": len(df[df["Rating"] == "B"])/len(df),
                "CCC": len(df[df["Rating"] == "CCC"])/len(df)}
rating_ratio

sample = 500
df_sample = pd.concat([df[df['Rating'] == k].sample(int(v * sample), replace=False, random_state=42) for k, v in rating_ratio.items()])
df_sample.shape

df_sample.to_csv("CCR_data_input_sample.csv", index=False)

!pip install smjsindustry --no-index --find-links file:../wheelhouse

# import boto3
# client = boto3.client('s3')
# client.download_file(BUCKET, '{}/{}'.format("nlp_score", 'ccr_nlp_score_sample.csv'), 'ccr_nlp_score_sample.csv')


df_tabtext_score = pd.read_csv('ccr_nlp_score_sample.csv')
df_tabtext_score.head()

! bash ../prepare_model_code.sh

