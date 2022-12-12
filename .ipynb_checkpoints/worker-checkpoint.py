import boto3
import sys
sqs = boto3.resource("sqs")

def process_message(message_body):
    print(f"processing message: {message_body}")
    # do what you want with the message here
    pass

if __name__ == "__main__":
    sqs_queue = sqs.get_queue_by_name(QueueName=sys.argv[1])

    while True:
        messages = sqs_queue.receive_messages()
        for message in messages:
            process_message(message.body)
            message.delete()