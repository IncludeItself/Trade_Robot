import akshare as ak
import pandas as pd


def get_history_data(symbol="sh600499"):
    """获取股票历史1分钟数据"""
    df = ak.stock_zh_a_minute(
        symbol="sh600499",  # 股票代码
        period="1",  # 1分钟线
        # start_date="2026-03-27",  # 上周五
        # end_date="2026-03-27"
    )


    sina_df=df[(df["day"].dt.month==3) & (df["day"].dt.day==17)]
    sina_df["timestamp"]=pd.to_datetime(sina_df["day"])
    sina_df["name"]="科达制造"
    sina_df["pre_close"]=16.84




    
    # 将数据写入到Excel文件的bar_data_2工作表
    excel_file = "e:\\workplace\\Trade_Robot\\mock\\simulate_response.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='bar_data_2', index=False)
    print(f"数据已成功写入到 {excel_file} 的 bar_data_2 工作表")
    return df


# 测试获取数据
get_history_data()
