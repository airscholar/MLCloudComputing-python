import datetime
import numpy as np

def reformat_data(data):
    return str(data).replace('\n', '')


def matrix_dot_product(matrix_a, matrix_b):
    # Check that the matrices have compatible dimensions
    if matrix_a.shape[1] != matrix_b.shape[0]:
        print("Error: Matrices have incompatible dimensions")
        exit(1)

    start_time = datetime.datetime.now()
    result = np.zeros(matrix_a.shape)

    for i in range(len(matrix_a)):
        row = []
        for j in range(len(matrix_b[0])):
            sum = 0
            for k in range(len(matrix_b)):
                sum += matrix_a[i][k] * matrix_b[k][j]
            row.append(sum)
        result.append(row)
    print('Computation time', datetime.datetime.now() - start_time)

    return np.array(result)


def matrix_add(matrix_1, matrix_2):
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
