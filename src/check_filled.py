import logging
import threading
from datetime import datetime
import time

from data.sqllite import get_bar_data, delete_tbl_pending_orders, insert_filled_order, get_filled_orders_symbol, \
    get_pending_orders_symbol, update_tbl_filled_orders_symbol
from src import state
from src.locks import orders_lock
from wecom.wecom import send_wecom_msg


def update_tbl_filled_orders(pending_order):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("update_tbl_filled_orders")
    test_logger.info(f"{pending_order['symbol']} {pending_order['direction']} {pending_order['price']} 已成交")
    symbol_filled=state.t_filled_orders.get(pending_order["symbol"],[])
    if symbol_filled and len(symbol_filled)>0:
        old_pos=symbol_filled[0]["pos_qty"]
    else:
        symbol_info=next(symbol_info for symbol_info in state.t_symbols if symbol_info["symbol"]==pending_order["symbol"])
        old_pos=symbol_info["core_position"]
    filled={
        "symbol": pending_order["symbol"],
        "timestamp": datetime.now(),
        "quantity": pending_order["qty"],
        "price": pending_order["price"],
        "pos_qty": old_pos+pending_order["qty"],
    }
    test_logger.info(f"插入新成交记录的filled_order：{filled}")
    logger.info(f"插入新成交记录的filled_order：{filled}")
    insert_filled_order(filled)
    state.t_filled_orders[pending_order["symbol"]]=get_filled_orders_symbol(pending_order["symbol"])

    filled_symbol=state.t_filled_orders[pending_order["symbol"]]
    index=0
    cum_qty=0
    profit=0
    while index<len(filled_symbol):
        cum_qty+=filled_symbol[index]["quantity"]
        profit+=-filled_symbol[index]["quantity"]*filled_symbol[index]["price"]
        if round(cum_qty,2)==0:
            for i in range(0,index+1):
                filled_symbol[i]["cleared"]=1
            test_logger.info(f"结清{index+1}条成交记录，利润：{profit}")
            logger.info(f"结清{index+1}条成交记录，利润：{profit}")
            send_wecom_msg(f"结清{index+1}条成交记录，利润：{profit}")
            # 将filled_symbol写入数据库
            update_tbl_filled_orders_symbol(filled_symbol)
            state.t_filled_orders[pending_order["symbol"]] = get_filled_orders_symbol(pending_order["symbol"])
            break

        index+=1

    pass


def update_tbl_pending_orders(pending_order):
    logger=logging.getLogger("update_tbl_pending_orders")
    logger.info(f"删除挂单{pending_order['id']}")
    delete_tbl_pending_orders(pending_order["id"])
    state.t_pending_orders[pending_order["symbol"]]=get_pending_orders_symbol(pending_order["symbol"])
    update_tbl_filled_orders(pending_order)
    pass


def check_filled():
    """你的核心业务逻辑（持续运行的任务）"""
    test_logger = logging.getLogger("test_logger")
    logger = logging.getLogger("check_filled")
    test_logger.info(f"✅ check_filled任务启动 | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    # 循环执行核心逻辑，直到标志位被置为False
    while state.is_task_running:
        for symbol_info in state.t_symbols:
            if symbol_info["platform"]=="ths" and state.is_in_a_period:
                pending_orders=state.t_pending_orders[symbol_info["symbol"]]
                test_logger.info(f"{symbol_info['symbol']}当前有 {len(pending_orders)} 条挂单：{pending_orders}")
                for pending_order in pending_orders:
                    # 检查订单是否已成交
                    if symbol_info and symbol_info["platform"]=="ths" :
                        test_logger.info(f"此挂单时间戳为：{pending_order['timestamp']}，现在的时间戳：{datetime.now().timestamp()}")
                        bars=get_bar_data(symbol_info["symbol"],pending_order["timestamp"],datetime.now().timestamp())
                        test_logger.info(f"获取到的bar数据{len(bars)}条")
                        # 订单已成交，从数据库删除
                        if pending_order["direction"]=="Sell" and any(bar["price"]>pending_order["price"] for bar in bars) or pending_order["direction"]=="Buy" and any(bar["price"]<pending_order["price"] for bar in bars):
                            with orders_lock:
                                test_logger.info(f"{pending_order['symbol']} {pending_order['direction']} {pending_order['price']} 已经成交")
                                logger.info(f"订单{pending_order}已成交")
                                send_wecom_msg(f"订单{pending_order}已成交")
                                # 已经成交
                                update_tbl_pending_orders(pending_order)
                            continue

        time.sleep(6)  # 模拟业务执行间隔，根据你的需求调整

    print(f"❌ check_filled任务停止 | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
