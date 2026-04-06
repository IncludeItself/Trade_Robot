import datetime
import logging
import time

from api.bnapi import BnApi
from data.sqllite import get_bar_data, insert_pending_order, get_pending_orders_symbol
from exception.exception_handler import exception_handler
from src.trade_advisor import price_advice_a
from src import state
from src.grid_limit import grid_allow
from src.locks import orders_lock
from src.stack_limit import stack_support_buy, stack_support_sell
from src.trade_advisor_bn import price_advice_bn
from wecom.wecom import send_wecom_msg


def place_order_ths(symbol:str, qty, price, direction):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("place_order_ths")
    test_logger.info(f"✅ 在同花顺桌面版上操作：{direction} {symbol} ，数量：{qty} ，价格：{price}")
    logger.info(f"✅ 在同花顺桌面版上操作：{direction} {symbol} ，数量：{qty} ，价格：{price}")
    pending_order={}
    if True:
        if direction=="Buy":
            pending_order={"symbol":symbol,"qty":qty,"price":price,"direction":direction,"timestamp":datetime.datetime.now().timestamp()}
        else:
            pending_order={"symbol":symbol,"qty":-qty,"price":price,"direction":direction,"timestamp":datetime.datetime.now().timestamp()}
        logger.info(f"将挂单 {pending_order}插入到tbl_appending_order")
        insert_pending_order(pending_order)
        state.t_pending_orders[symbol]=get_pending_orders_symbol(symbol)
    pass


def place_order(symbol, qty, price, direction):

    logger=logging.getLogger("place_order")
    test_logger = logging.getLogger("test_logger")
    logger.info(f"place_order: {symbol} /数量：{qty}/ 价格：{price} / 方向：{direction}")
    if qty<=0:
        test_logger.info(f"挂单数量小于等于0，不操作挂单")
        return
    symbol_info=next((s for s in state.t_symbols if s["symbol"]==symbol), None)
    if symbol_info is None:
        test_logger.info(f"❌ 未找到符号 {symbol} 的信息，不挂单")
        return
    # 执行订单操作
    if symbol_info["platform"]=="ths":
        send_wecom_msg(f"place_order in ths: {symbol} /数量：{qty}/ 价格：{price} / 方向：{direction}")
        logger.info(f"place_order in ths: {symbol} /数量：{qty}/ 价格：{price} / 方向：{direction}")
        place_order_ths(symbol, qty, price, direction)
    elif symbol_info["platform"]=="bn":
        bn=BnApi()

        try:
            bn.client.futures_create_order(
                symbol=symbol,
                type="LIMIT",
                side=direction.upper(),
                quantity=str(abs(round(qty,3))),
                price=str(round(price,int(symbol_info["decimal"]))),
                timeInForce='GTC',
                positionSide='LONG'
            )
        except Exception as e:
            exception_handler(e,f"币安挂单时错误,价格：{str(round(price,int(symbol_info["decimal"])))}，数量：{str(abs(round(qty,3)))}")
            pass
    pass

def sell_order_exist(symbol):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("sell_order_exist")
    symbol_pending=state.t_pending_orders[symbol]
    test_logger.info(f"目前存在的挂单：{symbol_pending}")
    result=any(order["symbol"]==symbol and order["direction"]=="Sell" for order in symbol_pending)
    test_logger.info(f"{symbol} 是否存在卖出订单: {result}")
    logger.info(f"{symbol} 是否存在卖出订单: {result}")
    return result


def buy_order_exist(symbol):
    test_logger = logging.getLogger("test_logger")
    symbol_pending=state.t_pending_orders[symbol]
    test_logger.info(f"目前存在的挂单：{symbol_pending}")
    result=any(order["symbol"]==symbol and order["direction"]=="Buy" for order in symbol_pending)
    test_logger.info(f"{symbol} 是否存在买入订单: {result}")
    return result


# def place_bn_orders(symbol):
#     """你的核心业务逻辑（持续运行的任务）"""
#     test_logger = logging.getLogger("test_logger")
#     logger=logging.getLogger("place_bn_orders")
#     pending_orders=state.t_pending_orders[symbol['symbol']]
#     bar_data=get_bar_data(symbol["symbol"],0,datetime.datetime.now().timestamp())
#
#     result=price_advice_bn(bar_data, symbol)
#     signal, reason, price = result["signal"], result["reason"], result["price"]
#     test_logger.info(f"{symbol['symbol']} 分析结果：{signal} {reason} 价格：{price}")
#     logger.info(f"{symbol['symbol']} 分析结果：{signal} {reason} 价格：{price}")
#
#     with orders_lock:
#         if signal=="Buy":
#             for i in range(5):





def place_orders():
    """你的核心业务逻辑（持续运行的任务）"""
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("place_orders")
    test_logger.info(f"✅ place_orders任务启动 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 循环执行核心逻辑，直到标志位被置为False
    while state.is_task_running:
        for symbol in state.t_symbols:
            bar_data = get_bar_data(symbol["symbol"], 0, datetime.datetime.now().timestamp())
            result=None
            if symbol["exchange"]=="a" and state.is_in_a_period:
                result=price_advice_a(bar_data, symbol)
            elif symbol["exchange"]=="bn" and state.is_in_bn_period:
                result = price_advice_bn(bar_data, symbol)
            if result is None:
                continue
            signal, reason, price = result["signal"], result["reason"], result["price"]
            test_logger.info(f"{symbol['symbol']} 分析结果：{signal} {reason} 价格：{price}")
            logger.info(f"{symbol['symbol']} 分析结果：{signal} {reason} 价格：{price}")
            if signal=="Wait":
                continue
            with orders_lock:
                if not sell_order_exist(symbol["symbol"]) and signal=="Sell":
                    qty_stack,stack_price,pos_qty=stack_support_sell(symbol,price)
                    qty_grid=grid_allow("Sell",symbol["symbol"],price,pos_qty)
                    if stack_price>round(bar_data[-1]["pre_close"]*(1+symbol["upper_limit"]),2):
                        test_logger.info(f"{symbol['symbol']} 卖出价格超过上轨，不操作挂单")
                        logger.info(f"{symbol['symbol']} 卖出价格超过上轨，不操作挂单")
                        continue
                    # 执行卖出操作
                    place_order(symbol["symbol"], min(qty_stack,qty_grid),max(price,stack_price), "Sell")

                if not buy_order_exist(symbol["symbol"]) and signal=="Buy":
                    qty_stack,stack_price,pos_qty=stack_support_buy(symbol,price)
                    qty_grid=grid_allow("Buy",symbol["symbol"],price,pos_qty)
                    # 执行买入操作
                    if stack_price<round(bar_data[-1]["pre_close"]*(1-symbol["lower_limit"]),2):
                        test_logger.info(f"{symbol['symbol']} 买入价格低于下轨，不操作挂单")
                        logger.info(f"{symbol['symbol']} 买入价格低于下轨，不操作挂单")
                        continue
                    # 执行买入操作
                    place_order(symbol["symbol"], min(qty_stack,qty_grid),min(price,stack_price), "Buy")


        time.sleep(10)  # 模拟业务执行间隔，根据你的需求调整

    print(f"❌ place_orders任务停止 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")