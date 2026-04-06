import logging

from src import state


def stack_support_sell(symbol,price):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("stack_support_sell")
    filled_orders=state.t_filled_orders.get(symbol["symbol"],[])

    if not filled_orders or len(filled_orders) == 0:
        test_logger.info(f"{symbol['symbol']} 不存在已成交的记录，返回最小交易数量{symbol['least_trade_qty']}，价格为0，持仓数量为底仓")
        return symbol["least_trade_qty"],price,symbol["core_position"]

    # filled_orders 按timestamp逆序排序
    filled_orders.sort(key=lambda x: x["timestamp"], reverse=True)
    pos_qty = filled_orders[0]["pos_qty"]
    test_logger.info(f"最新成交记录:{filled_orders[0]}，记录的持股数量为：{pos_qty}")
    count = 0
    qty = 0
    amt = 0
    profit = 0
    unit_cost = price
    best_qty = 0
    while count < len(filled_orders):
        qty += filled_orders[count]["quantity"]
        amt += filled_orders[count]["amount"]+filled_orders[count]["commission"]
        if qty > 0 and unit_cost > abs(amt / qty):
            unit_cost = abs(amt / qty)
            best_qty = qty
        count += 1
    if best_qty>0:
        logger.info(f"存在数量：{best_qty}，成本价格为{unit_cost}的持仓订单，乘以least_profit {1+ symbol["least_profit"]}，得到价格为{round(unit_cost * (1+ symbol["least_profit"]), 2)}")
        return best_qty, round(unit_cost * (1+ symbol["least_profit"]), 2), pos_qty
    elif price>filled_orders[0]["price"]*(1+ symbol["step_rate"]):
        logger.info(f"{symbol['symbol']} 最近一次成交为卖单，价格{filled_orders[0]['price']}*(1+ symbol['step_rate'])，小于现价{price}，要挂卖单")
        return symbol["least_trade_qty"], round(filled_orders[0]["price"]*(1+ symbol["step_rate"]), 2), pos_qty
    else:
        logger.info(f"{symbol['symbol']} 最近一次成交为卖单，价格为{filled_orders[0]['price']}，要在更高的价格卖才行")
        return 0, round(filled_orders[0]["price"]*(1+ symbol["step_rate"]), 2), pos_qty



def stack_support_buy(symbol,price):
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("stack_support_buy")
    filled_orders=state.t_filled_orders.get(symbol["symbol"],[])
    if not filled_orders or len(filled_orders)==0:
        return symbol["least_trade_qty"],price,symbol["core_position"]

    # filled_orders 按timestamp逆序排序
    filled_orders.sort(key=lambda x: x["timestamp"], reverse=True)

    pos_qty=filled_orders[0]["pos_qty"]

    count =0
    qty =0
    amt=0
    profit=0
    unit_cost=0
    best_qty=0
    while count<len(filled_orders):
        qty+=filled_orders[count]["quantity"]
        amt+=filled_orders[count]["amount"]+filled_orders[count]["commission"]
        if qty<0 and unit_cost<abs(amt/qty):
            unit_cost=abs(amt/qty)
            best_qty=qty
        count+=1
    if best_qty<0:
        logger.info(f"存在数量：{best_qty}，成本价格为{unit_cost}的持仓订单，乘以least_profit {1- symbol["least_profit"]}，得到价格为{round(unit_cost * (1- symbol["least_profit"]), 2)}")
        return -best_qty,round(unit_cost*(1-symbol["least_profit"]),2),pos_qty
    elif price<filled_orders[0]["price"]*(1- symbol["step_rate"]):
        logger.info(f"{symbol['symbol']} 最近一次成交为买单，价格{filled_orders[0]['price']}*(1- symbol['step_rate'])，大于现价{price}，要挂买单")
        return symbol["least_trade_qty"], round(filled_orders[0]["price"]*(1- symbol["step_rate"]), 2), pos_qty
    else:
        test_logger.info(f"{symbol['symbol']} 最近一次成交为买单，价格为{filled_orders[0]['price']}，加上step_rate，现在挂买单价格为{round(filled_orders[0]["price"]*(1- symbol["step_rate"]), 2)}，")
        logger.info(f"{symbol['symbol']} 最近一次成交为买单，价格为{filled_orders[0]['price']}，现在挂买单价格为{round(filled_orders[0]["price"] * (1 - symbol["step_rate"]), 2)}")
        return 0,round(filled_orders[0]["price"]*(1- symbol["step_rate"]), 2),pos_qty
