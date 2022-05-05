import os
import time
import logging
import functools
from typing import List, Any, Optional, Union, Tuple, Dict

from web3 import Web3
from web3.eth import Contract
from web3.auto import w3
import eth_account
from web3.contract import ContractFunction
from web3.types import (
    TxParams,
    Wei,
    Address,
    ChecksumAddress,
    Nonce,
    HexBytes,
)

from .util import (validate_address, load_contract_erc20, addr_to_str)
from .bmc_client import ETH_ADDRESS
from .util import load_contract, str_to_addr, load_json
from .tokens import EthNet
from .local_types import AddressLike
from .bmc_client import BmcClient
from .constants import _maze_contract_address, _nft_contract_address
from .log_service import log_service_manager


class MazeClient(BmcClient):
    def __init__(self,
                 address: Union[AddressLike, str, None],
                 private_key: Optional[str],
                 network=EthNet.MainNet.value,
                 provider: str = None,
                 ):
        '''
        hero_core继承了hero_erc721， hero_core是加密三国合约，最新的里面有cancel功能
        '''
        super(MazeClient, self).__init__(address=address, private_key=private_key, network=network, provider=provider)

        mazi_abi_name = "maze/auction_radical"
        self.maze_contract_address = _maze_contract_address[network]

        nft_hero_core_abi_name = "maze/hero_core"
        self.hero_core_contract_address = _nft_contract_address[network]

        self.maze_contract = load_contract(self.w3, abi_name=mazi_abi_name,
                                           address=str_to_addr(self.maze_contract_address))
        self.hero_contract = load_contract(self.w3, abi_name=nft_hero_core_abi_name,
                                           address=str_to_addr(self.hero_core_contract_address))


    @staticmethod
    def init_from_keystore(keystore_filepath, password, network):
        keystore_content_js = load_json(keystore_filepath)

        private_key = Web3().eth.account.decrypt(keystore_content_js, password)
        address = "0x" + keystore_content_js["address"]
        return MazeClient(address=address, private_key=private_key, network=network)

    def get_parameters_by_address(self, address):
        js_sql = '''
        {
          parameters(where:{taxReceiver:"%s"}){
            erc721Address
            feeRatio
            taxRatio
            taxReceiver
            erc20Address
          }
        }
        ''' % (address)
        url = self.host + "/subgraphs/name/bytom/maze-subgraph"
        return self.run_query(url, js_sql)

    def get_histories_by_erc721address(self, erc721Address):
        js_sql = '''
        {
          histories(where:{erc721Address:"%s",type:"deal"},orderBy: timestamp, orderDirection: desc){
            id
            erc721Address
            tokenId
            buyer
            seller
            price
            type
            txHash
            timestamp
            tax
            fee
          }
        }
        ''' % (erc721Address)
        url = self.host + "/subgraphs/name/bytom/maze-subgraph"
        return self.run_query(url, js_sql)

    def get_histories_by_address(self, address):
        ret_arr = []
        data = self.get_parameters_by_address(address)
        parameter_arr = data["data"]["parameters"]
        for parameter_dic in parameter_arr:
            erc721Address = parameter_dic["erc721Address"]
            data = self.get_histories_by_erc721address(erc721Address)
            ret_arr.extend(data["data"]["histories"])
        return ret_arr

    def get_nft_history(self, erc721Address, tokenId, Type):
        js_sql = '''
        {
          histories(where:{erc721Address:"%s",tokenId:%s, type:"%s"},orderBy: timestamp, orderDirection: desc){
            id
            erc721Address
            tokenId
            buyer
            seller
            price
            type
            txHash
            tax
            timestamp
          }
        }
        ''' % (erc721Address, str(tokenId), str(Type))
        url = self.host + "/subgraphs/name/bytom/maze-subgraph"
        return self.run_query(url, js_sql)

    def get_nft_history_by_deal_limit(self, limit):
        js_sql = '''
        {
          histories(where:{type:"deal"},orderBy: timestamp, orderDirection: desc, first: %s){
            id
            erc721Address
            tokenId
            buyer
            seller
            price
            type
            txHash
            tax
            timestamp
          }
        }
        ''' % (str(limit))
        url = self.host + "/subgraphs/name/bytom/maze-subgraph"
        return self.run_query(url, js_sql)

    def get_highest_auction_by_limit(self, limit):
        js_sql = '''
        {
          auctions(orderBy:price, orderDirection: desc, first:%s){
            id
            erc721Address  #erc721合约地址
            tokenId #token id
            seller #卖家地址
            deposit #保证金金额
            price #价格
            startAt #开始时间
            dealCount #成交次数
            offerCount #求购次数
          }
        }
        ''' % (str(limit))
        url = self.host + "/subgraphs/name/bytom/maze-subgraph"
        return self.run_query(url, js_sql)

    def get_lowest_auction_by_limit(self, limit):
        js_sql = '''
        {
          auctions(orderBy:price, orderDirection: asc, first:%s){
            id
            erc721Address  #erc721合约地址
            tokenId #token id
            seller #卖家地址
            deposit #保证金金额
            price #价格
            startAt #开始时间
            dealCount #成交次数
            offerCount #求购次数
          
          }
        }
        ''' % (str(limit))
        url = self.host + "/subgraphs/name/bytom/maze-subgraph"
        return self.run_query(url, js_sql)

    def set_approval_for_all(self, operator_address, flag=True):
        '''
        给操作的合约授权
        :param operator_address:
        :param flag:
        :return:
        '''
        return self.build_tx(
            self.hero_contract.functions.setApprovalForAll(
                operator_address, flag
            ),
        )

    def is_approval_for_all(self, address, operator_address):
        '''
        nft合约的函数
        :param address: 要判断的地址
        :param operator_address: maze的激进合约地址，操作的合约
        :return:
        '''
        return self.hero_contract.functions.isApprovedForAll(
            address, operator_address
        ).call()

    def is_maze_approval(self):
        return self.is_approval_for_all(self.address, self.maze_contract_address)

    def check_maze_approval_and_go_approve(self):
        if not self.is_maze_approval():
            transaction, tx_params = self.set_approval_for_all(self.maze_contract_address, True)
            log_service_manager.write_log(f"[work_client] set_approval_for_all transaction:{transaction},"
                                          f" tx_params:{tx_params}")
            data = self.signed_and_send(transaction, tx_params)
            log_service_manager.write_log(f"[work_client] data:{data}")
            time.sleep(6)

    def check_and_go_approve_for_maze(self, token: AddressLike):
        if ETH_ADDRESS != token:
            is_approved = self._is_token_approve_contract(token, self.maze_contract_address)
            log_service_manager.warning(f"Approved? {token}: {is_approved}")
            if not is_approved:
                log_service_manager.write_log(f"[check_and_go_approve_for_maze] go approve token:{token}")
                self._approve(token, self.maze_contract_address)
                time.sleep(6)

    def check_and_go_approve_erc721address_for_maze(self, erc721Address: AddressLike):
        fee_ratio, tax_ratio, tax_receiver, erc20_address = self.get_auction_param(
            Web3.toChecksumAddress(erc721Address))
        data = self.check_and_go_approve_for_maze(Web3.toChecksumAddress(Web3.toChecksumAddress(erc20_address)))
        log_service_manager.write_log(f"[work_client] check_and_go_aprove, data:{data}")

    @staticmethod
    def get_contract_amount(contract_address=ETH_ADDRESS, amount: Wei = 0) -> Wei:
        if not Web3.toChecksumAddress(contract_address) == Web3.toChecksumAddress(ETH_ADDRESS):
            amount = 0
        return amount

    def create_initial_auction(self, erc721address, token_id, initial_price):
        '''
        _initialPrice 拍卖价格
        创建初始激进拍卖，不需要保证金，只提供给NFT项目方的creator地址使用
        '''
        return self.build_tx(
            self.maze_contract.functions.createInitialAuction(
                erc721address, token_id, initial_price
            ),
        )

    def nft_transfer_from(self, from_address, to_address, token_id):
        return self.build_tx(
            self.hero_contract.functions.transferFrom(
                from_address, to_address, token_id
            )
        )

    def create_auction(self, erc721address, token_id, deposit, contract_address=ETH_ADDRESS):
        '''
        _deposit 保证金金额
        卖家创建激进拍卖，由NFT持有者发起，
        保证金可以为BTM或ERC20 USDT,如果保证金是BTM发送交易的value == _deposit，
        如果保证金是USDT需要发起者提前发送一笔交易调用USDT的approve方法，授权AuctionRadical合约地址转账
        '''
        return self.build_tx(
            self.maze_contract.functions.createAuction(
                erc721address, token_id, deposit
            ),
            tx_params=self._get_tx_params(value=MazeClient.get_contract_amount(contract_address, deposit))
        )

    def increase_deposit(self, erc721address, token_id, amount):
        '''
        _amount 增加的保证金金额
        卖家增加激进拍卖保证金，保证金可以为BTM或ERC20 USDT,如果保证金是BTM发送交易的value == _amount
        '''
        _, _, _, erc20_address = self.get_auction_param(erc721address)
        amount = int(float(amount) * self.get_decimal_mul_from_contract(erc20_address))
        # print(erc721address, token_id, amount)
        return self.build_tx(
            self.maze_contract.functions.increaseDeposit(
                erc721address, token_id, amount
            ),
            tx_params=self._get_tx_params(value=MazeClient.get_contract_amount(erc20_address, amount))
        )

    def decrease_deposit(self, erc721address, token_id, amount):
        '''
        _amount 减少的保证金金额
        卖家减少激进拍卖保证金
        '''
        _, _, _, erc20_address = self.get_auction_param(erc721address)
        amount = int(float(amount) * self.get_decimal_mul_from_contract(erc20_address))
        return self.build_tx(
            self.maze_contract.functions.decreaseDeposit(
                erc721address, token_id, amount
            ),
            tx_params=self._get_tx_params(value=MazeClient.get_contract_amount(erc20_address, amount))
        )

    def get_need_bid_amount(self, deposit, erc721address, token_id):
        seller, auction_deposit_amount, current_price, started_at = self.get_auction(erc721address, token_id)
        fee_ratio, tax_ratio, tax_receiver, erc20_address = self.get_auction_param(erc721address)
        fee_amount = int(current_price / int(fee_ratio))
        tax_amount = int(current_price / int(tax_ratio))
        return deposit + fee_amount + tax_amount + current_price

    def cancelAuction(self, erc721address, token_id):
        return self.build_tx(
            self.maze_contract.functions.cancelAuction(
                erc721address, token_id
            ),
        )

    def bid_auction(self, erc721address, token_id, deposit):
        '''
        _deposit 拍卖成功之后新的激进拍卖保证金金额
        买家参与拍卖，如果使用BTM参与拍卖发送交易的value == 交易金额 + 版税 + 手续费 + _deposit
        版税 = int(price / int(版税费率))
        手续费 = int(price / int(手续费率))
        '''
        _, _, _, erc20_address = self.get_auction_param(erc721address)
        deposit = int(deposit) * self.get_decimal_mul_from_contract(erc20_address)
        return self.build_tx(
            self.maze_contract.functions.bidAuction(
                erc721address, token_id, deposit
            ),
            tx_params=self._get_tx_params(value=MazeClient.get_contract_amount(
                erc20_address, self.get_need_bid_amount(deposit, erc721address, token_id)
            ))
        )

    def apply_offer(self, erc721address, token_id, offer_price, deposit, deadline):
        '''
        offerPrice 求购的金额
        _deposit 求购成功之后新的激进拍卖保证金金额
        _deadline 求购有效的时间戳
        买家发起求购请求，如果原拍卖使用的是BTM作为保证金，发起求购的用户钱包中需要有足够的WBTM，
        并且调用过WBTM合约approve方法授权AuctionRadical合约地址转账，每个地址只能向一个拍卖发起一次求购
        WBTM余额 >= _offerPrice + 版税 + 手续费 + _deposit
        '''
        _, _, _, erc20_address = self.get_auction_param(erc721address)
        deposit = int(float(deposit) * self.get_decimal_mul_from_contract(erc20_address))
        offer_price = int(float(offer_price) * self.get_decimal_mul_from_contract(erc20_address))
        return self.build_tx(
            self.maze_contract.functions.applyOffer(
                erc721address, token_id, offer_price, deposit, deadline
            ),
        )

    def get_offers(self, erc721address, token_id):
        '''
        获取拍卖的所有求购
        '''
        return self.maze_contract.functions.getOffers(
                erc721address, token_id
        ).call()

    def accept_offer(self, erc721address, token_id, buyer):
        '''
        _buyer 买家地址
        卖家接受买家的求购
        '''
        return self.build_tx(
            self.maze_contract.functions.acceptOffer(
                erc721address, token_id, buyer
            ),
        )

    def cancel_offer(self, erc721address, token_id):
        '''
        买家取消求购
        '''
        return self.build_tx(
            self.maze_contract.functions.cancelOffer(
                erc721address, token_id
            ),
        )

    def get_auction(self, erc721address, token_id):
        '''
        seller 卖家地址
        deposit 拍卖保证金金额
        currentPrice 拍卖当前价格
        startedAt 拍卖开始时间

        获取拍卖详情
        '''
        return self.maze_contract.functions.getAuction(
                erc721address, token_id
        ).call()

    def get_auction_param(self, erc721address):
        '''
        feeRatio 手续费费率, 手续费 = 拍卖金额 / _feeRatio
        taxRatio 版税费率 版税 = 拍卖金额 / _taxRatio
        taxReceiver 版税接收者，也是NFT的creator，能够调用createInitialAuction函数
        erc20Address ERC20保证金的合约地址，0x0表示只支持使用BTM作为保证金
        new add
        cancel_able
        获取拍卖参数
        '''
        feeRatio, taxRatio, taxReceiver, erc20Address = \
            self.maze_contract.functions.getAuctionParam(erc721address).call()
        return feeRatio, taxRatio, taxReceiver, erc20Address

    def get_supported_contracts(self):
        '''
        获取AuctionRadical目前已所有支持的NFT项目合约地址
        '''
        return self.maze_contract.functions.getSupportedContracts().call()

