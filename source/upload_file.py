import logging
import uuid
import boto3
from botocore.exceptions import ClientError
from PIL import Image

region = 'us-east-1'  

BUCKET_NAME = 'aws-input-cap'
UPLOAD_FOLDER = './upload_dir/'
OUTPUT_BUCKET_NAME = 'aws-output-cap'

def upload_file(file_name, bucket = BUCKET_NAME, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3', region_name = region)
    try:
        response = s3_client.upload_file(UPLOAD_FOLDER+file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def download_file(bucket = OUTPUT_BUCKET_NAME):
    # print("JI")
    # output_file = open("myfile.txt","w")
    s3_client = boto3.resource('s3', region_name = region)
    my_bucket = s3_client.Bucket(OUTPUT_BUCKET_NAME)
    print(len(list(my_bucket.objects.all())))
    try:
        for s3_object in my_bucket.objects.all():
            filename = s3_object.key
            print(s3_object.get()["Body"].read())
            imgname= str(s3_object.get()["Body"].read())[2:-1]
            print(imgname)
            op = filename +","+ imgname
            print(op)

        #img = s3_object["BODY"]
            # print(filename)
        #print(img.text)
            my_bucket.download_file(s3_object.key, filename)
    except Exception as e:
         print(e)

def get_file_output_from_s3(bucket,filename):
    try:
        s3_client = boto3.resource('s3')
        my_bucket = s3_client.Bucket(bucket)
        # print(my_bucket)
        for s3_object in my_bucket.objects.all():
            if(filename==s3_object.key):
                print(filename)
                return str(s3_object.get()["Body"].read())[2:-1]
    except Exception as e:
        print("#")
        print(e)
    return ""

def send_message(filename):
    # Create SQS client
    sqs = boto3.client('sqs', region_name = region)
    queue_url = 'https://sqs.us-east-1.amazonaws.com/321803667381/aws-capstone-input-queue'    
    # Send message to SQS queue
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=5,
        MessageAttributes={
            'filename': {
            'DataType': 'String',
            'StringValue': filename
            },
            'processed': {
            'DataType': 'String',
            'StringValue': "False"
            }
        },
        MessageBody=(filename),
        # MessageDeduplicationId=str(uuid.uuid4()),
        # MessageGroupId='aws-fifo-group'
    )

    print(response['MessageId'])