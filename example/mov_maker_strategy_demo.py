# coding=utf-8

from copy import copy

from mov_sdk.mov_api import MovApi

from util import *
from config import strategy_config, account_config


class SDKImpl(object):
    def __init__(self, _guid, _private_key):
        self.guid = _guid
        self.private_key = _private_key

        self.api = MovApi(self.guid, self.private_key)

    def get_price(self, symbol):
        data = self.api.get_depth(symbol)
        if not self.check_error(data, "query_depth"):
            asks = data["data"]["asks"]
            bids = data["data"]["bids"]
            asks.sort()
            bids.sort(reverse=True)
            if len(asks) > 0 and len(bids) > 0:
                return float(asks[0][0]), float(bids[0][0])
        return None, None

    def get_exchange(self):
        '''
        :return:
        '''
        ret = {}
        data = self.api.get_exchange_info()
        if not self.check_error(data, "query_exchange"):
            data = data["data"]
            for d in data:
                symbol = (d["base_asset"]["symbol"] + "_" + d["quote_asset"]["symbol"]).lower()
                price_tick = 1.0 / pow(10, d["price_decimal"])
                volume_tick = 1.0 / pow(10, d["amount_decimal"])
                ret[symbol] = {"price_tick": price_tick, "volume_tick": volume_tick}
        return ret

    def get_account(self):
        '''
        需要注意，account 只有可用余额的数据！
        :return:
        '''
        ret = {}
        data = self.api.get_balance()
        if not self.check_error(data, "query_balance"):
            balances = data["data"]["balances"]
            for dic in balances:
                alias = dic["asset"]["symbol"]
                ret[alias] = float(dic["balance"])
        return ret

    def send_order(self, symbol, side, price, volume):
        try:
            data_arr = self.api.send_order(symbol, side, price, volume)
            if data_arr:
                data = data_arr[-1]
                if not self.check_error(data, "query_send_order"):
                    orders = data["data"]["orders"]
                    if len(orders) > 0:
                        d = orders[0]
                        sys_order_id = str(d["order_id"])
                        order = OrderData()
                        order.symbol = symbol
                        order.direction = side
                        order.order_id = str(sys_order_id)
                        order.price = price
                        order.volume = volume
                        order.traded = 0
                        order.status = Status.SUBMITTING.value  # 报单状态
                        order.order_time = get_str_dt_use_timestamp(d["order_timestamp"], mill=1)
                        return order
        except Exception as ex:
            log_service_manager.write_log("[Info] send_order error ex:{}".format(ex))

    def cancel_order(self, order_id):
        log_service_manager.write_log("[Info] cancel:{}".format(order_id))
        return self.api.cancel_order(order_id)

    def query_open_orders(self, symbol):
        data = self.api.query_open_orders(symbol)
        ret = []
        if not self.check_error(data, "query_open_orders"):
            data = data["data"]
            for d in data:
                order = OrderData()
                order.symbol = d["symbol"]
                order.order_id = str(d["order_id"])
                order.direction = d["side"]
                order.price = float(d["open_price"])
                order.volume = float(d["amount"])
                order.traded = float(d["filled_amount"])
                order.status = STATUS_MOV2VT[d["status"]]
                order.order_time = get_str_dt_use_timestamp(d["order_timestamp"], mill=1)
                ret.append(order)
        return ret

    def query_list_orders(self, order_id_list):
        ret = []
        data = self.api.query_list_orders(order_id_list)
        if not self.check_error(data, "query_list_orders"):
            data = data["data"]
            for d in data:
                order = OrderData()
                order.symbol = d["symbol"]
                order.order_id = str(d["order_id"])
                order.direction = d["side"]
                order.price = float(d["open_price"])
                order.volume = float(d["amount"])
                order.traded = float(d["filled_amount"])
                order.status = STATUS_MOV2VT[d["status"]]
                order.order_time = get_str_dt_use_timestamp(d["order_timestamp"], mill=1)
                order.cancel_time = get_str_dt_use_timestamp(d["update_timestamp"], mill=1)
                ret.append(order)
        return ret

    def check_error(self, data, func=""):
        if int(data["code"]) == 200:
            return False

        error_code = data["code"]
        error_msg = data["msg"]

        log_service_manager.write_log(
            "{} query_failed, code:{},information:{}".format(str(func), str(error_code), str(error_msg)))
        return True


