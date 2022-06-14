from pyteal import *


class AppVariables:
    # global variables
    creator = Bytes('creator')  # asset creator, byteslice
    asset_id = Bytes('asset_id')  # asset id, byteslice
    royalty_fee = Bytes('royalty_fee')  # royalty fee in thousands, uint64
    waiting_time = Bytes('waiting_time')  # number of rounds to wait before the seller can force the transaction, uint64
    collected_fees = Bytes('collected_fees')  # amount of collected fees, stored globally, uint64,
    round_sale_began = Bytes('round_sale_began')  # round in which the sale began, uint64
    # locals
    amount_payment = Bytes('amount_payment')  # amt to be paid for the asset, stored on seller's account, uint64
    approve_transfer = Bytes('approve_transfer')  # approval variable stored on seller's and buyer's accounts, byteslice
    # method calls
    setup_sale = Bytes('setup_sale')
    buy = Bytes('buy')
    execute_transfer = Bytes('execute_transfer')
    claim_fees = Bytes('claim_fees')
    refund = Bytes('refund')


class AppArgs:
    setup_sale = 'setup_sale'.encode()
    buy = 'buy'.encode()
    execute_transfer = 'execute_transfer'.encode()
    claim_fees = 'claim_fees'.encode()
    refund = 'refund'.encode()


class DefaultValues:
    royalty_fee = int(50)
    waiting_time = int(15)
    nft_price = int(1000000)  # 1 algo
