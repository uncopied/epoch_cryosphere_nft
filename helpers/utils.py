import base64
import json

from algosdk import encoding, mnemonic, account, v2client
from algosdk.v2client.algod import AlgodClient


def get_algod_client():
    token = ''
    # endpoint = 'https://node.algoexplorerapi.io'
    endpoint = 'https://node.testnet.algoexplorerapi.io'
    headers = ''
    return v2client.algod.AlgodClient(token, endpoint, headers)


# wait until the transaction is confirmed before proceeding
def wait_for_confirmation(algod_client: AlgodClient, txn_id: str):
    last_round = algod_client.status().get('last-round')
    txn_info = algod_client.pending_transaction_info(txn_id)
    while not (txn_info.get('confirmed-round') and txn_info.get('confirmed-round') > 0):
        last_round += 1
        algod_client.status_after_block(last_round)
        txn_info = algod_client.pending_transaction_info(txn_id)
    print(f'transaction {txn_id} confirmed in round {txn_info.get("confirmed-round")}.')
    return txn_info


# prints created asset for account and asset_id
def print_created_asset(algod_client: AlgodClient, account: str, asset_id: int):
    account_info = algod_client.account_info(account)
    idx = 0
    for my_account_info in account_info['created-assets']:
        scrutinized_asset = account_info['created-assets'][idx]
        idx = idx + 1
        if scrutinized_asset['index'] == asset_id:
            print(f'asset ID: {scrutinized_asset["index"]}')
            print(json.dumps(my_account_info['params'], indent=4))
            break


# prints asset holding for account and asset_id
def print_asset_holding(algod_client: AlgodClient, account: str, asset_id: int):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = asset_id)
    # then loop thru the accounts returned and match the account you are looking for
    account_info = algod_client.account_info(account)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1
        if scrutinized_asset['asset-id'] == asset_id:
            print(f'account: {account}, asset ID: {scrutinized_asset["asset-id"]}')
            print(json.dumps(scrutinized_asset, indent=4))
            break


# creates asa metadata
def metadata_template(description, standard, external_url, attributes):
    metadata = {'description': description, 'standard': standard, 'external_url': external_url,
                'attributes': attributes}
    metadata_note = json.dumps(metadata).encode()
    return metadata_note


# compiles program source
def compile_program(algod_client: AlgodClient, source_code):
    compile_response = algod_client.compile(source_code)
    return base64.b64decode(compile_response['result'])


# converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


# converts a mnemonic passphrase into a public key
def get_public_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    public_key = account.address_from_private_key(private_key)
    return public_key


# converts 64-bit integer i to byte string
def int_to_bytes(i):
    return i.to_bytes(8, 'big')


# converts string s to byte string
def address_to_bytes(a):
    return encoding.decode_address(a)
