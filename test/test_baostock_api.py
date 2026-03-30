import baostock as bs
lg = bs.login()  # 无需账号，仅初始化
# 实时/历史行情（600519）
#   A 股首选
rs = bs.query_history_k_data_plus("sh.600519",
    "date,time,code,open,high,low,close,volume",
    start_date="2026-03-13", end_date="2026-03-13",
    frequency="5")  # 5分钟K线
data = rs.get_data()
print(data.tail())
bs.logout()