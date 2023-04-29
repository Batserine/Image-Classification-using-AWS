import logging
import boto3
import time
import subprocess

region = 'us-east-1'  

# user_data_script = """#!/bin/bash

# python3 /home/ubuntu/worker.py
# """

# Run the user data script
# subprocess.run(user_data_script, shell=True)

def get_request_queue_name(name="aws-capstone-input-queue"):
    sqs = boto3.resource('sqs', region_name = region)
    response = sqs.get_queue_by_name(QueueName='aws-capstone-input-queue')
    print("Request Queue URL: ", response.url)
    print("VisibilityTimeout of Request Queue: ", response.attributes.get('VisibilityTimeout'))
    print("ApproximateNumberOfMessages: ", response.attributes.get('ApproximateNumberOfMessages'))
    print("ApproximateNumberOfMessagesNotVisible: ", response.attributes.get('ApproximateNumberOfMessagesNotVisible'))
    return response

def create_instance(number_of_instances):
    ec2 = boto3.resource('ec2')
    instances = ec2.create_instances(
        ImageId='ami-xxx',  #write static image id here for debugging
        MinCount=1,
        MaxCount=number_of_instances,
        InstanceType='t2.small',
        KeyName='aws-capstone'
    )
    start_times = {}
    for instance in instances:
        instance.wait_until_running()
        start_times[instance.id] = time.time()
        print(f"Instance {instance.id} has started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_times[instance.id]))}")
    return instances, start_times

def get_started_instance_count():
    instances = boto3.resource('ec2').instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['pending', 'running']}])
    i = 1
    print("Instances in pending or running status: ")
    for instance in instances:
        print("Instance ", i, ": ", instance.id, instance.instance_type)
        i += 1
    return i-1

def restart_instance(ami_id, delay_secs=0):
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [ami_id]}, {'Name': 'instance-state-name', 'Values': ['running']}])
    num_instances_restarted = 0
    for instance in instances:
        if num_instances_restarted > 0:
            break
        response = get_request_queue_name()
        num_messages = int(response.attributes.get('ApproximateNumberOfMessages'))
        if num_messages == 0:
            print(f"Stopping instance {instance.id}...")
            instance.stop()
            instance.wait_until_stopped()
            stop_time = time.time()
            print(f"Instance {instance.id} has stopped at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stop_time))}")
            time.sleep(delay_secs)
            print(f"Starting instance {instance.id}...")
            instance.start()
            instance.wait_until_running()
            start_time = time.time()
            print(f"Instance {instance.id} has started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
            boot_time = start_time - stop_time
            print(f"Instance {instance.id} has a boot time of {boot_time:.2f} seconds")
            num_instances_restarted += 1
    print(f"Restarted {num_instances_restarted} instances.")

def controller():
    print("Controller Started")
    response = get_request_queue_name()
    num_messages = int(response.attributes.get('ApproximateNumberOfMessages'))
    print(num_messages)
    instance_to_start = num_messages
    if instance_to_start > 15:
        instance_to_start = 15
        running_instances = get_started_instance_count() - 2
    else:
        running_instances = get_started_instance_count() - 1
    if running_instances > 0 :
        instance_to_start = instance_to_start - running_instances
    if instance_to_start>0:
        create_instance(instance_to_start)
        print("Instances have Started")
        print("Number of Instances started : ", instance_to_start)
    print("Controller Ended")
    time.sleep(10)

if __name__=="__main__":
    while True:
        restart_instance('ami-xxx', delay_secs=30)  #write static image id here for debugging
        controller()