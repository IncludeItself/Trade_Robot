import logging

import requests


def get_sina_stock(stock_code):
    url = f"http://hq.sinajs.cn/list={stock_code}"

    # 完整的浏览器请求头（核心：模拟真实浏览器）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://finance.sina.com.cn/",  # 增加来源页
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive"
    }

    try:
        # 关闭重定向、添加超时
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=False,
            verify=False  # 忽略SSL验证（部分环境需要）
        )
        response.encoding = "gb2312"  # 必须指定编码

        if response.status_code == 200:
            data_str = response.text.split('"')[1]
            data_list = data_str.split(',')
            print(f"原始数据：\n"
                  f"0.名称：{data_list[0]}\n"
                  f"1.昨收盘价：{data_list[1]}\n"
                  f"2.开盘价：{data_list[2]}\n"
                  f"3.最新价：{data_list[3]}\n"
                  f"4.最高价：{data_list[4]}\n"
                  f"5.最低价：{data_list[5]}\n"
                  f"6.买一价：{data_list[6]}\n"
                  f"7.卖一价：{data_list[7]}\n"
                  f"8.成交量：{data_list[8]}\n"
                  f"9.成交额：{data_list[9]}\n"
                  f"10.买一量：{data_list[10]}\n"
                  f"11.买一价格：{data_list[11]}\n"
                  f"12.买二量：{data_list[12]}\n"
                  f"13.买二价格：{data_list[13]}\n"
                  f"14.买三量：{data_list[14]}\n"
                  f"15.买三价格：{data_list[15]}\n"
                  f"16.买四量：{data_list[16]}\n"
                  f"17.买四价格：{data_list[17]}\n"
                  f"18.买五量：{data_list[18]}\n"
                  f"19.买五价格：{data_list[19]}\n"
                  f"20.卖二量：{data_list[20]}\n"
                  f"21.卖二价格：{data_list[21]}\n"
                  f"22.卖三量：{data_list[22]}\n"
                  f"23.卖三价格：{data_list[23]}\n"
                  f"24.卖四量：{data_list[24]}\n"
                  f"25.卖四价格：{data_list[25]}\n"
                  f"26.卖五量：{data_list[26]}\n"
                  f"27.卖五价格：{data_list[27]}\n"
                  f"28.卖一量：{data_list[28]}\n"
                  f"30.最新成交日期：{data_list[30]}\n"
                  f"31.时间：{data_list[31]}\n"
                  f"32.状态标识：{data_list[32]}\n"
                  )
            return {
                "名称": data_list[0],
                "最新价": float(data_list[3]),
                "涨跌": round(float(data_list[3])-float(data_list[1]), 2),
            }
        else:
            return f"请求失败，状态码：{response.status_code}"

    except Exception as e:
        return f"查询异常：{str(e)}"


# 测试
if __name__ == "__main__":

    # 初始化logger
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    print(get_sina_stock("sh600499"))  # 贵州茅台