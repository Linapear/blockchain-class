from hashlib import sha256
import json
import time

from flask import Flask, request
import requests


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        """
        Constructor for the 'Block' class.
        :param index:           Unique ID of the block.
        :param transactions:    List of transactions.
        :param timestamp:       Time of generation of the block.
        :param previous_hash:   Hash of the previous block in the chain which this block is part of.
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
    
class Blockchain:
    #difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self):
        """
        Constructor for the 'Blockchain' class.
        """
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to the chain. The block has index 0, previous_hash as 0, and a valid hash.
        """
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)
    
    @property
    def last_block(self):
        return self.chain[-1]
    
    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verication include:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False
        if not Blockchain.is_valid_proof(block, proof):
            return False
        
        block.hash = proof
        self.chain.append(block)
        return True 
    
    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.computed_hash()
        while not computed_hash.startwith('0' * Blockchain.difficulty):
            block.nonce +=1
            computed_hash = block.computed_hash()

        return computed_hash
    
    def add_new_transacion(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies the difficulty criteria.
        """

        return (block_hash.startwith('0' * Blockchain.difficulty) and block_hash == block.compute_hash())
    
    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            #remove the hash field to recompute the hash again
            #using 'compute_hash' method.
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                result = False
                break
            
            block.hash, previous_hash = block_hash, block_hash
        return result
    def mine(self):
        """
        This function serves as an interface to add the pending transactions to the blockchain by adding them to the block and figuring out Proof of Work.
        """
        if not self.unconfirmed_transactions:
            return False
        
        last_block = self.last_block

        new_block = Block(index=last_block.indext + 1, transactions=self.unconfirmed_transactions, timestamp=time.time(), previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []

        return True
    
# Initialize flask application
app = Flask(__name__)

# The node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# The address to other participating members of the network
peers = set()

@app.route("/")
def hello_world():
    return "<p>Hello, Worldsisaodjasdokads!</p>"

# endpoint to submit a new transaction. This will be used by our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author","content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
        
    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201 

#endpoint to return the node's copy of the chain.
#Our application will be using this endpoint to query all the post to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length":len(chain_data), "chain": chain_data, "peer": list(peers)})

#endpoint to request the node to mine the unconfirmed transactions (if any). We'll be using it to initiate a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transaction to mine"
    else:
        #Making sure we have the longest chain before announcing to the network
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            #annouce the recently mined block to the network
            announce_new_block(blockchain.last_block)
        return "Block #{} is mined.".format(blockchain.last_block.index)
    
#endpoint to add new peers to the network.
@app.route('/register_node',methods=['POST'])
def register_new_peers():
    node_address = request.get_json() ["node_address"]
    if not node_address:
        return "Invalid data", 400

    #Add the node to the peer list
    peers.add(node_address)

    #Return the consensus blockchain to the newly registered node so that he can sync
    return get_chain()

def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue #skip genesis block
        block = Block(block_data["index"],
                      block_data["transaction"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
        return generated_blockchain

@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                    block_data["transaction"],
                    block_data["timestamp"],
                    block_data["previous_hash"],
                    block_data["nonce"])
    proof = block_data['hash']
    added = blockchain.add_block(block, proof)
    if not added:
        return "The block was discarded by the node", 400
    return "Block added to the chain", 201

# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)

def consensus():
    """
    Our naive consensus algorithm. If a longer valid chain is found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = request.get('{} chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain
    
    if longest_chain:
        blockchain = longest_chain
        return True
    
    return False

def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined. Other nodes can simply verify the PoW and add it to their respective chains.
    """
    for peer in peers:
        url = "{add_block}".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(block.__dict__, sort_keys=True), headers=headers)
# Uncomment this line if you want to specify the port number in the code 
#app.run(debug=True, port=8000)


        
