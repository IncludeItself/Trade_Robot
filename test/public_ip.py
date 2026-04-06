import requests



def get_public_ip(proxy=False):


    api_list = [
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://ifconfig.me/ip"
    ]
    # 🔴 关键：指定 Clash 本地代理
    proxies = {
        "http": "http://127.0.0.1:7897",  # 你的 Clash HTTP 端口
        "https": "http://127.0.0.1:7897",
    }

    # 结果ip
    ip=""

    for api in api_list:
        try:
            if proxy:
                # 带上 proxies 参数发起请求
                response = requests.get(api, proxies=proxies, timeout=5)
                ip=response.text.strip()
                break
            else:
                response = requests.get(api, timeout=5)
                ip=response.text.strip()
                break
        except:
            continue

    url = f"http://ip-api.com/json/{ip}?lang=zh-CN"

    try:
        if proxy:
            res = requests.get(url, proxies=proxies, timeout=8)
        else:
            res = requests.get(url, timeout=8)
        data = res.json()
        if data.get("status") == "success":
            return {
                "ip": ip,
                "国家": data.get("country"),
                "省份": data.get("regionName"),
                "城市": data.get("city"),
                "运营商": data.get("isp"),
                "经纬度": (data.get("lat"), data.get("lon"))
            }
        return {"错误": data.get("message", "查询失败")}
    except Exception as e:
        return {"错误": str(e)}

    return "所有接口都失败了"


print("你的外网IP地址是：", get_public_ip())
# 输出：代理后的公网IP
print("Clash 代理后的公网IP：", get_public_ip(proxy=True))
