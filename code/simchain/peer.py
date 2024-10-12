# -*- coding: utf-8 -*-
from datetime import datetime
import math
import random
import statistics
import sys
from collections import Counter
import time
import simchain
from simchain import addfunctions
from .ecc import VerifyingKey,build_message,convert_pubkey_to_addr
from .datatype import Pointer,Vin,Vout,UTXO,Tx,Block,get_merkle_root_of_txs
from .params import Params
from .consensus import mine,caculate_target
from .logger import logger
from .wallet import Wallet
from .vm import LittleMachine
from .merkletree import MerkleTree
from random import getrandbits
from itertools import repeat
from random import choice


detail_data=open("Transaction.log",'w')
normal_tx_num = 0
ts_value,mp_value,multi_value,con_value,com_value = 0,0,0,0,0
SENDERS = []

class Peer(object):

    def __init__(self,coords = None):
        self.coords = coords
        self.network = None
        self.txs = []
        self.candidate_block_txs = []
        self.candidate_block = None
        self.blockchain = []
        self.orphan_block = []
        self.utxo_set = {}
        self.mem_pool = {}
        self.orphan_pool = {}
        self.pid = None

        self.fee = 0 
        self.tx_choice_method = 'whole'
        self.current_tx = None
        self.allow_utxo_from_pool = True
        self.machine = LittleMachine()
        self._is_wallet_generated = False
        self.generate_wallet()
        
        self._is_block_candidate_created = False
        self._is_current_tx_created = False
        self._is_current_tx_sent = False
        self._delayed_tx = None
        self._delayed_block = None
        self._utxos_from_vins = None
        self._pointers_from_vouts = None
        self._utxos_from_vouts = None
        self._txs_removed = None


    
    ############################################################
    # peer as wallet
    ############################################################
    """
    Generate wallet
    """
    
    def generate_wallet(self):
        if not self._is_wallet_generated:
            self.wallet = Wallet()
            self._is_wallet_generated = True


    @property
    def sk(self):
        return self.wallet.keys[-1].sk.to_bytes() if self.wallet.keys else None

    @property
    def pk(self):
        return self.wallet.keys[-1].pk.to_bytes() if self.wallet.keys else None


    @property
    def addr(self):
        return self.wallet.addrs[-1] if self.wallet.addrs else None

    @property
    def key_base_len(self):
        return len(self.sk)
        
    """
    your bank balance
    """
    def get_balance(self):
        utxos = self.get_utxo()
        return sum(utxo.vout.value for utxo in utxos)
    
    """
    your output
    """
    
    def get_utxo(self):
        return [utxo for utxo in self.utxo_set.values()
                if (utxo.vout.to_addr in self.wallet.addrs) and utxo.unspent]
        
    def get_unconfirmed_utxo(self):
        utxos = self.get_utxo()
        return [utxo for utxo in utxos if not utxo.confirmed]
    
    def get_confirmed_utxo(self):
        utxos = self.get_utxo()
        return [utxo for utxo in utxos if utxo.confirmed]
    
    def set_fee(self,value):
        self.fee = value
    
    def get_fee(self):
        return self.fee

    def calculate_fees(self,txs=[]):
        return sum(tx.fee for tx in txs)

    
    def get_block_reward(self):
        return Params.FIX_BLOCK_REWARD


    """
    create a transaction 
    """

    #@Counter.counts

    def create_transfers_transaction(self, to_addr,
                                     value,
                                     tx_type = "transfers"):
        RECEIVER = simchain.network.Receiver
        if tx_type == 'transfers':
            outputs = create_transfers_tx(self,to_addr,value)

            if outputs:
                tx_in,tx_out,fee = outputs
                self.current_tx = Tx(tx_in,tx_out,fee = fee,nlocktime = 0)
                self.txs.append(self.current_tx)
                self._is_current_tx_created = True
                value = simchain.peer.ts_value

                logger.info('{0}(pid={1}) created a transaction'.format(self,self.pid))
                logger.info('{0} sent a transaction to {1} with {2} BTC'.format(self,RECEIVER,value))

                print('{0} sent a transaction to {1} with {2} BTC'.format(self, RECEIVER, value), file=detail_data)

                return True
            return False

    def create_multipay0_transaction(self, to_addr,
                              value,
                              tx_type = "multipay"):
        RECEIVER = simchain.network.Receiver
        if tx_type == 'multipay':
            outputs = create_multipay0_tx(self,to_addr,value)

            if outputs:
                tx_in,tx_out,fee = outputs
                self.current_tx = Tx(tx_in,tx_out,fee = fee,nlocktime = 0)
                self.txs.append(self.current_tx)
                self._is_current_tx_created = True
                value = simchain.peer.mp_value

                logger.info('{0}(pid={1}) created a transaction'.format(self,self.pid))
                logger.info('{0} sent a transaction to {1} with {2} BTC'.format(self,RECEIVER,value))

                print('{0} sent a transaction to {1} with {2} BTC'.format(self, RECEIVER, value), file=detail_data)

                return True
            return False

    def create_multi_transaction(self,senders,value,*Addrs,tx_type = "multiple_peers"):
        receivers = simchain.network.Receivers
        Addrs=simchain.network.Addrs
        if tx_type == 'multiple_peers':
            outputs = create_multi_tx(self,value,Addrs)

            if outputs:
                self = updated_senders_list
                value= simchain.peer.multi_value
                tx_in,tx_out,fee = outputs
                for sender in self:
                    sender.current_tx = Tx(tx_in,tx_out,fee = fee,nlocktime = 0)
                    sender.txs.append(sender.current_tx)
                    sender._is_current_tx_created = True

                logger.info('{0} created a transaction'.format(list(self)))
                logger.info('{0} sent a transaction to {1} with {2} BTC'.format(list(self),list(receivers),value))              
                print('{0} sent a transaction to {1} with {2} BTC'.format(list(self),list(receivers),value),file=detail_data)

                return True
            return False

    def create_consolidation0_transaction(self, to_addr,
                              value,
                              tx_type = "consolidation"):
        RECEIVER = simchain.network.Receiver
        if tx_type == 'consolidation':
            outputs = create_consolidation0_tx(self,to_addr,value)

            if outputs:
                tx_in,tx_out,fee = outputs
                self.current_tx = Tx(tx_in,tx_out,fee = fee,nlocktime = 0)
                self.txs.append(self.current_tx)
                self._is_current_tx_created = True
                value = simchain.peer.con_value

                logger.info('{0}(pid={1}) created a transaction'.format(self,self.pid))

                logger.info('{0} sent a transaction to {1} with {2} BTC'.format(self,RECEIVER,value))

                print('{0} sent a transaction to {1} with {2} BTC'.format(self, RECEIVER, value), file=detail_data)

                return True
            return False

    def create_complex0_transaction(self, to_addr,
                           value,
                           tx_type = "complex"):
      RECEIVER = simchain.network.Receiver
      if tx_type == 'complex':
            outputs = create_complex0_tx(self,to_addr,value)

            if outputs:
                tx_in,tx_out,fee = outputs
                self.current_tx = Tx(tx_in,tx_out,fee = fee,nlocktime = 0)
                self.txs.append(self.current_tx)
                self._is_current_tx_created = True
                value = simchain.peer.com_value

                logger.info('{0}(pid={1}) created a transaction'.format(self,self.pid))

                logger.info('{0} sent a transaction to {1} with {2} BTC'.format(self,RECEIVER,value))

                print('{0} sent a transaction to {1} with {2} BTC'.format(self, RECEIVER, value), file=detail_data)

                return True
            return False



    """
    if this is a recorder peer, build rewards for self after winning
    """
    def create_coinbase(self,value):
        self.wallet.generate_keys()
        return Tx.create_coinbase(self.wallet.addrs[-1],value = value)

    
    ############################################################
    # peer as route
    ############################################################
    """
    broadcast a transaction 
    """
    def send_transaction(self):
        if not self.txs:
            return False
        
        if self._is_current_tx_created:
            sign_utxo_from_tx(self.utxo_set,self.current_tx)
            
            add_tx_to_mem_pool(self,self.current_tx) 
            self._is_current_tx_created = False
            self._is_current_tx_sent = True
            
            logger.info("{0}(pid={1}) sent a transaction to network".format(self,self.pid))
            time.sleep(5)
            return True
        return False

    def send_multi_transaction(self,n_values):
        i=0
        PID=[]
        for index,sender in enumerate(self):
            if not sender.txs:
                return False

            if sender._is_current_tx_created:
                #sign_utxo_from_tx(sender.utxo_set,sender.current_tx)
                sign_utxo_from_tx_multi(sender.utxo_set,sender.current_tx,n_values,index)

                add_tx_to_mem_pool(sender,sender.current_tx)
                sender._is_current_tx_created = False
                sender._is_current_tx_sent = True
                PID.append(sender.pid)
                i+=1

        if i ==len(self):
            logger.info("{0}(pid={1}) sent a transaction to network".format(list(self),PID))
            time.sleep(5)
            return True
        return False
    
    
    def recieve_transaction(self,tx):
        if tx and (tx not in self.mem_pool):
            if self.verify_transaction(tx,self.mem_pool): 
                add_tx_to_mem_pool(self,tx)
                return True
        
        return False

            
    def broadcast_transaction(self,tx = None):
        if not self._is_current_tx_sent:
            self.send_transaction()

        self._is_current_tx_created = False
        self._is_current_tx_sent = False
        
        tx = tx or self.current_tx
        if tx:
            peers = self.network.peers[:]
            peers.remove(self)
            number = broadcast_tx(peers,tx)
            self.current_tx = None
            
            logger.info("{0}(pid={1})'s transaction verified by {2} peers".format(self,self.pid,number))
            print('Txid: {0}'.format(tx.id)+"\n",file=detail_data)

            return number
        return 0


    # for multiple senders
    def broadcast_multi_transaction(self,n_values,tx = None):
        global SENDERS
        SENDERS=self       
        PID = []
        TX = 0
        i=0
        broadcast_flag = False
        for sender in self:
            if not sender._is_current_tx_sent:
                i+=1

        if i==len(self):
            Peer.send_multi_transaction(self,n_values)

        for sender in self:
            sender._is_current_tx_created = False
            sender._is_current_tx_sent = False

            tx = tx or sender.current_tx
            if tx:
                TX+=1
                PID.append(sender.pid)

        # broadcast
        if TX==len(self):
            sender_selected = choice(self)
            peers = sender_selected.network.peers[:]
            peers=list(set(peers).difference(set(self)))  
            number = broadcast_tx(peers,tx)
            broadcast_flag = True
            time.sleep(1)

        if broadcast_flag:
            for sender in self:
                sender.current_tx = None

            print('Txid: {0}'.format(tx.id)+"\n",file=detail_data)
            logger.info("{0}(pid={1})'s transaction verified by {2} peers".format(list(self),PID,number))  
            return number

        return 0

        
    """
    broadcast a transaction 
    """ 
    def broadcast_block(self,block):
        peers = self.network.peers[:]
        peers.remove(self)
        number = broadcast_winner_block(peers,block)

        logger.info('{0} received by {1} peers (timestamp: {2})'.format(block,number,block.timestamp))
        #return current_block_time
                
                
    def locate_block(self,block_hash):
       return locate_block_by_hash(self,block_hash)
   
    
    def recieve_block(self,block):
        if not self.verify_block(block):
            return False
        return try_to_add_block(self,block)
    
    
    """
    verify a transaction
    """
    
    def verify_transaction(self,tx,pool = {}):
        if tx in self.txs:
            return True
        return verify_tx(self,tx,pool)

    """
    verify a block
    """ 
    
    def verify_block(self,block):
        if self._delayed_tx:
            fill_mem_pool(self)
            
        if self.orphan_pool:
            check_orphan_tx_from_pool(self)
            
        if block == self.candidate_block:
            return True
        
        if not verify_winner_block(self,block):
            return False

        return True
    
    def response_path(self,tx):
        if tx.id in self.mem_pool:
            return "unconfirmed"

        tot_height = self.get_height()
        for i in range(tot_height):
            txs = self.blockchain[-i-1].txs
            if tx in txs:
                break
            else:
                return False

        height = tot_height - i
        idx = txs.index(tx)
        idxs = [tx.id for tx in txs]
        merkle = MerkleTree(idxs)
        path = merkle.get_path(idx)
        return height,path
            

        
    """
    peer links to p2p network
    """
    
    def login(self):
        assert self in self.network.off_peers,(
                "This peer does not connect to network or online"
                )
        repeat_log_in(self,self.network)
        self.update_blockchain()
        
                
    """
    peer logs out 
    """
    def logout(self):
        assert self in self.network.peers,(
                "This peer does not connect to network"
                )
        log_out(self,self.network)
    
    
    
    def update_blockchain(self,other):
        return update_chain(self,other)
                
    
    def update_mem_pool(self,other):
        if other._delayed_tx:
            fill_mem_pool(other)
        return update_pool(self,other.mem_pool)


    def update_utxo_set(self,other):
        self.utxo_set.update(other.utxo_set)
              
    ############################################################
    # peer as recorder
    ############################################################
    
    """
    if u r a consensus peer, u have create a candidate block
    """
    
    def create_candidate_block(self):
        self.choose_tx_candidates()
        txs = self.candidate_block_txs
        value = self.get_block_reward() + self.calculate_fees(txs)    
        coinbase = self.create_coinbase(value)

        txs = [coinbase]+txs
        
        prev_block_hash = self.blockchain[-1].hash
        bits = Params.INITIAL_DIFFICULTY_BITS 
        self.candidate_block = Block(version=0, 
                                     prev_block_hash=prev_block_hash,
                                     #timestamp = self.network.time[-1],
                                     timestamp = datetime.now(),
                                     bits = bits, 
                                     nonce = 0,
                                     txs = txs or [])
        
        self._is_block_candidate_created = True
        return value
        
    
    '''
    pow used right now
    '''        
    def consensus(self,meth = 'pow'):
        if not self._is_block_candidate_created:
            self.create_candidate_block()
            self._is_block_candidate_created = False
            
        if meth == 'pow':
            return mine(self.candidate_block)

    """
    if this is a recorder peer, we have package the candidate block
    """
    def package_block(self,nonce):
        block = self.candidate_block._replace(nonce = nonce)
        return block

    """
    choose transactions for candidate block 
    """
    def choose_tx_candidates(self):
        if self.tx_choice_method == 'whole':
            if not self.mem_pool:
                self.update_mem_pool(self.network.peers[0])
            self.candidate_block_txs = choose_whole_txs_from_pool(self.mem_pool)
        
        elif self.tx_choice_method == 'random':
            if not self.mem_pool:
                self.update_mem_pool(self.network.peers[0])
            self.candidate_block_txs = choose_raondom_txs_from_pool(self.mem_pool)

    """
    get transactions for candidate block
    """
    def get_tx_candidates(self):  
        return self.candidate_block_txs
    
    def get_height(self):
        return len(self.blockchain)
    
    def roll_back_now(self):
        roll_back(self)

    def __repr__(self):
        return 'peer{0}'.format(self.coords)
    
    
