# -*- coding: utf-8 -*-

import time
import random
from simchain import addfunctions
import numpy
from datetime import datetime, time

from collections import Counter
from .datatype import Vin,Vout,Tx,Block,get_merkle_root_of_txs
from .logger import logger
from .peer import Peer,find_utxos_from_block,add_utxos_to_set

from .consensus import consensus_with_fasttest_minner
from .params import Params
from math import ceil
from itertools import accumulate
import simchain
coinbase_tx_num = 0
Max_number_of_peers = Params.INIT_NUMBER_OF_PEERS


class Network(object):


    def __init__(self,nop = None,von = None):
        
        self.peers = []
        self.off_peers = []
        self.consensus_peers = []
        self.current_winner = None
        self.winner = []
        self.init_peers_number = nop or Params.INIT_NUMBER_OF_PEERS
        self.init_value = von or Params.INIT_COIN_PER_PEER
        self.create_genesis_block(self.init_peers_number,self.init_value)
        self.time_spent = [0]

        self._is_consensus_peers_chosen = False
        self._not = 0


    # follow probability distribution
    def N_value():
       interval1 = random.randint(16,50)
       interval2 = random.randint(51,100)
       interval3 = random.randint(101,200)
       interval4 = random.randint(201,300)
       numbers = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,interval1,interval2,interval3,interval4]
       probabilities_in = [0.534167040535623, 0.1653310990895722, 0.08639010870543662, 0.048310032619690135, 0.029394010343765303, 0.019156124579094366, 0.013471230758136422, 0.01008787997427895, 0.010524385802186002, 0.006844124722289904, 0.005372301082328679, 0.004954390390117691, 0.0037004236216661604, 0.0033435369932077966, 0.03746981030266825, 0.012672071588514801, 0.005141967826106974, 0.003669461065316707]
       probabilities_out = [0.8727682829961668, 0.05965419534030503, 0.015202813355591073, 0.008677291721039506, 0.006790623311789357, 0.004464685837863972, 0.0029024057840096114, 0.0024064538479873685, 0.0019176049141278965, 0.0028182169266189588, 0.0015210735004293802, 0.001260511345959131, 0.0010213415413031033, 0.0008556267802092406, 0.012866073511230406, 0.0029179614125159686, 0.001267129074885574, 0.0006877087979676144]
       in_num = random.choices(numbers, weights=probabilities_in)[0]
       out_num = random.choices(numbers, weights=probabilities_out)[0]
       
       return in_num, out_num

    # senders
    def verify_senders(senders):
        condition = False
        if len(set(senders.tolist())) != 1:    
            senders_counts = Counter(senders)
            result = dict(senders_counts) 
            repeat_peers_dict = {key:value for key,value in result.items()if value > 1}  
            if repeat_peers_dict == {}: # senders: no duplicate peer
                condition = True
            elif repeat_peers_dict:  
                keys_list = list(repeat_peers_dict.keys())
                values_list = list(repeat_peers_dict.values())  
                senders = senders.tolist()
                counts = 0
                for index,sender in enumerate(keys_list):
                    utxos = sender.get_utxo()
                    if len(utxos) < values_list[index]:  counts += 1    # no enough utxo
                if counts == 0: condition = True

        return condition
    
    def init_peers(self,number):
        for _ in range(number):
            coords = generate_random_coords()
            peer = Peer(coords)
            create_peer(self,peer)
    
    def add_peer(self):
        coords = generate_random_coords()
        peer = Peer(coords)
        create_peer(self,peer)
        peer.update_blockchain(self.peers[0])
        peer.update_mem_pool(self.peers[0])
        peer.update_utxo_set(self.peers[0])
        logger.info('A new peer joined in --> {0}(pid={1})'.format(peer,peer.pid))
        
    def create_genesis_block(self,number,value):
        self.init_peers(number = number)
        tx_in =[Vin(to_spend = None,
                    signature = b'I love blockchain',
                    pubkey = None,
                    sequence = None,
                    witness = None)]
        
        tx_out = [Vout(addr_type=addfunctions.Address_type(),value = value,to_addr = peer.wallet.addrs[-1])
                  for peer in self.peers]
        
        
        txs = [Tx(tx_in = tx_in,tx_out = tx_out,nlocktime = 0)]
        genesis_block = Block(version=0,
                              prev_block_hash=None,
                              timestamp = datetime.now(),
                              bits = 0,
                              nonce = 0,
                              txs = txs)
        
        logger.info('A blockchain p2p network created, {0} peers joined'.format(self.nop))
        logger.info('genesis block (hash: {0}) has been generated (timestamp: {1})'.format(genesis_block.hash,genesis_block.timestamp))

        # update addr_type_dict
        for each_vout in tx_out:
            addfunctions.addr_type_dict.update({each_vout.to_addr: each_vout.addr_type})

        utxos = find_utxos_from_block(txs)
        for peer in self.peers:
            peer.blockchain.append(genesis_block)
            add_utxos_to_set(peer.utxo_set,utxos)
        

    def make_transfers_transactions(self):
        global Receiver
        receiver = numpy.random.choice(self.peers[0:], 1)

        while True:    
            sender = numpy.random.choice(self.peers[0:], 1)
            if sender[0].get_balance() != 0: break
            else: continue
        receiver = receiver[0]
        Receiver = receiver
        sender = sender[0]


        if random.randint(1,10) is not 1:    # set reuse rate
           receiver.wallet.generate_keys() 

        sender.create_transfers_transaction(receiver.wallet.addrs[-1],
                                     value=0)

        sender.broadcast_transaction()

    def make_multipay_transactions(self):   # two posibilities
        def a(self):
            # one peer to one peer
            global Receiver
            receiver = numpy.random.choice(self.peers[0:], 1)

            while True:    
                sender = numpy.random.choice(self.peers[0:], 1)
                if sender[0].get_balance() != 0: break
                else: continue
                    
            receiver = receiver[0]
            Receiver = receiver
            sender = sender[0]

            sender.create_multipay0_transaction(receiver.wallet.addrs[-1],
                                               value=0)

            sender.broadcast_transaction()

        def b(self):  # one peer to multiple peers
            global Receivers, Senders, Addrs, multipay_flag
            multipay_flag = True
            no_use_num, vout_num = Network.N_value()

            while True:    
                senders = numpy.random.choice(self.peers[0:], 1)
                if senders[0].get_balance() != 0: break
                else: continue

            while True:    
                receivers = numpy.random.choice(self.peers[0:], vout_num, replace=True) 
                if len(set(receivers.tolist())) != 1: break   # avoid one peer to one peer
                else: continue 

            Receivers = receivers
            Senders = senders

            Addrs = []
            output = Peer.create_multi_transaction(senders, Addrs, value=0)  
            if output:
                senders[0].broadcast_transaction()  

        random.choice([a, b])(self)


    def make_consolidation_transactions(self):   # two posibilities
        def a(self):   # one peer to one peer
            global Receiver
            receiver = numpy.random.choice(self.peers[0:], 1)

            loop_counts = 0      
            while True:    
                sender = numpy.random.choice(self.peers[0:], 1)
                if len(sender[0].get_utxo()) > 1 or loop_counts == 11: break    
                else: 
                    loop_counts += 1
                    continue
            receiver = receiver[0]
            Receiver = receiver
            sender = sender[0]

            if random.randint(1,10) is not 1:   
               receiver.wallet.generate_keys() 

            sender.create_consolidation0_transaction(receiver.wallet.addrs[-1],
                                               value=0)

            sender.broadcast_transaction()

        def b(self):  # multiple peers to one peer

            global Receivers, Senders, Addrs,loop_flag, complex_flag
            loop_flag = False
            
            vin_num, no_use_num = Network.N_value()     
            receivers = numpy.random.choice(self.peers[0:], 1, replace=True) 

            loop_counts = 0
            while True:    
                senders = numpy.random.choice(self.peers[0:], vin_num, replace=True) 
                if Network.verify_senders(senders) or loop_counts == 11: break   
                else: 
                    loop_counts += 1
                    continue                 
            
            if loop_counts == 11:
                loop_flag = True
                global vin_num_used
                vin_num_used = vin_num
                senders = []
                for peer in self.peers[0:]:
                    if peer.get_balance() != 0: 
                        senders.append(peer)
                senders = numpy.array(senders)

            Receivers = receivers
            Senders = senders
            complex_flag = False

        Addrs = []
            output = Peer.create_multi_transaction(senders, Addrs, value=0)  
            if output:
                Peer.broadcast_multi_transaction(simchain.peer.updated_senders_list,simchain.peer.n_values)


        random.choice([a, b])(self)


    def make_complex_transactions(self):
        def a(self):  # one peer to one peer
            global Receiver
            receiver = numpy.random.choice(self.peers[0:], 1)

            loop_counts = 0       
            while True:    
                sender = numpy.random.choice(self.peers[0:], 1)
                if len(sender[0].get_utxo()) > 1 or loop_counts == 11: break     
                else: 
                    loop_counts += 1
                    continue
            receiver = receiver[0]
            Receiver = receiver
            sender = sender[0]

            sender.create_complex0_transaction(receiver.wallet.addrs[-1],
                                                value=0)

            sender.broadcast_transaction()

        def b(self):  # multiple peers to multiple peers

            global Receivers, Senders, Addrs,loop_flag
            loop_flag = False

            vin_num, vout_num = Network.N_value()

            while True:    
                receivers = numpy.random.choice(self.peers[0:], vout_num, replace=True)  
                if len(set(receivers.tolist())) != 1: break   
                else: continue 

            loop_counts = 0
            while True:    
                senders = numpy.random.choice(self.peers[0:], vin_num, replace=True)  
                if Network.verify_senders(senders) or loop_counts == 11: break  
                else: 
                    loop_counts += 1
                    continue
            
            if loop_counts == 11:
                loop_flag = True
                global vin_num_used
                vin_num_used = vin_num
                senders = []
                for peer in self.peers[0:]:
                    if peer.get_balance() != 0: 
                        senders.append(peer)
                senders = numpy.array(senders)

            Receivers = receivers
            Senders = senders

            Addrs = []
            output = Peer.create_multi_transaction(senders, Addrs, value=0)  
            if output:
                Peer.broadcast_multi_transaction(simchain.peer.updated_senders_list,simchain.peer.n_values)


        def c(self):  # one peer to multiple peers
            global Receivers, Senders, Addrs,multipay_flag
            no_use_num, vout_num = Network.N_value()

            loop_counts = 0      
            while True:    
                senders = numpy.random.choice(self.peers[0:], 1)
                if len(senders[0].get_utxo()) > 1 or loop_counts == 11: break      
                else: 
                    loop_counts += 1
                    continue

            while True:    
                receivers = numpy.random.choice(self.peers[0:], vout_num, replace=True) 
                if len(set(receivers.tolist())) != 1: break   
                else: continue

            Receivers = receivers
            Senders = senders
            multipay_flag = False

            Addrs = []
            output = Peer.create_multi_transaction(senders, Addrs, value=0)  
            if output:
                senders[0].broadcast_transaction() 


        def d(self):  # multiple peers to one peer

            global Receivers, Senders, Addrs,loop_flag, complex_flag, vout_num_used_complex   
            loop_flag = False
            complex_flag = True

            vin_num, vout_num_used_complex = Network.N_value()     
            receivers = numpy.random.choice(self.peers[0:], 1, replace=True)  

            loop_counts = 0
            while True:    
                senders = numpy.random.choice(self.peers[0:], vin_num, replace=True) 
                if Network.verify_senders(senders) or loop_counts == 11: break   
                else: 
                    loop_counts += 1
                    continue
            
            if loop_counts == 11:
                loop_flag = True
                global vin_num_used
                vin_num_used = vin_num
                senders = []
                for peer in self.peers[0:]:
                    if peer.get_balance() != 0: 
                        senders.append(peer)
                senders = numpy.array(senders)

            Receivers = receivers
            Senders = senders

            Addrs = []
            output = Peer.create_multi_transaction(senders, Addrs, value=0)  
            if output:
                Peer.broadcast_multi_transaction(simchain.peer.updated_senders_list,simchain.peer.n_values)


        random.choice([a, b, c, d])(self)



    def set_consensus_peers(self,*idx):
        for i in idx:
            self.consensus_peers.append(self.peers[i])
            
        self._is_consensus_peers_chosen = True
    
    def choose_random_consensus_peers(self):
        n = self.nop
        #we suppose we have 20%~60% nodes are consensus node
        ub,lb = Params.UPPER_BOUND_OF_CONSENSUS_PEERS,\
                Params.LOWWER_BOUND_OF_CONSENSUS_PEERS
        k = random.randint(ceil(lb*n),ceil(ub*n))
        self.consensus_peers = random.sample(self.peers,k)     
        self._is_consensus_peers_chosen = True
        
        
    def consensus(self,meth = 'pow'):
        global coinbase_tx_num
        if not self._is_consensus_peers_chosen:
            self.choose_random_consensus_peers()
        
        if meth == 'pow':
            logger.info('{0} peers are mining'.format(len(self.consensus_peers)))
            n,nonce,time = consensus_with_fasttest_minner(self.consensus_peers)
            self.time_spent.append(time)
            self.current_winner = self.consensus_peers[n]
            self.winner.append(self.current_winner)
            
            logger.info('{0}(pid={1}) is winner,{2} secs used'.format(
                    self.current_winner,
                    self.current_winner.pid,
                    time
                    ))
            logger.info('{0}(pid={1}) created a coinbase transaction'.format(self.current_winner,self.current_winner.pid)) 
            coinbase_tx_num += 1

            block = self.current_winner.package_block(nonce = nonce)
            self.current_winner.recieve_block(block)
            self.current_winner.broadcast_block(block)

            addfunctions.addr_type_dict.update({block.txs[0].tx_out[0].to_addr: block.txs[0].tx_out[0].addr_type})     #更新addr_type_dict
         
    def draw(self):
        pass
    
    @property
    def time(self):
        return _accumulate(self.time_spent)

    def get_time(self):
        return self.time[-1]
 
    @property
    def nop(self):
        return len(self.peers)
    
    def __repr__(self):
        return 'A p2p blockchain network with {0} peers'.format(self.nop)

def create_peer(net,peer):
    peer.pid = net.nop
    peer.network = net
    peer.wallet.generate_keys()
    net.peers.append(peer)


#functions
# =============================================================================



#Iterables 
# =============================================================================
    


def addr_finder(tx):
    return (out.vout.to_addr for out in tx.tx_out)

def _accumulate(l):
    return list(accumulate(l))
    
#random data
# =============================================================================

def tx_random_value():  
    return random.uniform(0.1, 20.0) 


def generate_random_coords():
    return (random.randint(0,100),random.randint(0,100))

    
if __name__ == "__main__":
    pass
    net = Network()
    net.make_transfers_transactions()
    net.make_multipay_transactions()
    net.make_consolidation_transactions()
    net.make_complex_transactions()
    net.consensus()





        

