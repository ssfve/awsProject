import json
import boto3
import time

s3 = boto3.client('s3')


def lambda_handler(event, context):
    # read parameteres from Step Functions
    bucket = event['bucket_name']
    input_file = event['input_file']
    output_folder = event['output_folder']
    local_file = 'portfolio.json'

    print('bucket:' + bucket)
    print('input_file:' + input_file)
    print('output_folder:' + output_folder)

    # download main file containing the options to be processed
    s3.download_file(bucket, input_file, '/tmp/' + local_file)
    files_to_upload = []
    files_to_upload_full_path = []

    # split the main file in many small files, to allow parallel processing
    with open('/tmp/' + local_file, 'r') as infile:
        o = json.load(infile)
        chunkSize = 10
        for i in range(0, len(o), chunkSize):
            split_file_name = local_file + '_' + str(i // chunkSize) + '.json'
            with open('/tmp/' + split_file_name, 'w') as outfile:
                json.dump(o[i:i + chunkSize], outfile)
                files_to_upload.append(split_file_name)

                # upload the splitted files to S3, to be processed by AWS Batch
    print(files_to_upload)
    for fl in files_to_upload:
        print("uploading: " + fl)
        resp = s3.upload_file('/tmp/' + fl, bucket, output_folder + '/jobs/' + fl)

        files_to_upload_full_path.append(output_folder + '/jobs/' + fl)
        print(resp)

    # return a list containing the splitted files to be processed
    return files_to_upload_full_path