import boto3
import io


class AWSSetup:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name):
        self.boto3_client = None
        self.ec2_client = None
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name

    def setup(self):
        """
        Setup AWS credentials
        :return:
        """
        session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

        return session

    def create_boto3_client(self):
        """
        Create a boto3 client
        :return: boto3 client
        """
        client = self.setup().client('ec2')
        self.boto3_client = client
        return client

    def create_queue(self, queue_name):
        """
        Create a new SQS queue
        :param queue_name: string name of the queue
        :return: the created queue
        """
        sqs = self.setup().resource('sqs')
        queue = sqs.create_queue(QueueName=queue_name)
        return queue

    def get_key_pairs(self, client, key_name, removeExisting=False):
        if removeExisting:
            client.delete_key_pair(KeyName=key_name)

        keypairs = client.describe_key_pairs()['KeyPairs']
        keypair = list(filter(lambda x: x['KeyName'] == key_name, keypairs))

        if not keypair:
            keypair = client.create_key_pair(KeyName=key_name)
            f = io.StringIO(keypair['KeyMaterial'])
            data = f.read()
            file = open('labsuser.pem', 'w')
            file.write(data)
            file.close()
        else:
            keypair = keypair[0]

        return keypair

    def create_new_instance(self, image_id, instance_type, key_name, security_group, instance_count=1):
        # ec2 = self.setup().resource('ec2')
        client = self.create_boto3_client()

        response = client.run_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroups=[security_group],
            MinCount=instance_count,
            MaxCount=instance_count
        )

        ec2_inst_ids = [res["InstanceId"] for res in response]
        waiter = client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[ec2_inst_ids])

        return ec2_inst_ids

    def get_security_group(self, client, key_name, group_name='default'):
        """
        Get security group by name
        :param key_name:
        :param group_name:
        :return: the default security group
        """
        # extract key_name attribute from the security groups returned
        response = [group[key_name] for group in client.describe_security_groups()['SecurityGroups'] if
                    group['GroupName'] == group_name]

        return response

    def create_security_group(self, group_name, description):
        """
        Create a new security group
        :param group_name: name of the security group
        :param description: description of the security group
        :return: the created security group
        """
        ec2 = self.setup().resource('ec2')
        security_group = ec2.create_security_group(GroupName=group_name, Description=description)
        return security_group


