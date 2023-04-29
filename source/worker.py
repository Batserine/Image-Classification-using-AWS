import json
import logging
import boto3
import uuid
import time
import botocore
import os
import os.path
from os import path
from botocore.exceptions import ClientError
import subprocess
from time import time

region = 'us-east-1'  


BUCKET_NAME='aws-input-cap'
OUTPUT_BUCKET = 'aws-output-cap'
RESULT = 'result.txt'

def number_of_messages_in_Queue(name="aws-capstone-input-queue"):
    sqs = boto3.resource('sqs', region_name = region)
    response = sqs.get_queue_by_name(QueueName='aws-capstone-input-queue')
    print("Request Queue URL: ", response.url)
    print("VisibilityTimeout of Request Queue: ", response.attributes.get('VisibilityTimeout'))
    print("ApproximateNumberOfMessages: ", response.attributes.get('ApproximateNumberOfMessages'))
    print("ApproximateNumberOfMessagesNotVisible: ", response.attributes.get('ApproximateNumberOfMessagesNotVisible'))
    return int(response.attributes.get('ApproximateNumberOfMessages'))

def receive_message():
    try:
        sqs = boto3.client('sqs')
        queue_url = 'https://sqs.us-east-1.amazonaws.com/321803667381/aws-capstone-input-queue'
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
            )
        print(response)
        print(response['ResponseMetadata']['HTTPStatusCode'])
        if 'Messages' not in response:
            print("Message not received")
            # stop_instances()
            # exit(0)
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        filename = message['MessageAttributes']['filename']['StringValue']
        message_body = message['Body']
        print('Received message: %s' %filename)
    except Exception as e:
        print("Error receiving message:", e)
        # return None, None
        # stop_instances()
        # exit(0)
    return filename, message, receipt_handle, message_body

def send_message(filename, value):
    # Create SQS client
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/321803667381/aws-capstone-output-queue'
    # Send message to SQS queue
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=5,
        MessageAttributes={
            'filename': {
            'DataType': 'String',
            'StringValue': filename
            },
            'value': {
            'DataType': 'String',
            'StringValue': value
            }
        },
        MessageBody=(filename),
        # MessageDeduplicationId=str(uuid.uuid4()),
        # MessageGroupId='aws-fifo-group',
        # ContentBasedDeduplication='true'
    )

    print(response['MessageId'])

def delete_input_data(message, receipt_handle):
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/321803667381/aws-capstone-input-queue'
    
    # receipt_handle = message['ReceiptHandle']
    try:
        sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
        )
        print(f"Message deleted: {message['MessageId']}")
    except botocore.exceptions.ClientError as e:
        print(f"Error deleting message: {e}")

def delete_all_objects_in_bucket(bucket_name):
    """
    Deletes all objects in the specified S3 bucket.
    """
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    bucket.objects.all().delete()

def download_message(key):
    s3 = boto3.resource('s3', region_name = region)
    try:
        s3.Bucket(BUCKET_NAME).download_file(key, key)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

def stop_instances():
    instance_id = subprocess.check_output(["ec2metadata", "--instance-id"], universal_newlines=True).strip()
    print(instance_id)
    current_instance_id = "" #write static instance id here for debugging
    print("current instance is:", current_instance_id)
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    instance_ids_to_stop = []
    for instance in instances:
        if instance.id != current_instance_id:
            instance_ids_to_stop.append(instance.id)
    if len(instance_ids_to_stop) > 0:
        client = boto3.client('ec2')
        response = client.stop_instances(InstanceIds=instance_ids_to_stop)
        print(response)
    else:
        print("No instances to stop")

def terminate_instances():
    # instance_id = subprocess.check_output(["ec2metadata", "--instance-id"], universal_newlines=True).strip()
    instance_id = ""  #write static instance id here for debugging
    print("Current instance ID is:", instance_id)
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    instance_ids_to_terminate = []
    for instance in instances:
        if instance.id != instance_id:
            instance_ids_to_terminate.append(instance.id)
    if len(instance_ids_to_terminate) > 0:
        client = boto3.client('ec2')
        response = client.terminate_instances(InstanceIds=instance_ids_to_terminate)
        print(response)
    else:
        print("No instances to terminate")

def stop_all():
    instance_id = subprocess.check_output(["ec2metadata", "--instance-id"], universal_newlines=True).strip()
    ec2 = boto3.resource('ec2')
    response = ec2.stop_instances(InstanceIds=[instance_id])
    print(response)


def upload_file(file_name, file_content, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    bucket = OUTPUT_BUCKET
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.put_object(Bucket=bucket, Key=object_name, Body=file_content)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def worker():
    messages = number_of_messages_in_Queue()
    print(messages)
    if messages==0:
        print("Queue is Empty")
        delete_all_objects_in_bucket(BUCKET_NAME)
        # delete_all_objects_in_bucket(OUTPUT_BUCKET)
        exit(1)
    filename, message, receipt_handle, message_body = receive_message()
    download_message(filename)
    delete_input_data(message, receipt_handle)
    s = subprocess.getstatusoutput("python3 /home/ubuntu/classifier/image_classification.py "+filename)
    output_lines = s[1].split('\n')
    last_line = output_lines[-1]
    print(last_line)
    file1 = open(RESULT,"w")
    file1.write(last_line)
    file1.close()
    # os.system("python3 /home/ubuntu/classifier/image_classification.py "+filename+" > "+ RESULT)
    while(not path.exists(RESULT)):
        print("Path does not exist")
        continue
    upload_file(RESULT, filename)
    send_message(filename, last_line)
    os.remove(RESULT)

if __name__=="__main__":
    while True:
        print("Worker is running")
        worker()
