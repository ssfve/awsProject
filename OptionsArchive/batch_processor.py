import boto3
import argparse
import json
import logging
import traceback
import sys
from european_options import evaluate_european_option
from american_options import evaluate_american_option

def evaluate_option(option):
    print("evaluating " + str(option))
    try:
        if option["exercise"] == "European":
            return evaluate_european_option(option)
        elif option["exercise"] == "American":
            return evaluate_american_option(option)
        else:
            raise Exception("Can not evaluate, exercise type is not supported: {}".format(option["exercise"]))

    except Exception as e:
        print(e)
        return f"Error in processing option [{option}] error: [{e}] trace: [{traceback.format_exc()}]"


def lambda_handler(event, context):
    results = [evaluate_option(opt) for opt in event]
    logging.info(results)
    return {
        "results": results
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--InputFile", type=str, required=True)
    parser.add_argument("--BucketName", type=str, required=True)
    parser.add_argument("--OutputFolder", type=str, required=True)
    args = parser.parse_args()
    
    input_file_name = args.InputFile
    bucket = args.BucketName
    output_folder = args.OutputFolder
    single_input_file_name = input_file_name.split("/")[-1]
    output_file_name = single_input_file_name + '.result.json'
    
    s3 = boto3.client('s3')
    s3.download_file(bucket, input_file_name, single_input_file_name)

    with open(single_input_file_name) as json_file:
        portfolio = json.load(json_file)

        results = lambda_handler(portfolio, None)
        print("results")
        print(results)
        
        with open(output_file_name, 'w') as outfile:
            json.dump(results, outfile)

        resp = s3.upload_file(output_file_name, bucket, output_folder + '/results/' + output_file_name)