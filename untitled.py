import numpy as np
import datetime 

def generate_array(nrows, ncols):
    arr = np.random.randint(10, size=(nrows, ncols))
    # # print('arr 1:\n', arr)
    # arr = split_row(arr, 1, split_size)
    arr1 = np.random.randint(20, size=(nrows, ncols))
    # print('arr 2:\n', arr1)
    # arr1 = split_col(arr1, 1, split_size)
    return arr, arr1

def matrix_dot_product(matrix_a, matrix_b):
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


ARRAY_SIZE = 5000
start_time = datetime.datetime.now()
arr, arr1 = generate_array(ARRAY_SIZE,ARRAY_SIZE)
print('Generation time', datetime.datetime.now() - start_time)
print('generated')
addition = matrix_dot_product(arr, arr1)
print('Computation time', datetime.datetime.now() - start_time)
