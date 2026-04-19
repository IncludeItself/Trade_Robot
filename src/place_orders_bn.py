import logging
from datetime import datetime

from dateparser import date

from api.api import place_order_api, get_current_price, get_pending_orders
from api.bnapi import BnApi
from exception.exception_handler import exception_handler
from logs import logger
from src import state
from src.locks import orders_lock


def cal_line(P1, q1, P2, q2, k):
    """
    求解幂函数方程 P(q) = A/(q-c)^k 的参数 A 和 c

    参数:
        P1 (float): 第一点的函数值
        q1 (float): 第一点的自变量值
        P2 (float): 第二点的函数值
        q2 (float): 第二点的自变量值
        k (float): 幂指数

    返回:
        tuple: (A, c) 计算得到的两个参数

    异常:
        ValueError: 输入参数不合法（除零、负数开方等）
    """
    # 基础参数校验
    if k == 0:
        raise ValueError("幂指数 k 不能为 0")
    if P1 <= 0 or P2 <= 0:
        raise ValueError("P1 和 P2 必须为正数")

    try:
        # 计算 1/k 次方
        p1_pow = P1 ** (1 / k)
        p2_pow = P2 ** (1 / k)

        # 计算分母，避免除零错误
        denominator = p1_pow - p2_pow
        if abs(denominator) < 1e-12:
            raise ValueError("两点参数导致分母为 0，无唯一解")

        # 求解 c
        c = (q2 * p1_pow - q1 * p2_pow) / denominator

        # 求解 A
        A = P1 * (q1 - c) ** k

        return A, c

    except Exception as e:
        raise ValueError(f"参数计算失败: {str(e)}")


def order_exist(symbol,order_type="Sell"):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("order_exist")
    result=True
    if symbol["platform"]=="bn":
        try:
            symbol_pending=state.t_pending_orders.get(symbol["symbol"],[])
            if not symbol_pending:
                result=False
            result=any(order["side"]==order_type.upper() for order in symbol_pending)
            test_logger.info(f"{symbol['symbol']} 是否存在{order_type}订单: {result}")
            logger.info(f"{symbol['symbol']} 是否存在{order_type}订单: {result}")
        except Exception as e:
            exception_handler(e,f"币安获取{symbol['symbol']}的挂单时错误：{e}")
    return result


def filled_recently_or_gap_small(symbol,current_price,order_type="Sell")->bool:
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("filled_recently_or_gap_small")
    result=False
    filled=state.t_filled_orders.get(symbol["symbol"],[])
    now_timestamp=datetime.now().timestamp()
    sell_filled=next((order for order in filled if order["quantity"]<0),None)
    if order_type=="Sell" and sell_filled and now_timestamp-int(sell_filled["timestamp"])<2*60*60:
        result=True
    buy_filled=next((order for order in filled if order["quantity"]>0),None)
    if order_type=="Buy" and buy_filled and now_timestamp-int(buy_filled["timestamp"])<2*60*60:
        result=True
    pending=state.t_pending_orders.get(symbol["symbol"],[])
    sell_pending=next((order for order in pending if order["side"]==order_type.upper()),None)
    if order_type=="Sell" and sell_pending and current_price>0 and float(sell_pending["price"])/current_price-1<=0.001:
        result=True
    buy_pending=next((order for order in pending if order["side"]==order_type.upper()),None)
    if order_type=="Buy" and buy_pending and current_price>0 and current_price/float(buy_pending["price"])-1<=0.001:
        result=True
    return result


def change_pending_price(symbol,current_price, direction="Sell"):

    pass


def place_orders_by_line(symbol, current_price, direction="Sell"):
    logger=logging.getLogger("place_orders_by_line")
    holding_qty = state.get_position(symbol["symbol"])["pos_qty"]
    grid_up = state.get_grid_up(symbol["symbol"], current_price)
    grid_down = state.get_grid_down(symbol["symbol"], current_price)
    if grid_down is None or grid_up is None:
        return
    A,c=cal_line(grid_up["price"]/(1+grid_down["f"]),grid_up["qty"],grid_down["price"],grid_down["qty"], grid_down["k"])
    # current_down=A/(holding_qty-c)**symbol["k"]
    # current_up=current_down*(1+symbol["f"])
    if symbol["least_trade_qty"]==0:
        pass
    if direction=="Sell":
        count=(holding_qty-grid_up["qty"])/symbol["least_trade_qty"]
        while holding_qty>grid_up["qty"]:
            price=max(grid_down["f"]*A/(holding_qty-c)**grid_down["k"],current_price*1.0001)
            try:
                logger.info(f"{symbol['symbol']} 卖出{symbol['least_trade_qty']}，价格{price}")
                place_order_api({"symbol":symbol["symbol"], "qty":-symbol["least_trade_qty"], "price":round(price, int(symbol["decimal"]))}, "bn")
                holding_qty-=count
            except Exception as e:
                exception_handler(e,f"币安卖出{symbol['symbol']}时错误：{e}")
                pass
    elif direction=="Buy":
        count=(grid_down["qty"]-holding_qty)/symbol["least_trade_qty"]
        while holding_qty<grid_down["qty"]:
            holding_qty += count
            price=min(A/(holding_qty-c)**grid_down["k"],current_price*0.9999)
            try:
                logger.info(f"{symbol['symbol']} 买入{symbol['least_trade_qty']}，价格{price}")
                place_order_api({"symbol":symbol["symbol"], "qty":symbol["least_trade_qty"], "price":round(price, int(symbol["decimal"]))}, "bn")
            except Exception as e:
                exception_handler(e,f"币安买入{symbol['symbol']}时错误：{e}")
                pass
        pass
    pass


def place_order_bn(symbol):

    current_price=get_current_price(symbol["symbol"], symbol["platform"])
    if current_price is None:
        return

    try:
        state.t_pending_orders[symbol["symbol"]]=get_pending_orders(symbol["symbol"])
    except Exception as e:
        exception_handler(e,f"币安获取{symbol['symbol']}的挂单时错误：{e}")
        return
    with orders_lock:
        if order_exist(symbol,"Sell"):
            if not filled_recently_or_gap_small(symbol,current_price,"Sell"):
                change_pending_price(symbol,current_price,"Sell")
        else:
            place_orders_by_line(symbol,current_price,"Sell")
        if order_exist(symbol,"Buy"):
            if not filled_recently_or_gap_small(symbol,current_price,"Buy"):
                change_pending_price(symbol,current_price,"Buy")
        else:
            place_orders_by_line(symbol,current_price,"Buy")
        pass