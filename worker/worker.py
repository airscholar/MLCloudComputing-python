import boto3
import sys
import numpy as np
from ast import literal_eval
import helper
import queue_helper as qh

sqs = boto3.resource("sqs")
QUEUE_NAME = 'airscholar-queue'
RESULT_QUEUE_NAME = 'result-queue'
def process_message(matrix_a, matrix_b):
    print(matrix_a)
    print(matrix_b)

    print(matrix_a[0][0])
    print(matrix_b[0][0])
    result = np.add(matrix_a, matrix_b)

    print("Addition result:", result)
    # do what you want with the message here
    pass


if __name__ == "__main__":
    # sqs_queue = sqs.get_queue_by_name(QueueName=sys.argv[1])
    sqs_queue = sqs.get_queue_by_name(QueueName='queue4')

    # while True:
    #     messages = sqs_queue.receive_messages()
    #
    #     for message in messages:
    #         # print(message.body)
    #         a, b = literal_eval(message.body)
    #         a = literal_eval(a)
    #         b = literal_eval(b)
    #
    #         result = helper.add(a, b)
    #         # result = helper.reformat_data(result)
    #         # result = result.split(' ')
    #         # result = ''.join(result)
    #         result = np.array(result).tolist()
    #
    #         # [{"Id": f"{idx}", "MessageBody": str((reformat_data(s_arr[idx]), reformat_data(s_arr1[idx])))} for idx in
    #         #  range(5, 10)]
    #         response = list([{"Id": "2", "MessageBody": str(result)}])
    #         qh.send_message_to_queue(sqs, RESULT_QUEUE_NAME, response)
    #         print('message processed!')
    #         message.delete()

        # if len(matrix) == 2:
        #     process_message(matrix)
#result
    # while True:
    #     messages = sqs_queue.receive_messages()
    #
    #     for message in messages:
    #         # print(message.body)
    #         print(message.body)