import boto3
import io
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from datetime import datetime

import sagemaker
import sagemaker.amazon.common as smac
from sagemaker import get_execution_role

def print_time():
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    print("Date and Time:",date_time)

# Set data locations
bucket = sagemaker.Session().default_bucket()
prefix = "sagemaker/creditcard_fraud_linear_learner"
s3_train_key = "{}/train/recordio-pb-data".format(prefix)
s3_train_path = os.path.join("s3://", bucket, s3_train_key)
local_raw_data = "creditcard_csv.csv"
role = get_execution_role()

# Confirm access to s3 bucket
for obj in boto3.resource("s3").Bucket(bucket).objects.all():
    print(obj.key)

# Read the data, shuffle, and split into train and test sets, separating the labels (last column) from the features
raw_data = pd.read_csv(local_raw_data).values
np.random.seed(0)
np.random.shuffle(raw_data)
train_size = int(raw_data.shape[0] * 0.7)
train_features = raw_data[:train_size, :-1]
train_labels = np.array([x.strip("'") for x in raw_data[:train_size, -1]]).astype(int)
test_features = raw_data[train_size:, :-1]
test_labels = np.array([x.strip("'") for x in raw_data[train_size:, -1]]).astype(int)


# Convert the processed training data to protobuf and write to S3 for linear learner
vectors = np.array([t.tolist() for t in train_features]).astype("float32")
labels = np.array([t.tolist() for t in train_labels]).astype("float32")
buf = io.BytesIO()
smac.write_numpy_to_dense_tensor(buf, vectors, labels)
buf.seek(0)
boto3.resource("s3").Bucket(bucket).Object(s3_train_key).upload_fileobj(buf)

from sagemaker.image_uris import retrieve

def predictor_from_hyperparams(s3_train_data, hyperparams, output_path):
    """
    Create an Estimator from the given hyperparams, fit to training data, and return a deployed predictor
    """
    # specify algorithm containers and instantiate an Estimator with given hyperparams
    container = retrieve(region=boto3.Session().region_name, framework="linear-learner")

    linear = sagemaker.estimator.Estimator(
        container,
        role,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        output_path=output_path,
        sagemaker_session=sagemaker.Session(),
    )
    linear.set_hyperparameters(**hyperparams)
    # train model
    linear.fit({"train": s3_train_data})
    # deploy a predictor
    linear_predictor = linear.deploy(initial_instance_count=1, instance_type="ml.m5.xlarge")
    linear_predictor.serializer = sagemaker.serializers.CSVSerializer()
    linear_predictor.deserializer = sagemaker.deserializers.JSONDeserializer()
    return linear_predictor

def evaluate(linear_predictor, test_features, test_labels, model_name, verbose=True):
    """
    Evaluate a model on a test set given the prediction endpoint.  Return binary classification metrics.
    """
    # split the test data set into 100 batches and evaluate using prediction endpoint
    prediction_batches = [
        linear_predictor.predict(batch)["predictions"]
        for batch in np.array_split(test_features, 100)
    ]
    # parse raw predictions json to exctract predicted label
    test_preds = np.concatenate(
        [np.array([x["predicted_label"] for x in batch]) for batch in prediction_batches]
    )

    # calculate true positives, false positives, true negatives, false negatives
    tp = np.logical_and(test_labels, test_preds).sum()
    fp = np.logical_and(1 - test_labels, test_preds).sum()
    tn = np.logical_and(1 - test_labels, 1 - test_preds).sum()
    fn = np.logical_and(test_labels, 1 - test_preds).sum()

    # calculate binary classification metrics
    recall = tp / (tp + fn)
    precision = tp / (tp + fp)
    accuracy = (tp + tn) / (tp + fp + tn + fn)
    f1 = 2 * precision * recall / (precision + recall)

    if verbose:
        print(pd.crosstab(test_labels, test_preds, rownames=["actuals"], colnames=["predictions"]))
        print("\n{:<11} {:.3f}".format("Recall:", recall))
        print("{:<11} {:.3f}".format("Precision:", precision))
        print("{:<11} {:.3f}".format("Accuracy:", accuracy))
        print("{:<11} {:.3f}".format("F1:", f1))

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "Precision": precision,
        "Recall": recall,
        "Accuracy": accuracy,
        "F1": f1,
        "Model": model_name,
    }

# Training a binary classifier with hinge loss, balanced class weights, and automated threshold tuning
svm_balanced_hyperparams = {
    "feature_dim": 30,
    "predictor_type": "binary_classifier",
    "loss": "hinge_loss",
    "binary_classifier_model_selection_criteria": "precision_at_target_recall",
    "target_recall": 0.9,
    "positive_example_weight_mult": "balanced",
    "epochs": 40,
}
svm_balanced_output_path = "s3://{}/{}/svm_balanced/output".format(bucket, prefix)
svm_balanced_predictor = predictor_from_hyperparams(
    s3_train_path, svm_balanced_hyperparams, svm_balanced_output_path
)

# Evaluate the trained models
predictors = {
    "Hinge with class weights": svm_balanced_predictor
}
metrics = {
    key: evaluate(predictor, test_features, test_labels, key, False)
    for key, predictor in predictors.items()
}
pd.set_option("display.float_format", lambda x: "%.3f" % x)
display(
    pd.DataFrame(list(metrics.values())).loc[:, ["Model", "Recall", "Precision", "Accuracy", "F1"]]
)