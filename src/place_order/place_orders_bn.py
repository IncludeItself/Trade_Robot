import logging

import math

from api.api import place_order_api, get_current_price, get_pending_orders
from src import state
from src.common import sell_order_exist, buy_order_exist


def place_order_bn(symbol_dict:dict)->bool:
    symbol=symbol_dict["symbol"]
    current_price=get_current_price(symbol,"bn")
    if not sell_order_exist(symbol_dict):
        place_order_direction(symbol,current_price,"sell")
    if not buy_order_exist(symbol_dict):
        place_order_direction(symbol,current_price,"buy")

def place_order_direction(symbol:str, price, direction):
    """
    在没有挂单时的初始下单
    :param symbol: 合约符号
    :param price: 下单价格
    :param direction: 下单方向
    :return: 是否成功下单
    """

    logger = logging.getLogger("place_order_bn")
    pos_qty=state.get_position(symbol)["pos_qty"]
    logger.info(f"current position qty:{symbol}={pos_qty}")
    symbol_dict=state.get_symbol_info(symbol)
    if direction.lower() == "sell":
        grid_up=state.get_grid_up(symbol,price)
        logger.info(f"grid_up:{grid_up}")
        count=math.ceil(math.log(grid_up["price"]/price)/math.log(1+grid_up["f"]))
        logger.info(f"count:{count}")
        qty=max(round((pos_qty-grid_up["qty"])/count,int(symbol_dict["qty_decimal"])),symbol_dict["least_trade_qty"])
        while pos_qty>grid_up["qty"]:
            price*=1+grid_up["f"]
            place_order_api({"symbol":symbol,"price":round(price,int(symbol_dict['decimal'])),"qty":-float(qty)},"bn")
            pos_qty-=qty

    else:
        grid_down=state.get_grid_down(symbol,price)
        logger.info(f"grid_down:{grid_down}")
        count=math.ceil(math.log(price/grid_down["price"])/math.log(1+grid_down["f"]))
        logger.info(f"count:{count}")
        qty=max(round((grid_down["qty"]-pos_qty)/count,int(symbol_dict["qty_decimal"])),symbol_dict["least_trade_qty"])
        while pos_qty<grid_down["qty"]:
            price/=1+grid_down["f"]
            place_order_api({"symbol":symbol,"price":round(price,int(symbol_dict['decimal'])),"qty":float(qty)},"bn")
            pos_qty+=qty



