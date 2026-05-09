import logging

from api.api import get_pending_orders
from data.sqllite import insert_filled_order, get_filled_orders_symbol, delete_tbl_pending_orders, \
    get_pending_orders_symbol, update_tbl_filled_orders_symbol
from src import state
from wecom.wecom import send_wecom_msg


def sell_order_exist(symbol):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("sell_order_exist")
    result=True
    if symbol["platform"]=="ths":
        symbol_pending=state.t_pending_orders[symbol["symbol"]]
        test_logger.info(f"目前存在的挂单：{symbol_pending}")
        result=any(order["symbol"]==symbol["symbol"] and order["direction"]=="Sell" for order in symbol_pending)
        test_logger.info(f"{symbol['symbol']} 是否存在卖出订单: {result}")
        logger.info(f"{symbol['symbol']} 是否存在卖出订单: {result}")
    elif symbol["platform"]=="bn":
        symbol_pending=get_pending_orders(symbol["symbol"])
        result=any(order["side"]=="SELL" for order in symbol_pending)
    return result


def buy_order_exist(symbol):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("buy_order_exist")
    result=True
    if symbol["platform"]=="ths":
        symbol_pending=state.t_pending_orders[symbol["symbol"]]
        test_logger.info(f"目前存在的挂单：{symbol_pending}")
        result=any(order["symbol"]==symbol["symbol"] and order["direction"]=="Buy" for order in symbol_pending)
        test_logger.info(f"{symbol['symbol']} 是否存在买入订单: {result}")
        logger.info(f"{symbol['symbol']} 是否存在买入订单: {result}")
    elif symbol["platform"]=="bn":
        symbol_pending=get_pending_orders(symbol["symbol"])
        result=any(order["side"]=="BUY" for order in symbol_pending)
    return result


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

def update_tbl_pending_orders(pending_order):
    logger=logging.getLogger("update_tbl_pending_orders")
    logger.info(f"删除挂单{pending_order['id']}")
    delete_tbl_pending_orders(pending_order["id"])
    state.t_pending_orders[pending_order["symbol"]]=get_pending_orders_symbol(pending_order["symbol"])
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
            profit_dict=state.get_profit(symbol)
            profit_dict["dtd"]+=profit
            profit_dict["mtd"]+=profit
            profit_dict["ytd"]+=profit
            state.update_profit_symbol(symbol,profit_dict)
            test_logger.info(f"结清({current_length}) {round(profit,4)}/{round(profit_dict["dtd"],4)}/{round(profit_dict["mtd"],4)}/{round(profit_dict["ytd"],4)}")
            logger.info(f"结清({current_length}) {round(profit,4)}/{round(profit_dict["dtd"],4)}/{round(profit_dict["mtd"],4)}/{round(profit_dict["ytd"],4)}")
            send_wecom_msg(f"结清({current_length}) {round(profit,4)}/{round(profit_dict["dtd"],4)}/{round(profit_dict["mtd"],4)}/{round(profit_dict["ytd"],4)}")
            # 将filled_symbol写入数据库
            update_tbl_filled_orders_symbol(filled_symbol)
            state.t_filled_orders[symbol] = get_filled_orders_symbol(symbol)
            break