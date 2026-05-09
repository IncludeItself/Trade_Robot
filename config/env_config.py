import os
import sys
from dotenv import load_dotenv

def get_base_path():
    # 打包后 exe 运行
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # 开发环境运行
    else:
        return os.path.abspath(os.path.dirname(__file__))

# 加载 exe 同级目录下的 .env
env_path = os.path.join(get_base_path(), '.env')
load_dotenv(dotenv_path=env_path)


class EnvConfig:
    """配置类"""
    # 环境配置
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'DEV')

    # 网络配置
    HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', '30'))
    HTTP_RETRIES = int(os.getenv('HTTP_RETRIES', '3'))
    HTTP_BACKOFF_FACTOR = float(os.getenv('HTTP_BACKOFF_FACTOR', '1'))

    @property
    def proxy_http(self):
        return os.getenv('PROXY_HTTP', '')
    @property
    def proxy_https(self):
        return os.getenv('PROXY_HTTPS', '')

    @property
    def api_key(self):
        """根据当前环境返回API Key"""
        if self.ENVIRONMENT == 'PROD':
            return os.getenv('PROD_API_KEY', '')
        return os.getenv('DEV_API_KEY', '')

    @property
    def api_secret(self):
        """根据当前环境返回API Secret"""
        if self.ENVIRONMENT == 'PROD':
            return os.getenv('PROD_API_SECRET', '')
        return os.getenv('DEV_API_SECRET', '')

    @property
    def testnet(self):
        """根据当前环境返回是否使用测试网"""
        if self.ENVIRONMENT == 'PROD':
            return os.getenv('PROD_TESTNET', 'False').lower() == 'true'
        return os.getenv('DEV_TESTNET', 'True').lower() == 'true'

    @property
    def base_url(self):
        """根据当前环境返回API基础URL"""
        if self.ENVIRONMENT == 'PROD':
            return os.getenv('PROD_BASE_URL', 'https://api.binance.com')
        return os.getenv('DEV_BASE_URL', 'https://testnet.binance.vision')

    @property
    def env(self):
        """根据当前环境返回环境名称"""
        if self.ENVIRONMENT == 'PROD':
            return 'PROD'
        elif self.ENVIRONMENT == 'TEST':
            return 'TEST'
        return 'DEV'

    @property
    def wecom_webhook_url(self):
        return os.getenv('WECOM_WEBHOOK_URL', '')


# 创建全局配置实例
config = EnvConfig()
