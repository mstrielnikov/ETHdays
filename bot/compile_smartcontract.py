from solcx import compile_standard, install_solc, get_installable_solc_versions
import json, os
from web3 import Web3


# available_versions = get_installable_solc_versions()
# print("Available solc versions:", available_versions)


def deploy_smartcontract(w3_provider, chain_id, private_key, address, sol_smartcontract_filepath):
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
        ContactList = w3_provider.eth.contract(abi=abi, bytecode=bytecode)

        # Get the number of latest transaction
        nonce = w3_provider.eth.get_transaction_count(address)

        transaction = ContactList.constructor().build_transaction(
            {
                "chainId": chain_id,
                "gasPrice": w3_provider.eth.gas_price,
                "from": address,
                "nonce": nonce,
            }
        )

        # Sign the transaction
        sign_transaction = w3_provider.eth.account.sign_transaction(transaction, private_key=private_key)
        print("Deploying Contract!")

        # Send the transaction
        transaction_hash = w3_provider.eth.send_raw_transaction(sign_transaction.rawTransaction)

        # Wait for the transaction to be mined, and get the transaction receipt
        print("Waiting for transaction to finish...")

        transaction_receipt = w3_provider.eth.wait_for_transaction_receipt(transaction_hash)
        print(f"Done! Contract deployed to {transaction_receipt}")

        # contact_list = w3.eth.contract(address=transaction_receipt., abi=abi)
        return transaction_hash


def get_eth_sepolia_scanner_link(transaction_hash):
    return f"https://sepolia.etherscan.io/tx/{transaction_hash}"