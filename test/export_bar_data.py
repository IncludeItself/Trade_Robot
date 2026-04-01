import os
import pandas as pd
from datetime import datetime
from data.sqllite import get_db_connection

def export_bar_data_to_excel():
    """
    将数据库tbl_bar_data表中的数据导出到/data/history目录下的Excel文件
    文件名格式：symbol_date.xlsx（如600499_20260330.xlsx）
    """
    # 创建历史数据目录
    history_dir = "data/history"
    os.makedirs(history_dir, exist_ok=True)
    
    # 获取数据库连接
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 查询所有数据
        query = """
            SELECT symbol, timestamp, price, pre_close, open, highest, lowest, volume, value
            FROM tbl_bar_data
            ORDER BY symbol, timestamp
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ 数据库中没有数据")
            return
        
        # 将数据转换为DataFrame
        df = pd.DataFrame(rows, columns=['symbol', 'timestamp', 'price', 'pre_close', 'open', 'highest', 'lowest', 'volume', 'value'])
        
        # 转换timestamp为日期格式，用于分组
        df['date'] = pd.to_datetime(df['timestamp'], unit='s').dt.strftime('%Y%m%d')
        
        # 按股票代码和日期分组导出
        for (symbol, date), group in df.groupby(['symbol', 'date']):
            # 计算累计成交量和成交额
            group['total_volume'] = group['volume'].cumsum()
            group['total_value'] = group['value'].cumsum()
            
            # 选择需要的字段
            export_df = group[['symbol', 'timestamp', 'price', 'pre_close', 'open', 'highest', 'lowest', 'volume', 'value', 'total_volume', 'total_value']]
            
            # 生成文件名
            filename = f"{symbol}_{date}.xlsx"
            filepath = os.path.join(history_dir, filename)
            
            # 导出到Excel
            export_df.to_excel(filepath, index=False)
            print(f"✅ 已导出文件: {filepath}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    export_bar_data_to_excel()