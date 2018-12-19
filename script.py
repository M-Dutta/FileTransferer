import time
import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--n',type=str, nargs=1, required = True)
args = parser.parse_args()
loc = args.n[0]

for i in range(1,17):
    size =1024
    while size <= 204800: ##25 
        os.system("python3 ftclient.py --server vcf3.cs.uga.edu:47636 -c "+str(i)+" -s "+str(size)
                  +" --send "+loc +" big.txt")
        size = size+1024
        time.sleep(2.5)
        
