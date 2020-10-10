# coding=utf-8

strategy_config = {
    "symbol_pair": "BTM/USDT",  # 交易对
    "long_config": {  # 挂多单的参数
        "run": True,  # 是否运行
        "start_volume": 0.1,  # 首单占总资金量的  (百分之)
        "inc_volume": 0.1,  # 每次挂单增量    (百分之)
        "inc_spread": 0.6,  # 每次挂单间距增加  (百分之)
        "put_order_num": 6,  # 挂买单数量
        "profit_spread": 0.3,  # 哪个价格盈利出
        "avg_price": 0,  # 初始持仓均价
        "now_position": 0  # 初始需要平仓的买单数量
    },
    "short_config": {  # 挂空单的参数
        "run": True,  # 是否运行
        "start_volume": 0.1,  # 首单占总资金量的 (百分之)
        "inc_volume": 0.1,  # 每次挂单增量  (百分之)
        "inc_spread": 0.1,  # 每次挂单间距增加 (百分之)
        "put_order_num": 6,  # 挂卖单数量
        "profit_spread": 0.3,  # 哪个价格盈利出
        "avg_price": 0,  # 初始持仓均价
        "now_position": 0  # 初始需要平仓的卖单数量
    },
    "exchange_info": {
        "fee_rate": 0.001,  # 手续费
        "pos_target_symbol_percent_use": 0.03,  # 准备使用总资金的比例  (百分之)  如 btm/usdt中的btm
        "pos_base_symbol_percent_use": 40  # 准备使用总资金的比例  (百分之)  如 btm/usdt中的usdt
    }
}

account_config = {
    "private_key": ""
}
