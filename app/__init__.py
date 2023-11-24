from uuid import uuid4

from flask import Flask

from app.blockchain import BlockChain
from app.endpoints import blueprint

app = Flask(__name__)
app.config["BLOCKCHAIN_INSTANCE"] = BlockChain()  # Create a blockchain instance and store it in app context
# Generate a globally unique address for this node
app.config["NODE_IDENTIFIER"] = node_identifier = str(uuid4()).replace("-", "")
app.register_blueprint(blueprint)
