import unittest
import MLBD
import numpy as np


class TestMLBD(unittest.TestCase):
    def test_generate_array(self):
        rows = 3
        columns = 3
        max_value = 10
        matrix_a, matrix_b = MLBD.MLBDApp.generate_array(self, rows, columns, max_value)
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
        result = MLBD.MLBDApp.matrix_add(self, matrix_a, matrix_b)
        self.assertEqual(result, [[2, 4, 6], [8, 10, 12], [14, 16, 18]])

    def test_matrix_dot_product(self):
        matrix_a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        matrix_b = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        print("Matrix Multiplication Test")
        result = MLBD.MLBDApp.matrix_dot_product(self, matrix_a, matrix_b)
        self.assertEqual(result, [[30, 36, 42], [66, 81, 96], [102, 126, 150]])

    def test_reformat_data(self):
        matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        result = MLBD.MLBDApp.reformat_data(self, matrix)
        self.assertEqual(result, '[[1, 2, 3], [4, 5, 6], [7, 8, 9]]')

    def test_split_row(self):
        matrix = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
        result = MLBD.MLBDApp.split_row(self, matrix, 2, 2)
        self.assertEqual(result[0], [1, 2])


if __name__ == '__main__':
    unittest.main()
