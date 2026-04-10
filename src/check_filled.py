import logging
import threading
from datetime import datetime
import time

from api.bnapi import BnApi
from data.sqllite import get_bar_data, delete_tbl_pending_orders, insert_filled_order, get_filled_orders_symbol, \
    get_pending_orders_symbol, update_tbl_filled_orders_symbol
from exception.exception_handler import exception_handler
from src import state
from src.locks import orders_lock
from src.public_ip import get_public_ip
from wecom.wecom import send_wecom_msg


def cal_commission(pending_order):
    symbol_info=next(symbol_info for symbol_info in state.t_symbols if symbol_info["symbol"]==pending_order["symbol"])
    if symbol_info["pre_fix"].lower()=="sh":
        """
            计算财通证券交易税费（完全复刻 Excel 公式逻辑）
            :param trade_type: 交易方向：>0=买入，<0=卖出
            :param amount: 交易金额（成交金额）
            :return: 交易税费（保留2位小数）
            """
        amount=pending_order["qty"]*pending_order["price"]
        if pending_order["direction"]=="Buy":
            # 买入逻辑
            fee1 = round(amount * 0.00001, 2)
            # 计算佣金：最低5元
            commission = round(amount * 0.0002354, 2)
            commission = 5 if commission <= 5 else commission
            total_fee = fee1 + commission
        else:
            # 卖出逻辑
            fee1 = round(-amount * 0.00001, 2)
            fee2 = round(-amount * 0.0005, 2)
            # 计算佣金：最低5元
            commission = round(-amount * 0.0002354, 2)
            commission = 5 if commission <= 5 else commission
            total_fee = fee1 + fee2 + commission
        return total_fee
    else:
        return 0
    pass


def update_tbl_filled_orders(filled):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("update_tbl_filled_orders")
    test_logger.info(f"插入新成交记录的filled_order：{filled}")
    logger.info(f"插入新成交记录的filled_order：{filled}")
    insert_filled_order(filled)
    state.t_filled_orders[filled["symbol"]]=get_filled_orders_symbol(filled["symbol"])
    pass

def clear_orders(symbol:str):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("clear_orders")
    filled_symbol = state.t_filled_orders[symbol]
    n = len(filled_symbol)

    # 从 全部长度 N → N-1 → ... → 1 依次遍历
    for current_length in range(n, 0, -1):
        # 取前 current_length 个元素
        sub_list = filled_symbol[:current_length]

        # 计算 qty 总和
        cum_qty = sum(item.get("quantity", 0) for item in sub_list)
        profit =sum(item["amount"] + item["commission"] for item in sub_list)
        if round(cum_qty, 3) == 0:
            for i in range(0, current_length):
                filled_symbol[i]["cleared"] = 1
            test_logger.info(f"结清{current_length}条成交记录，利润：{profit}")
            logger.info(f"结清{current_length}条成交记录，利润：{profit}")
            send_wecom_msg(f"结清{current_length}条成交记录，利润：{profit}")
            # 将filled_symbol写入数据库
            update_tbl_filled_orders_symbol(filled_symbol)
            state.t_filled_orders[symbol] = get_filled_orders_symbol(symbol)
            break



def update_tbl_pending_orders(pending_order):
    logger=logging.getLogger("update_tbl_pending_orders")
    logger.info(f"删除挂单{pending_order['id']}")
    delete_tbl_pending_orders(pending_order["id"])
    state.t_pending_orders[pending_order["symbol"]]=get_pending_orders_symbol(pending_order["symbol"])
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
                            symbol_filled = state.t_filled_orders.get(pending_order["symbol"], [])
                            if symbol_filled and len(symbol_filled) > 0:
                                old_pos = symbol_filled[0]["pos_qty"]
                            else:
                                old_pos = symbol_info["core_position"]
                            filled_order={
                                "symbol": pending_order["symbol"],
                                "timestamp": datetime.now(),
                                "quantity": pending_order["qty"],
                                "price": pending_order["price"],
                                "pos_qty": old_pos + pending_order["qty"],
                                "commission": -cal_commission(pending_order),
                                "amount": -pending_order["qty"] * pending_order["price"]
                            }
                            update_tbl_filled_orders(filled_order)
                            clear_orders(pending_order["symbol"])
                        continue
            elif symbol_info["platform"]=="bn" and state.is_in_bn_period:
                bn=BnApi()
                end_timestamp=datetime.now().timestamp()
                start_timestamp=max(state.t_filled_timestamp.get(symbol_info["symbol"],0),end_timestamp-7*24*60*60)*1000+1
                end_timestamp=end_timestamp*1000
                try:
                    filled_rows=bn.client.futures_account_trades(
                                                                    symbol=symbol_info["symbol"],
                                                                    limit="1000",
                                                                    startTime=str(int(start_timestamp)),
                                                                    endTime=str(int(end_timestamp)),
                                                                    fromId=None
                                                                )
                except Exception as e:
                    exception_handler(e,f"币安查询成交记录时错误,时间：{start_timestamp}到{end_timestamp}")
                    send_wecom_msg(get_public_ip())
                    continue
                if filled_rows and len(filled_rows)>0:
                    msg_str=""
                    for filled_row in filled_rows:
                        msg_str+=f"{filled_row['side']} {filled_row['symbol']} {filled_row['qty']} {filled_row['price']}/{filled_row['commission']}\n"
                    send_wecom_msg(msg_str)
                for filled_row in filled_rows:
                    with orders_lock:
                        symbol_filled = state.t_filled_orders.get(filled_row["symbol"], [])
                        if symbol_filled and len(symbol_filled) > 0:
                            old_pos = symbol_filled[0]["pos_qty"]
                        else:
                            old_pos = symbol_info["core_position"]
                        quantity=float(filled_row["qty"]) if filled_row["side"]=="BUY" else -float(filled_row["qty"])
                        timestamp=int(filled_row["time"]) / 1000
                        if timestamp>state.t_filled_timestamp.get(symbol_info["symbol"], 0):
                            state.t_filled_timestamp[symbol_info["symbol"]]=timestamp
                        update_tbl_filled_orders({
                            "symbol": filled_row["symbol"],
                            "quantity": quantity,
                            "price": float(filled_row["price"]),
                            "pos_qty": old_pos + quantity,
                            "timestamp": timestamp,
                            "id": filled_row["id"],
                            "cleared": 0,
                            "amount": -float(filled_row["quoteQty"]) if filled_row["side"]=="BUY" else float(filled_row["quoteQty"]),
                            "commission": -float(filled_row["commission"]),
                        })
                clear_orders(symbol_info["symbol"])

        time.sleep(6)  # 模拟业务执行间隔，根据你的需求调整

    print(f"❌ check_filled任务停止 | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
