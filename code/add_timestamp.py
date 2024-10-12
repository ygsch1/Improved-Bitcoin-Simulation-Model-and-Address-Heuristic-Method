

import logging
import os
import random
import sys
import time
import hashlib
import pandas as pd
import time
import datetime
import time as timelibrary
import string
from datetime import datetime, time
from time import mktime as mktime
from time import strptime as strptime


df = pd.read_csv('Block.csv')
Timestamp = df["Timestamp"].values.tolist()
Txs = df["Txs"].values.tolist()

with open('detaildata.log', 'r') as f:
    lines = f.readlines()

    for index, txs in enumerate(Txs):
        if index != 0:
            txs = txs.split(",")
            timestamp = int(mktime(strptime(str(Timestamp[index]).rsplit('.', 1)[0], "%Y-%m-%d %H:%M:%S")))
            for each_txid in txs[1:]:     
                for index, line in enumerate(lines):
                    if each_txid in line:
                        lines.insert(index, 'timestamp: '+ str(timestamp)+'\n')
                        break

with open('Transaction.log', 'w') as f1:
    f1.writelines(lines)
    f1.close()
