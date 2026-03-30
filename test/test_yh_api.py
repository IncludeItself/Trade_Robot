import yfinance as yf
# 实时价格（苹果AAPL、腾讯0700.HK、贵州茅台600519.SS）,覆盖美股、港股、A 股、加密货币、外汇
ticker = yf.Ticker("AAPL")
print(ticker.info["currentPrice"])  # 实时价
# 历史数据
hist = ticker.history(period="1d", interval="1m")  # 日内1分钟K线
print(hist["Close"].iloc[-1])