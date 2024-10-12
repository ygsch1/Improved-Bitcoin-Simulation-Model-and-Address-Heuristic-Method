
import random
import csv
import time
import pandas as pd
from simchain import addfunctions, network, peer
from simchain.network import Network
from simchain.params import Params


basic_data=open("Wallet.log",'w')

# create a blockchain network
print("Create a blockchain network:",file=basic_data)
net = Network()
a = net.peers
print(a,file=basic_data)

Max_NUMBER_OF_PEERS = Params.INIT_NUMBER_OF_PEERS

for i in range(Max_NUMBER_OF_PEERS):
   print("Basic info of Peer " + str(i) + ": " + str(a[i]),file=basic_data)
   print("Wallet's address list: " + str(net.peers[i].wallet.addrs),file=basic_data)
   print("\n",file=basic_data)


# make random transactions and reach consensus
TOTAL_TX_NUM = 0    
exit_flag = False

# tx_count in each block
def tx_count_in_block():
   interval1 = random.randint(1,500)
   interval2 = random.randint(501,1000)
   interval3 = random.randint(1001,1500)
   interval4 = random.randint(1501,2000)
   interval5 = random.randint(2001,2500)
   interval6 = random.randint(2501,3000)
   interval7 = random.randint(3001,3500)
   interval8 = random.randint(3501,4000)
   interval9 = random.randint(4001,12239)  # the largest tx num in one block on BTC blockchain
   numbers = [interval1,interval2,interval3,interval4,interval5,interval6,interval7,interval8,interval9]
   probabilities = [0.4410477963937236, 0.11208372077214228, 0.07815500627590174, 0.08917243070409063, 0.11439378673587558, 0.10237853034647348, 0.04088319053734829, 0.01033763623076867, 0.011547902003675711]
   tx_count = random.choices(numbers, weights=probabilities)[0]

   return tx_count


while True:
   # tx num in each block
   tx_num = tx_count_in_block()
   print("tx_num:" + str(tx_num))

   for n in range(tx_num):       
      i = random.random()          
      if i < 0.1601234409904172:
         net.make_transfers_transactions()

      elif 0.1601234409904172 <= i < 0.7475209092225663:
         net.make_multipay_transactions()

      elif 0.7475209092225663 <= i < 0.8002498189861795:
         net.make_consolidation_transactions()

      else:
         net.make_complex_transactions()
         #time.sleep(10)

      TOTAL_TX_NUM += 1
      print(TOTAL_TX_NUM)

      if peer.normal_tx_num == 25000:     
         exit_flag = True
         break

   if exit_flag == True:
      net.consensus()
      break

   net.consensus()

print("\n",file=basic_data)


print("Results:",file=basic_data)
for b in range(Max_NUMBER_OF_PEERS):
   print("\n",file=basic_data)
   print("Basic info of Peer " + str(b) + ": " + str(a[b]),file=basic_data)
   print("Balance is " + str(net.peers[b].get_balance()) + "BTC",file=basic_data)
   print("Address list: " + str(net.peers[b].wallet.addrs),file=basic_data)
   print("UTXO: " + str(net.peers[b].get_utxo()),file=basic_data)
   print("Confirmed UTXO: " + str(net.peers[b].get_confirmed_utxo()),file=basic_data)
   print("Unconfirmed UTXO: " + str(net.peers[b].get_unconfirmed_utxo()),file=basic_data)


print("Normal TX: "+ str(peer.normal_tx_num),file=basic_data)
print("Coinbase TX: "+ str(network.coinbase_tx_num),file=basic_data)



print("Finish.")

# addr_type_dict
dict_data = addfunctions.addr_type_dict
pd.DataFrame.from_dict(data=dict_data, orient='index').to_csv('Addr_type.csv', header=False)


# save block data
with open("Block.csv", "w", newline="") as f:
   writer = csv.writer(f)
   writer.writerow(["Block Hash","Timestamp","Number of Txs","Txs","Coinbase Txid","Coinbase Tx Version","Coinbase Tx Sequence Number","Coinbase Tx Locktime","Coinbase Tx SegWit","Coinbase Tx Vout","Coinbase Vout Addr","Coinbase Tx Value"])
   genesis_block_hash = net.peers[0].blockchain[0].hash
   genesis_block_timestamp = net.peers[0].blockchain[0].timestamp
   genesis_block_txs_num = len(net.peers[0].blockchain[0].txs)
   genesis_block_txs = net.peers[0].blockchain[0].txs
   genesis_block_coinbase_txid = net.peers[0].blockchain[0].txs[0].id
   genesis_block_coinbase_tx = net.peers[0].blockchain[0].txs    
   genesis_block_coinbase_tx_version = "1"
   genesis_block_coinbase_tx_sequence_number = "4294967295"
   genesis_block_coinbase_tx_locktime = '0'
   genesis_block_coinbase_tx_segwit = "None"
   genesis_block_coinbase_tx_vout_addr = []
   for i in range(Max_NUMBER_OF_PEERS):
      genesis_block_coinbase_tx_vout_addr.append(net.peers[0].blockchain[0].txs[0].tx_out[i].to_addr)
   block_coinbase_tx_value = Max_NUMBER_OF_PEERS * net.peers[0].blockchain[0].txs[0].tx_out[0].value
   writer.writerow([genesis_block_hash,genesis_block_timestamp,genesis_block_txs_num,genesis_block_txs,genesis_block_coinbase_txid,genesis_block_coinbase_tx_version,genesis_block_coinbase_tx_sequence_number,genesis_block_coinbase_tx_locktime,genesis_block_coinbase_tx_segwit,genesis_block_coinbase_tx,genesis_block_coinbase_tx_vout_addr,block_coinbase_tx_value])
   for current_block in net.peers[0].blockchain[1:]:
      block_hash = current_block.hash
      block_timestamp = current_block.timestamp
      block_txs_num = len(current_block.txs)
      block_txs = []
      for tx in current_block.txs:
         block_txs.append(tx.id)
      block_coinbase_txid = current_block.txs[0].id
      block_coinbase_tx = current_block.txs[0].tx_out[0]
      block_coinbase_tx_version = addfunctions.tx_version()
      block_coinbase_tx_sequence_number = addfunctions.coinbase_sequence_number()
      block_coinbase_tx_locktime = None
      if block_coinbase_tx_sequence_number == 4294967295:        
         block_coinbase_tx_locktime = 0
      elif block_coinbase_tx_sequence_number == 4294967294:
         block_coinbase_tx_locktime = addfunctions.generate_locktime_data()
      else:
         if random.randint(0, 1) == 1:        
            block_coinbase_tx_locktime = addfunctions.generate_locktime_data()
         else: block_coinbase_tx_locktime = 0
      block_coinbase_tx_segwit = addfunctions.coinbase_segwit()
      block_coinbase_tx_vout_addr = current_block.txs[0].tx_out[0].to_addr
      block_coinbase_tx_value = current_block.txs[0].tx_out[0].value
      writer.writerow([block_hash,block_timestamp,block_txs_num,block_txs,block_coinbase_txid,block_coinbase_tx_version,block_coinbase_tx_sequence_number,block_coinbase_tx_locktime,block_coinbase_tx_segwit,block_coinbase_tx,block_coinbase_tx_vout_addr,block_coinbase_tx_value])


basic_data.close()
peer.detail_data.close()

