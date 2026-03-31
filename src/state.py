# 全局状态变量，用于标记核心任务是否正在运行
from datetime import datetime

from config.app_config import appConfig
from data.sqllite import get_last_day_bar

is_task_running = False
is_in_a_period = False
is_in_h_period = False
is_in_us_period = False

t_symbols = []
t_pending_orders={}
# t_bar_data=[]
t_filled_orders={}
t_grid={}

# 最近的成交记录
t_last_bar_data={}
t_last_bar_history={}

# 可交易时间
t_period= {}


def get_last_bar_history(symbol:str):
    last_day_bar=t_last_bar_history.get(symbol,{})
    if last_day_bar is None:
        last_day_bar=get_last_day_bar(symbol)
        t_last_bar_history[symbol]=last_day_bar
    return t_last_bar_history[symbol]


def get_period(exchange:str):
    period=t_period.get(exchange,0)
    if period is None or period == 0:
        def to_seconds(time_str):
            # 把 "9:30" 转成 当天的时间戳
            h, m = map(int, time_str.split(":"))
            dt = datetime.now().replace(hour=h, minute=m, second=0)
            return dt.timestamp()

        start_sec_morning = to_seconds(appConfig[f"{exchange}_morning_trade_start"])
        end_sec_morning = to_seconds(appConfig[f"{exchange}_morning_trade_end"])
        start_sec_afternoon = to_seconds(appConfig[f"{exchange}_afternoon_trade_start"])
        end_sec_afternoon = to_seconds(appConfig[f"{exchange}_afternoon_trade_end"])
        period = int(abs(end_sec_morning - start_sec_morning + end_sec_afternoon - start_sec_afternoon))  # 绝对值，避免顺序问题
        t_period[exchange] = period
    return t_period[exchange]