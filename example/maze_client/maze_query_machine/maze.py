import requests
import getpass
import time
import sys

import eth_account
import os

from web3 import Web3
import json
import codecs
from collections import defaultdict

from bmc_sdk.constants import Direction
from bmc_sdk.bmc_client import BmcClient
from bmc_sdk.constants import EthNet
from bmc_sdk.bmc_client import ETH_ADDRESS

from bmc_sdk.log_service import log_service_manager
from bmc_sdk.maze_client import MazeClient
from bmc_sdk.util import load_json, save_json


class MazeQuery(object):
    @staticmethod
    def create_account(password, filepath):
        # 创建账户
        w3 = Web3()
        account = w3.eth.account.create()
        # private_key = account.key.hex()
        address = account.address
        keystore = account.encrypt(password)

        save_json(filepath, keystore)
        return {
            "status": "success",
            "data": {
                "address": address,
                "filepath": filepath
            }
        }

    @staticmethod
    def check_approve(client, erc721Address):
        # if not client.is_maze_approval():
        #     transaction, tx_params = client.set_approval_for_all(client.maze_contract_address, True)
        #     log_service_manager.write_log(f"[work_client] set_approval_for_all transaction:{transaction},"
        #                                   f" tx_params:{tx_params}")
        #     data = client.signed_and_send(transaction, tx_params)
        #     log_service_manager.write_log(f"[work_client] data:{data}")
        #     time.sleep(6)
        # 同意maze使用合约
        client.check_maze_approval_and_go_approve()
        # 同意erc721内的合约花费
        client.check_and_go_approve_erc721address_for_maze(erc721Address)
        # fee_ratio, tax_ratio, tax_receiver, erc20_address = client.get_auction_param(Web3.toChecksumAddress(erc721Address))
        # data = client.check_and_go_approve_for_maze(Web3.toChecksumAddress(Web3.toChecksumAddress(erc20_address)))
        # log_service_manager.write_log(f"[work_client] check_and_go_aprove, data:{data}")

    @staticmethod
    def update_account():
        pass

    @staticmethod
    def query_account(network, address):
        client = MazeClient(address=address, private_key="", network=network)
        asset_data = client.get_balance_from_bmc_wallet()
        query_assets_contracts = [(dic["asset"]["symbol"].lower(),
                                   dic["asset"]["contract_address"].lower()) for dic in asset_data["data"]]
        balances = []

        contract_dic = {}
        for asset, contract_address in query_assets_contracts:
            contract_dic[asset] = contract_address

            if asset == "btm":
                contract_address = ETH_ADDRESS
            bal = client.get_token_balance(contract_address)
            balances.append({
                "asset": asset,
                "balance": bal
            })

        own_nfts = []
        data = client.query_erc721_by_address(address)
        for dic in data["data"]["tokens"]:
            erc721Address = dic["contract"]["id"]
            tokenId = dic["tokenId"]
            own_nfts.append({
                "erc721Address": erc721Address,
                "tokenId": tokenId,
                "id": f"{erc721Address}:{tokenId}"
            })
            # print(f"[query_account] now has nft: {contract_address}:{token_id}")
            # seller, deposit, current_price, started_at = client.get_auction(
            #     Web3.toChecksumAddress(contract_address), int(token_id))
            # print(f"[query_account] {seller}, {deposit}, {current_price}, {started_at}!")

        return {
            "status": "success",
            "data": {
                "balances": balances,
                "own-nfts": own_nfts
            }
        }

    @staticmethod
    def query_account_income_single(client, address):
        erc721_income_dic = defaultdict(float)
        erc20_income_dic = defaultdict(float)

        data = client.query_buyer_by_address(address)
        for dic in data["data"]["histories"]:
            buyer = dic["buyer"]
            erc721Address = dic["erc721Address"]
            tokenId = dic["id"]
            price = float(dic["price"])
            seller = dic["seller"]

            fee_ratio, tax_ratio, tax_receiver, erc20_address \
                = client.get_auction_param(Web3.toChecksumAddress(erc721Address))

            erc721_income_dic[erc721Address] -= price
            erc20_income_dic[erc20_address] -= price
            print("buyer", erc20_address, price)

        data = client.query_seller_by_address(address)
        for dic in data["data"]["histories"]:
            buyer = dic["buyer"]
            erc721Address = dic["erc721Address"]
            _id = dic["id"]
            price = float(dic["price"])
            seller = dic["seller"]

            fee_ratio, tax_ratio, tax_receiver, erc20_address = client.get_auction_param(
                Web3.toChecksumAddress(erc721Address))

            erc721_income_dic[erc721Address] += price
            erc20_income_dic[erc20_address] += price
            print("seller", erc20_address, price)

        income_arr = []
        for erc20_address, income_score in erc20_income_dic.items():
            token_obj = client.get_token(Web3.toChecksumAddress(erc20_address))
            income_arr.append({"asset": token_obj.symbol.lower(), "balance": income_score})
        return income_arr

    @staticmethod
    def query_tax_income_by_address(client, address):
        histories_arr = client.get_histories_by_address(address)

        symbol_dic = defaultdict(float)
        for history_dic in histories_arr:
            fee_ratio, tax_ratio, tax_receiver, erc20_address = client.get_auction_param(
                Web3.toChecksumAddress(history_dic["erc721Address"]))
            token_obj = client.get_token(Web3.toChecksumAddress(erc20_address))
            symbol_dic[token_obj.symbol] += float(history_dic["tax"])

        ret_arr = []
        for symbol, tax in symbol_dic.items():
            ret_arr.append({
                "asset": symbol,
                "balance": tax
            })
        return ret_arr

    @staticmethod
    def query_account_income(network, address):
        '''
        账户盈亏= 卖出NFT的累计金额 - 买入nft的累计金额
        '''
        client = MazeClient("0x69d154840242a9e7e55c824b2060fb77c5abbe3b",
                            "0x224c9fbac2e06052af9a7aa3bbcd52542628cd4dc69e561a6b2727bc06f58162",
                            network=network)
        income_arr = MazeQuery.query_account_income_single(client, address)
        own_nfts = []
        data = client.query_erc721_by_address(address)
        for dic in data["data"]["tokens"]:
            erc721Address = dic["contract"]["id"]
            tokenId = dic["tokenId"]
            own_nfts.append({
                "erc721Address": erc721Address,
                "tokenId": tokenId,
                "id": f"{erc721Address}:{tokenId}"
            })
        return {
            "status": "success",
            "data": {
                "incomes": income_arr,
                "own-nfts": own_nfts
            }
        }

    @staticmethod
    def buy_nft(network, erc721Address, tokenId, deposit, password, filepath):
        client = MazeClient.init_from_keystore(filepath, password, network)
        MazeQuery.check_approve(client, erc721Address)
        transaction, tx_params = client.bid_auction(Web3.toChecksumAddress(erc721Address), tokenId, deposit)
        print(client.estimate_gas(transaction))
        data = client.signed_and_send(transaction, tx_params)
        log_service_manager.write_log(f"[buy_nft] data:{data}!")
        if data:
            tx_hash = data.hex()
            return {
                "status": "success",
                "data": {
                    "txHash": tx_hash,
                    "error": ""
                }
            }
        else:
            return {
                "status": "failed",
                "data": {
                    "txHash": "",
                    "error": ""
                }
            }

    @staticmethod
    def adjust_nft_deposit(network, erc721Address, tokenId, amount, password, filepath):
        client = MazeClient.init_from_keystore(filepath, password, network)
        MazeQuery.check_approve(client, erc721Address)
        if amount > 0:
            transaction, tx_params = client.increase_deposit(erc721Address, tokenId, amount)
        else:
            transaction, tx_params = client.decrease_deposit(erc721Address, tokenId, abs(amount))
        data = client.signed_and_send(transaction, tx_params)
        log_service_manager.write_log(f"[adjust_nft_caution_money] data:{data}!")
        if data:
            tx_hash = data.hex()
            return {
                "status": "success",
                "data": {
                    "txHash": tx_hash,
                    "error": ""
                }
            }
        else:
            return {
                "status": "failed",
                "data": {
                    "txHash": "",
                    "error": data
                }
            }

    @staticmethod
    def apply_offer(network, erc721Address, tokenId, price, deposit, password, filepath):
        client = MazeClient.init_from_keystore(filepath, password, network)
        MazeQuery.check_approve(client, erc721Address)
        deadline = int(time.time()) + 10 * 60
        transaction, tx_params = client.apply_offer(erc721Address, tokenId, price, deposit, deadline)

        data = client.signed_and_send(transaction, tx_params)
        log_service_manager.write_log(f"[apply_offer] data:{data}!")
        if data:
            tx_hash = data.hex()
            return {
                "status": "success",
                "data": {
                    "txHash": tx_hash,
                    "error": ""
                }
            }
        else:
            return {
                "status": "failed",
                "data": {
                    "txHash": "",
                    "error": data
                }
            }

    @staticmethod
    def get_offers(network, erc721Address, token_id):
        client = MazeClient("0x69d154840242a9e7e55c824b2060fb77c5abbe3b",
                            "0x224c9fbac2e06052af9a7aa3bbcd52542628cd4dc69e561a6b2727bc06f58162",
                            network=network)
        offers = client.get_offers(erc721Address, token_id)
        ret = {
            "status": "success",
            "data": {
                "buyers_info": [

                ]
            }
        }
        for i in range(len(offers)):
            ret["data"]["buyers_info"].append({
                "address": offers[i][0],
                "offer_price": offers[i][1],
                "deposit": offers[i][2],
                "deadline": offers[i][2],
            })
        return ret

    @staticmethod
    def cancel_offer(network, erc721Address, tokenId, password, filepath):
        client = MazeClient.init_from_keystore(filepath, password, network)
        MazeQuery.check_approve(client, erc721Address)
        transaction, tx_params = client.cancel_offer(erc721Address, tokenId)
        data = client.signed_and_send(transaction, tx_params)
        log_service_manager.write_log(f"[cancel_offer] data:{data}!")
        if data:
            tx_hash = data.hex()
            return {
                "status": "success",
                "data": {
                    "txHash": tx_hash,
                    "error": ""
                }
            }
        else:
            return {
                "status": "failed",
                "data": {
                    "txHash": "",
                    "error": data
                }
            }

    @staticmethod
    def give_nft(network, erc721Address, tokenId, toAddress, password, filepath):
        '''
        赠送nft
        1、如果该nft 还没在拍卖里面，则直接transfer即可
        2、如果该nft 在拍卖里面， 则如何转移时带上保证金？
            加密三国 的可以取消拍卖，然后再转账
            激进拍卖 的因为不可用取消拍卖，目前还实现不了这个转账功能
        '''
        log_service_manager.write_log("[give_nft]")
        client = MazeClient.init_from_keystore(filepath, password, network)

        try:
            transaction, tx_params = client.cancelAuction(erc721Address, tokenId)
            data = client.signed_and_send(transaction, tx_params)
            log_service_manager.write_log(f"[cancel_offer] data:{data}!")
            time.sleep(6)
        except Exception as ex:
            log_service_manager.write_log(f"[give_nft] ex:{ex}!")

        ## 写转账代码
        transaction, tx_params = client.nft_transfer_from(client.address, toAddress, tokenId)
        data = client.signed_and_send(transaction, tx_params)
        log_service_manager.write_log(f"[cancel_offer] data:{data}!")
        if data:
            return {
                "status": "success",
                "data": {
                    "txHash": data.hex(),
                    "err": ""
                }
            }
        else:
            return {
                "status": "failed",
                "data": {
                    "txHash": "",
                    "err": data
                }
            }

    @staticmethod
    def query_nft_detail(network, erc721Address, tokenId):
        client = MazeClient("0x69d154840242a9e7e55c824b2060fb77c5abbe3b",
                            "0x224c9fbac2e06052af9a7aa3bbcd52542628cd4dc69e561a6b2727bc06f58162",
                            network=network)
        data = client.get_nft_history(erc721Address, tokenId, "deal")
        histories = data["data"]["histories"]
        if len(histories):
            ret_data = histories[0]
            return {
                "status": "success",
                "data": ret_data
            }
        else:
            return {
                "status": "failed",
                "data": {}
            }

    @staticmethod
    def query_author(network, address):
        '''
        目前暂时做不了这个，测试环境还没有，暂不支持
        http://127.0.0.1:3000/maze/user-info?address=
        // UserInfoResp user info resp
        type UserInfoResp struct {
         Name            string `json:"name"`
         Address         string `json:"address"`
         AuditStatus     string `json:"audit_status"`
         AuditFailReason string `json:"audit_fail_reason"`
         Desc            string `json:"desc"`
         SocialContact   string `json:"social_contact"`
        }
        '''
        client = MazeClient("0x69d154840242a9e7e55c824b2060fb77c5abbe3b",
                            "0x224c9fbac2e06052af9a7aa3bbcd52542628cd4dc69e561a6b2727bc06f58162",
                            network=network)
        income_arr = MazeQuery.query_account_income_single(client, address)
        tax_arr = MazeQuery.query_tax_income_by_address(client, address)

        data = client.query_seller_by_address(address)
        sell_nft_arr = data["data"]["histories"]

        return {
            "status": "success",
            "data": {
                "incomes": income_arr,
                "taxes": tax_arr,
                "sell_nft_history": sell_nft_arr
            }
        }

    @staticmethod
    def query_market_info(network, market_type, limit):
        '''
        ● String  - market_type, 查看的市场类型,
          ○ Const - trade, 查询最近成交的
          ○ Const - high_price, 查询价格最贵的
          ○ Const - low_price, 查询价格最便宜的
        ● Integer - limit, 查看多少条数量
        查询指定市场TOP信息（ 最近成交的， 价格最贵的， 价格最便宜的）
        '''
        client = MazeClient("0x69d154840242a9e7e55c824b2060fb77c5abbe3b",
                            "0x224c9fbac2e06052af9a7aa3bbcd52542628cd4dc69e561a6b2727bc06f58162",
                            network=network)
        if market_type == "trade":
            data = client.get_nft_history_by_deal_limit(limit)
            histories = data["data"]["histories"]
            return {
                "status": "success",
                "data": {
                    "market_type": market_type,
                    "nft_dealinfo": histories
                }
            }
        elif market_type == "high_price":
            data = client.get_highest_auction_by_limit(limit)

            return {
                "status": "success",
                "data": {
                    "market_type": market_type,
                    "nft_dealinfo": data["data"]["auctions"]
                }
            }
        elif market_type == "low_price":
            data = client.get_lowest_auction_by_limit(limit)
            return {
                "status": "success",
                "data": {
                    "market_type": market_type,
                    "nft_dealinfo": data["data"]["auctions"]
                }
            }
        else:
            return {
                "status": "failed",
                "data": {
                    "market_type": market_type,
                    "err": "market_type not right!"
                }
            }

    @staticmethod
    def work(method, network, js_data):
        ret = {
            "status": "failed"
        }
        if method == "create-account":
            password = js_data["password"]
            filepath = js_data["filepath"]
            ret = MazeQuery.create_account(password, filepath)
        elif method == "update-account":
            ret = MazeQuery.update_account()
        elif method == "query-account":
            address = js_data["address"]
            ret = MazeQuery.query_account(network, address)
        elif method == "query-account-income":
            address = js_data["address"]
            ret = MazeQuery.query_account_income(network, address)
        elif method == "buy-nft":
            erc721Address = js_data["erc721Address"]
            tokenId = js_data["tokenId"]
            deposit = js_data["deposit"]
            password = js_data["password"]
            filepath = js_data["filepath"]
            ret = MazeQuery.buy_nft(network, erc721Address, tokenId, deposit, password, filepath)
        elif method == "adjust-nft-deposit":
            erc721Address = js_data["erc721Address"]
            tokenId = js_data["tokenId"]
            deposit = js_data["deposit"]
            password = js_data["password"]
            filepath = js_data["filepath"]
            ret = MazeQuery.adjust_nft_deposit(network, erc721Address, tokenId, deposit, password, filepath)
        elif method == "apply-offer":
            erc721Address = js_data["erc721Address"]
            tokenId = js_data["tokenId"]
            price = js_data["price"]
            deposit = js_data["deposit"]
            password = js_data["password"]
            filepath = js_data["filepath"]
            ret = MazeQuery.apply_offer(network, erc721Address, tokenId, price, deposit, password, filepath)
        elif method == "query-offers":
            erc721Address = js_data["erc721Address"]
            tokenId = js_data["tokenId"]
            ret = MazeQuery.get_offers(network, erc721Address, tokenId)
        elif method == "cancel-offer":
            erc721Address = js_data["erc721Address"]
            tokenId = js_data["tokenId"]
            password = js_data["password"]
            filepath = js_data["filepath"]
            ret = MazeQuery.cancel_offer(network, erc721Address, tokenId, password, filepath)
        elif method == "give-nft":
            erc721Address = js_data["erc721Address"]
            tokenId = js_data["tokenId"]
            toAddress = js_data["toAddress"]
            password = js_data["password"]
            filepath = js_data["filepath"]
            ret = MazeQuery.give_nft(network, erc721Address, tokenId, toAddress, password, filepath)
        elif method == "query-nft-detail":
            erc721Address = js_data["erc721Address"]
            tokenId = js_data["tokenId"]
            ret = MazeQuery.query_nft_detail(network, erc721Address, tokenId)

        elif method == "query-author":
            address = js_data["address"]
            ret = MazeQuery.query_author(network, address)

        elif method == "query-market-info":
            market_type = js_data["market_type"]
            limit = js_data["limit"]
            ret = MazeQuery.query_market_info(network, market_type, limit)

        print(ret)


if __name__ == "__main__":
    if len(sys.argv) > 3:
        method = sys.argv[1]
        network = sys.argv[2]
        msg = sys.argv[3]
        data = json.loads(msg)
        print(data)

        MazeQuery.work(method, network, data)
