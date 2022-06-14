import os

from algosdk.future import transaction
from dotenv import load_dotenv

from helpers.consts import DefaultValues, AppArgs
from helpers.operations import (send_funds, setup_sale, buy_asset, buyer_execute_transfer, opt_in, set_clawback,
                                creator_claim_fees)
from helpers.utils import (get_public_key_from_mnemonic, get_private_key_from_mnemonic, int_to_bytes,
                           print_asset_holding,
                           wait_for_confirmation, get_algod_client)

load_dotenv()
cwd = os.getcwd()

mnemonics = [
    os.getenv('CREATOR_MNEMONIC'),
    os.getenv('BUYER_1_MNEMONIC'),
    os.getenv('BUYER_2_MNEMONIC'),
]

asset_id = int(os.getenv('ASSET_ID'))
app_id = int(os.getenv('APP_ID'))
app_address = os.getenv('APP_ADDRESS')

# for ease of reference, add account public and private keys to an accounts dict
accounts = {}
counter = 1
for i, m in enumerate(mnemonics):
    accounts[i] = {}
    accounts[i]['pk'] = get_public_key_from_mnemonic(m)
    accounts[i]['sk'] = get_private_key_from_mnemonic(m)

creator_private_key = get_private_key_from_mnemonic(os.getenv('CREATOR_MNEMONIC'))
buyer_1_private_key = get_private_key_from_mnemonic(os.getenv('BUYER_1_MNEMONIC'))
buyer_2_private_key = get_private_key_from_mnemonic(os.getenv('BUYER_2_MNEMONIC'))

creator_public_key = get_public_key_from_mnemonic(os.getenv('CREATOR_MNEMONIC'))
buyer_1_public_key = get_public_key_from_mnemonic(os.getenv('BUYER_1_MNEMONIC'))
buyer_2_public_key = get_public_key_from_mnemonic(os.getenv('BUYER_2_MNEMONIC'))

# create purestake algod_client
algod_client = get_algod_client()
params = algod_client.suggested_params()

# asset opt in
for wallet, value in accounts.items():
    # check if asset_id is in account 2 and 3's asset holdings prior to opt-in
    account_info = algod_client.account_info(accounts[wallet]['pk'])
    holding = None
    for index, my_account_info in enumerate(account_info['assets']):
        scrutinized_asset = account_info['assets'][index]
        if scrutinized_asset['asset-id'] == asset_id:
            holding = True
            break

    if holding:
        print(f'confirming asset is already in account for address: {accounts[wallet]["pk"]}')
    else:
        # use the AssetTransferTxn class to begin accepting an asset
        txn = transaction.AssetTransferTxn(
            sender=accounts[wallet]['pk'],
            sp=params,
            receiver=accounts[wallet]['pk'],
            amt=0,
            index=asset_id,
        )
        signed_txn = txn.sign(accounts[wallet]['sk'])
        txn_id = algod_client.send_transaction(signed_txn)
        print('txn_id:', txn_id)
        wait_for_confirmation(algod_client, txn_id)
        # check the asset holding for that account (should now show a holding with a balance of 0)
        print(f'asset opt-in for address: {accounts[wallet]["pk"]}')
        print_asset_holding(algod_client, accounts[wallet]['pk'], asset_id)

# fund application
send_funds(algod_client, creator_private_key, app_address)

# setting clawback to app
set_clawback(algod_client, creator_private_key, asset_id, app_address)
print(f'set clawback address to: {app_address}')

# opt into application
opt_in(algod_client, creator_private_key, app_id)
opt_in(algod_client, buyer_1_private_key, app_id)
opt_in(algod_client, buyer_2_private_key, app_id)

foreign_assets = [asset_id]

# create list of bytes for sale setup app args
sale_args = [AppArgs.setup_sale, int_to_bytes(DefaultValues.nft_price)]

print('---------------------------------- initiate purchase by buyer 1 ----------------------------------')
setup_txn_id = setup_sale(algod_client, creator_private_key, app_id, sale_args, foreign_assets)
print(f'setup sale transaction id: {setup_txn_id}')
buy_args = [AppArgs.buy, int_to_bytes(asset_id)]
# buyer posting buy transactions
buy_asset(algod_client, buyer_1_private_key, creator_public_key, app_id, buy_args, foreign_assets,
          DefaultValues.nft_price)
buyer_execute_args = [AppArgs.execute_transfer]

# buyer executing transfer
buyer_execute_transfer(algod_client, buyer_1_private_key, creator_public_key, app_id, buyer_execute_args,
                       foreign_assets)
print('---------------------------------- sale from creator to buyer 1 completed ----------------------------------')
print('creator:')
print_asset_holding(algod_client, creator_public_key, asset_id)
print('buyer 1:')
print_asset_holding(algod_client, buyer_1_public_key, asset_id)

print('---------------------------------- initiate purchase by buyer 2 ----------------------------------')
setup_txn_id_b = setup_sale(algod_client, buyer_1_private_key, app_id, sale_args, foreign_assets)
print(f'setup sale transaction ID: {setup_txn_id_b}')
# buyer posting buy transactions
buy_asset(algod_client, buyer_2_private_key, buyer_1_public_key, app_id, buy_args, foreign_assets,
          DefaultValues.nft_price)
# buyer executing transfer
buyer_execute_transfer(algod_client, buyer_2_private_key, buyer_1_public_key, app_id, buyer_execute_args,
                       foreign_assets)

print('---------------------------------- sale from buyer 1 to buyer 2 completed ----------------------------------')
print_asset_holding(algod_client, buyer_1_public_key, asset_id)
print_asset_holding(algod_client, buyer_2_public_key, asset_id)
creator_claim_args = [AppArgs.claim_fees]
creator_account_before = algod_client.account_info(creator_public_key).get('amount')
print(f'creator account balance before claiming fees: {creator_account_before} microAlgos.')
creator_claim_fees(algod_client, creator_private_key, app_id, creator_claim_args)
creator_account_after = algod_client.account_info(creator_public_key).get('amount')
print(f'creator account balance after claiming fees: {creator_account_after} microAlgos.')
print(f'total fees claimed: {creator_account_after - creator_account_before} microAlgos')
