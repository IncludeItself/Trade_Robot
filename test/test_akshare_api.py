# 单只实时（贵州茅台）
import akshare as ak
import pandas as pd

# 获取某股票历史1分钟数据（可指定日期）
df = ak.stock_zh_a_minute(
    symbol="sh600499",  # 股票代码
    period="1",       # 1分钟线
    # start_date="2026-03-27",  # 上周五
    # end_date="2026-03-27"
)

# 筛选指定时间点（如 14:30:00）
target_time = "2026-03-27 14:30:00"
# point_data = df[df["time"] == target_time]
print(df)