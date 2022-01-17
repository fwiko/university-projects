import os
import sys
import argparse
from collections import defaultdict

def find(*, directory, filename):
    output = os.path.join(directory, 'output')
    try:
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isdir(path):
                if filename in os.listdir(path):
                    print(path, filename)
                find(directory=path, filename=filename)
    except PermissionError:
        pass
                
if __name__ == "__main__":
    filetree = defaultdict(list)
    directory = "C:\\"
    if os.path.exists(directory) and os.path.isdir(directory):
        find(directory=directory, filename="ShareX-Log-2021-08.txt")
            
    