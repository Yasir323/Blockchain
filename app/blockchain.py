from dataclasses import asdict
import hashlib
import json
import time
from typing import List, Optional, Set
from urllib.parse import urlparse

import requests

from app.data_models import Block, Transaction


class BlockChain:
    """Responsible for managing the chain. It will store transactions and have some
    helper methods for adding new blocks to the chain."""

    def __init__(self):
        self.chain: List[Block] = []
        self.current_transactions: List[Transaction] = []
        self.nodes: Set[str] = set()
        self.create_genesis_block()
        self._num_zeros = 1  # TODO: This keeps increasing with time

    @property
    def num_zeros(self):
        return self._num_zeros

    @num_zeros.setter
    def num_zeros(self, n) -> None:
        self._num_zeros = n

    def create_genesis_block(self):
        self.new_block(previous_hash="1", proof=1)

    def new_block(self, previous_hash: str, proof: int) -> Block:
        """
        Creates a new block and adds it to the chain

        :param previous_hash: Hash of the last block in the chain
        :param proof: The proof given by the Proof of Work algorithm. Default: 1 - for Genesis Block.
        :return Block: The added new block
        """

        block = Block(
            index=len(self.chain) + 1,
            timestamp=time.time(),
            transactions=self.current_transactions,
            proof=proof,
            previous_hash=previous_hash if previous_hash else self.hash(self.chain[-1])
        )
        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def add_new_transaction(self, sender: str, recipient: str, amount: float) -> int:
        """
        Adds a new transaction to the list of transactions

        :param sender: Sender
        :param recipient: Receiver
        :param amount: Amount transferred
        :return: index of newly added transaction
        """
        self.current_transactions.append(Transaction(sender, recipient, amount))
        return self.last_block.index + 1

    @staticmethod
    def hash(block: Block) -> str:
        serialized_block = json.dumps(asdict(block), sort_keys=True).encode()
        return hashlib.sha256(serialized_block).hexdigest()

    @property
    def last_block(self) -> Optional[Block]:
        return self.chain[-1] if self.chain else None

    def proof_of_work(self, last_block: Block) -> int:
        """
        Simple Proof of Work Algorithm:
        - Find a number y such that hash(x * y) contains n trailing zeros, where x is the previous y.
        - x is the previous proof, and y is the new proof
        :param last_block: Last Block
        :return: New Proof
        """
        last_proof = last_block.proof
        last_hash = self.hash(last_block)
        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1
        return proof

    def valid_proof(self, last_proof: int, curr_proof: int, last_hash: str) -> bool:
        """
        Validate the Proof: Does hash(last_proof, curr_proof) contain n trailing zeros?
        :param last_proof: Previous Proof
        :param curr_proof: Current Proof
        :param last_hash: Hash of last block
        :return: True if valid, False otherwise
        """
        guess = f'{last_proof}{curr_proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[-self._num_zeros:] == "0" * self._num_zeros

    def register_node(self, address: str) -> None:
        """
        Add a new node to the list of nodes.
        :param address: IP Address of the node
        :return: None
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts a URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain: List[Block]) -> bool:
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True, if blockchain is valid else False
        """
        previous_block = chain[0]
        current_index = 1
        while current_index < len(chain):

            current_block = chain[current_index]
            print(previous_block)
            print(current_block)
            print("\n-----------------\n")

            # Check that the hash of the block ios correct
            last_block_hash = self.hash(previous_block)
            if current_block.previous_hash != last_block_hash:
                print("Previous hash not correct")
                return False

            # Check that the proof of work is correct
            if not self.valid_proof(previous_block.proof, current_block.proof, last_block_hash):
                print("Proof of work incorrect")
                return False

            previous_block = current_block
            current_index += 1
        return True

    def resolve_conflicts(self) -> bool:
        """
        Consensus Algorithm: It resolves conflicts by replacing our
        chain with the longest chain in the network

        :return: <bool> True if our chain was replaced, False otherwise
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = []
                for block in response.json()['chain']:
                    transactions = []
                    for transaction in block["transactions"]:
                        transactions.append(Transaction(
                            sender=transaction["sender"],
                            recipient=transaction["recipient"],
                            amount=transaction["amount"]
                        ))
                    chain.append(Block(
                        index=block["index"],
                        timestamp=block["timestamp"],
                        transactions=transactions,
                        proof=block["proof"],
                        previous_hash=block["previous_hash"]
                    ))

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False
