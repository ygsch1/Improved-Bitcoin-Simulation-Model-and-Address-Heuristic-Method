
import logging
import os
import random
import sys
import time
import hashlib
import simchain
import string


global addr_type_dict
addr_type_dict = {}



# tx_version [1/2]; (coinbase)
def tx_version():
   numbers = [1,2]
   probabilities = [0.70724106723088530021, 0.29275893276911469979]   
   txversion = random.choices(numbers, weights=probabilities)
   version = txversion[0]
   return version

# Address_type [4 types]; (coinbase)
def Address_type():
   types = ['Paytopubkeyhash','Paytoscripthash','Paytowitnesspubkeyhash','Paytowitnessscripthash']
   probabilities = [0.582564013668576835,0.288530719589426750,0.118097859783246279,0.010807406958750136]   
   address_type = random.choices(types, weights=probabilities)
   addr_type = address_type[0]
   return addr_type

# sequence_number[4294967295/4294967294/others]; (no coinbase)
def sequence_number():
   others = random.randint(0,4294967293)
   numbers = [4294967295,4294967294,others]
   probabilities = [0.71904390827349975147,0.11638153222198432004,0.16457455950451592849]    
   sequence_num = random.choices(numbers, weights=probabilities)
   sequence = sequence_num[0]
   return sequence

# locktime
def generate_locktime_data():
   nonzero = random.randint(1,1673832909)
   nlocktime = nonzero
   return nlocktime


# inputs' witness data filed
# Paytowitnesspubkeyhash/Paytowitnessscripthash/Paytoscripthash
def witness_data_field():
   witness_data = '['+str(''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(30)))+']'
   return witness_data


# Coinbase
def coinbase_segwit():
   types = [True,False]
   probabilities = [0.41367296846511108467, 0.58632703153488891533]      
   coinbasesegwit = random.choices(types, weights=probabilities)
   segwit = coinbasesegwit[0]
   return segwit

def coinbase_sequence_number():
   others = random.randint(0,4294967293)
   numbers = [4294967295,4294967294,others]
   probabilities = [0.7905633259,0,0.2094366741]       
   coinbasesequence_num = random.choices(numbers, weights=probabilities)
   coinbase_sequence = coinbasesequence_num[0]
   return coinbase_sequence


# timestamp
def match_then_insert(filename, match, content):
   lines = open(filename).read().splitlines()
   whole_string = "Txid: " + str(match)
   if whole_string in lines:
      index = lines.index(whole_string)
      lines.insert(index, content)
      open(filename, mode='w').write('\n'.join(lines))