# =============================================================================
#login and logout

def repeat_log_in(peer,net):
    net.off_peers.remove(peer)
    net.peers.append(peer)
    
def log_out(peer,net):
    net.peers.remove(peer)
    net.off_peers.append(peer)
    peer.mem_pool = []

def update_chain(peer,other):
    other_height = other.get_height()
    height = peer.get_height()
    if other_height > height:
        peer.blockchain = []
        for block in other.blockchain:
            peer.blockchain.append(block)
        return True
    return False
    

def update_pool(peer,pool):
    a,b = set(peer.mem_pool),set(pool)
    for tx_id in (b-a):
        tx = pool.get(tx_id)
        peer.mem_pool[tx_id] = tx
    
    if peer._delayed_tx:
        fill_mem_pool(peer)
    
    if peer.orphan_pool:
        check_orphan_tx_from_pool(peer)
        
    return True

    

# =============================================================================         
#create transactions

# follow probability distribution
def UTXO_value():
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


def create_transfers_tx(peer, to_addr, value) :
    global normal_tx_num,ts_value
    utxos,balance = peer.get_utxo(),peer.get_balance()
    fee,wallet = peer.fee,peer.wallet

    tx_in,tx_out = [],[]
    need_to_spend, n = 0, 1
    if balance == 0:    # no balance
        logger.info('no enough money for transaction for {0}(pid = {1})'.format(peer,peer.pid))
        return

    need_to_spend += utxos[0].vout.value

    if need_to_spend != 0:
        value = need_to_spend
        fee = value * 0.0001  # fee: 0.01%
        ts_value = value-fee  

        if to_addr not in addfunctions.addr_type_dict:
            addr_type = addfunctions.Address_type()                      
            addfunctions.addr_type_dict.update({to_addr: addr_type})     
        else: addr_type = addfunctions.addr_type_dict.get(to_addr)       
        tx_out += [Vout(to_addr,value-fee,addr_type)] 


    sequence = addfunctions.sequence_number()  
    for utxo in utxos[:n]:
        addr = utxo.vout.to_addr
        addr_type = utxo.vout.addr_type
        idx = wallet.addrs.index(addr)
        sk,pk = wallet.keys[idx].sk,wallet.keys[idx].pk

        witness_data = None
        if addr_type == "Paytopubkeyhash":                
            witness_data = []
        elif addr_type == "Paytowitnesspubkeyhash" or addr_type == "Paytowitnessscripthash":    
            witness_data = addfunctions.witness_data_field()
        elif addr_type == "Paytoscripthash":
            if random.randint(0, 1) == 1:
                witness_data = addfunctions.witness_data_field()
            else: witness_data = []

        string = str(utxo.pointer) + str(pk.to_bytes()) + str(tx_out)
        message = build_message(string)
        signature = sk.sign(message)

        tx_in.append(Vin(utxo.pointer,signature,pk.to_bytes(),sequence,witness_data))


    normal_tx_num += 1

    print(str(tx_in),file=detail_data)
    print("vin_sz: "+ str(len(tx_in)),file=detail_data)
    print(str(tx_out),file=detail_data)
    print("vout_sz: "+str(len(tx_out)),file=detail_data)
    print(str(utxos[:n]),file=detail_data)
    tx_version = addfunctions.tx_version()

    locktime = None
    if sequence == 4294967295:         
        locktime = 0
    elif sequence == 4294967294:
        locktime = addfunctions.generate_locktime_data()
    else:
        if random.random() < 0.28167753191759468926:    
            locktime = addfunctions.generate_locktime_data()
        else: locktime = 0

    print('version: {0}'.format(tx_version),file=detail_data)    
    print('locktime: {0}'.format(locktime),file=detail_data)     
    print("fee: "+str(fee),file=detail_data)     
    #print('timestamp: {0}'.format(peer.blockchain[-1].timestamp),file=detail_data)   
    #print('timestamp: {0}'.format(int(time.mktime(peer.blockchain[-1].timestamp.timetuple()))),file=detail_data) 

    return tx_in,tx_out,fee

