import datetime
import logging
import time

from src import state
from src.place_order.place_orders_a import place_orders_a
from src.place_order.place_orders_bn import place_order_bn


def place_orders():
    """你的核心业务逻辑（持续运行的任务）"""
    test_logger = logging.getLogger("test_logger")
    logger=logging.getLogger("place_orders")
    test_logger.info(f"✅ place_orders任务启动 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 循环执行核心逻辑，直到标志位被置为False
    while state.is_task_running:
        for symbol in state.t_symbols:

            if symbol["exchange"]=="a" and state.is_in_a_period:
                if not place_orders_a(symbol):
                    continue
            elif symbol["exchange"] == "bn" and state.is_in_bn_period:
                if not place_order_bn(symbol):
                    continue


        time.sleep(10)  # 模拟业务执行间隔，根据你的需求调整

    print(f"❌ place_orders任务停止 | 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")