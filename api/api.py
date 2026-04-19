import logging

from datetime import datetime
from functools import wraps
import time

import requests
from binance import BinanceRequestException, BinanceAPIException

from api.bnapi import BnApi
from config.env_config import config
from logs import logger
from mock.excel import excel_to_dict_list
from api.get_sina_stock import get_sina_stock
from wecom.wecom import send_wecom_msg

access_time = 0

def retry_api(max_retries=5, delay=0.5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (BinanceRequestException, ConnectionError,
                    requests.exceptions.ConnectionError,  # 新增
                    ConnectionResetError,                 # 新增
                    ConnectionAbortedError,                # 新增
                    ConnectionRefusedError,                # 新增
                    requests.exceptions.ReadTimeout,        # 新增
                    requests.exceptions.ConnectTimeout,    # 新增
                    requests.exceptions.SSLError,         # 新增
                    requests.exceptions.ChunkedEncodingError,  # 新增
                    TimeoutError) as e:
                    # 只重试【网络类错误】
                    last_exception = e
                    print(f"⚠️  网络波动，第 {attempt} 次重试，等待 {delay}s...")
                    time.sleep(delay)
                except BinanceAPIException as e:
                    # 币安服务器错误（5xx）也重试，业务错误（4xx）不重试
                    last_exception = e
                    if 500 <= e.code <= 599 or e.code in [-1003, -1006, -1007]:
                        print(f"⚠️  服务端错误，第 {attempt} 次重试，等待 {delay}s...")
                        time.sleep(delay)
                    else:
                        pass
                        # 业务错误（key错、参数错）直接失败，不重试
                        # raise
            # 全部重试失败 → 抛出最终异常
            send_wecom_msg(f"❌ 连续 {max_retries} 次接口调用失败")
            # raise Exception(f"❌ 连续 {max_retries} 次接口调用失败") from last_exception
        return wrapper
    return decorator

@retry_api(max_retries=5, delay=0.5)
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
            line = bn.client.futures_klines(symbol=stock_code, interval='1m', limit=1)
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

# @retry_api(max_retries=5, delay=0.5)
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


@retry_api(max_retries=5, delay=0.5)
def place_order_api(pending_order:dict, platform:str):
    logger=logging.getLogger("api->place_order_api")
    if platform.lower() == "bn":
        side = "BUY" if pending_order["qty"] > 0 else "SELL"
        qty_str = str(abs(pending_order["qty"]))
        position_side = "LONG"
        bn = BnApi()
        try:
            bn.client.futures_create_order(
                symbol=pending_order["symbol"],
                type="LIMIT",
                side=side,
                quantity=qty_str,
                price=str(pending_order["price"]),
                timeInForce='GTC',
                positionSide=position_side
            )
        except Exception as e:
            position_side="SHORT"
            try:
                bn.client.futures_create_order(
                    symbol=pending_order["symbol"],
                    type="LIMIT",
                    side=side,
                    quantity=qty_str,
                    price=str(pending_order["price"]),
                    timeInForce='GTC',
                    positionSide=position_side
                )
            except Exception as e:
                logger.error(f"place order bn error: {e}")
                send_wecom_msg(f"place order bn error: {e}")

@retry_api(max_retries=5, delay=0.5)
def get_positions(symbol:str, platform:str):
    logger=logging.getLogger("api->get_positions")
    if platform.lower() == "bn":
        bn = BnApi()

        positions = bn.client.futures_position_information(symbol=symbol)
        logger.info(f"get positions bn: {positions}")
        if not positions:
            return 0
        return sum(float(order["positionAmt"]) for order in positions),max(float(order["updateTime"]) for order in positions)/1000

    return None


@retry_api(max_retries=5, delay=0.5)
def get_current_price(symbol: str, platform: str):
    logger = logging.getLogger("api->get_current_price")

    if platform.lower() == "bn":
        bn = BnApi()
        price = float(bn.client.futures_symbol_ticker(symbol=symbol)["price"])
        logger.info(f"get current price bn: {price}")
        return price
    else:
        return 0


@retry_api(max_retries=5, delay=0.5)
def get_filled_orders(symbol:str,start_time="0",end_time="0",platform:str="bn"):
    logger=logging.getLogger("api->get_filled_orders")
    if platform.lower() == "bn":
        bn = BnApi()

        filled_rows = bn.client.futures_account_trades(
            symbol=symbol,
            limit="1000",
            startTime=start_time,
            endTime=end_time,
            fromId=None
        )

        return filled_rows
    return None

@retry_api(max_retries=5, delay=0.5)
def get_pending_orders(symbol:str,platform:str="bn"):
    logger=logging.getLogger("api->get_pending_orders")
    if platform.lower() == "bn":
        bn = BnApi()
        pending_orders = bn.client.futures_get_open_orders(symbol=symbol)
        logger.info(f"get pending orders bn: {pending_orders}")
        return pending_orders
    return None
