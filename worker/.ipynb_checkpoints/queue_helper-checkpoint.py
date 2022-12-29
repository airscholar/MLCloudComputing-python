import boto3

sqs = boto3.resource('sqs', region_name='us-east-1')

def send_message_to_queue(sqs, queue_name, message):
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    # Send message to SQS queue
    response = queue.send_messages(
        Entries=message
    )
    return response