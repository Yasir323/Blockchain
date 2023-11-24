from dataclasses import dataclass
from typing import List


@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: float


@dataclass
class Block:
    index: int
    timestamp: float
    transactions: List[Transaction]
    proof: int
    previous_hash: str