def create_multipay0_tx(peer, to_addr, value) :
    global normal_tx_num,mp_value
    utxos,balance = peer.get_utxo(),peer.get_balance()
    fee,wallet = peer.fee,peer.wallet
    m_value = 0

    tx_in,tx_out = [],[]
    need_to_spend, n = 0, 1
    if balance == 0:   
        logger.info('no enough money for transaction for {0}(pid = {1})'.format(peer,peer.pid))
        return

    need_to_spend += utxos[0].vout.value
    no_use_num, vout_num  = UTXO_value()     

    if need_to_spend != 0:
        value = need_to_spend
        fee = value * 0.0001  
        mp_value = value - fee 

    receiver = simchain.network.Receiver
    for k in range(vout_num):
        if random.randint(1,10) is not 1:      
            receiver.wallet.generate_keys() 
        to_addr = receiver.wallet.addrs[-1]

        if to_addr not in addfunctions.addr_type_dict:
            addr_type = addfunctions.Address_type()                    
            addfunctions.addr_type_dict.update({to_addr: addr_type})     
        else: addr_type = addfunctions.addr_type_dict.get(to_addr)       

        if k != int(vout_num) -1:
            value1 = random.uniform(0.00001*value, (mp_value)/int(vout_num))  
            tx_out += [Vout(to_addr,value1,addr_type)]
            m_value += value1
        else: tx_out += [Vout(to_addr,mp_value-m_value,addr_type)]


    sequence = addfunctions.sequence_number()  
    for utxo in utxos[:n]:
        addr = utxo.vout.to_addr
        addr_type = utxo.vout.addr_type
        idx = wallet.addrs.index(addr)
        sk,pk = wallet.keys[idx].sk,wallet.keys[idx].pk

        witness_data = None
        if addr_type == "Paytopubkeyhash":                 
            witness_data = []
        elif addr_type == "Paytowitnesspubkeyhash" or addr_type == "Paytowitnessscripthash":    
            witness_data = addfunctions.witness_data_field()
        elif addr_type == "Paytoscripthash":
            if random.randint(0, 1) == 1:
                witness_data = addfunctions.witness_data_field()
            else: witness_data = []

        string = str(utxo.pointer) + str(pk.to_bytes()) + str(tx_out)
        message = build_message(string)
        signature = sk.sign(message)

        tx_in.append(Vin(utxo.pointer,signature,pk.to_bytes(),sequence,witness_data))


    normal_tx_num += 1

    print(str(tx_in),file=detail_data)
    print("vin_sz: "+ str(len(tx_in)),file=detail_data)
    print(str(tx_out),file=detail_data)
    print("vout_sz: "+str(len(tx_out)),file=detail_data)
    print(str(utxos[:n]),file=detail_data)
    tx_version = addfunctions.tx_version()

    locktime = None
    if sequence == 4294967295:         
        locktime = 0
    elif sequence == 4294967294:
        locktime = addfunctions.generate_locktime_data()
    else:
        if random.random() < 0.28167753191759468926:  
            locktime = addfunctions.generate_locktime_data()
        else: locktime = 0

    print('version: {0}'.format(tx_version),file=detail_data)     
    print('locktime: {0}'.format(locktime),file=detail_data)     
    print("fee: "+str(fee),file=detail_data)    
    #print('timestamp: {0}'.format(peer.blockchain[-1].timestamp),file=detail_data)    
    #print('timestamp: {0}'.format(int(time.mktime(peer.blockchain[-1].timestamp.timetuple()))),file=detail_data)  

    return tx_in,tx_out,fee

