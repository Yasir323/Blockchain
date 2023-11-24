from typing import List

from pydantic import BaseModel

from app.data_models import Block


class TransactionBody(BaseModel):
    sender: str
    recipient: str
    amount: float


class ChainResponse(BaseModel):
    chain: List[Block]
    length: int
