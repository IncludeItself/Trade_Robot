import logging
from datetime import datetime

from api.api import get_filled_orders, place_order_api, get_current_price, get_pending_orders
from logs import logger
from src import state
from src.common import update_tbl_filled_orders
from src.locks import orders_lock
from wecom.wecom import send_wecom_msg


def place_reverse_order(symbol_info, filled_rows_tbl:list):
    group={}
    for filled_row in filled_rows_tbl:
        price_str=str(filled_row["price"])
        item=group.get(price_str,None)
        if item:
            item["quantity"]+=float(filled_row["quantity"])
            item["amount"]+=float(filled_row["amount"])
            item["commission"]+=float(filled_row["commission"])
            item["price"]=-(item["amount"]+item["commission"])/item["quantity"] if item["quantity"]>0 else item["price"]
            group[price_str]=item
        else:
            group[price_str] = filled_row

    filled_rows=list(group.values())
    filled_rows.sort(key=lambda x: float(x["price"]))
    for filled_row in filled_rows:
        qty=round(filled_row["quantity"],int(symbol_info["qty_decimal"]))
    # if qty > 0:
        current_price=get_current_price(symbol_info["symbol"],"bn")
    #     grid_up=state.get_grid_up(symbol_info["symbol"],current_price)
    #     grid_up_f=grid_up["f"]
    #     min_price=max(min([float(x["price"]) for x in filled_rows]),current_price)
    #     pending=get_pending_orders(symbol_info["symbol"],"bn")
    #     min_pending_price=min([float(x["price"]) for x in pending if x["side"] == "SELL"])
    #     max_price = min(max([float(x["price"]) for x in filled_rows])*(1+grid_up_f),min_pending_price)
    #     step_rate=grid_up_f/5
    #     while min_price<=max_price:
    #
    #
    #         min_price*=step_rate+1
    #     pos=state.t_filled_orders[symbol_info["symbol"]][0]["pos_qty"]
        if qty>0:
            grid_up = state.get_grid_up(symbol_info["symbol"], current_price)
            price = float(filled_row["price"]) * (1 + grid_up["f"])
        else:
            grid_down = state.get_grid_down(symbol_info["symbol"], current_price)
            price = float(filled_row["price"]) / (1 + grid_down["f"])
        place_order_api({
            "symbol":filled_row["symbol"],
            "qty":-qty,
            "price":round(price, int(symbol_info["decimal"])),
        },"bn")


def check_filled_bn(symbol_dict:dict)->bool:
    logger=logging.getLogger("check_filled_bn")
    end_timestamp = datetime.now().timestamp()
    filled_timestamp=state.t_filled_timestamp.get(symbol_dict["symbol"], 0)
    logger.info(f"check_filled_bn: symbol:{symbol_dict['symbol']}, filled_timestamp:{filled_timestamp}")
    if filled_timestamp == 0:
        return False
    start_timestamp = max(filled_timestamp,
                          end_timestamp - 7 * 24 * 60 * 60) * 1000 + 1
    end_timestamp = end_timestamp * 1000
    filled_rows = get_filled_orders(symbol_dict["symbol"], str(int(start_timestamp)), str(int(end_timestamp)),symbol_dict["platform"])
    if filled_rows and len(filled_rows) > 0:
        lines = [
            f"{row['symbol']} {'+' if row['side'] == 'BUY' else '-'}{row['qty']} {row['price']}/{row['commission']}"
            for row in filled_rows
        ]
        # 用 \n 连接，最后不会多换行
        msg_str = "\n".join(lines)
        send_wecom_msg(msg_str)
    else:
        return False
    filled_rows_tbl = []
    with orders_lock:
        for filled_row in filled_rows:
            symbol_filled = state.t_filled_orders.get(filled_row["symbol"], [])
            if symbol_filled and len(symbol_filled) > 0:
                old_pos = symbol_filled[0]["pos_qty"]
            else:
                old_pos = symbol_dict["core_position"]
            quantity = float(filled_row["qty"]) if filled_row["side"] == "BUY" else -float(filled_row["qty"])
            timestamp = int(filled_row["time"]) / 1000
            if timestamp > state.t_filled_timestamp.get(symbol_dict["symbol"], 0):
                state.t_filled_timestamp[symbol_dict["symbol"]] = timestamp
            filled_item = {
                "symbol": filled_row["symbol"],
                "quantity": quantity,
                "price": float(filled_row["price"]),
                "pos_qty": old_pos + quantity,
                "timestamp": timestamp,
                "id": filled_row["id"],
                "cleared": 0,
                "amount": -float(filled_row["quoteQty"]) if filled_row["side"] == "BUY" else float(
                    filled_row["quoteQty"]),
                "commission": -float(filled_row["commission"]),
            }
            update_tbl_filled_orders(filled_item)
            filled_rows_tbl.append(filled_item)
        place_reverse_order(symbol_dict, filled_rows_tbl)
    return True
