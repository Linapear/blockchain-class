from hashlib import sha256
import json
import time

from flask import Flask, request
import requests

from models.block import Block
from models.blockchain import Blockchain

# Initialize flask application
app = Flask(__name__)

# The node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# The address to other participating members of the network
peers = set()

@app.route("/")
def hello_world():
    return "<p>Hello, Blockchain!</p>"

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
    proof = block.compute_hash()
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


        
