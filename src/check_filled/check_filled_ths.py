import logging
from datetime import datetime

from data.sqllite import delete_tbl_pending_orders, get_pending_orders_symbol, get_bar_data
from src import state
from src.common import cal_commission, update_tbl_filled_orders
from src.locks import orders_lock
from wecom.wecom import send_wecom_msg


def update_tbl_pending_orders(pending_order):
    logger=logging.getLogger("update_tbl_pending_orders")
    logger.info(f"删除挂单{pending_order['id']}")
    delete_tbl_pending_orders(pending_order["id"])
    state.t_pending_orders[pending_order["symbol"]]=get_pending_orders_symbol(pending_order["symbol"])
    pass


def check_filled_ths(symbol_dict:dict)->bool:
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("check_filled_orders")
    logger.info(f"check_filled_orders {symbol_dict}")
    pending_orders = state.t_pending_orders[symbol_dict["symbol"]]
    test_logger.info(f"{symbol_dict['symbol']}当前有 {len(pending_orders)} 条挂单：{pending_orders}")
    for pending_order in pending_orders:
        test_logger.info(f"此挂单时间戳为：{pending_order['timestamp']}，现在的时间戳：{datetime.now().timestamp()}")
        bars = get_bar_data(symbol_dict["symbol"], pending_order["timestamp"], datetime.now().timestamp())
        test_logger.info(f"获取到的bar数据{len(bars)}条")
        # 订单已成交，从数据库删除
        if pending_order["direction"] == "Sell" and any(bar["price"] > pending_order["price"] for bar in bars) or \
                pending_order["direction"] == "Buy" and any(bar["price"] < pending_order["price"] for bar in bars):
            with orders_lock:
                test_logger.info(
                    f"{pending_order['symbol']} {pending_order['direction']} {pending_order['price']} 已经成交")
                logger.info(f"订单{pending_order}已成交")
                send_wecom_msg(f"订单{pending_order}已成交")
                # 已经成交
                update_tbl_pending_orders(pending_order)
                symbol_filled = state.t_filled_orders.get(pending_order["symbol"], [])
                if symbol_filled and len(symbol_filled) > 0:
                    old_pos = symbol_filled[0]["pos_qty"]
                else:
                    old_pos = symbol_dict["core_position"]
                filled_order = {
                    "symbol": pending_order["symbol"],
                    "timestamp": datetime.now(),
                    "quantity": pending_order["qty"],
                    "price": pending_order["price"],
                    "pos_qty": old_pos + pending_order["qty"],
                    "commission": -cal_commission(pending_order),
                    "amount": -pending_order["qty"] * pending_order["price"]
                }
                update_tbl_filled_orders(filled_order)
            continue