class MovMakerStrategy(object):
    def __init__(self, _account_config, _config):
        self.account_config = _account_config
        self.guid = _account_config.get("guid", "")
        self.private_key = _account_config.get("private_key", "")
        self.impl = SDKImpl(self.guid, self.private_key)
        self.config = _config

        self.target_symbol, self.base_symbol = self.config["symbol_pair"].split('/')
        self.exchange_info = {"pos_base_symbol": 0, "pos_target_symbol": 0}

        self.put_order_dict = {}
        self.buy_cover_order = None
        self.sell_cover_order = None

        self.avg_price_long = self.config["long_config"]["avg_price"]
        self.position_long = self.config["long_config"]["now_position"]

        self.avg_price_short = self.config["short_config"]["avg_price"]
        self.position_short = self.config["short_config"]["now_position"]

        self.cover_rate = 1 - self.config["exchange_info"]["fee_rate"]

        self.ask = 0
        self.bid = 0

    def update_account(self):
        try:
            balance_dic = self.impl.get_account()
            self.exchange_info["pos_target_symbol"] = balance_dic[self.target_symbol] * self.config["exchange_info"][
                "pos_target_symbol_percent_use"]
            self.exchange_info["pos_base_symbol"] = balance_dic[self.base_symbol] * self.config["exchange_info"][
                "pos_base_symbol_percent_use"]
        except Exception as ex:
            log_service_manager.write_log("[Error] MovMakerStrategy,update_account ex:{}".format(ex))

    def update_exchange(self):
        try:
            exchange_dic = self.impl.get_exchange()
            dic = exchange_dic.get(self.config["symbol_pair"], {})
            if dic:
                self.exchange_info["price_tick"] = dic["price_tick"]
                self.exchange_info["volume_tick"] = dic["volume_tick"]
        except Exception as ex:
            log_service_manager.write_log("[Error] MovMakerStrategy,update_exchange ex:{}".format(ex))

    def get_now_has_order_ids(self):
        ret = list(self.put_order_dict.keys())
        if self.buy_cover_order:
            ret.append(self.buy_cover_order.order_id)
        if self.sell_cover_order:
            ret.append(self.sell_cover_order.order_id)
        return ret

    def get_price_list(self, direction):
        items = self.put_order_dict.items()
        order_ids = [x[0] for x in items]
        orders = [x[1] for x in items]
        price_lists = [order.price for order in orders if order.direction == direction]
        if direction == "sell":
            price_lists.sort()
        else:
            price_lists.sort(reverse=True)
        return price_lists

    def cancel_not_belong_orders(self):
        now_order_ids = self.get_now_has_order_ids()
        orders = self.impl.query_open_orders(self.config["symbol_pair"])
        for order in orders:
            if order.order_id not in now_order_ids:
                log_service_manager.write_log("cancel:{}".format(order.order_id))
                self.impl.cancel_order(order.order_id)

    def put_long_orders(self):
        if self.position_long:
            return
        start_price = (self.bid + self.ask) / 2.0
        start_volume = self.config["long_config"]["start_volume"] * self.exchange_info[
            "pos_base_symbol"] / self.bid / 100.0

        if not start_volume > 0:
            return
        inc_price = self.config["long_config"]["inc_spread"] * self.bid / 100.0
        inc_volume = self.config["long_config"]["inc_volume"] * self.exchange_info["pos_base_symbol"] / self.bid / 100.0
        left_base_amount = self.exchange_info["pos_base_symbol"]

        start_price -= inc_price

        log_service_manager.write_log(
            "put_long_orders,start_price:{},start_volume:{},inc_price:{},inc_volume:{}".format(start_price,
                                                                                               start_volume, inc_price,
                                                                                               inc_volume))
        order_list = []
        ind = 0
        now_price_list = self.get_price_list("buy")
        len_all = len(now_price_list)
        left_num = self.config["long_config"]["put_order_num"] - len_all
        for i in range(self.config["long_config"]["put_order_num"]):
            if left_num > 0 and start_price * start_volume < left_base_amount * 0.95:
                if (len_all == 0) or (ind == 0 and start_price - inc_price >= now_price_list[0]) \
                        or (ind > 0 and ind + 1 == len_all and now_price_list[ind - 1] - inc_price >= start_price) \
                        or (ind > 0 and ind + 1 < len_all and now_price_list[ind - 1] - inc_price >= start_price
                            and start_price - inc_price >= now_price_list[ind]):
                    use_volume = get_round_order_price(start_volume, self.exchange_info["volume_tick"])
                    use_price = get_round_order_price(start_price, self.exchange_info["price_tick"])

                    order_list.append(("buy", use_price, use_volume))
                    left_base_amount -= use_volume * use_price
                    left_num -= 1
                    start_volume += inc_volume

                start_price -= inc_price
            else:
                break

            while ind < len_all and start_price < now_price_list[ind]:
                ind += 1

        self.send_order_list(order_list)

    def put_short_orders(self):
        if self.position_short:
            return
        start_price = (self.bid + self.ask) / 2.0
        start_volume = self.config["short_config"]["start_volume"] * self.exchange_info["pos_target_symbol"] / 100.0
        if not start_volume > 0:
            return
        inc_volume = self.config["short_config"]["inc_volume"] * self.exchange_info["pos_target_symbol"] / 100.0
        inc_price = self.config["short_config"]["inc_spread"] * self.bid / 100.0
        left_target_amount = self.exchange_info["pos_target_symbol"]

        start_price += inc_price

        log_service_manager.write_log(
            "put_short_orders,start_price:{},start_volume:{},inc_price:{},inc_volume:{}".format(start_price,
                                                                                                start_volume, inc_price,
                                                                                                inc_volume))
        order_list = []
        ind = 0
        now_price_list = self.get_price_list("sell")
        len_all = len(now_price_list)
        left_num = self.config["short_config"]["put_order_num"] - len_all

        for i in range(self.config["short_config"]["put_order_num"]):
            if left_num > 0 and start_volume < left_target_amount * 0.95:
                if (len_all == 0) or (ind == 0 and start_price + inc_price <= now_price_list[0]) \
                        or (ind > 0 and ind + 1 == len_all and now_price_list[ind - 1] + inc_price >= start_price) \
                        or (ind > 0 and ind + 1 < len_all and now_price_list[ind - 1] + inc_price >= start_price
                            and start_price + inc_price <= now_price_list[ind + 1]):
                    use_volume = get_round_order_price(start_volume, self.exchange_info["volume_tick"])
                    use_price = get_round_order_price(start_price, self.exchange_info["price_tick"])

                    order_list.append(("sell", use_price, use_volume))
                    left_target_amount -= use_volume
                    left_num -= 1
                    start_volume += inc_volume

                start_price += inc_price
            else:
                break

            while ind < len_all and start_price > now_price_list[ind]:
                ind += 1

        self.send_order_list(order_list)

    def send_order_list(self, order_list):
        for side, price, volume in order_list:
            order = self.impl.send_order(self.config["symbol_pair"], side, price, volume)
            if order:
                self.put_order_dict[order.order_id] = copy(order)
                if side == "buy":
                    self.exchange_info["pos_base_symbol"] -= order.price * order.volume
                else:
                    self.exchange_info["pos_target_symbol"] -= order.volume

    def put_orders(self):
        self.put_long_orders()
        self.put_short_orders()

    def compute_avg_price(self, new_trade_price, new_trade_volume, new_trade_direction):
        if new_trade_direction == "buy":
            self.avg_price_long = (self.avg_price_long * self.position_long + new_trade_price * new_trade_volume) / (
                    self.position_long + new_trade_volume)
            self.position_long += new_trade_volume
        else:
            self.avg_price_short = (self.avg_price_short * self.position_short + new_trade_price * new_trade_volume) / (
                    self.position_short + new_trade_volume)
            self.position_short += new_trade_volume

        log_service_manager.write_log(
            "[compute_avg_price] [long:{},{}] [short:{},{}]".format(self.avg_price_long, self.position_long,
                                                                    self.avg_price_short,
                                                                    self.position_short))

    def cover_orders(self):
        now_order_ids = self.get_now_has_order_ids()
        orders = self.impl.query_list_orders(now_order_ids)
        all_new_traded_long = 0
        all_new_traded_short = 0
        for order in orders:
            bef_order = self.put_order_dict.get(order.order_id, None)
            if bef_order:
                new_traded = order.traded - bef_order.traded
                self.put_order_dict[order.order_id] = copy(order)
                if not order.is_active():
                    self.put_order_dict.pop(order.order_id)
                    new_return_frozen_volume = order.volume - order.traded
                    if order.direction == "buy":
                        self.exchange_info["pos_base_symbol"] += new_return_frozen_volume * order.price
                    else:
                        self.exchange_info["pos_target_symbol"] += new_return_frozen_volume
                if new_traded > 0:
                    self.compute_avg_price(order.price, new_traded, order.direction)
                    if order.direction == "buy":
                        all_new_traded_long += new_traded
                        self.exchange_info["pos_base_symbol"] -= new_traded * order.price
                        self.exchange_info["pos_target_symbol"] += new_traded * (1 - self.cover_rate)
                    else:
                        all_new_traded_short += new_traded
                        self.exchange_info["pos_base_symbol"] += new_traded * order.price * (1 - self.cover_rate)
                        self.exchange_info["pos_target_symbol"] -= new_traded

            if self.buy_cover_order and order.order_id == self.buy_cover_order.order_id:
                new_traded = order.traded - self.buy_cover_order.traded
                if new_traded > 0:
                    self.position_long -= new_traded
                    self.exchange_info["pos_base_symbol"] -= new_traded * self.buy_cover_order.price
                    self.exchange_info["pos_target_symbol"] += new_traded * (1 - self.cover_rate)
                self.buy_cover_order = copy(order)
                if not order.is_active():
                    new_return_frozen_volume = self.buy_cover_order.volume - self.buy_cover_order.traded
                    self.exchange_info["pos_base_symbol"] += new_return_frozen_volume * self.buy_cover_order.price
                    self.buy_cover_order = None
                    self.put_long_orders()
            if self.sell_cover_order and order.order_id == self.sell_cover_order.order_id:
                new_traded = order.traded - self.sell_cover_order.traded
                if new_traded > 0:
                    self.position_long -= new_traded
                    self.exchange_info["pos_base_symbol"] += new_traded * self.sell_cover_order.price * (
                            1 - self.cover_rate)
                    self.exchange_info["pos_target_symbol"] -= new_traded
                self.sell_cover_order = copy(order)
                if not order.is_active():
                    new_return_frozen_volume = self.sell_cover_order.volume - self.sell_cover_order.traded
                    self.exchange_info["pos_target_symbol"] += new_return_frozen_volume
                    self.sell_cover_order = None
                    self.put_short_orders()
        if all_new_traded_long > 0:
            if self.sell_cover_order:
                self.impl.cancel_order(self.sell_cover_order.order_id)
            price = self.avg_price_short * (1 - self.config["short_config"]["profit_spread"] / 100.0)
            self.sell_cover_order = self.impl.send_order(self.config["symbol_pair"], "sell", price,
                                                         abs(self.position_long))

            log_service_manager.write_log(
                "[cover_orders] [short:{},{}]".format(self.avg_price_short, self.position_short))

        if all_new_traded_short > 0:
            if self.buy_cover_order:
                self.impl.cancel_order(self.buy_cover_order.order_id)
            price = self.avg_price_long * (1 + self.config["long_config"]["profit_spread"] / 100.0)
            self.buy_cover_order = self.impl.send_order(self.config["symbol_pair"], "buy", price,
                                                        abs(self.position_short))
            log_service_manager.write_log("[cover_orders] [long:{},{}]".format(self.avg_price_long, self.position_long))

    def run(self):
        self.update_exchange()
        self.update_account()
        count = 0
        while True:
            try:
                if count % 6 == 0:
                    self.cancel_not_belong_orders()
                self.ask, self.bid = self.impl.get_price(self.config["symbol_pair"])
                if self.ask and self.bid:
                    # log_service_manager.write_log("[Info] cover_orders")
                    self.cover_orders()
                    # log_service_manager.write_log("[Info] put_orders")
                    self.put_orders()
                count += 1
            except Exception as ex:
                log_service_manager.write_log("[Error] MovMakerStrategy,run ex:{}".format(ex))


if __name__ == "__main__":
    s = MovMakerStrategy(account_config, strategy_config)
    s.run()
