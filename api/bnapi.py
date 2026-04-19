from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from config.env_config import config
import time

from src.public_ip import get_public_ip
from wecom.wecom import send_wecom_msg


class BnApi:
    _instance = None
    _initialized = False  # 新增：标记是否真正初始化完成

    def __new__(cls):
        # 1. 单例：确保只创建一次实例
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        # 2. 只执行一次初始化逻辑
        if not cls._initialized:
            cls._instance._init_client()
            cls._initialized = cls._instance._test_connection()

            # 如果初始化失败，重置状态，保证外部调用一定拿到有效实例
            if not cls._initialized:
                cls._instance = None
                send_wecom_msg(get_public_ip())
                raise Exception("❌ 币安API初始化失败：5秒内无法连接")

        return cls._instance

    def _init_client(self):
        """初始化客户端"""
        proxies = {
            "http": config.proxy_http,
            "https": config.proxy_https,
        }

        self.client = Client(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet,
            requests_params={"proxies": proxies}
        )

    def _test_connection(self) -> bool:
        """测试连接，5秒超时，返回是否成功"""
        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                self.client.futures_symbol_ticker(symbol="BTCUSDT")
                print("✅ 币安API连接成功")
                return True
            except Exception as e:
                print(f"⏳ 测试连接中... {str(e)}")
                time.sleep(0.5)

        print("❌ 连接超时：5秒内无法连接币安API")
        return False

    # ------------------------------
    # 下面是你原本的接口方法（无修改）
    # ------------------------------
    def get_user_trades(
            self,
            symbol: str,
            limit: str = "500",
            start_time: int = None,
            end_time: int = None,
            from_id: int = None
    ) -> list:
        try:
            trades = self.client.futures_account_trades(
                symbol=symbol,
                limit=limit,
                startTime=start_time,
                endTime=end_time,
                fromId=from_id
            )
            return trades
        except BinanceAPIException as e:
            error_msg = f"❌ API错误 - 代码：{e.code}，信息：{e.message}"
            print(error_msg)
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
            print(f"请求错误：{str(e)}")
            return []
        except Exception as e:
            print(f"未知错误：{str(e)}")
            return []

    def futures_cancel_all_open_orders(self, param) -> bool:
        self.client.futures_cancel_all_open_orders(symbol=param["symbol"])
        return True

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