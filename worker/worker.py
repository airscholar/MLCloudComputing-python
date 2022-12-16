import boto3
import sys
import numpy as np
from ast import literal_eval
import helper
import queue_helper as qh

sqs = boto3.resource("sqs", region_name='us-east-1')
QUEUE_NAME = 'airscholar-queue'
RESULT_QUEUE_NAME = 'queue0'

if __name__ == "__main__":
    # sqs_queue = sqs.get_queue_by_name(QueueName=sys.argv[1])
    QUEUE_NAME = f"queue{sys.argv[1]}"
    RESULT_QUEUE_NAME = f"result-queue-{sys.argv[1]}"

    print(f"Worker {sys.argv[1]} started")
    sqs_queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)
    print("Queue url:", sqs_queue.url)

    while True:
        messages = sqs_queue.receive_messages()

        for message in messages:
            # print(message.body)
            operation, data = literal_eval(message.body)
            index, matrices = data
            matrix_a, matrix_b = matrices

            matrix_a = matrix_a.replace('  ', ',').replace('[ ', '[').replace(' ', ',')
            matrix_b = matrix_b.replace('  ', ',').replace('[ ', '[').replace(' ', ',')

            matrix_a = np.array(literal_eval(matrix_a))
            matrix_b = np.array(literal_eval(matrix_b))

            if operation == 'addition':
                result = helper.matrix_add(matrix_a, matrix_b)
            elif operation == 'multiply':
                result = helper.matrix_dot_product(matrix_a, matrix_b)
            else:
                raise Exception("Unknown operation")

            print("Matrix 1: =>", matrix_a, "Matrix 2:", matrix_b, f"Result: {index} =>", result)
            print(f'Message {(index+1)} processed!')
            response = [{"Id": f"{index+1}", "MessageBody": str((index, helper.reformat_data(result)))}]
            qh.send_message_to_queue(sqs, RESULT_QUEUE_NAME, response)

            print(f"Message {(index+1)} sent to result queue")
            message.delete()

#result
    # while True:
    #     messages = sqs_queue.receive_messages()
    #
    #     for message in messages:
    #         # print(message.body)
    #         print(message.body)