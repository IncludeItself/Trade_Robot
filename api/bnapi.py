from binance.client import Client

from binance.exceptions import BinanceAPIException, BinanceRequestException

from config.env_config import config


class BnApi:
    _instance = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BnApi, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):

        proxies={
            "http": config.proxy_http,
            "https": config.proxy_https,
        }

        self.client = Client(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet,
            requests_params={"proxies": proxies}
        )

    def get_user_trades(
            self,
            symbol: str,
            limit: str = "500",  # 最多返回500条，币安接口限制
            start_time: int = None,  # 起始时间戳（毫秒）
            end_time: int = None,  # 结束时间戳（毫秒）
            from_id: int = None  # 从指定成交ID开始返回

    ) -> list:
        try:
            # 调用/fapi/v1/userTrades接口（底层映射）
            trades = self.client.futures_account_trades(
                symbol=symbol,
                limit=limit,
                startTime=start_time,
                endTime=end_time,
                fromId=from_id
            )
            return trades
        except BinanceAPIException as e:
            # 针对性错误提示（辅助排查）
            error_msg = f"❌ API错误 - 代码：{e.code}，信息：{e.message}"
            print(error_msg)
            # 常见错误码解读
            if e.code == -2015:
                print("   → 原因：API Key/Secret错误、IP白名单未配置、期货权限未开启")
            elif e.code == -1022:
                print("   → 原因：签名无效（时间偏移过大/API Secret错误）")
            elif e.code == -1121:
                print("   → 原因：交易对不存在（测试网需用带后缀格式，如BTCUSDT_240628）")
            elif e.code == -4003:
                print("   → 原因：API Key未开启期货交易权限")
            return []
        except BinanceRequestException as e:
            # 网络/请求层面错误（如超时、连接失败）
            print(f"请求错误：{str(e)}")
            return []
        except Exception as e:
            # 其他未知错误
            print(f"未知错误：{str(e)}")
            return []

    def futures_cancel_all_open_orders(self, param) -> bool:
        self.client.futures_cancel_all_open_orders(symbol=param["symbol"])

    def futures_get_open_orders(self, param) -> list:
        return self.client.futures_get_open_orders(**param)

    def futures_symbol_ticker(self, symbol) -> dict:

        return self.client.futures_symbol_ticker(symbol=symbol)

    def futures_position_information(self, symbol) -> dict:

        return self.client.futures_position_information(symbol=symbol)

    def futures_create_order(self, symbol, type, side, quantity, timeInForce, price, positionSide) -> dict:

        return self.client.futures_create_order(
            symbol=symbol,
            type=type,
            side=side,
            quantity=quantity,
            price=price,
            timeInForce=timeInForce,
            positionSide=positionSide
        )