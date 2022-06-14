import os
from dotenv import load_dotenv

from algosdk import mnemonic
from algosdk.future import transaction
from algosdk.logic import get_application_address
from pyteal import compileTeal, Mode

from contract import approval, clear
from helpers.consts import DefaultValues
from helpers.operations import create_app
from helpers.utils import (
    compile_program,
    get_public_key_from_mnemonic,
    address_to_bytes,
    int_to_bytes,
    print_asset_holding,
)
from helpers.utils import get_algod_client

load_dotenv()

creator_mnemonic = os.getenv('CREATOR_MNEMONIC')
asset_id = int(os.getenv('ASSET_ID'))
royalty_fee = DefaultValues.royalty_fee
waiting_time = DefaultValues.waiting_time

print(f'creator public key: {get_public_key_from_mnemonic(creator_mnemonic)}')
print(f'asset ID: {asset_id}')
print(f'royalty fee: {royalty_fee / 10}%')
print(f'waiting time: {waiting_time} seconds')

# create purestake client
algod_client = get_algod_client()

# define private keys
creator_private_key = mnemonic.to_private_key(creator_mnemonic)

# declare application state storage (immutable)
local_ints = 3
local_bytes = 0
global_ints = 4
global_bytes = 1
global_schema = transaction.StateSchema(global_ints, global_bytes)
local_schema = transaction.StateSchema(local_ints, local_bytes)

# get pyteal approval program
approval_program_ast = approval()
# compile program to TEAL assembly
approval_program_teal = compileTeal(approval_program_ast, mode=Mode.Application, version=5)
# compile program to binary
approval_program_compiled = compile_program(algod_client, approval_program_teal)
# create approval teal file for verification
with open('../teal/approval.teal', 'w+') as f:
    f.write(str(approval_program_teal))

# get pyteal clear state program
clear_state_program_ast = clear()
# compile program to TEAL assembly
clear_state_program_teal = compileTeal(clear_state_program_ast, mode=Mode.Application, version=5)
# compile program to binary
clear_state_program_compiled = compile_program(algod_client, clear_state_program_teal)
# create clear teal file for verification
with open('../teal/clear.teal', 'w+') as f:
    f.write(str(clear_state_program_teal))

# configure app args
creator_public_key = get_public_key_from_mnemonic(creator_mnemonic)
print_asset_holding(algod_client, creator_public_key, asset_id)

# create list of bytes for app args
app_args = [
    address_to_bytes(creator_public_key),
    int_to_bytes(asset_id),
    int_to_bytes(royalty_fee),
    int_to_bytes(waiting_time),
]

foreign_assets = [asset_id]

# create new application
app_id = create_app(
    algod_client,
    creator_private_key,
    approval_program_compiled,
    clear_state_program_compiled,
    global_schema,
    local_schema,
    app_args,
    foreign_assets,
)

app_address = get_application_address(app_id)

print(f'application id: {app_id}')
print(f'application address: {app_address}')

with open('../.env', 'a') as f:
    f.write(f'APP_ID={app_id}\n')
    f.write(f'APP_ADDRESS={app_address}\n')
