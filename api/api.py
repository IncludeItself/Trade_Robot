import logging

from datetime import datetime
from config.env_config import config
from logs import logger
from mock.excel import excel_to_dict_list
from api.get_sina_stock import get_sina_stock

access_time = 0

def get_symbol_bar_data(exchange,stock_code):
    logger = logging.getLogger(__name__)
    test_logger = logging.getLogger("test_logger")
    if config.env == "TEST":
        global access_time
        access_time += 1
        if access_time>2000:
            access_time=1
        data = excel_to_dict_list("mock/simulate_response.xlsx","bar_data" ,rows=[access_time])
        # 过滤，保留data中symbol字段为stock_code的item
        data = [item for item in data if item["symbol"] == stock_code]
        if data is None or len(data) == 0:
            return None
        return {
            "code": stock_code,
            "name": data[0]["name"],
            "timestamp": datetime.now().timestamp(),
            "pre_close": float(data[0]["pre_close"]),
            "open": float(data[0]["open"]),
            "price": float(data[0]["price"]),
            "highest": float(data[0]["highest"]),
            "lowest": float(data[0]["lowest"]),
            "buy1": float(data[0]["buy1"]),
            "buy2": float(data[0]["buy2"]),
            "buy3": float(data[0]["buy3"]),
            "buy4": float(data[0]["buy4"]),
            "buy5": float(data[0]["buy5"]),
            "sell1": float(data[0]["sell1"]),
            "sell2": float(data[0]["sell2"]),
            "sell3": float(data[0]["sell3"]),
            "sell4": float(data[0]["sell4"]),
            "sell5": float(data[0]["sell5"]),
            "volume": float(data[0]["volume"]),
            "turnover": float(data[0]["turnover"])
        }
    if exchange.lower() == "a":
        data_list = get_sina_stock(stock_code)
        timestamp = int(datetime.strptime(data_list[30] + " " + data_list[31], "%Y-%m-%d %H:%M:%S").timestamp())
        return {
            "code": stock_code,
            "name": data_list[0],
            "timestamp": timestamp,
            "pre_close": float(data_list[1]),
            "open": float(data_list[2]),
            "price": float(data_list[3]),
            "highest": float(data_list[4]),
            "lowest": float(data_list[5]),
            "buy1": float(data_list[6]),
            "buy2": float(data_list[7]),
            "buy3": float(data_list[8]),
            "buy4": float(data_list[9]),
            "buy5": float(data_list[10]),
            "sell1": float(data_list[11]),
            "sell2": float(data_list[12]),
            "sell3": float(data_list[13]),
            "sell4": float(data_list[14]),
            "sell5": float(data_list[15]),
            "volume": float(data_list[16]),
            "turnover": float(data_list[17])
        }
    return None