def create_multi_tx(senders,value,Addrs) :
    global normal_tx_num,multi_value
    receivers = simchain.network.Receivers
    fee = 0
    UTxo=[]
    tx_in,tx_out = [],[]
    need_to_spend,m_value = 0,0
    need_to_spend_l=[]
    global updated_senders_list, n_values
    n_values = [] 

    if len(senders) == 1:  
        utxos,balance = senders[0].get_utxo(),senders[0].get_balance()
        if balance == 0:  
            logger.info('no enough money for transaction for {0}(pid = {1})'.format(senders[0], senders[0].pid))
            return

        if simchain.network.multipay_flag == True:  
            n = 1    
            need_to_spend += utxos[0].vout.value

        else: 
            n, vout_num_create_multi_tx = UTXO_value()   
            if n > len(utxos): n = len(utxos)  

            for j, utxo in enumerate(utxos):
                need_to_spend += utxo.vout.value
                if j == n - 1:
                    break

        if need_to_spend != 0:
            value = need_to_spend
            fee = value*0.0001   
            multi_value = need_to_spend-fee


        for k,receiver in enumerate(receivers):
            if random.randint(1,10) is not 1:     
                receiver.wallet.generate_keys() 
            to_addr = receiver.wallet.addrs[-1]

            if to_addr not in addfunctions.addr_type_dict:
                addr_type = addfunctions.Address_type()                    
                addfunctions.addr_type_dict.update({to_addr: addr_type})    
            else: addr_type = addfunctions.addr_type_dict.get(to_addr)      

            if k != len(receivers) -1:
                value1 = random.uniform(0.00001*value, (multi_value)/len(receivers))  
                tx_out += [Vout(to_addr,value1,addr_type)]
                m_value += value1
            else: tx_out += [Vout(to_addr,multi_value-m_value,addr_type)]

        sequence = addfunctions.sequence_number() 

        wallet = senders[0].wallet
        utxos = senders[0].get_utxo()
        for utxo in utxos[:n]:
            UTxo.append(utxo)
            addr = utxo.vout.to_addr
            addr_type = utxo.vout.addr_type
            idx = wallet.addrs.index(addr)
            sk,pk = wallet.keys[idx].sk,wallet.keys[idx].pk

            witness_data = None
            if addr_type == "Paytopubkeyhash":               
                witness_data = []
            elif addr_type == "Paytowitnesspubkeyhash" or addr_type == "Paytowitnessscripthash":    
                witness_data = addfunctions.witness_data_field()
            elif addr_type == "Paytoscripthash":
                if random.randint(0, 1) == 1:
                    witness_data = addfunctions.witness_data_field()
                else: witness_data = []

            string = str(utxo.pointer) + str(pk.to_bytes()) + str(tx_out)
            message = build_message(string)
            signature = sk.sign(message)

            tx_in.append(Vin(utxo.pointer,signature,pk.to_bytes(),sequence,witness_data))

        updated_senders_list = senders
        n_values = [1]

    else: 
        if simchain.network.loop_flag == True:   
            N = simchain.network.vin_num_used
            N_counts = 0
            updated_senders = [] 

            for sender in senders:  
                utxos,balance = sender.get_utxo(),sender.get_balance()

                if balance == 0:    
                    logger.info('no enough money for transaction for {0}(pid = {1})'.format(sender,sender.pid))
                    return

                n = random.randint(1,len(utxos))
                n_values.append(n)
                N_counts += n
                updated_senders.append(sender)
                for j,utxo in enumerate(utxos):
                    need_to_spend += utxo.vout.value
                    need_to_spend_l.append(utxo.vout.value)
                    if j == n-1:
                        break

                if N_counts >= N: break
                else: continue

            if need_to_spend != 0:
                value = need_to_spend
                fee = value*0.0001    
                multi_value = need_to_spend - fee

            
            if len(receivers) == 1 and simchain.network.complex_flag == True: 
                vout_num_complex = simchain.network.vout_num_used_complex  

                receiver = receivers[0]
                for k in range(vout_num_complex):
                    if random.randint(1,10) is not 1:       
                        receiver.wallet.generate_keys()  
                    to_addr = receiver.wallet.addrs[-1]

                    if to_addr not in addfunctions.addr_type_dict:
                        addr_type = addfunctions.Address_type()                     
                        addfunctions.addr_type_dict.update({to_addr: addr_type})     
                    else: addr_type = addfunctions.addr_type_dict.get(to_addr)       

                    if k != int(vout_num_complex) -1:
                        value1 = random.uniform(0.00001*value, (multi_value)/int(vout_num_complex))  
                        tx_out += [Vout(to_addr,value1,addr_type)]
                        m_value += value1
                    else: tx_out += [Vout(to_addr,multi_value-m_value,addr_type)]

            else:   
                for k,receiver in enumerate(receivers):
                    if random.randint(1,10) is not 1:        
                        receiver.wallet.generate_keys()   
                    to_addr = receiver.wallet.addrs[-1]

                    if to_addr not in addfunctions.addr_type_dict:
                        addr_type = addfunctions.Address_type()                     
                        addfunctions.addr_type_dict.update({to_addr: addr_type})    
                    else: addr_type = addfunctions.addr_type_dict.get(to_addr)       

                    if k != len(receivers) -1:
                        value1 = random.uniform(0.00001*value, (multi_value)/len(receivers))   
                        tx_out += [Vout(to_addr,value1,addr_type)]
                        m_value += value1
                    else: tx_out += [Vout(to_addr,multi_value-m_value,addr_type)]

            sequence = addfunctions.sequence_number()   
            for index,sender in enumerate(updated_senders):
                wallet = sender.wallet
                utxos = sender.get_utxo()
                n = n_values[index]
                for utxo in utxos[:n]:
                    UTxo.append(utxo)
                    addr = utxo.vout.to_addr
                    addr_type = utxo.vout.addr_type
                    idx = wallet.addrs.index(addr)
                    sk,pk = wallet.keys[idx].sk,wallet.keys[idx].pk

                    witness_data = None
                    if addr_type == "Paytopubkeyhash":                
                        witness_data = []
                    elif addr_type == "Paytowitnesspubkeyhash" or addr_type == "Paytowitnessscripthash":     
                        witness_data = addfunctions.witness_data_field()
                    elif addr_type == "Paytoscripthash":
                        if random.randint(0, 1) == 1:
                            witness_data = addfunctions.witness_data_field()
                        else: witness_data = []

                    string = str(utxo.pointer) + str(pk.to_bytes()) + str(tx_out)
                    message = build_message(string)
                    signature = sk.sign(message)

                    tx_in.append(Vin(utxo.pointer,signature,pk.to_bytes(),sequence,witness_data))

            updated_senders_list = updated_senders

        else:  
            
            sender_counts=Counter(senders)
            result=dict(sender_counts) 
            repeat_peers_dict = {key:value for key,value in result.items()if value > 1}   

            if repeat_peers_dict:  
                repeat_keys_list = list(repeat_peers_dict.keys())
                values_list = list(repeat_peers_dict.values())   
                no_repeat_list = list(filter(lambda x: x not in repeat_keys_list, senders))   

                senders_remove_duplicate_list = repeat_keys_list + no_repeat_list      

                for current_index,sender in enumerate(repeat_keys_list): 
                    utxos,balance = sender.get_utxo(),sender.get_balance()

                    if balance == 0:    
                        logger.info('no enough money for transaction for {0}(pid = {1})'.format(sender,sender.pid))
                        return
      
                    repeat_values = values_list[current_index]
                    n_values.append(repeat_values)
                    for j,utxo in enumerate(utxos):
                        need_to_spend += utxo.vout.value
                        need_to_spend_l.append(utxo.vout.value)
                        if j == repeat_values - 1:
                            break

 
                for sender in no_repeat_list:  
                    utxos,balance = sender.get_utxo(),sender.get_balance()

                    if balance == 0:    
                        logger.info('no enough money for transaction for {0}(pid = {1})'.format(sender,sender.pid))
                        return

                    n_values.append(1)
                    need_to_spend += utxos[0].vout.value
                    need_to_spend_l.append(utxos[0].vout.value)

                if need_to_spend != 0:
                    value = need_to_spend
                    fee = value*0.0001     
                    multi_value = need_to_spend - fee

                
                if len(receivers) == 1 and simchain.network.complex_flag == True: 
                    vout_num_complex = simchain.network.vout_num_used_complex   

                    receiver = receivers[0]
                    for k in range(vout_num_complex):
                        if random.randint(1,10) is not 1:       
                            receiver.wallet.generate_keys()   
                        to_addr = receiver.wallet.addrs[-1]

                        if to_addr not in addfunctions.addr_type_dict:
                            addr_type = addfunctions.Address_type()                     
                            addfunctions.addr_type_dict.update({to_addr: addr_type})     
                        else: addr_type = addfunctions.addr_type_dict.get(to_addr)      

                        if k != int(vout_num_complex) -1:
                            value1 = random.uniform(0.00001*value, (multi_value)/int(vout_num_complex))   
                            tx_out += [Vout(to_addr,value1,addr_type)]
                            m_value += value1
                        else: tx_out += [Vout(to_addr,multi_value-m_value,addr_type)]

                else:  
                    for k,receiver in enumerate(receivers):
                        if random.randint(1,10) is not 1:       
                            receiver.wallet.generate_keys()  
                        to_addr = receiver.wallet.addrs[-1]

                        if to_addr not in addfunctions.addr_type_dict:
                            addr_type = addfunctions.Address_type()                    
                            addfunctions.addr_type_dict.update({to_addr: addr_type})     
                        else: addr_type = addfunctions.addr_type_dict.get(to_addr)       

                        if k != len(receivers) -1:
                            value1 = random.uniform(0.00001*value, (multi_value)/len(receivers))  
                            tx_out += [Vout(to_addr,value1,addr_type)]
                            m_value += value1
                        else: tx_out += [Vout(to_addr,multi_value-m_value,addr_type)]

                sequence = addfunctions.sequence_number()   
                for index,sender in enumerate(senders_remove_duplicate_list):
                    wallet = sender.wallet
                    utxos = sender.get_utxo()
                    n = n_values[index]
                    for utxo in utxos[:n]:
                        UTxo.append(utxo)
                        addr = utxo.vout.to_addr
                        addr_type = utxo.vout.addr_type
                        idx = wallet.addrs.index(addr)
                        sk,pk = wallet.keys[idx].sk,wallet.keys[idx].pk

                        witness_data = None
                        if addr_type == "Paytopubkeyhash":               
                            witness_data = []
                        elif addr_type == "Paytowitnesspubkeyhash" or addr_type == "Paytowitnessscripthash":   
                            witness_data = addfunctions.witness_data_field()
                        elif addr_type == "Paytoscripthash":
                            if random.randint(0, 1) == 1:
                                witness_data = addfunctions.witness_data_field()
                            else: witness_data = []

                        string = str(utxo.pointer) + str(pk.to_bytes()) + str(tx_out)
                        message = build_message(string)
                        signature = sk.sign(message)

                        tx_in.append(Vin(utxo.pointer,signature,pk.to_bytes(),sequence,witness_data))

                updated_senders_list = senders_remove_duplicate_list

            else:
                for sender in senders:
                    utxos,balance = sender.get_utxo(),sender.get_balance()

                    if balance == 0:   
                        logger.info('no enough money for transaction for {0}(pid = {1})'.format(sender,sender.pid))
                        return

                    need_to_spend += utxos[0].vout.value
                    need_to_spend_l.append(utxos[0].vout.value)

                if need_to_spend != 0:
                    value = need_to_spend
                    fee = value*0.0001    
                    multi_value = need_to_spend-fee

                if len(receivers) == 1 and simchain.network.complex_flag == True:  
                    vout_num_complex = simchain.network.vout_num_used_complex   

                    receiver = receivers[0]
                    for k in range(vout_num_complex):
                        if random.randint(1,10) is not 1:       
                            receiver.wallet.generate_keys()   

                        to_addr = receiver.wallet.addrs[-1]

                        if to_addr not in addfunctions.addr_type_dict:
                            addr_type = addfunctions.Address_type()                    
                            addfunctions.addr_type_dict.update({to_addr: addr_type})     
                        else: addr_type = addfunctions.addr_type_dict.get(to_addr)       

                        if k != int(vout_num_complex) -1:
                            value1 = random.uniform(0.00001*value, (multi_value)/int(vout_num_complex))   
                            tx_out += [Vout(to_addr,value1,addr_type)]
                            m_value += value1
                        else: tx_out += [Vout(to_addr,multi_value-m_value,addr_type)]

                else:  
                    for k,receiver in enumerate(receivers):
                        if random.randint(1,10) is not 1:       
                            receiver.wallet.generate_keys()   
                        to_addr = receiver.wallet.addrs[-1]

                        if to_addr not in addfunctions.addr_type_dict:
                            addr_type = addfunctions.Address_type()                     
                            addfunctions.addr_type_dict.update({to_addr: addr_type})     
                        else: addr_type = addfunctions.addr_type_dict.get(to_addr)       

                        if k != len(receivers) -1:
                            value1 = random.uniform(0.00001*value, (multi_value)/len(receivers))  
                            tx_out += [Vout(to_addr,value1,addr_type)]
                            m_value += value1
                        else: tx_out += [Vout(to_addr,multi_value-m_value,addr_type)]


                sequence = addfunctions.sequence_number()  
                for sender in senders:
                    wallet = sender.wallet
                    utxos = sender.get_utxo()
                    for utxo in utxos[:1]:
                        UTxo.append(utxos[:1])
                        addr = utxo.vout.to_addr
                        addr_type = utxo.vout.addr_type
                        idx = wallet.addrs.index(addr)
                        sk,pk = wallet.keys[idx].sk,wallet.keys[idx].pk

                        witness_data = None
                        if addr_type == "Paytopubkeyhash":                
                            witness_data = []
                        elif addr_type == "Paytowitnesspubkeyhash" or addr_type == "Paytowitnessscripthash":   
                            witness_data = addfunctions.witness_data_field()
                        elif addr_type == "Paytoscripthash":
                            if random.randint(0, 1) == 1:
                                witness_data = addfunctions.witness_data_field()
                            else: witness_data = []

                        string = str(utxo.pointer) + str(pk.to_bytes()) + str(tx_out)
                        message = build_message(string)
                        signature = sk.sign(message)

                        tx_in.append(Vin(utxo.pointer,signature,pk.to_bytes(),sequence,witness_data))

                updated_senders_list = senders
                n_values = [1] * len(senders)


    normal_tx_num += 1
    print(str(tx_in),file=detail_data)
    print("vin_sz: "+ str(len(tx_in)),file=detail_data)
    print(str(tx_out),file=detail_data)
    print("vout_sz: "+str(len(tx_out)),file=detail_data)
    print(str(UTxo),file=detail_data)
    tx_version = addfunctions.tx_version()

    locktime = None
    if sequence == 4294967295:        
        locktime = 0
    elif sequence == 4294967294:
        locktime = addfunctions.generate_locktime_data()
    else:
        if random.random() < 0.28167753191759468926:    
            locktime = addfunctions.generate_locktime_data()
        else: locktime = 0

    print('version: {0}'.format(tx_version),file=detail_data)     
    print('locktime: {0}'.format(locktime),file=detail_data)     
    print("fee: "+str(fee),file=detail_data)    

    #print('timestamp: {0}'.format(sender.blockchain[-1].timestamp),file=detail_data)     #新加timestamp
    #print('timestamp: {0}'.format(int(time.mktime(sender.blockchain[-1].timestamp.timetuple()))),file=detail_data)   #新加timestamp


    return tx_in,tx_out,fee

