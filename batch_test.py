import boto3
import time
import webbrowser
import uuid
import argparse

client = boto3.client('batch')
cloudwatch = boto3.client('logs')

parser = argparse.ArgumentParser()
parser.add_argument("-r", type=str, default="examples/recipes/v2/one_sphere.json", help="recipe")
parser.add_argument("-c", type=str, default="examples/packing-configs/run.json", help="config")
args = parser.parse_args()

# Submit Job to AWS batch using config and recipe from commandline
response = client.submit_job(
    jobName=str(uuid.uuid4()),
    jobQueue='arn:aws:batch:us-west-2:771753870375:job-queue/alli-ruge-job-queue',
    jobDefinition='cellpack-test-job-definition',
    parameters={},
    containerOverrides={
        'command': [
            'echo',
            'hello world',
        ],
        'environment': [
            {
                'name': 'config',
                'value': args.c
            },
            {
                'name': 'recipe',
                'value': args.r
            },
        ],
        'resourceRequirements': []
    },
)

if response and response.get('jobId'):
    jobId = response.get('jobId')
    jobStatus = "N/A"
    while jobStatus not in ["SUCCEEDED", "FAILED"]:
        # While the job is processing, check job status every 2 seconds and
        # print the status when it changes
        time.sleep(2)
        descriptionResponse = client.describe_jobs(
            jobs=[
                jobId,
            ]
        )
        if descriptionResponse and descriptionResponse.get('jobs') and len(descriptionResponse.get('jobs')) > 0:
            newStatus = descriptionResponse.get('jobs')[0].get("status")
            if newStatus != jobStatus:
                print(newStatus)
                jobStatus = newStatus
                logStreamName = descriptionResponse.get('jobs')[0].get("container", {}).get("logStreamName")
        else:
            print("something went wrong, leaving!")
            continue
    
    # Using logStreamName provided while checking status, get all of the logs from the job run
    cloudwatchResponse = cloudwatch.get_log_events(
        logStreamName=logStreamName,
        logGroupIdentifier="/aws/batch/job"
    )

    print(f"\nLogs from AWS Batch Run:")
    for event in cloudwatchResponse.get("events", {}):
        message = event.get("message")
        if message.startswith("View in Simularium:"):
            # We found the log with the simularium url!
            url = message[20:]
            webbrowser.open_new_tab(url)
        else:
            print(message)
else:
    print("Error: response didn't have jobId")

