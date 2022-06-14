from pyteal import *

from helpers.consts import AppVariables


def approval():
    @Subroutine(TealType.none)
    def default_transaction_checks(txn_id: Int) -> TealType.none:
        # verifies the rekeyTo, closeRemainderTo, and the assetCloseTo attributes are set equal to the zero address
        return Seq(
            [
                Assert(txn_id < Global.group_size()),
                Assert(Gtxn[txn_id].rekey_to() == Global.zero_address()),
                Assert(Gtxn[txn_id].close_remainder_to() == Global.zero_address()),
                Assert(Gtxn[txn_id].asset_close_to() == Global.zero_address()),
            ]
        )

    @Subroutine(TealType.none)
    def send_payment(receiver: Addr, amount: Int) -> TealType.none:
        # sends payments from asc to other accounts in microalgos using inner transactions
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: amount,
                TxnField.receiver: receiver,
                TxnField.fee: Global.min_txn_fee()
            }),
            InnerTxnBuilder.Submit(),
        ])

    @Subroutine(TealType.none)
    def transfer_asset(sender: Addr, receiver: Addr, asset_id: Int) -> TealType.none:
        # transfers an asset from one acct to another
        # can be used to opt in an asset if 'amount' is 0 and `sender` is equal to `receiver`
        # asset_id must also be passed in the `foreign_assets` field in the outer transaction to avoid reference error
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_amount: Int(1),  # 1/1 for nft
                TxnField.asset_receiver: receiver,
                TxnField.asset_sender: sender,  # indicates a clawback transaction
                # TxnField.sender: sender,
                TxnField.xfer_asset: asset_id,
                TxnField.fee: Global.min_txn_fee()
            }),
            InnerTxnBuilder.Submit(),
        ])

    @Subroutine(TealType.none)
    def check_nft_balance(account: Addr, asset_id: Int) -> TealType.none:
        # checks acct owns nft
        # note: asset id must also be passed in as `foreignAssets` in the outer transaction to avoid reference error
        asset_acct_balance = AssetHolding.balance(account, asset_id)
        return Seq([
            asset_acct_balance,
            Assert(asset_acct_balance.hasValue() == Int(1)),
            Assert(asset_acct_balance.value() == Int(1))
        ])

    @Subroutine(TealType.uint64)
    def compute_royalty_fee(amount: Int, fee: Int) -> TealType.uint64:
        # computes the fee given a specific `amount` and predefined `fee` (expressed in thousands)
        # note: must call check_royalty_fee_computation() before calling this function
        # the safety of computing `remainder` and `division` is given by calling check_royalty_fee_computation()
        remainder = ScratchVar(TealType.uint64)
        division = ScratchVar(TealType.uint64)
        # if the fee is equal to 0, or the amount is very small, the fee will be 0
        # if the royalty fee is larger or equal to 1000, then return the original amount
        # if the remainder of fee * amount / 1000 is larger than 500 round up the
        # result and return  1 + fee * amount / 1000
        # otherwise  just return fee * amount / 1000
        return Seq([
            check_royalty_fee_computation(amount, fee),
            remainder.store(Mod(Mul(amount, fee), Int(1000))),
            division.store(Div(Mul(amount, fee), Int(1000))),
            Return(If(Or(fee == Int(0), division.load() == Int(0))).Then(Int(0)) \
                   .ElseIf(fee >= Int(1000)).Then(amount) \
                   .ElseIf(remainder.load() > Int(500)).Then(division.load() + Int(1)) \
                   .Else(division.load()))
        ])

    @Subroutine(TealType.none)
    def check_royalty_fee_computation(amount: Int, fee: Int) -> TealType.none:
        # checks that there are no problems computing the royalty fee given a specific `amount` and `fee`
        # `fee` must be expressed in thousands
        return Seq([
            Assert(amount > Int(0)),
            Assert(fee <= Div(Int(2 ** 64 - 1), amount)),
        ])

    # [step 1] initialize smart contract; called only at creation
    service_cost = Int(2) * Global.min_txn_fee()  # cost of 2 inner transactions
    royalty_fee = Btoi(Txn.application_args[2])
    asset_decimals = AssetParam.decimals(Btoi(Txn.application_args[1]))
    asset_frozen = AssetParam.defaultFrozen(Btoi(Txn.application_args[1]))
    initialize = Seq([
        Assert(Txn.type_enum() == TxnType.ApplicationCall),  # ensure type is an application call
        Assert(Txn.application_args.length() == Int(4)),  # check for 4 args: creator, asset_id, fee, roundWait
        Assert(Int(0) < royalty_fee <= Int(1000)),  # verify fee is between 0 and 1000
        default_transaction_checks(Int(0)),  # call default transaction checks
        asset_decimals,  # load the asset decimals
        Assert(asset_decimals.hasValue()),
        Assert(asset_decimals.value() == Int(0)),  # verify that there are no decimal
        # asset_frozen,  # load the frozen parameter of the asset
        # Assert(asset_frozen.hasValue()),
        # Assert(asset_frozen.value() == Global.current_application_address()),  # verify the freeze address is contract
        # Assert(asset_frozen.value() == Int(0)),  # verify that the asset is not frozen
        App.globalPut(AppVariables.creator, Txn.application_args[0]),  # save the initial creator
        App.globalPut(AppVariables.asset_id, Btoi(Txn.application_args[1])),  # save the asset ID
        App.globalPut(AppVariables.royalty_fee, royalty_fee),  # save the royalty fee
        App.globalPut(AppVariables.waiting_time, Btoi(Txn.application_args[3])),
        # save waiting_time in number of rounds
        Approve()
    ])

    # [step 2] set up NFT sale with two arguments:
    #   1. the command to execute, in this case 'setup_sale'
    #   2. payment amount
    # first verify the seller owns the NFT, then locally save the arguments
    price = Btoi(Txn.application_args[1])
    asset_clawback = AssetParam.clawback(App.globalGet(AppVariables.asset_id))
    # asset_freeze = AssetParam.freeze(App.globalGet(AppVariables.asset_id))
    setup_sale = Seq([
        Assert(Txn.application_args.length() == Int(2)),  # check that there are 2 arguments
        Assert(Global.group_size() == Int(1)),  # verify that it is only 1 transaction
        default_transaction_checks(Int(0)),  # perform default transaction checks
        Assert(price > Int(0)),  # check that the price is greater than 0
        asset_clawback,  # verify that the clawback address is the contract
        Assert(asset_clawback.hasValue()),
        Assert(asset_clawback.value() == Global.current_application_address()),
        # asset_freeze,  # verify that the freeze address is the contract
        # Assert(asset_freeze.hasValue()),
        # Assert(asset_freeze.value() == Global.current_application_address()),
        check_nft_balance(Txn.sender(), App.globalGet(AppVariables.asset_id)),  # verify that the seller owns the NFT
        Assert(price > service_cost),  # check that the price is greater than the service cost
        App.localPut(Txn.sender(), AppVariables.amount_payment, price),  # save the price
        App.localPut(Txn.sender(), AppVariables.approve_transfer, Int(0)),  # reject transfer until payment is done
        Approve()
    ])

    # [step 3] approve the payment with two transactions:
    # first transaction is a NoOp call requiring 2 arguments:
    #   1. command to execute, in this case 'buy'
    #   2. asset id
    # also pass the seller's address into first transaction
    # second transaction is a payment (the receiver is the app)
    seller = Gtxn[0].accounts[1]  # get seller's address
    amt_to_pay = App.localGet(seller, AppVariables.amount_payment)  # get amount to be paid
    transfer_approval = App.localGet(seller, AppVariables.approve_transfer)  # check if the transfer has been approved
    buyer = Gtxn[0].sender()
    buy = Seq([
        Assert(Gtxn[0].application_args.length() == Int(2)),  # check that there are 2 arguments
        Assert(Global.group_size() == Int(2)),  # check that there are 2 transactions
        Assert(Gtxn[1].type_enum() == TxnType.Payment),  # check that the second transaction is a payment
        Assert(App.globalGet(AppVariables.asset_id) == Btoi(Gtxn[0].application_args[1])),  # ensure correct asset_id
        Assert(transfer_approval == Int(0)),  # check that the transfer has not been issued yet
        Assert(amt_to_pay == Gtxn[1].amount()),  # check that the amount to be paid is correct
        Assert(Global.current_application_address() == Gtxn[1].receiver()),  # ensure payment receiver is current app
        # default_transaction_checks(Int(0)),  # perform default transaction checks
        # default_transaction_checks(Int(1)),  # perform default transaction checks
        check_nft_balance(seller, App.globalGet(AppVariables.asset_id)),  # check that the seller owns the NFT
        Assert(buyer != seller),  # make sure the seller is not the buyer
        App.localPut(seller, AppVariables.approve_transfer, Int(1)),  # approve the transfer from seller' side
        App.localPut(buyer, AppVariables.approve_transfer, Int(1)),  # approve the transfer from buyer' side
        App.localPut(seller, AppVariables.round_sale_began, Global.round()),  # save the round number
        Approve()
    ])

    # [step 4] transfer the NFT: pay the seller and send royalty fees to the creator(s),
    # requires a NoOp App call transaction, with 1 argument:
    #   1. command to execute, in this case 'execute_transfer'
    # also account for the service_cost to pay the inner transaction
    royalty_fee = App.globalGet(AppVariables.royalty_fee)
    collected_fees = App.globalGet(AppVariables.collected_fees)
    fees_to_pay = ScratchVar(TealType.uint64)
    execute_transfer = Seq([
        Assert(Gtxn[0].application_args.length() == Int(1)),  # check that there is only 1 argument
        Assert(Global.group_size() == Int(1)),  # check that is only 1 transaction
        default_transaction_checks(Int(0)),  # perform default transaction checks
        Assert(App.localGet(seller, AppVariables.approve_transfer) == Int(1)),  # check seller side transfer_approval
        # check transfer_approval from buyer' side, alternatively, seller can force transaction if enough time has passed
        Assert(Or(And(seller != buyer, App.localGet(buyer, AppVariables.approve_transfer) == Int(1)),
                  Global.round() > App.globalGet(AppVariables.waiting_time) + App.localGet(seller,
                                                                                           AppVariables.round_sale_began))),
        Assert(service_cost < amt_to_pay),  # check underflow
        check_nft_balance(seller, App.globalGet(AppVariables.asset_id)),  # check that the seller owns the NFT
        # reduce number of subroutine calls by saving the variable inside a `temp` variable
        fees_to_pay.store(If(seller == App.globalGet(AppVariables.creator)).Then(Int(1)).Else(
            compute_royalty_fee(amt_to_pay - service_cost, royalty_fee))),
        # compute royalty fees: if the seller is the creator, the fees are 0
        Assert(Int(2 ** 64 - 1) - fees_to_pay.load() >= amt_to_pay - service_cost),  # check overflow on payment
        Assert(Int(2 ** 64 - 1) - collected_fees >= fees_to_pay.load()),  # check overflow on collected fees
        Assert(amt_to_pay - service_cost > fees_to_pay.load()),

        transfer_asset(seller, buyer, App.globalGet(AppVariables.asset_id)),
        send_payment(seller, amt_to_pay - service_cost - fees_to_pay.load()),  # pay seller
        App.globalPut(AppVariables.collected_fees, collected_fees + fees_to_pay.load()),  # collect fees
        App.localDel(seller, AppVariables.amount_payment),  # delete local variables
        App.localDel(seller, AppVariables.approve_transfer),
        App.localDel(buyer, AppVariables.approve_transfer),
        Approve()
    ])

    # [refund sequence]
    # buyer can get a refund if the payment has already been done but the NFT has not been transferred yet
    refund = Seq([
        Assert(Global.group_size() == Int(1)),  # verify that it is only 1 transaction
        Assert(Txn.application_args.length() == Int(1)),  # check that there is only 1 argument
        default_transaction_checks(Int(0)),  # perform default transaction checks
        Assert(buyer != seller),  # assert that the buyer is not the seller
        Assert(App.localGet(seller, AppVariables.approve_transfer) == Int(1)),  # assert payment has already been done
        Assert(App.localGet(buyer, AppVariables.approve_transfer) == Int(1)),
        Assert(amt_to_pay > Global.min_txn_fee()),  # underflow check: verify amount is greater than transaction fee
        send_payment(buyer, amt_to_pay - Global.min_txn_fee()),  # refund buyer
        App.localPut(seller, AppVariables.approve_transfer, Int(0)),  # reset local variables
        App.localDel(buyer, AppVariables.approve_transfer),
        Approve()
    ])

    # [claim fees sequence]
    # sequence can be called only by the creator, used to claim all the royalty fees
    # may fail if the contract does not have enough algo to pay the inner transaction
    # (the creator should take care of funding the contract in this case)
    claim_fees = Seq([
        Assert(Global.group_size() == Int(1)),  # verify that it is only 1 transaction
        Assert(Txn.application_args.length() == Int(1)),  # check that there is only 1 argument
        default_transaction_checks(Int(0)),  # perform default transaction checks
        Assert(Txn.sender() == App.globalGet(AppVariables.creator)),  # verify that the sender is the creator
        Assert(App.globalGet(AppVariables.collected_fees) > Int(0)),  # check that there are enough fees to collect
        send_payment(App.globalGet(AppVariables.creator), App.globalGet(AppVariables.collected_fees)),  # pay creator
        App.globalPut(AppVariables.collected_fees, Int(0)),  # reset collected fees
        Approve()
    ])

    # [call sequence]
    # checks that the first transaction is an Application call, and that there is at least 1 argument
    # then checks the first argument of the call, the first argument must be a valid value between
    # 'setup_sale', 'buy', 'execute_transfer', 'refund' and 'claim_fees'
    on_call = If(Or(Txn.type_enum() != TxnType.ApplicationCall, Txn.application_args.length() == Int(0))).Then(
        Reject()).ElseIf(Txn.application_args[0] == AppVariables.setup_sale).Then(setup_sale).ElseIf(
        Txn.application_args[0] == AppVariables.buy).Then(buy).ElseIf(
        Txn.application_args[0] == AppVariables.execute_transfer).Then(execute_transfer).ElseIf(
        Txn.application_args[0] == AppVariables.refund).Then(refund).ElseIf(
        Txn.application_args[0] == AppVariables.claim_fees).Then(claim_fees).Else(Reject())

    # check the transaction type and execute the corresponding code
    #   1. if application_id() is 0 then the program has just been created, so initialize it
    #   2. if on_completion() is 0, execute the on_call code
    return If(Txn.application_id() == Int(0)).Then(initialize).ElseIf(Txn.on_completion() == OnComplete.CloseOut).Then(
        Approve()).ElseIf(Txn.on_completion() == OnComplete.OptIn).Then(Approve()).ElseIf(
        Txn.on_completion() == Int(0)).Then(on_call).Else(Reject())


def clear():
    return Approve()

# if __name__ == '__main__':
#     # Compiles the approval program
#     with open(sys.argv[1], 'w+') as f:
#         compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
#         f.write(compiled)
#
#     # Compiles the clear program
#     with open(sys.argv[2], 'w+') as f:
#         compiled = compileTeal(clear_program(), mode=Mode.Application, version=5)
#         f.write(compiled)
