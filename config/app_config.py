import configparser
import os



class AppConfig:
    """配置管理类"""
    _instance = None

    def __new__(cls):
        """单例模式，确保配置只被加载一次"""
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化配置"""
        # 读取交易配置
        self._trade_config = self._load_config("app.ini")
        self.appConfig = {
            "a_morning_trade_start": self._trade_config.get("trading_time", "a_morning_trade_start"),
            "a_morning_trade_end": self._trade_config.get("trading_time", "a_morning_trade_end"),
            "a_afternoon_trade_start": self._trade_config.get("trading_time", "a_afternoon_trade_start"),
            "a_afternoon_trade_end": self._trade_config.get("trading_time", "a_afternoon_trade_end"),
            "a_trade_day": self._trade_config.get("trading_time", "a_trade_day"),
            "start_time": self._trade_config.get("trading_time", "start_time"),
            "end_time": self._trade_config.get("trading_time", "end_time"),
            "break_up": self._trade_config.getfloat("threshold", "break_up"),
        }

    def _load_config(self, filename):
        """加载配置文件"""
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), filename)
        if not config.read(config_path, encoding="utf-8"):
            raise FileNotFoundError(f"配置文件 {config_path} 不存在或格式错误")
        return config



# 创建全局配置实例
_config_instance = AppConfig()

# 导出配置对象
appConfig = _config_instance.appConfig
# databaseConfig = _config_instance.databaseConfig