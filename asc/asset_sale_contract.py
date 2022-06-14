from pyteal import *

from helpers.consts import DefaultValues


def asset_sale_contract(seller: str, asset_index: int, price: int):
    # collaborating artists: 60% total
    COLLAB_1_ADDRESS = 'HV7FWNWDGRTAP4WOOW7T6ZCFELJ4OSFWKELNCPRSLS4HHAODOHLI6IFNCU'
    COLLAB_2_ADDRESS = '26QGZSQQRNPNKB6PS5KWKTZ4EUXB7XYM4DHBYKL3JHBAEAYOWBBXRF5ZFY'
    COLLAB_3_ADDRESS = 'P5P4TLUPASQ765EY7A3MVLN5HA7F55FX3CWAVZH6UQHMRY2TT37S7HHFVI'
    COLLAB_4_ADDRESS = 'ZZY2232VV7JT7V53O3Q3USKOIYHQFOVZC3JMX3KKNZIS6FT4C7JYKAHZ4Q'
    COLLAB_5_ADDRESS = 'UYV5MBXUPA5LFPDHENPLAYB2YQWYFH5JIXC3GVQN33FKHK5O4TT2VI35ZI'
    COLLAB_6_ADDRESS = 'JF2ZUJ6C3HJTTB5GHOYDT733VPQGNTE5XVVWADUSZRFHTFYW6HHSR4B5OY'
    COLLAB_7_ADDRESS = 'CIAV5DLVUF52WMDYDIBB6JPJPYLOG7HJBE4LHLWBBG2MIS5LIUIB4IG4GQ'
    # alaska organization: 15%
    COLLAB_8_ADDRESS = 'LAYPCJKT4ZASLKKXYYDDGJZUJQF3CFSNTLMAYUO37HRRJJHKSV2LZOV6UU'

    put_on_sale = And(
        Global.group_size() == Int(3),
        # fund escrow
        Gtxn[0].type_enum() == TxnType.Payment,
        Gtxn[0].amount() == Int(int(0.5)),
        Gtxn[0].sender() == Addr(seller),
        Gtxn[0].close_remainder_to() == Global.zero_address(),
        # opt in escrow
        Gtxn[1].type_enum() == TxnType.AssetTransfer,
        Gtxn[1].asset_amount() == Int(0),
        Gtxn[1].sender() == Gtxn[0].receiver(),
        Gtxn[1].sender() == Gtxn[1].asset_receiver(),
        Gtxn[1].asset_close_to() == Global.zero_address(),
        Gtxn[1].xfer_asset() == Int(asset_index),
        # transfer asset to escrow
        Gtxn[2].type_enum() == TxnType.AssetTransfer,
        Gtxn[2].asset_amount() == Int(1),
        Gtxn[2].sender() == Addr(seller),
        Gtxn[2].asset_receiver() == Gtxn[1].sender(),
        Gtxn[2].asset_close_to() == Global.zero_address(),
        Gtxn[2].xfer_asset() == Int(asset_index),
    )

    buy_asset = And(
        Global.group_size() == Int(12),
        # pay seller 25% of the sale
        Gtxn[0].type_enum() == TxnType.Payment,
        Gtxn[0].amount() == Int(int(price * 0.25)),
        Gtxn[0].receiver() == Addr(seller),
        Gtxn[0].close_remainder_to() == Global.zero_address(),
        # opt in buyer to nft
        Gtxn[1].type_enum() == TxnType.AssetTransfer,
        Gtxn[1].asset_amount() == Int(0),
        Gtxn[1].sender() == Gtxn[0].sender(),
        Gtxn[1].sender() == Gtxn[1].asset_receiver(),
        Gtxn[1].asset_close_to() == Global.zero_address(),
        Gtxn[1].xfer_asset() == Int(asset_index),
        # transfer asset to buyer
        Gtxn[2].type_enum() == TxnType.AssetTransfer,
        Gtxn[2].asset_amount() == Int(1),
        Gtxn[2].asset_receiver() == Gtxn[1].sender(),
        Gtxn[2].asset_close_to() == Gtxn[1].sender(),
        Gtxn[2].xfer_asset() == Int(asset_index),
        # pay collaborator 1 (60/7)% of the sale
        Gtxn[3].type_enum() == TxnType.Payment,
        Gtxn[3].amount() == Int(int(price * 0.6 / 7)),
        Gtxn[3].receiver() == Addr(COLLAB_1_ADDRESS),
        Gtxn[3].close_remainder_to() == Global.zero_address(),
        # pay collaborator 2 (60/7)% of the sale
        Gtxn[4].type_enum() == TxnType.Payment,
        Gtxn[4].amount() == Int(int(price * 0.6 / 7)),
        Gtxn[4].receiver() == Addr(COLLAB_2_ADDRESS),
        Gtxn[4].close_remainder_to() == Global.zero_address(),
        # pay collaborator 3 (60/7)% of the sale
        Gtxn[5].type_enum() == TxnType.Payment,
        Gtxn[5].amount() == Int(int(price * 0.6 / 7)),
        Gtxn[5].receiver() == Addr(COLLAB_3_ADDRESS),
        Gtxn[5].close_remainder_to() == Global.zero_address(),
        # pay collaborator 4 (60/7)% of the sale
        Gtxn[6].type_enum() == TxnType.Payment,
        Gtxn[6].amount() == Int(int(price * 0.6 / 7)),
        Gtxn[6].receiver() == Addr(COLLAB_4_ADDRESS),
        Gtxn[6].close_remainder_to() == Global.zero_address(),
        # pay collaborator 5 (60/7)% of the sale
        Gtxn[7].type_enum() == TxnType.Payment,
        Gtxn[7].amount() == Int(int(price * 0.6 / 7)),
        Gtxn[7].receiver() == Addr(COLLAB_5_ADDRESS),
        Gtxn[7].close_remainder_to() == Global.zero_address(),
        # pay collaborator 6 (60/7)% of the sale
        Gtxn[8].type_enum() == TxnType.Payment,
        Gtxn[8].amount() == Int(int(price * 0.6 / 7)),
        Gtxn[8].receiver() == Addr(COLLAB_6_ADDRESS),
        Gtxn[8].close_remainder_to() == Global.zero_address(),
        # pay collaborator 7 (60/7)% of the sale
        Gtxn[9].type_enum() == TxnType.Payment,
        Gtxn[9].amount() == Int(int(price * 0.6 / 7)),
        Gtxn[9].receiver() == Addr(COLLAB_7_ADDRESS),
        Gtxn[9].close_remainder_to() == Global.zero_address(),
        # pay collaborator 8 15% of the sale
        Gtxn[10].type_enum() == TxnType.Payment,
        Gtxn[10].amount() == Int(int(price * 0.15)),
        Gtxn[10].receiver() == Addr(COLLAB_8_ADDRESS),
        Gtxn[10].close_remainder_to() == Global.zero_address(),
    )

    cancel = And(
        Global.group_size() == Int(3),
        # close asset to seller
        Gtxn[0].type_enum() == TxnType.AssetTransfer,
        Gtxn[0].asset_amount() == Int(1),
        Gtxn[0].xfer_asset() == Int(asset_index),
        Gtxn[0].asset_receiver() == Addr(seller),
        Gtxn[0].asset_close_to() == Addr(seller),
        # close escrow remainder to seller
        Gtxn[1].type_enum() == TxnType.Payment,
        Gtxn[1].amount() == Int(0),
        Gtxn[1].sender() == Gtxn[1].sender(),
        Gtxn[1].receiver() == Addr(seller),
        Gtxn[1].close_remainder_to() == Addr(seller),
    )

    security = And(
        Txn.fee() <= Global.min_txn_fee(),
        Txn.lease() == Global.zero_address(),
        Txn.rekey_to() == Global.zero_address(),
    )

    contract_py = And(
        security,
        Cond(
            [Global.group_size() == Int(2), cancel],
            [Global.group_size() == Int(3), put_on_sale],
            [Global.group_size() == Int(12), buy_asset],
        ),
    )

    return compileTeal(contract_py, Mode.Signature, version=6)


# test run
CREATOR_ADDRESS = "E6U45JTJJQKGIQXECBTUAEARHU7PKCSRVLR5Q4PWT2EDG5XSOVOMK77LUA"
ASSET_ID = 78961298

contract_teal = asset_sale_contract(CREATOR_ADDRESS, ASSET_ID, DefaultValues.royalty_fee)
with open('../teal/asset_sale_contract.teal', 'w+') as f:
    f.write(str(contract_teal))
