# main.py
import sys
import json
import numpy as np

arr1 = np.array(json.loads(sys.argv[1]))
arr2 =  np.array(json.loads(sys.argv[2]))
print(np.dot(arr1, arr2))

