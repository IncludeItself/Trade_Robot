from binance.base_client import BaseClient
from binance.client import Client

import time

from config.env_config import config

proxy_http=config.proxy_http
proxy_https=config.proxy_https
api_key = config.api_key
api_secret = config.api_secret


# 初始化客户端
# BaseClient.request_params = {
#     "proxies": {
#         "http": proxy_http,
#         "https": proxy_https,
#     }
# }

client = Client(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )

symbol = "BTCUSDT"
interval = "15m"  # 15分钟K线

# 获取最近 1 根 15分钟K线（已闭合）
klines = client.klines(symbol=symbol, interval=interval, limit=1)
k = klines[0]

# K线字段解释
open_time = time.ctime(k[0] / 1000)  # 开盘时间
open_price = float(k[1])            # 开盘价
high = float(k[2])                  # 最高价
low = float(k[3])                   # 最低价
close = float(k[4])                 # 收盘价
volume = float(k[5])                # 成交量（币量）
quote_volume = float(k[7])          # 成交额（USDT）

# 输出
print(f"交易对：{symbol} 15分钟K线")
print(f"开盘时间：{open_time}")
print(f"开盘价：{open_price:.2f}")
print(f"最高价：{high:.2f}")
print(f"最低价：{low:.2f}")
print(f"收盘价：{close:.2f}")
print(f"成交量：{volume:.2f} BTC")
print(f"成交额：{quote_volume:.2f} USDT")