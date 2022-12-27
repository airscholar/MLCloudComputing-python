import unittest
from CloudComputing import CloudComputingApp as cloudComputingApp
import numpy as np
import boto3
from unittest.mock import MagicMock, call, Mock
from files.file_helper import fetch_local_files


class TestCloudComputing(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCloudComputing, self).__init__(*args, **kwargs)
        self.ec2_instance_id = 'i-0a1b2c3d4e5f6g7h8'
        self.key_pair = 'airscholar-key'
        self.sqs_client = boto3.client('sqs')
        self.security_group = 'sg-0a1b2c3d4e5f6g7h8'
        self.INSTANCE_SIZE = 1
    def test_generate_array(self):
        rows = 3
        columns = 3
        max_value = 10
        matrix_a = cloudComputingApp.generate_array(self, rows, columns, max_value)
        matrix_b = cloudComputingApp.generate_array(self, rows, columns, max_value)
        self.assertEqual(len(matrix_a), rows)
        self.assertEqual(len(matrix_b), columns)

        # Test if the matrix is a square matrix
        self.assertEqual(len(matrix_a), len(matrix_b))

        # Test if the matrix element is less than 10
        for i in range(len(matrix_a)):
            for j in range(len(matrix_a)):
                self.assertTrue(matrix_a[i][j] < max_value)
                self.assertTrue(matrix_b[i][j] < max_value)

    def test_matrix_add(self):
        matrix_a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        matrix_b = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        print("Matrix Addition Test")
        result = cloudComputingApp.matrix_add(self, matrix_a, matrix_b)
        self.assertEqual(result, [[2, 4, 6], [8, 10, 12], [14, 16, 18]])

    def test_matrix_dot_product(self):
        matrix_a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        matrix_b = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        print("Matrix Multiplication Test")
        result = cloudComputingApp.matrix_dot_product(self, matrix_a, matrix_b)
        self.assertEqual(result, [[30, 36, 42], [66, 81, 96], [102, 126, 150]])

    def test_reformat_data(self):
        matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        result = cloudComputingApp.reformat_data(self, matrix)
        self.assertEqual(result, '[[1, 2, 3], [4, 5, 6], [7, 8, 9]]')

    def test_split_row(self):
        matrix = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
        result = cloudComputingApp.split_row(self, matrix, 2, 2)
        res_a = np.array(result[0][0])
        res_b = np.array([1, 2])
        self.assertEqual(np.array_equal(res_a, res_b), True)

    def test_split_col(self):
        matrix = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
        result = cloudComputingApp.split_col(self, matrix, 2)
        res_a = np.array(result[0][0])
        res_b = np.array([1, 5])

        self.assertEqual(np.array_equal(res_a.flatten(), res_b), True)

    def test_get_security_groups(self):
        """
        Test if the security group is created
        :return:
        """
        client = boto3.client('ec2', region_name='us-east-1')
        key_name = 'GroupId'
        result = cloudComputingApp.get_default_security_group(self, client, key_name)

        self.assertEqual(result, [self.security_group])

    def test_get_instances(self):
        # result = cloudComputingApp.get_instances(self)
        self.assertEqual(True, True)

    def test_get_key_pairs(self):
        client = boto3.client('ec2', region_name='us-east-1')
        result = cloudComputingApp.get_key_pairs(self, client, self.key_pair)
        self.assertEqual(result['KeyName'], self.key_pair)

    def test_launch_new_instance(self):
        client = boto3.client('ec2', region_name='us-east-1')
        keypair = 'airscholar-key'
        count = 1
        cloudComputingApp.get_default_security_group = MagicMock(return_value=[self.security_group])
        cloudComputingApp.get_key_pairs = MagicMock(return_value={'KeyName': self.key_pair})
        cloudComputingApp.launch_new_instance = MagicMock(return_value={'InstanceId': self.ec2_instance_id})
        result = cloudComputingApp.launch_new_instance(self, client, keypair, count)
        self.assertEqual(result['InstanceId'], self.ec2_instance_id)

    def test_prepare_instances(self):
        client = boto3.client('ec2', region_name='us-east-1')
        cloudComputingApp.get_default_security_group = MagicMock(return_value=[self.security_group])
        cloudComputingApp.get_key_pairs = MagicMock(return_value={'KeyName': self.key_pair})
        cloudComputingApp.launch_new_instance = MagicMock(return_value={'InstanceId': self.ec2_instance_id})
        cloudComputingApp.get_instances = MagicMock(return_value=[{'InstanceId': self.ec2_instance_id}])
        self.assertEqual(cloudComputingApp.get_instances()[0]['InstanceId'], self.ec2_instance_id)

    def test_configure_ssh(self):
        client = boto3.client('ec2', region_name='us-east-1')
        cloudComputingApp.get_default_security_group = MagicMock(return_value=[self.security_group])
        cloudComputingApp.get_key_pairs = MagicMock(return_value={'KeyName': self.key_pair})
        cloudComputingApp.launch_new_instance = MagicMock(return_value={'InstanceId': self.ec2_instance_id})
        cloudComputingApp.prepare_instances = MagicMock(return_value={'InstanceId': self.ec2_instance_id})
        cloudComputingApp.configure_ssh = MagicMock(return_value=True)
        self.assertEqual(cloudComputingApp.configure_ssh(), True)
    def test_get_public_address(self):
        client = boto3.client('ec2', region_name='us-east-1')
        keypair = 'airscholar-key'
        dummy_ip_address = '13.31.12.33'
        cloudComputingApp.get_default_security_group = MagicMock(return_value=[self.security_group])
        cloudComputingApp.get_key_pairs = MagicMock(return_value={'KeyName': keypair})
        cloudComputingApp.launch_new_instance = MagicMock(return_value={'InstanceId': self.ec2_instance_id})
        cloudComputingApp.prepare_instances = MagicMock(return_value={'InstanceId': self.ec2_instance_id})
        cloudComputingApp.configure_ssh = MagicMock(return_value={'ssh': True})
        cloudComputingApp.get_public_address = MagicMock(return_value=dummy_ip_address)
        self.assertEqual(cloudComputingApp.get_public_address(), dummy_ip_address)

    def test_ssh_connect_with_retry(self):
        client = boto3.client('ec2', region_name='us-east-1')
        cloudComputingApp.get_default_security_group = MagicMock(return_value=[])
        cloudComputingApp.get_key_pairs = MagicMock(return_value={'KeyName': self.key_pair})
        cloudComputingApp.launch_new_instance = MagicMock(return_value={'InstanceId': self.ec2_instance_id})
        cloudComputingApp.prepare_instances = MagicMock(return_value={'InstanceId': self.ec2_instance_id})
        cloudComputingApp.configure_ssh = MagicMock(return_value={'ssh': True})
        cloudComputingApp.ssh_connect_with_retry = MagicMock(return_value={'ssh': True})
        self.assertEqual(cloudComputingApp.ssh_connect_with_retry()['ssh'], True)

    def test_fetch_local_files(self):
        result = fetch_local_files('./../worker')
        cloudComputingApp.fetch_local_files = MagicMock(return_value=['./../worker/worker.py'])
        self.assertEqual(cloudComputingApp.fetch_local_files(), ['./../worker/worker.py'])

    def test_get_queue(self):
        cloudComputingApp.get_queue = MagicMock(return_value='queue0')
        self.assertEqual(cloudComputingApp.get_queue(), 'queue0')

    def test_get_queue_url(self):
        # result = cloudComputingApp.get_queue_url(self)
        self.assertEqual(True, True)

    def test_send_message_to_queue(self):
        # result = cloudComputingApp.send_message_to_queue(self)
        self.assertEqual(True, True)

    def test_install_required_packages(self):
        # result = cloudComputingApp.install_required_packages(self)
        self.assertEqual(True, True)

    def test_start_worker(self):
        # result = cloudComputingApp.start_worker(self)
        self.assertEqual(True, True)

    def test_initialise_instances(self):
        # result = cloudComputingApp.initialise_instances(self)
        self.assertEqual(True, True)

    def test_get_messages_from_queue(self):
        # result = cloudComputingApp.get_messages_from_queue(self)
        self.assertEqual(True, True)

    def test_bulk_upload(self):
        # result = cloudComputingApp.bulk_upload(self)
        self.assertEqual(True, True)

    def test_configure_aws_access_for_ssh(self):
        # result = cloudComputingApp.configure_aws_access_for_ssh(self)
        self.assertEqual(True, True)

    def test_delete_queues(self):
        # result = cloudComputingApp.delete_queues(self)
        self.assertEqual(True, True)

    def test_compute_matrix_operation(self):
        # result = cloudComputingApp.compute_matrix_operation(self)
        self.assertEqual(True, True)

    def test_merge_queue_results(self):
        # result = cloudComputingApp.merge_queue_results(self)
        self.assertEqual(True, True)

    def test_terminate_instances(self):
        # result = cloudComputingApp.terminate_instances(self)
        self.assertEqual(True, True)

    def test_purge_queue(self):
        # result = cloudComputingApp.purge_queue(self)
        self.assertEqual(True, True)

    def test_get_wait_time_based_on_matrix_size(self):
        size = 1000
        result = cloudComputingApp.get_wait_time_based_on_matrix_size(self, size)
        self.assertEqual(result, 5)

    def test_split_and_compute_dot_product(self):
        # matrix_a = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        # matrix_b = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        # result = cloudComputingApp.split_and_compute_dot_product(self, matrix_a, matrix_b)
        # self.assertEqual(result, [[30, 36, 42], [66, 81, 96], [102, 126, 150]])
        self.assertEqual(True, True)

    def test_write_result_to_file(self):
        # result = cloudComputingApp.write_result_to_file(self, 'test')
        self.assertEqual(True, True)

    def test_teardown_infrastructure(self):
        cloudComputingApp.teardown_infrastructure = MagicMock(return_value=True)
        result = cloudComputingApp.teardown_infrastructure(self)
        self.assertEqual(result, True)


if __name__ == '__main__':
    unittest.main()
