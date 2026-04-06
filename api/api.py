import logging

from datetime import datetime

from api.bnapi import BnApi
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
            "date":datetime.now().date(),
            "time":datetime.now().time(),
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
            "value": float(data[0]["value"])
        }
    if exchange.lower() == "a":
        data_list = get_sina_stock(stock_code)
        timestamp = datetime.strptime(data_list[30] + " " + data_list[31], "%Y-%m-%d %H:%M:%S").timestamp()
        return {
            "code": stock_code,
            "name": data_list[0],
            "timestamp": timestamp,
            "date":data_list[30],
            "time":data_list[31],
            "pre_close": float(data_list[1]),
            "open": float(data_list[2]),
            "price": float(data_list[3]),
            "highest": float(data_list[4]),
            "lowest": float(data_list[5]),
            "buy1": float(data_list[6]),
            "buy2": float(data_list[13]),
            "buy3": float(data_list[15]),
            "buy4": float(data_list[17]),
            "buy5": float(data_list[19]),
            "sell1": float(data_list[7]),
            "sell2": float(data_list[21]),
            "sell3": float(data_list[23]),
            "sell4": float(data_list[25]),
            "sell5": float(data_list[27]),
            "volume": float(data_list[8]),
            "value": float(data_list[9])
        }
    elif exchange.lower() == "bn":
        try:
            bn = BnApi()
            line = bn.client.futures_klines(symbol=stock_code, interval='5m', limit=1)
            # logger.info(f"get bar data bn: {line}")
            if line and len(line) > 0:
                timestamp = line[0][0] / 1000
                date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                time = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                return {
                    "code": stock_code,
                    "timestamp": timestamp,
                    "price": line[0][4],
                    "pre_close": line[0][1],
                    "open": line[0][1],
                    "highest": line[0][2],
                    "lowest": line[0][3],
                    "volume": line[0][5],
                    "value": line[0][7],
                    "total_volume": 0,
                    "total_value": 0,
                    "date": date,
                    "time": time,
                }
            else:
                return None

        except Exception as e:
            logger.error(f"get bar data bn error: {e}")
            return None
    return None


def get_bar_history(exchange,prefix,symbol):
    if exchange.lower() == "a":
        data_list = get_sina_stock(prefix+symbol)

        return {
            "symbol": symbol,
            "date": data_list[30],
            # "pre_close": float(data_list[1]),
            "open": float(data_list[2]),
            "close": float(data_list[3]),
            "highest": float(data_list[4]),
            "lowest": float(data_list[5]),
            # "buy1": float(data_list[6]),
            # "buy2": float(data_list[7]),
            # "buy3": float(data_list[8]),
            # "buy4": float(data_list[9]),
            # "buy5": float(data_list[10]),
            # "sell1": float(data_list[11]),
            # "sell2": float(data_list[12]),
            # "sell3": float(data_list[13]),
            # "sell4": float(data_list[14]),
            # "sell5": float(data_list[15]),
            "volume": float(data_list[8]),
            "value": float(data_list[9])
        }
    return None