def create_consolidation0_tx(peer, to_addr, value) :
    global normal_tx_num,con_value  
    utxos,balance = peer.get_utxo(),peer.get_balance()
    fee,wallet = peer.fee,peer.wallet

    tx_in,tx_out = [],[]
    if balance == 0:    
        logger.info('no enough money for transaction for {0}(pid = {1})'.format(peer,peer.pid))
        return

    need_to_spend = 0
    n, no_use_num = UTXO_value()

    if n > len(utxos): n = len(utxos)  

    for j,utxo in enumerate(utxos):
        need_to_spend += utxo.vout.value
        if j == n-1:
            break
    
    if need_to_spend != 0:
        value = need_to_spend  
        fee = need_to_spend * 0.0001   
        con_value = need_to_spend-fee   

        if to_addr not in addfunctions.addr_type_dict:
            addr_type = addfunctions.Address_type()                       
            addfunctions.addr_type_dict.update({to_addr: addr_type})     
        else: addr_type = addfunctions.addr_type_dict.get(to_addr)       
        tx_out += [Vout(to_addr,value-fee,addr_type)]   

    sequence = addfunctions.sequence_number()  
    for utxo in utxos[:n]:
        addr = utxo.vout.to_addr
        addr_type = utxo.vout.addr_type
        idx = wallet.addrs.index(addr)
        sk,pk = wallet.keys[idx].sk,wallet.keys[idx].pk

        witness_data = None
        if addr_type == "Paytopubkeyhash":             
            witness_data = []
        elif addr_type == "Paytowitnesspubkeyhash" or addr_type == "Paytowitnessscripthash":   
            witness_data = addfunctions.witness_data_field()
        elif addr_type == "Paytoscripthash":
            if random.randint(0, 1) == 1:
                witness_data = addfunctions.witness_data_field()
            else: witness_data = []

        string = str(utxo.pointer) + str(pk.to_bytes()) + str(tx_out)
        message = build_message(string)
        signature = sk.sign(message)

        tx_in.append(Vin(utxo.pointer,signature,pk.to_bytes(),sequence,witness_data))

    normal_tx_num += 1

    print(str(tx_in),file=detail_data)
    print("vin_sz: "+ str(len(tx_in)),file=detail_data)
    print(str(tx_out),file=detail_data)
    print("vout_sz: "+str(len(tx_out)),file=detail_data)
    print(str(utxos[:n]),file=detail_data)
    tx_version = addfunctions.tx_version()

    locktime = None
    if sequence == 4294967295:          
        locktime = 0
    elif sequence == 4294967294:
        locktime = addfunctions.generate_locktime_data()
    else:
        if random.random() < 0.28167753191759468926:   
            locktime = addfunctions.generate_locktime_data()
        else: locktime = 0

    print('version: {0}'.format(tx_version),file=detail_data)     
    print('locktime: {0}'.format(locktime),file=detail_data)    
    print("fee: "+str(fee),file=detail_data)     
    #print('timestamp: {0}'.format(peer.blockchain[-1].timestamp),file=detail_data)     
    #print('timestamp: {0}'.format(int(time.mktime(peer.blockchain[-1].timestamp.timetuple()))),file=detail_data)   

    return tx_in,tx_out,fee


