import datetime
import logging
import time

from api.api import get_symbol_bar_data
from api.bnapi import BnApi
from data.sqllite import insert_bar_data, get_last_bar_data
from src import state
# from api.api import get_symbol_bar_data




def get_bar_data():
    """你的核心业务逻辑（持续运行的任务）"""
    test_logger = logging.getLogger("test_logger")
    logger = logging.getLogger("get_bar_data")
    test_logger.info(f"✅ get bar data任务启动 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 循环执行核心逻辑，直到标志位被置为False

    test_logger.info(f"is_task_running: {state.is_task_running}")
    while state.is_task_running:
        for symbol in state.t_symbols:
            last_bar_data=state.t_last_bar_data.get(symbol["symbol"],None)
            if last_bar_data or last_bar_data is None:
                last_bar_data=get_last_bar_data(symbol["symbol"])
            exchange = symbol["exchange"]
            if exchange=="a" and state.is_in_a_period:
                bar_data=get_symbol_bar_data(exchange,symbol["pre_fix"]+symbol["symbol"])
                if bar_data and len(bar_data)>0:
                    new_bar_data={
                        "code": symbol["symbol"],
                        "timestamp": bar_data["timestamp"],
                        "date": bar_data["date"],
                        "time": bar_data["time"],
                        "price": bar_data["price"],
                        "pre_close": bar_data["pre_close"],
                        "open": bar_data["open"],
                        "highest": bar_data["highest"],
                        "lowest": bar_data["lowest"],
                        "volume": bar_data["volume"]-last_bar_data["total_volume"] if last_bar_data else bar_data["volume"],
                        "value": bar_data["value"]-last_bar_data["total_value"] if last_bar_data else bar_data["value"],
                        "total_volume": bar_data["volume"],
                        "total_value": bar_data["value"],
                    }
                    insert_bar_data(new_bar_data)
                    logger.info(f"insert bar data: {new_bar_data}")
                    state.t_last_bar_data[symbol["symbol"]]=new_bar_data
            elif exchange=="bn" and state.is_in_bn_period:
                now_timestamp = datetime.datetime.now().timestamp()
                if last_bar_data is not None and now_timestamp-last_bar_data["timestamp"]<5*60+5:
                    continue
                new_bar_data=get_symbol_bar_data(exchange,symbol["symbol"])
                if new_bar_data is None or (last_bar_data is not None and new_bar_data["timestamp"]==last_bar_data["timestamp"]):
                    continue
                else:
                    insert_bar_data(new_bar_data)
                    logger.info(f"insert bar data: {new_bar_data}")
                    state.t_last_bar_data[symbol["symbol"]] = new_bar_data
            # 获取所有股票代码
            # symbol_list = get_symbol_bar_data()



        time.sleep(6)  # 模拟业务执行间隔，根据你的需求调整

    test_logger.info(f"❌ get bar data任务停止 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# if __name__=="__main__":
#     bar_data=get_bar_data_bn("XAUUSDT","5m")
#     print(bar_data)
