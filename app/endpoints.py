from dataclasses import asdict

from flask import current_app, jsonify, request, Blueprint
from flask_pydantic import validate

from app.api_models import TransactionBody, ChainResponse

blueprint = Blueprint("blockchain", __name__)


def get_blockchain_instance():
    with current_app.app_context():
        return current_app.config["BLOCKCHAIN_INSTANCE"]


def get_node_identifier_instance():
    with current_app.app_context():
        return current_app.config["NODE_IDENTIFIER"]


@blueprint.route("/nodes", methods=["POST"])
def register_nodes():
    values = request.get_json()
    nodes = values.get("nodes")
    if not nodes:
        return "Error: Please supply a valid list of nodes", 400

    blockchain = get_blockchain_instance()
    for node in nodes:
        blockchain.register_node(node)

    response = {
        "message": "New nodes have been added",
        "total_nodes": list(blockchain.nodes)
    }
    return jsonify(response), 201


@blueprint.route("/nodes/resolve", methods=["GET"])
def consensus():
    blockchain = get_blockchain_instance()
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            "message": "Our chain was replaced",
            "new_chain": blockchain.chain
        }
    else:
        response = {
            "message": "Our chain is authoritative",
            "chain": blockchain.chain
        }
    return jsonify(response), 200


@blueprint.route("/mine", methods=["GET"])
def mine():
    print("Mining...")
    # Run the proof of work algorithm to get the next proof
    blockchain = get_blockchain_instance()
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # Receive a reward for  finding a proof
    # The sender is "0" to signify that this node has mined a new coin.
    node_identifier = get_node_identifier_instance()
    # TODO: The amount keeps on reducing after a period of time
    blockchain.add_new_transaction(sender="0", recipient=node_identifier, amount=1)
    # Forge the new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    print(last_block)
    print(previous_hash)
    block = blockchain.new_block(previous_hash, proof)

    response = {
        "message": "New Block Forged",
        "index": block.index,
        "transactions": [asdict(txn) for txn in block.transactions],
        "proof": block.proof,
        "previous_hash": block.previous_hash
    }
    return jsonify(response), 200


@blueprint.route("/transactions", methods=["GET", "POST"])
@validate(body=TransactionBody)
def add_transactions():
    values = request.get_json()
    # Create a new transaction
    blockchain = get_blockchain_instance()
    index = blockchain.add_new_transaction(values["sender"], values["recipient"], values["amount"])
    response = {"message": f"Transaction will be added to Block {index}"}
    return jsonify(response), 201


@blueprint.route("/chain", methods=["GET"])
@validate()
def get_block_chain():
    blockchain = get_blockchain_instance()
    return ChainResponse(
        chain=blockchain.chain,
        length=len(blockchain.chain)
    ), 200