def create_complex0_tx(peer, to_addr, value):
    global normal_tx_num, com_value
    utxos, balance = peer.get_utxo(), peer.get_balance()
    fee, wallet = peer.fee, peer.wallet
    m_value = 0

    tx_in, tx_out = [], []
    if balance == 0:  
        logger.info('no enough money for transaction for {0}(pid = {1})'.format(peer, peer.pid))
        return

    need_to_spend = 0
    n, vout_num = UTXO_value()

    if n > len(utxos): n = len(utxos)  

    for j,utxo in enumerate(utxos):
        need_to_spend += utxo.vout.value
        if j == n-1:
            break
  
   
    if need_to_spend != 0:
        value = need_to_spend
        fee = value * 0.0001   
        com_value = value - fee   

    receiver = simchain.network.Receiver
    for k in range(vout_num):
        if random.randint(1,10) is not 1:       
            receiver.wallet.generate_keys()  
        to_addr = receiver.wallet.addrs[-1]

        if to_addr not in addfunctions.addr_type_dict:
            addr_type = addfunctions.Address_type()                    
            addfunctions.addr_type_dict.update({to_addr: addr_type})      
        else: addr_type = addfunctions.addr_type_dict.get(to_addr)     

        if k != int(vout_num) -1:
            value1 = random.uniform(0.00001*value, (com_value)/int(vout_num))   
            tx_out += [Vout(to_addr,value1,addr_type)]
            m_value += value1
        else: tx_out += [Vout(to_addr,com_value-m_value,addr_type)]


    sequence = addfunctions.sequence_number()   
    for utxo in utxos[:n]:
        addr = utxo.vout.to_addr
        addr_type = utxo.vout.addr_type
        idx = wallet.addrs.index(addr)
        sk, pk = wallet.keys[idx].sk, wallet.keys[idx].pk

        witness_data = None
        if addr_type == "Paytopubkeyhash":                 
            witness_data = []
        elif addr_type == "Paytowitnesspubkeyhash" or addr_type == "Paytowitnessscripthash":     
            witness_data = addfunctions.witness_data_field()
        elif addr_type == "Paytoscripthash":
            if random.randint(0, 1) == 1:
                witness_data = addfunctions.witness_data_field()
            else: witness_data = []

        string = str(utxo.pointer) + str(pk.to_bytes()) + str(tx_out)
        message = build_message(string)
        signature = sk.sign(message)

        tx_in.append(Vin(utxo.pointer,signature,pk.to_bytes(),sequence,witness_data))

    normal_tx_num += 1

    print(str(tx_in), file=detail_data)
    print("vin_sz: " + str(len(tx_in)), file=detail_data)
    print(str(tx_out), file=detail_data)
    print("vout_sz: " + str(len(tx_out)), file=detail_data)
    print(str(utxos[:n]), file=detail_data)
    tx_version = addfunctions.tx_version()

    locktime = None
    if sequence == 4294967295:         
        locktime = 0
    elif sequence == 4294967294:
        locktime = addfunctions.generate_locktime_data()
    else:        
        if random.random() < 0.28167753191759468926:   
            locktime = addfunctions.generate_locktime_data()
        else: locktime = 0

    print('version: {0}'.format(tx_version),file=detail_data)      
    print('locktime: {0}'.format(locktime),file=detail_data)   
    print("fee: "+str(fee),file=detail_data)    
    #print('timestamp: {0}'.format(peer.blockchain[-1].timestamp),file=detail_data)   
    #print('timestamp: {0}'.format(int(time.mktime(peer.blockchain[-1].timestamp.timetuple()))),file=detail_data)   

    return tx_in, tx_out, fee


