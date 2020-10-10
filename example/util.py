# coding=utf-8

from enum import Enum
import logging
import os
from multiprocessing import Value
from datetime import datetime
from decimal import Decimal

EMPTY_STRING = ""
EMPTY_UNICODE = ""
EMPTY_FLOAT = 0
EMPTY_INT = 0


def get_round_order_price(price, price_tick):
    """
    根据交易所的每个合约的最小交易精度数据，得到准备的下单价格
    up=True 是 返回价格 >= price  (通过加一个或0个精度得到)
    up=False 是 返回价格 <= price (通过减1一个或0个精度得到)
    """
    if price_tick < 1e-12:
        return price
    price = Decimal(str(price))
    price_tick = Decimal(str(price_tick))
    rounded = float(int(round(price / price_tick)) * price_tick)
    return rounded


def get_folder_path(folder_name):
    """
    Get path for temp folder with folder name.
    """
    folder_path = os.path.join(str("."), str(folder_name))
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    return folder_path


def get_str_dt_use_timestamp(nt, mill=1000):
    """
    从时间戳中获得日期
    """
    dt = datetime.fromtimestamp(float(nt) / mill)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class Status(Enum):
    """
    Order status.
    """
    SUBMITTING = "SUBMITTING"  # 已提交
    NOTTRADED = "NOTTRADED"  # 未成交
    PARTTRADED = "PARTTRADED"  # 部分成交
    ALLTRADED = "ALLTRADED"  # 全部成交
    CANCELLED = "CANCELLED"  # 已撤销
    REJECTED = "REJECTED"  # 拒绝


STATUS_MOV2VT = {
    "submitted": Status.SUBMITTING.value,
    "open": Status.NOTTRADED.value,
    "partial": Status.PARTTRADED.value,
    "filled": Status.ALLTRADED.value,
    "canceled": Status.CANCELLED.value,
}

LIVE_LIMIT_ORDER_CONDITIONS = [Status.SUBMITTING.value, Status.NOTTRADED.value, Status.PARTTRADED.value]


class OrderData(object):
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""

        # 代码编号相关
        self.symbol = EMPTY_STRING  # 合约代码
        self.order_id = EMPTY_STRING  # 订单编号

        # 报单相关
        self.direction = EMPTY_UNICODE  # 报单方向
        self.price = EMPTY_FLOAT  # 报单价格
        self.volume = EMPTY_INT  # 报单总数量
        self.traded = EMPTY_INT  # 报单成交数量
        self.status = Status.SUBMITTING.value  # 报单状态

        self.order_time = EMPTY_STRING  # 发单时间
        self.cancel_time = EMPTY_STRING  # 撤单时间

        self.gateway_name = EMPTY_STRING  # gateway

    def is_active(self):
        return self.status in LIVE_LIMIT_ORDER_CONDITIONS


class LogService(object):

    def __init__(self):
        self.level = logging.DEBUG
        self.logger = logging.getLogger("tumbler")
        self.logger.setLevel(self.level)

        self.lock_counter = Value('i', 0)

        self.formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()
        self.add_console_handler()
        self.add_file_handler()

    def write_log(self, msg, level=logging.INFO):
        """
        write log info
        """
        with self.lock_counter.get_lock():
            self.logger.log(level, msg)

    def add_null_handler(self):
        """
        Add null handler for logger.
        """
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self):
        """
        Add console output of log.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self):
        """
        Add file output of log.
        """
        today_date = datetime.now().strftime("%Y%m%d")
        filename = "vt_{}.log".format(today_date)
        log_path = get_folder_path("log")
        file_path = os.path.join(log_path, filename)

        file_handler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)


log_service_manager = LogService()
