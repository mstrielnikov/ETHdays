from eth_tester import EthereumTester
import json


tester = EthereumTester()

test_account_list = tester.get_accounts()
print("Test account list addresses", test_account_list)

test_account_sender_address = test_account_list[0]
print("Test account sender address: ", test_account_sender_address)

test_account_sender_balance = tester.get_balance(test_account_sender_address)
print("Test account sender balance: ", test_account_sender_balance)

test_account_receiver_adress = test_account_list[1]
print("Test account receiver address: ", test_account_receiver_adress)

test_account_receiver_balance = tester.get_balance(test_account_sender_address)
print("Test account receiver balance: ", test_account_receiver_balance)

test_tx_address = tester.send_transaction({
     'from': test_account_sender_address,
     'to': test_account_receiver_adress,
     'gas': 30000,
     'value': 1,
     'max_fee_per_gas': 1000000000,
     'max_priority_fee_per_gas': 1000000000,
     'chain_id': 131277322940537,
     'access_list': (
         {
             'address': '0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae',
             'storage_keys': (
                 '0x0000000000000000000000000000000000000000000000000000000000000003',
                 '0x0000000000000000000000000000000000000000000000000000000000000007',
             )
         },
         {
             'address': '0xbb9bc244d798123fde783fcc1c72d3bb8c189413',
             'storage_keys': ()
         },
     )
 })

print("Test TX address: ", test_tx_address)

tx = tester.get_transaction_by_hash(test_tx_address)
print("View test transaction: \n", json.dumps(tx, indent=4))

tx_receipt = tester.get_transaction_receipt(test_tx_address)
print("View test transaction receipt: \n", json.dumps({key: str(value) for (key, value) in tx_receipt.items()}, indent=4))