def create_subtle_tx(nd,to_addr,value):
    pass

def choose_raondom_txs_from_pool(pool):
    n = len(pool)
    n = n if n < Params.MAX_TX_NUMBER_FOR_MINER else Params.MAX_TX_NUMBER_FOR_MINER
    candidates = random.sample(list(pool.keys()),n)
    return [pool.get(t) for t in candidates]

def choose_whole_txs_from_pool(pool):
    return list(pool.values())

# =============================================================================
#broadcast transactions  
# =============================================================================
    
def broadcast_tx(peers,current_tx):    
    rand,idxs,choice = random.uniform(0,1),range(len(peers)),[-1]
    number_of_verification = 0
    
    if rand < Params.SLOW_PEERS_IN_NETWORK:
        choice = [random.choice(idxs)]
    if rand < Params.SLOWER_PEERS_IN_NETWORK:
        choice = random.sample(idxs,k = 2)

    for i,peer in enumerate(peers): 
        if peer._delayed_tx:
            dice = random.uniform(0,1)
            if dice > Params.SLOW_PEERS_IN_NETWORK:
                fill_mem_pool(peer)
            
        if peer.verify_transaction(current_tx,peer.mem_pool):
            if (i in choice) and (not peer._delayed_tx):
                peer._delayed_tx = current_tx
                continue
            
            add_tx_to_mem_pool(peer,current_tx)  
            number_of_verification += 1 
            
        if peer.orphan_pool:
            check_orphan_tx_from_pool(peer)
            
    return number_of_verification


def check_orphan_tx_from_pool(peer):
    copy_pool = peer.orphan_pool.copy()
    for tx in copy_pool.values():
        if not verify_tx(tx,peer.mem_pool):
            return False
        add_tx_to_mem_pool(peer,tx)
        del peer.orphan_pool[tx.id]
    return True
            
# =============================================================================
#broadcast_block
# =============================================================================
    
def broadcast_winner_block(peers,block): 
    number_of_verification = 0
    for peer in peers: 
        if peer.verify_block(block):
            try_to_add_block(peer,block)
            number_of_verification += 1
    
    return number_of_verification
    
        
# =============================================================================
#UTXO functions
# =============================================================================

def find_utxos_from_txs(txs):
    return [UTXO(vout,Pointer(tx.id,i),tx.is_coinbase)
            for tx in txs for i,vout in enumerate(tx.tx_out)]
    
def find_utxos_from_block(txs):
    return [UTXO(vout,Pointer(tx.id,i),tx.is_coinbase,True,True)
            for tx in txs for i,vout in enumerate(tx.tx_out)]
    
def find_utxos_from_tx(tx):
    return [UTXO(vout,Pointer(tx.id,i),tx.is_coinbase)
            for i,vout in enumerate(tx.tx_out)]

def find_vout_pointer_from_txs(txs):
    return [Pointer(tx.id,i) for tx in txs for i,vout in enumerate(tx.tx_out)]
    
def find_vin_pointer_from_txs(txs):
    return [vin.to_spend for tx in txs for vin in tx.tx_in]
            

def confirm_utxos_from_txs(utxo_set,txs,allow_utxo_from_pool):
    if allow_utxo_from_pool:
        utxos = find_utxos_from_txs(txs[1:])
        add_utxo_from_block_to_set(utxo_set,txs)
        pointers = find_vout_pointer_from_txs(txs)
        return pointers,utxos
    else:
        utxos = find_utxos_from_block(txs)
        pointers = find_vout_pointer_from_txs(txs)
        add_utxos_to_set(utxo_set,utxos)
        return pointers,[]
    
def remove_spent_utxo_from_txs(utxo_set,txs):
    pointers = find_vin_pointer_from_txs(txs)
    utxos = delete_utxo_by_pointers(utxo_set,pointers)
    return utxos

def delete_utxo_by_pointers(utxo_set,pointers):
    utxos_from_vins = []
    for pointer in pointers:
        if pointer in utxo_set:
            utxos_from_vins.append(utxo_set[pointer])
            del utxo_set[pointer]
    return utxos_from_vins
            
def sign_utxo_from_tx(utxo_set,tx):
    for vin in tx.tx_in:
        try: 
            pointer = vin.to_spend
            utxo = utxo_set[pointer]
            utxo = utxo._replace(unspent = False)
            utxo_set[pointer] = utxo
        except KeyError:
            print("KeyError")
            print(tx.tx_in)
            print(pointer)

def sign_utxo_from_tx_multi(utxo_set,tx,n_values,index):
    m = 0
    for i in range(index+1):
        m += n_values[i]
    n = m - n_values[index]
    for vin in tx.tx_in[n:m]:
        try: 
            pointer = vin.to_spend
            utxo = utxo_set[pointer]
            utxo = utxo._replace(unspent = False)
            utxo_set[pointer] = utxo
        except KeyError:
            print("KeyError")
            print(tx.tx_in)
            print(pointer)

                    
def add_utxos_from_tx_to_set(utxo_set,tx):
    utxos = find_utxos_from_tx(tx)
    for utxo in utxos:
        utxo_set[utxo.pointer] = utxo
        
        
def add_utxo_from_txs_to_set(utxo_set,txs):
    utxos = find_utxos_from_txs(txs)
    add_utxos_to_set(utxo_set,utxos)

def add_utxo_from_block_to_set(utxo_set,txs):
    utxos = find_utxos_from_block(txs)
    add_utxos_to_set(utxo_set,utxos)
    
def add_utxos_to_set(utxo_set,utxos):
    if isinstance(utxos,dict):
        utxos = utxos.values()
        
    for utxo in utxos:
        utxo_set[utxo.pointer] = utxo

def remove_utxos_from_set(utxo_set,pointers):
    for pointer in pointers:
        if pointer in utxo_set:
            del utxo_set[pointer]
    
# =============================================================================
#verify transaction
# =============================================================================
        
def verify_tx(peer,tx,pool = {}):
    
    if not verify_tx_basics(tx):
        return False

    if double_payment(pool,tx):
        logger.info('{0} double payment'.format(tx))
        return False
    
    available_value = 0

    for vin in tx.tx_in:
        utxo = peer.utxo_set.get(vin.to_spend)
        
        if not utxo:
            logger.info(
                    '{0}(pid={1}) find the orphan transaction {2}'.format(peer,peer.pid,tx)
                    )
            peer.orphan_pool[tx.id] = tx
            return False

        if not verify_signature(peer,vin,utxo,tx.tx_out):
            logger.info('signature does not match for {0}'.format(tx))
            return False
    
        available_value += utxo.vout.value
        
    if available_value < sum(vout.value for vout in tx.tx_out):
        logger.info(
                '{0} no enough available value to spend by {1}(pid={2})'.format(tx,peer,peer.pid)
                )
        return False

    return True

def verify_multi_tx(peer,tx,pool = {}):
    
    if not verify_tx_basics(tx):
        return False

    if double_payment(pool,tx):
        logger.info('{0} double payment'.format(tx))
        return False
    
    available_value = 0

    for vin in tx.tx_in:
        utxo = peer.utxo_set.get(vin.to_spend)
        
        if not utxo:
            logger.info(
                    '{0}(pid={1}) find the orphan transaction {2}'.format(peer,peer.pid,tx)
                    )
            peer.orphan_pool[tx.id] = tx
            return False

        if not verify_signature(peer,vin,utxo,tx.tx_out):
            logger.info('signature does not match for {0}'.format(tx))
            print(str(peer))
            return False
    
        available_value += utxo.vout.value
        
    if available_value < sum(vout.value for vout in tx.tx_out):
        logger.info(
                '{0} no enough available value to spend by {1}(pid={2})'.format(tx,peer,peer.pid)
                )
        return False

    return True

