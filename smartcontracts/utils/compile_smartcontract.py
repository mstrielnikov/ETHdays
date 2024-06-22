import pathlib

from solcx import compile_standard, install_solc, get_installable_solc_versions
import json, os
from web3 import Web3


address_str = os.getenv("METAMASK_WALLET_ADDRESS")
private_key_str = os.getenv("METAMASK_WALLET_PRIVATE_KEY")

# available_versions = get_installable_solc_versions()
# print("Available solc versions:", available_versions)

address = Web3.to_checksum_address(address_str)

private_key = private_key_str

w3 = Web3(Web3.HTTPProvider("https://rpc2.sepolia.org"))

chain_id = 11155111

sol_smartcontract_filepath = "../../solidity/contracts/intent.sol"

if not pathlib.Path.exists(pathlib.Path(sol_smartcontract_filepath)):
    raise FileNotFoundError(f"Smartcontract file path not found: {sol_smartcontract_filepath}")

with open(sol_smartcontract_filepath, "r") as file:
    solidity_file = file.read()

    install_solc("0.8.2")
    print("installed")

    compiled_sol = compile_standard(
        {
                    "language": "Solidity",
                    "sources": {"intent.sol": {"content": solidity_file}},
                    "settings": {
                        "outputSelection": {
                            "*": {
                                "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"] # output needed to interact with and deploy contract
                            }
                        }
                    },
                },
        solc_version="0.8.2",
    )
    print("Compiled solidity contract:")
    print(50*"=")
    print(compiled_sol)
    print(50 * "=")

bytecode = compiled_sol["contracts"]["intent.sol"]["Intent"]["evm"]["bytecode"]["object"]

print("Compiled solidity contract bytecode:")
print(50 * "=")
print(bytecode)
print(50 * "=")

abi = json.loads(compiled_sol["contracts"]["intent.sol"]["Intent"]["metadata"])["output"]["abi"]

print("abi:")
print(50 * "=")
print(abi)
print(50 * "=")

# Create the contract in Python
ContactList = w3.eth.contract(abi=abi, bytecode=bytecode)

# Get the number of latest transaction
nonce = w3.eth.get_transaction_count(address)

transaction = ContactList.constructor().build_transaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": address,
        "nonce": nonce,
    }
)

# Sign the transaction
sign_transaction = w3.eth.account.sign_transaction(transaction, private_key=private_key)
print("Deploying Contract!")

# Send the transaction
transaction_hash = w3.eth.send_raw_transaction(sign_transaction.rawTransaction)

# Wait for the transaction to be mined, and get the transaction receipt
print("Waiting for transaction to finish...")

transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
print(f"Done! Contract deployed to {transaction_receipt}")

# contact_list = w3.eth.contract(address=transaction_receipt., abi=abi)
