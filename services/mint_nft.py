import os

from algosdk import account
from algosdk.future import transaction
from dotenv import load_dotenv

from helpers.utils import get_algod_client

CID = 'QmRm2AFpxXTAoQ1wXXc8WmxvP8vXMJtNqgHrtU5vhvLQ8k'
IPFS_URL = 'ipfs://' + CID
print(f'ipfs url: {IPFS_URL}')

json_metadata_raw = open('../assets/mock_metadata.json')
json_metadata = json_metadata_raw.read()


def create_asa():
    private_key = os.getenv('CREATOR_SECRET')
    address = account.address_from_private_key(private_key)

    # create purestake algod_client to send requests
    algod_client = get_algod_client()
    params = algod_client.suggested_params()

    txn = transaction.AssetConfigTxn(
        sender=address,
        sp=params,
        total=1,
        default_frozen=False,
        unit_name='nft',
        asset_name='nancy baker mushroom cloud',
        manager=address,
        reserve='',
        freeze='',
        clawback='',
        url=IPFS_URL,
        # metadata_hash=json_metadata_hash,
        strict_empty_address_check=False,
        decimals=0,
        # TODO: add ARC69 metadata
        # note=json_metadata.encode(),
    )

    # sign transaction with our private key to confirm authorization
    signed_txn = txn.sign(private_key)
    print('signing transaction to create asa...')

    try:
        # send transaction to the network using purestake
        txn_id = algod_client.send_transaction(signed_txn)
        resp = transaction.wait_for_confirmation(algod_client, txn_id, 5)
        asset_id = resp['asset-index']

        with open('../.env', 'a') as f:
            f.write(f'ASSET_ID={asset_id}\n')
            f.flush()

        print(f'successfully sent transaction with id: {txn_id}')
        print(f'response: {resp}')
        print(f'asset ID: {asset_id}')
        print(f'ipfs url: https://ipfs.io/ipfs/{CID}')
        print(f'algoexplorer: https://testnet.algoexplorer.io/asset/{resp["asset-index"]}')

    except Exception as err:
        print(err)


if __name__ == '__main__':
    load_dotenv()
    create_asa()
