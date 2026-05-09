import requests
import json

from config.env_config import config

# 替换你的Webhook key

WEBHOOK_URL = config.wecom_webhook_url

def send_wecom_msg(content):

    data = {"msgtype": "text", "text": {"content": content}}
    resp = requests.post(WEBHOOK_URL,proxies="", json=data)
    # print(resp.json())

# 测试
if __name__ == "__main__":
    send_wecom_msg("测试：企业微信消息推送（原群机器人）")

