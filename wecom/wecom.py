import requests
import json

# 替换你的Webhook key
WEBHOOK_KEY = "5000b7ee-424b-4b4a-99df-f366a393f0d3"
WEBHOOK_URL = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WEBHOOK_KEY}"

def send_wecom_msg(content):

    data = {"msgtype": "text", "text": {"content": content}}
    resp = requests.post(WEBHOOK_URL,proxies="", json=data)
    # print(resp.json())

# 测试
send_wecom_msg("测试：企业微信消息推送（原群机器人）")

