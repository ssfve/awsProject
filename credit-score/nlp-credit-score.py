%%script false --no-raise-error #This line keeps this cell from running by accident.  If you try, it will fail.


import sagemaker
from smjsindustry import NLPScoreType, NLPSCORE_NO_WORD_LIST
from smjsindustry import NLPScorer, NLPScorerConfig

score_type_list = list(
    NLPScoreType(score_type, [])
    for score_type in NLPScoreType.DEFAULT_SCORE_TYPES
    if score_type not in NLPSCORE_NO_WORD_LIST
)

score_type_list.extend([NLPScoreType(score_type, None) for score_type in NLPSCORE_NO_WORD_LIST])
nlp_scorer_config = NLPScorerConfig(score_type_list)

nlp_score_processor = NLPScorer(
        ROLE,
        1,
        'ml.c5.18xlarge',
        volume_size_in_gb=30,
        volume_kms_key=None,
        output_kms_key=None,
        max_runtime_in_seconds=None,
        sagemaker_session=sagemaker.Session(default_bucket=BUCKET),
        tags=None)

nlp_score_processor.calculate(
    nlp_scorer_config,
    "MDNA",
    "CCR_data_input_sample.csv",               # replace this with CCR_data_input.csv if you want to use the full dataset
    's3://{}/{}'.format(BUCKET, "nlp_score"),
    'ccr_nlp_score_sample.csv')

# start to train model

from sklearn.model_selection import train_test_split
train_data, test_data = train_test_split(
    df_tabtext_score, test_size=0.2, random_state=42, stratify=df_tabtext_score['Rating']
)

import sagemaker
session = sagemaker.Session()

train_data.to_csv("train_data.csv", index=False)
test_data.to_csv("test_data.csv", index=False)

train_s3_path = session.upload_data('train_data.csv', bucket=BUCKET, key_prefix='data')
test_s3_path = session.upload_data('test_data.csv', bucket=BUCKET, key_prefix='data')

from sagemaker.mxnet import MXNet

init_args = {
  'label': 'Rating'
}

hyperparameters = {'init_args': str(init_args)}

tags = [{'Key' : 'AlgorithmName', 'Value' : 'AutoGluon-Tabular'},
        {'Key' : 'ProjectName', 'Value' : 'Jumpstart-Industry-Finance'},]

estimator = MXNet(
    entry_point="train.py",
    role=ROLE,
    instance_count=1,
    instance_type="ml.c5.2xlarge", # Specify the desired instance type
    framework_version="1.8.0",
    py_version="py37",
    source_dir="../model-training",
    base_job_name='sagemaker-soln-ccr-js-training',
    hyperparameters=hyperparameters,
    tags=tags,
    disable_profiler=True,
    debugger_hook_config=False,
    enable_network_isolation=True,  # Set enable_network_isolation=True to ensure a security running environment
    output_path = 's3://{}/{}'.format(BUCKET, "output")
)


inputs = {'training': train_s3_path, 'testing': test_s3_path}

estimator.fit(inputs)
import boto3

s3_client = boto3.client("s3")
job_name = estimator._current_job_name
s3_client.download_file(BUCKET, '{}/{}/{}/{}'.format('output', job_name, 'output', 'output.tar.gz'), "output.tar.gz")
!tar -xvzf output.tar.gz
import json

with open('evaluation.json') as f:
    data = json.load(f)
print(data)
print("The test accuracy is {}.".format(data['accuracy']))
from IPython.display import display, Image
display(Image(filename='confusion_matrix.png'))
training_job_name = estimator.latest_training_job.name
print("Training job name: ", training_job_name)

from sagemaker.mxnet import MXNet
attached_estimator = MXNet.attach(training_job_name)
attached_estimator.model_data

# deploy an inference endpoint

from sagemaker.mxnet import MXNetModel

endpoint_name = SOLUTION_PREFIX + "-endpoint"

deployed_model = MXNetModel(
    framework_version="1.8.0",
    py_version="py37",
    model_data=attached_estimator.model_data,
    role=ROLE,
    entry_point="inference.py",
    code_location='s3://{}'.format(BUCKET),
    source_dir="../model-inference",
    name=SOLUTION_PREFIX + "-model",
    enable_network_isolation=True)     # Set enable_network_isolation=True to ensure a security running environment

ccr_endpoint = deployed_model.deploy(
    instance_type='ml.m5.xlarge',
    initial_instance_count=1,
    endpoint_name=endpoint_name,
    wait=True)

test_endpoint_data = test_data.sample(n=5).drop(["Rating"], axis=1)
test_endpoint_data

import sagemaker
from sagemaker import Predictor

endpoint_name = SOLUTION_PREFIX + "-endpoint"


predictor = Predictor(
    endpoint_name=endpoint_name,
    sagemaker_session=sagemaker.Session(),
    deserializer=sagemaker.deserializers.JSONDeserializer(),
    serializer=sagemaker.serializers.CSVSerializer(),
)

predictor.predict(test_endpoint_data.values)