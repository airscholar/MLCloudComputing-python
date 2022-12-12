import boto3
import sys
import numpy as np
from ast import literal_eval

sqs = boto3.resource("sqs")
import matrix_addition


def process_message(matrix_arr):
    a = matrix_arr[0]
    b = matrix_arr[1]

    result = matrix_addition.compute_addition(a, b)

    print("Addition result:", result)
    # do what you want with the message here
    pass


if __name__ == "__main__":
    # sqs_queue = sqs.get_queue_by_name(QueueName=sys.argv[1])
    sqs_queue = sqs.get_queue_by_name(QueueName='airscholar-queue')

    while True:
        messages = sqs_queue.receive_messages()
        matrix = []
        for message in messages:
            matrix.append(literal_eval(message.body))
            print(matrix)
            message.delete()
        if len(matrix) == 2:
            process_message(matrix)
