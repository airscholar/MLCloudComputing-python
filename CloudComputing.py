import os
import boto3
import subprocess
import numpy as np
import time
import datetime
import paramiko
import io
from scp import SCPClient, SCPException
import sys
from ast import literal_eval
from files.file_helper import fetch_local_files

np.set_printoptions(threshold=sys.maxsize)


class CloudComputingApp:
    def __init__(self, instance_size):
        self.INSTANCE_SIZE = instance_size
        self.sqs = boto3.resource('sqs', region_name='us-east-1')
        self.ec2 = boto3.client('ec2', region_name='us-east-1')
        self.sqs_client = boto3.client('sqs')

    def get_default_security_group(self, client, key_name):
        """
        Get default security group
        :param client: ec2 client
        :param key_name: key name to get value from
        :return: list of security group ids
        """
        # extract key_name attribute from the security groups returned
        response = [group[key_name] for group in client.describe_security_groups()['SecurityGroups'] if
                    group['GroupName'] == 'default']

        return response

    def get_key_pairs(self, client, key_name, removeExisting=False):
        """
        Get key pairs. If removeExisting is True, delete existing key pairs and create a new one
        :param client: ec2 client
        :param removeExisting: remove existing key pairs or not
        :return: key pair name
        """
        if removeExisting:
            client.delete_key_pair(KeyName=key_name)

        # get all key pairs
        keypairs = client.describe_key_pairs()['KeyPairs']

        # if key pair exists, return the key pair name
        keypair = list(filter(lambda x: x['KeyName'] == key_name, keypairs))

        if not keypair:
            # create a new key pair
            keypair = client.create_key_pair(KeyName=key_name)
            f = io.StringIO(keypair['KeyMaterial'])
            data = f.read()
            # write the key pair to a file
            file = open('labsuser.pem', 'w')
            file.write(data)
            file.close()
        else:
            keypair = keypair[0]

        return keypair

    def launch_new_instance(self, client, keypair, count=1):
        """
        Launch new instance(s)
        :param client: ec2 client
        :param keypair: key pair name
        :param count: number of instances to launch
        :return: list of instance ids
        """
        response = client.run_instances(
            ImageId='ami-05723c3b9cf4bf4ff',
            InstanceType='t2.micro',
            KeyName=keypair,
            MaxCount=count,
            MinCount=count,
            Monitoring={
                'Enabled': True
            },
            SecurityGroupIds=self.get_default_security_group(client, key_name='GroupId')
        )
        ec2_inst_ids = [res["InstanceId"] for res in response if res]
        # wait for all the instances to be running
        waiter = client.get_waiter('instance_running')
        # extract instance ids of the instances launched
        waiter.wait(InstanceIds=[ec2_inst_ids])
        return ec2_inst_ids

    def prepare_instances(self, client, keypair, count):
        """
        Prepare instances by launching new instances. If there are existing instances and the new count is greater than the
        existing count, launch new additional instances. If the new count is less than the existing count, return the count requested

        :param client: ec2 client
        :param keypair: key pair name
        :param count: number of instances to launch
        :return: tuple of (ec2 object,  instance ids)
        """
        ec2 = boto3.resource('ec2')
        ec2_inst_ids = []

        deployed_count = 0
        # get all instances
        for instance in ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'pending']}]):
            # if instance is running, add the instance id to the list else start all the instances
            deployed_count += 1
            client.start_instances(InstanceIds=[instance.id])
            ec2_inst_ids.append(instance.id)

        # if the new count is greater than the existing count, launch new instances
        if deployed_count < count:
            ec2_inst_ids.append(self.launch_new_instance(client, keypair, (count - deployed_count)))

        # if there are no instances, launch new instances
        if not ec2_inst_ids:
            ec2_inst_ids.append(self.launch_new_instance(client, keypair, count))

        return ec2, ec2_inst_ids

    def configure_ssh(self):
        """
        Configure ssh connection.
        :return: ssh object
        """

        sshs = []
        for count in range(self.INSTANCE_SIZE):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            sshs.append(ssh)
        return sshs

    def ssh_connect_with_retry(self, ssh, ip_address, retries):
        """
        Connect to ssh with retries
        :param ssh: ssh object
        :param ip_address: ip address of the instance
        :param retries: number of retries to attempt connection
        :return: Boolean. True if connection is successful, False otherwise
        """
        if retries > 3:
            return False
        # read the private key
        f = open('labsuser.pem', 'r')
        private_key = paramiko.RSAKey.from_private_key(f)

        interval = 5
        try:
            retries += 1
            print('SSH into the instance: {}'.format(ip_address))
            ssh.connect(hostname=ip_address,
                        username='ec2-user', pkey=private_key)
            return True
        except Exception as e:
            print(e)
            time.sleep(interval)
            print('Retrying SSH connection to {}'.format(ip_address))
            self.ssh_connect_with_retry(ssh, ip_address, retries)

    def ssh_disconnect(self, ssh):
        """
        Close ssh connection.
        :param ssh: ssh object to close
        """
        if ssh:
            ssh.close()

    def get_public_address(self, ec2, instance_id):
        """
        Get public address of the instance
        :param ec2: ec2 object
        :param instance_id: instance id
        :return: public IP address of the instance
        """
        instance = ec2.Instance(id=instance_id)
        instance.wait_until_running()
        current_instance = list(ec2.instances.filter(InstanceIds=[instance_id]))
        ip_address = current_instance[0].public_ip_address

        return ip_address

    def get_queue(self, sqs):
        """
        Get queue. If queue does not exist, create two queues, one for the computation and one for the result
        :param sqs: sqs client
        """

        attributes = {
            'DelaySeconds': '0',
            'MessageRetentionPeriod': '86400',
            "ReceiveMessageWaitTimeSeconds": "0"
        }
        queue_name = 'queue'

        for idx in range(self.INSTANCE_SIZE):
            # create a computation queue for each instance
            sqs.create_queue(
                QueueName=f"{queue_name}{idx}",
                Attributes=attributes
            )

            # create a result queue for each instance
            sqs.create_queue(
                QueueName=f'result-{queue_name}-{idx}',
                Attributes=attributes
            )

    def send_message_to_queue(self, sqs, queue_name, message):
        """
        Send message to queue
        :param sqs: sqs client
        :param queue_name: queue name
        :param message: message to send
        :return: message id
        """
        # get the queue
        queue = sqs.get_queue_by_name(QueueName=queue_name)
        # Send message to SQS queue
        response = queue.send_messages(
            Entries=message
        )
        return response

    def install_required_packages(self, ssh):
        """
        Install required packages on the instance
        :param ssh: ssh client with connection to the instance
        :return: tuple of (stdout {result of successful completion}, stderr {error message})
        """
        stdin, stdout, stderr = ssh.exec_command("sudo yum install pip -y && sudo pip install numpy boto3")
        return stdout, stderr

    def start_worker(self, ssh, instance_id):
        """
        Start worker on the instance
        :param ssh: ssh client with connection to the instance
        :param instance_id: instance id
        :return: tuple of (stdout {result of successful completion}, stderr {error message})
        """
        stdin, stdout, stderr = ssh.exec_command(f"nohup python3 worker.py {instance_id} > worker.log 2>&1 &")
        print("Worker started")
        return stdout, stderr

    def initialise_instances(self, client):
        """
        Initialise instances by installing required packages
        :param client: ec2 client
        """
        print('Preparing SSH connection')
        sshs = self.configure_ssh()
        print('Getting keypairs')
        keypair = self.get_key_pairs(client, 'airscholar-key', False)
        print('Preparing instances')
        ec2, instances = self.prepare_instances(client, keypair['KeyName'], self.INSTANCE_SIZE)
        print('Getting public addresses')
        ip_addresses = [self.get_public_address(ec2, instance) for instance in instances]
        print(list(ip_addresses))
        # connect to each instance and install required packages
        for idx in range(0, len(sshs)):
            ssh = sshs[idx]
            ip_address = ip_addresses[idx]
            # connect to ssh
            print(f"Conencting to Instance-{idx} with IP Address {ip_address}")
            self.ssh_connect_with_retry(ssh, ip_address, 0)
            # install required python packages
            print(f"Installing required packages for Instance-{idx} with IP Address {ip_address}")
            stdout, stderr = self.install_required_packages(ssh)
            print(stdout.read().decode('utf-8'))
            print(stderr.read().decode('utf-8'))

            # configure aws access to the instance
            print(f"Configuring Instance -{idx} with IP Address {ip_address} for remote access")
            self.configure_aws_access_for_ssh(ssh, ip_address)

            # upload worker file to the instance
            scp = SCPClient(ssh.get_transport())
            self.bulk_upload(scp, fetch_local_files('./worker'), '~', ip_address)

            # start worker on the instance
            print(f"Starting worker {idx}")
            self.start_worker(ssh, idx)
            # stdin, stdout, stderr = ssh.exec_command(f'python ./worker.py {idx}', get_pty=True)
            # only for debugging purposes. This prints the output of the worker non-stop.
            # if idx == 3:
            #     for line in iter(stdout.readline, ""):
            #         print(line, end="")
            # print(stdout.read().decode('utf-8'))
            # print(stderr.read().decode('utf-8'))

    def get_messages_from_queue(self, queue, message_size=10):
        """
        Get messages from queue
        :param instance_size: number of instances
        :param queue: queue name
        :param message_size: number of messages to get
        :return: list of messages
        """
        messages = []
        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=queue)

        # get messages from the queue
        for message in queue.receive_messages(MaxNumberOfMessages=message_size, MessageAttributeNames=['All'],
                                              WaitTimeSeconds=0):
            messages.append(eval(message.body))
            message.delete()
        return messages

    def split_row(self, array, nrows, ncols):
        """
        Split array into sub-arrays
        :param array: array to split
        :param nrows: number of rows
        :param ncols: number of columns
        """
        height, width = array.shape
        assert height % nrows == 0, f"{height} rows is not evenly divisible by {nrows}"
        assert width % ncols == 0, f"{width} cols is not evenly divisible by {ncols}"
        return (array.reshape(height // nrows, nrows, -1, ncols)
                .swapaxes(1, 2)
                .reshape(-1, nrows, ncols))

    def split_col(self, array, split_size):
        """
        Split a matrix into sub-matrices.
        :param array: array to split
        :param split_size: size of the sub-matrices
        :return: list of sub-matrices
        """

        r, h = array.shape
        return [np.vsplit(i, split_size) for i in np.hsplit(array, r)]

    def generate_array(self, nrows, ncols, max_value=10):
        """
        Generate a random array of size nrows x ncols with values between 0 and max_value
        :return:
        :param nrows: number of rows
        :param ncols: number of columns
        :param max_value: max value of the array element
        :return: generated array
        """
        arr = np.random.randint(max_value, size=(nrows, ncols))

        return arr

    def bulk_upload(self, scp, filepaths: list[str], remote_path, host):
        """
        Upload multiple files to a remote directory.
        :param List[str] filepaths: List of local files to be uploaded.
        """
        try:
            scp.put(filepaths, remote_path=remote_path, recursive=True)
            print(f"Finished uploading {len(filepaths)} files to {remote_path} on {host}")
        except SCPException as e:
            print(f"SCPException during bulk upload: {e}")
        except Exception as e:
            print(f"Unexpected exception during bulk upload: {e}")

    def configure_aws_access_for_ssh(self, ssh, ip_address):
        """
        This function extracts the AWS configuration you have locally and push to the server
        :param ssh:ssh object
        :return:
        """
        output = subprocess.getoutput("cat ~/.aws/credentials")
        ssh.exec_command(f'mkdir ~/.aws && touch ~/.aws/credentials')
        ssh.exec_command(f"echo '{output}' > ~/.aws/credentials")
        print(f'SSH AWS configuration done for {ip_address}')

    def matrix_dot_product(self, matrix_a, matrix_b):
        """
        This function calculates the dot product of two matrices
        :param matrix_a: matrix a
        :param matrix_b: matrix b
        :return: dot product of matrix a and matrix b
        """
        start_time = datetime.datetime.now()
        result = []
        for i in range(len(matrix_a)):
            row = []
            for j in range(len(matrix_b[0])):
                sum = 0
                for k in range(len(matrix_b)):
                    sum += matrix_a[i][k] * matrix_b[k][j]
                row.append(sum)
            result.append(row)
        print('Computation time', datetime.datetime.now() - start_time)

        return result

    def matrix_add(self, matrix_1, matrix_2):
        """
        This function adds two matrices
        :param matrix_1: matrix 1
        :param matrix_2: matrix 2
        :return: sum of matrix 1 and matrix 2
        """
        start_time = datetime.datetime.now()
        result = []
        for idx_row in range(0, len(matrix_1)):
            row = matrix_1[idx_row]
            row1 = matrix_2[idx_row]
            cols = []
            for idx_col in range(0, len(row)):
                cols.append(row[idx_col] + row1[idx_col])
            result.append(cols)
        print('Computation time', datetime.datetime.now() - start_time)
        return result

    def delete_queues(self):
        """
        Delete all queues in the SQS
        """
        # get all the queues
        client = self.sqs_client
        response = client.list_queues(
            MaxResults=123)

        # delete all the queues
        for queue in response['QueueUrls']:
            client.delete_queue(QueueUrl=queue)
            print(f'{queue} deleted!')

    def reformat_data(self, data):
        """
        This function reformats the data to be sent to the server
        :param data: data to be reformatted
        :return: reformatted data
        """
        return str(data).replace('\n', '')

    def compute_matrix_operation(self, operation, split_array1, split_array2):
        """
        This function computes the matrix operation
        :param operation: operation to be performed
        :param split_array1: split array 1
        :param split_array2: split array 2
        :return: result of the operation
        """
        if operation == 'addition':
            for queue_id, dt in enumerate(np.array_split(np.arange(0, len(split_array1)), self.INSTANCE_SIZE)):
                print(f'Processing Queue {queue_id} with {len(dt)} tasks')
                # send the data to the server
                [self.send_message_to_queue(self.sqs, f'queue{queue_id}',
                                            [{"Id": f"{idx + 1}", "MessageBody": str((operation, (idx, (
                                                self.reformat_data(split_array1[idx]),
                                                self.reformat_data(split_array2[idx])))))}])
                 for idx in range(min(dt), max(dt) + 1) if len(dt) > 0]
        elif operation == 'multiplication':
            for queue_id, dt in enumerate(np.array_split(np.arange(0, len(split_array1)), self.INSTANCE_SIZE)):
                [print(f'queue{queue_id}', split_array1[idx], split_array2[idx]) for idx in range(min(dt), max(dt) + 1)
                 if
                 len(dt) > 0]

    def merge_queue_result(self, split_array, array_size, chunk_size):
        """
        This function merges the results from the queue
        :param split_array: split array
        :param array_size: array size
        :param chunk_size: chunk size
        :return: merged array
        """
        temp_res = []

        for a, b in enumerate(np.array_split(np.arange(0, len(split_array)), self.INSTANCE_SIZE)):
            compute_res = []
            print(f"Received {len(b)} results from queue{a}")
            # get the result from the queue
            for i in range(len(b)):
                res = self.get_messages_from_queue(f'result-queue-{a}', 1)
                [compute_res.append(msg) for msg in res]
            # sort the result by the index
            compute_res.sort()
            # append the result to the temp_res
            [temp_res.append(literal_eval(res)) for (index, res) in compute_res]

        final_res = []
        temp = []
        for idx, data in enumerate(temp_res):
            temp.append(data)
            # if the index is equal to the chunk size, append the temp to the final_res
            if idx % int(array_size / chunk_size) == int(array_size / chunk_size) - 1:
                final_res.append(np.hstack([tuple(t) for t in temp]))
                temp = []
        return np.concatenate(final_res)

    def terminate_instances(self):
        """
        This function terminates all the instances
        """
        ec2 = boto3.resource('ec2')
        for instance in ec2.instances.all():
            # terminate all instances
            print(f'Terminating {instance.id}')
            instance.terminate()

    def purge_queue(self):
        """
        This function purges all the queues
        """
        client = self.sqs_client
        response = client.list_queues(
            MaxResults=123)

        for queue in response['QueueUrls']:
            print(f'Purging {queue}')
            client.purge_queue(QueueUrl=queue)

    def get_wait_time_based_on_matrix_size(self, size):
        """
        This function returns the wait time based on the matrix size
        :param size: matrix size
        :return: wait time
        """
        if size <= 1000:
            return 5
        elif size <= 10000:
            return 30
        elif size <= 100000:
            return 60
        elif size <= 1000000:
            return 120

    def split_and_compute_dot_product(matrix_a, matrix_b, chunk_size):
        """
        Splits two huge matrices into smaller chunks and computes the dot product for each pair of chunks without using any libraries.

        Parameters:
        - matrix_a (list): The first matrix to split and compute the dot product for.
        - matrix_b (list): The second matrix to split and compute the dot product for.
        - chunk_size (int): The size of each chunk.

        Returns:
        - dot_products (list): A list of dot products for each pair of chunks.
        """
        # Split the matrices into chunks
        chunks_a = [matrix_a[i:i + chunk_size] for i in range(0, len(matrix_a), chunk_size)]
        chunks_b = [matrix_b[i:i + chunk_size] for i in range(0, len(matrix_b), chunk_size)]

        # Initialize a list to store the dot products
        dot_products = []

        # Iterate over the chunks and compute the dot product for each pair of chunks
        for chunk_a, chunk_b in zip(chunks_a, chunks_b):
            print(chunk_a, chunk_b)
            dot_product = [[0 for j in range(len(chunk_a))] for i in range(len(chunk_b[0]))]
            print(dot_product)
            for i in range(len(chunk_b)):
                for j in range(len(chunk_a[0])):
                    for k in range(len(chunk_b[0])):
                        dot_product[i][j] += chunk_b[i][k] * chunk_a[k][j]

            dot_products.append(dot_product)

        return dot_products
    def write_result_to_file(self, result, filename):
        with open(filename, 'w') as f:
            for item in result.tolist():
                f.write("%s " % item)

    def prepare_architecture(self):
        self.get_queue(self.sqs_client)
        self.initialise_instances(self.ec2)
        print("INFRASTRUCTURE DONE!")

    def teardown_infrastructure(self):
        try:
            self.terminate_instances()
            self.delete_queues()
            print("TEARDOWN DONE!")
            return True
        except Exception as e:
            return False

# cc = CloudComputingApp(8)
# cc.initialise_instances(cc.ec2)