from datetime import datetime

from api.bnapi import BnApi
bn = BnApi()

# trades = bn.futures_symbol_ticker("XAUUSDT")


# line=bn.client.futures_klines(symbol="BTCUSDT", interval="5m", limit=2)
# print(line[0])


current_price=bn.client.futures_symbol_ticker(symbol="BTCUSDT")
print(current_price)


# bn.client.futures_create_order(
#                 symbol='BTCUSDT',
#                 type="LIMIT",
#                 side='SELL',
#                 quantity='0.002',
#                 price='80000',
#                 timeInForce='GTC',
#                 positionSide='SHORT'
# )



# print(f"str(datetime.now().timestamp()*1000):{int(datetime.now().timestamp()*1000)}")
# trades=bn.client.futures_account_trades(
#                 symbol='BTCUSDT',
#                 limit="1000",
#                 startTime="1774972800000",
#                 endTime=str(int(datetime.now().timestamp()*1000)),
#                 fromId=None
#             )
# print(trades)

# pending_orders=bn.client.futures_get_open_orders(symbol="BTCUSDT")
# print(pending_orders)


# holding=bn.client.futures_position_information(symbol="TSLAUSDT")
# print(holding)