def verify_signature(peer,vin,utxo,tx_out):
    script = check_script_for_vin(vin,utxo,peer.key_base_len)
    if not script:
        return False
    string = str(vin.to_spend) + str(vin.pubkey) + str(tx_out)
    message = build_message(string)
    peer.machine.set_script(script,message)
    return peer.machine.run()


def check_script_for_vin(vin,utxo,baselen):
    sig_script,pubkey_script = vin.sig_script,utxo.pubkey_script
    double,fourfold = int(baselen*2),int(baselen*4)
    if len(sig_script) != fourfold:
        return False
    sig_scrip = [sig_script[:double],sig_script[double:]]
    try:
        pubkey_script = pubkey_script.split(' ')
    except Exception:
        return False

    return sig_scrip+pubkey_script


def verify_signature_for_vin(vin,utxo,tx_out):
    pk_str,signature = vin.pubkey,vin.signature
    to_addr = utxo.vout.to_addr
    string = str(vin.to_spend) + str(pk_str) + str(tx_out)
    message = build_message(string)
    pubkey_as_addr = convert_pubkey_to_addr(pk_str)
    verifying_key = VerifyingKey.from_bytes(pk_str)

    if pubkey_as_addr != to_addr:
        return False
    
    if not verifying_key.verify(signature, message):
        return False

    return True

    
def verify_tx_basics(tx):
    if not isinstance(tx,Tx):
        logger.info('{0} is not Tx type'.format(tx))
        return False
    
    if (not tx.tx_out) or (not tx.tx_in):
        logger.info('{0} Missing tx_out or tx_in'.format(tx))
        return False
    return True

def double_payment(pool,tx):
    S = SENDERS   
    if len(S)>1:
        if tx.id in pool:
            return set()

    else:
        if tx.id in pool:
            return True
        a = {vin.to_spend for vin in tx.tx_in}
        b = {vin.to_spend for tx in pool.values() for vin in tx.tx_in}
        return a.intersection(b)

def verify_coinbase(tx,reward):
    if not isinstance(tx,Tx):
        return False
    if not tx.is_coinbase:
        return False

    if (not (len(tx.tx_out) == 1)) or (tx.tx_out[0].value != reward):
        return False
    return True

# =============================================================================
#verify block
# =============================================================================
    
def verify_winner_block(peer,block):

    if not isinstance(block,Block):
        return False
    
    if int(block.hash, 16) > caculate_target(block.bits):
        logger.info('{0} wrong answer'.format(block))
        return False
    
    txs = block.txs
    if not isinstance(txs,list) and \
       not isinstance(txs,tuple):
        logger.info('incorrect txs type in {0}'.format(block))
        return False
    
    if len(txs) < 2:
        logger.info('no enough txs for txs {0}'.format(block))
        return False

    block_txs = txs[1:]
    rewards = peer.get_block_reward()+peer.calculate_fees(block_txs)

    if not verify_coinbase(block.txs[0],rewards):
        logger.info('{0} coinbase incorrect'.format(block))
        return False

    
    if double_payment_in_block_txs(block_txs):
        logger.info('double payment in {0}'.format(block))
        return False

    for tx in block_txs:
        if not verify_tx(peer,tx):
            return False
    return True

def double_payment_in_block_txs(txs):
    a = {vin.to_spend for tx in txs for vin in tx.tx_in}
    b = [vin.to_spend for tx in txs for vin in tx.tx_in]
    return len(a) != len(b)
    
    
# =============================================================================
#try to receive a block
# =============================================================================
    
def locate_block_by_hash(peer,block_hash):
    for height,block in enumerate(peer.blockchain):
        if block.hash == block_hash:
            return height+1
    return None
        
def try_to_add_block(peer,block):  
    prev_hash = block.prev_block_hash                                                  
    height = locate_block_by_hash(peer,prev_hash)
    if not height:
        logger.info('{0}(pid={1} find a orphan {2})'.format(peer,peer.pid,block))
        peer.orphan_block.append(block)
        return False
    
    if height == peer.get_height():
        peer.blockchain.append(block)
        recieve_new_prev_hash_block(peer,block.txs)
        return True
    
    elif height == peer.get_height()-1:
        b1,b2 = peer.blockchain[-1],block
        a,b = int(b1.hash,16),int(b2.hash,16)
        if a < b:
            return False
        else:
            peer.blookchian.pop()
            peer.blockchain.append(block)
            recieve_exist_prev_hash_block(peer,block.txs)
    else:
        return False
    
def check_orphan_block(peer):
    pass

def recieve_new_prev_hash_block(peer,txs):
    utxo_set,pool = peer.utxo_set,peer.mem_pool
    allow_utxo_from_pool = peer.allow_utxo_from_pool
    peer._utxos_from_vins = remove_spent_utxo_from_txs(utxo_set,txs)
    peer._pointers_from_vouts,peer._utxos_from_vouts = confirm_utxos_from_txs(
            utxo_set,txs,allow_utxo_from_pool
            )
    peer._txs_removed = remove_txs_from_pool(pool,txs)
    
    
def recieve_exist_prev_hash_block(peer,txs):
    roll_back(peer)
    recieve_new_prev_hash_block(peer,txs)

def roll_back(peer):
    peer.mem_pool.update(peer._txs_removed)
    add_utxos_to_set(peer.utxo_set,peer._utxos_from_vins)
    remove_utxos_from_set(peer.utxo_set,peer._pointers_from_vouts)
    add_utxos_to_set(peer.utxo_set,peer._utxos_from_vouts)
    peer._utxos_from_vins = []
    peer._pointers_from_vouts = []
    peer._utxos_from_vouts = []
    peer._txs_removed = {}
    
def compare_block_by_hash(a,b):
    pass
        
# =============================================================================
#transactions functions
# =============================================================================
    
def get_unknown_txs_from_block(mem_pool,txs):
    substraction = {}
    for tx in txs:
        if tx not in mem_pool.values():
            substraction[tx.id] = tx
    return substraction


def fill_mem_pool(peer):
    add_tx_to_mem_pool(peer,peer._delayed_tx)
    peer._delayed_tx = None
        

def remove_txs_from_pool(pool,txs):
    n_txs = {}
    for tx in txs:
        if tx.id in pool:
            n_txs[tx.id] = tx
            del pool[tx.id]
    return n_txs
                
def add_txs_to_pool(pool,txs):
    for tx in txs:
        pool[tx.id] = tx
           
def add_tx_to_mem_pool(peer,tx):
    peer.mem_pool[tx.id] = tx
    if peer.allow_utxo_from_pool:
        add_utxos_from_tx_to_set(peer.utxo_set,tx)

def calculate_next_block_bits(local_time,prev_height,prev_bits):
    flag = (prev_height + 1) % Params.TOTAL_BLOCKS
    if flag != 0:
        return prev_bits
    
    count = ((prev_height + 1)//Params.TOTAL_BLOCKS)*Params.TOTAL_BLOCKS
    actual_time_taken = local_time[:prev_height] - local_time[:count]
    
    if actual_time_taken < Params.PERIOD_FOR_TOTAL_BLOCKS:
        return prev_bits + 1
    elif actual_time_taken > Params.PERIOD_FOR_TOTAL_BLOCKS:
        return prev_bits - 1
    else:
        return prev_bits


          
if __name__ == '__main__':
    a,b = Peer(),Peer()
