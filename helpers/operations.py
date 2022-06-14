from algosdk import account
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk.v2client.algod import AlgodClient

from helpers.utils import wait_for_confirmation


# create new application
def create_app(
        client: AlgodClient,
        private_key,
        approval_program,
        clear_program,
        global_schema,
        local_schema,
        app_args,
        foreign_assets,
):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        approval_program,
        clear_program,
        global_schema,
        local_schema,
        app_args,
        foreign_assets=foreign_assets,
    )
    signed_txn = txn.sign(private_key)
    txn_id = signed_txn.transaction.get_txid()

    print('sending create_app transaction')
    client.send_transactions([signed_txn])
    print('waiting for create_app confirmation')
    wait_for_confirmation(client, txn_id)

    # display results
    transaction_response = client.pending_transaction_info(txn_id)
    app_id = transaction_response['application-index']
    print('created new app with id:', app_id)
    return app_id


# opt-in to application
def opt_in(client: AlgodClient, private_key: str, index: int):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print('opt-in from account: ', sender)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationOptInTxn(sender, params, index)
    signed_txn = txn.sign(private_key)
    txn_id = signed_txn.transaction.get_txid()

    print('sending opt_in transaction')
    client.send_transactions([signed_txn])
    print('waiting for opt_in transaction')
    wait_for_confirmation(client, txn_id)

    # display results
    transaction_response = client.pending_transaction_info(txn_id)
    print('opt-in to app with id:', transaction_response['txn']['txn']['apid'])


def send_funds(client, private_key, receiver):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.PaymentTxn(sender, params, receiver, 200000, None)
    signed_txn = txn.sign(private_key)
    txn_id = signed_txn.transaction.get_txid()

    print('sending send_funds transaction')
    client.send_transactions([signed_txn])
    print('waiting for send_funds transaction')
    wait_for_confirmation(client, txn_id)
    print(f'transaction id: {txn_id}')


def set_clawback(client: AlgodClient, private_key: str, asset_id: int, app_address: str):
    # define manager as creator
    manager = account.address_from_private_key(private_key)
    print('manager address:', manager)
    print('app address:', app_address)
    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.AssetConfigTxn(
        sender=manager,
        sp=params,
        index=asset_id,
        manager=manager,
        reserve=manager,
        freeze=app_address,
        clawback=app_address,
    )
    signed_txn = txn.sign(private_key)
    txn_id = signed_txn.transaction.get_txid()

    print('sending set_clawback transaction')
    client.send_transactions([signed_txn])
    print('waiting for set_clawback confirmation')
    wait_for_confirmation(client, txn_id)

    return txn_id


# setup sale using the application
def setup_sale(client: AlgodClient, private_key, app_id, app_args, foreign_assets):
    # define sender as creator
    sender = account.address_from_private_key(private_key)
    on_complete = transaction.OnComplete.NoOpOC
    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationCallTxn(
        sender=sender,
        sp=params,
        index=app_id,
        on_complete=on_complete,
        app_args=app_args,
        foreign_assets=foreign_assets,
    )
    signed_txn = txn.sign(private_key)
    txn_id = signed_txn.transaction.get_txid()

    print('sending setup_sale transaction')
    client.send_transactions([signed_txn])
    print('waiting for setup_sale confirmation')
    wait_for_confirmation(client, txn_id)

    return txn_id


# setup sale using the application
def buy_asset(client: AlgodClient, private_key, app_account, app_id, app_args, foreign_assets, price: int):
    # define sender as creator
    buyer = account.address_from_private_key(private_key)
    app_address = get_application_address(app_id)
    on_complete = transaction.OnComplete.NoOpOC

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two lines to use suggested fees
    # params.flat_fee = True
    # params.fee = 1000

    # create unsigned app call transaction
    app_call_txn = transaction.ApplicationCallTxn(
        sender=buyer,
        sp=params,
        index=app_id,
        on_complete=on_complete,
        app_args=app_args,
        accounts=[app_account],
        foreign_assets=foreign_assets,
    )

    # create unsigned payment transaction
    pay_txn = transaction.PaymentTxn(sender=buyer, receiver=app_address, amt=price, sp=params)

    transaction.assign_group_id([app_call_txn, pay_txn])
    signed_app_call_txn = app_call_txn.sign(private_key)
    signed_pay_txn = pay_txn.sign(private_key)

    print('sending buy_asset transactions')
    client.send_transactions([signed_app_call_txn, signed_pay_txn])

    app_txn_id = signed_app_call_txn.transaction.get_txid()
    pay_txn_id = signed_pay_txn.transaction.get_txid()

    print('waiting for buy_asset confirmation')
    wait_for_confirmation(client, app_txn_id)
    wait_for_confirmation(client, pay_txn_id)

    return app_txn_id, pay_txn_id


# TODO: refund the transaction

# execute the transfer
def buyer_execute_transfer(client: AlgodClient, buyer_private_key, seller_address, app_id, app_args, foreign_assets):
    # define sender as creator
    buyer = account.address_from_private_key(buyer_private_key)

    on_complete = transaction.OnComplete.NoOpOC

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    # params.flat_fee = True
    # params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationCallTxn(
        sender=buyer,
        sp=params,
        index=app_id,
        on_complete=on_complete,
        app_args=app_args,
        accounts=[seller_address],
        foreign_assets=foreign_assets,
    )
    signed_txn = txn.sign(buyer_private_key)
    txn_id = signed_txn.transaction.get_txid()

    print('sending buyer execution transaction')
    client.send_transactions([signed_txn])
    print('waiting for buyer_execute_transfer confirmation')
    wait_for_confirmation(client, txn_id)

    return txn_id


# claim royalty fees
def creator_claim_fees(client: AlgodClient, private_key: str, app_id: int, app_args):
    creator = account.address_from_private_key(private_key)  # define sender as creator
    on_complete = transaction.OnComplete.NoOpOC  # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationCallTxn(
        sender=creator,
        sp=params,
        index=app_id,
        on_complete=on_complete,
        app_args=app_args,
    )
    signed_txn = txn.sign(private_key)
    txn_id = signed_txn.transaction.get_txid()

    print('sending claim_fees transaction')
    client.send_transactions([signed_txn])
    print('waiting for claim_fees confirmation')
    wait_for_confirmation(client, txn_id)

    return txn_id
