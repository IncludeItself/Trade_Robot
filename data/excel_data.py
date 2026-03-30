import pandas as pd




def excel_to_dict_list(file_path, sheet_name=0, rows=None):
    """
    读取Excel文件，提取指定行转为字典列表（每个字典的键为Excel第一行的字段名）

    Args:
        file_path: Excel文件路径（如"test.xlsx"）
        sheet_name: 工作表名/索引，默认0（第一个工作表）
        rows: 要提取的行，支持多种格式：
              - None: 提取所有行
              - 整数: 提取指定单行（行号从0开始，对应Excel第二行）
              - 列表: 提取指定多行（如[0,2,3]）
              - 切片: 提取连续行（如1:4，提取第2-4行）

    Returns:
        dict_list: 字典列表，每个元素为一行数据的字典
    """
    # 读取Excel，第一行作为列名
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # 处理行提取逻辑
    if rows is None:
        selected_df = df  # 所有行
    elif isinstance(rows, int):
        selected_df = df.iloc[[rows]]  # 单行（转为DataFrame保持结构）
    elif isinstance(rows, list):
        selected_df = df.iloc[rows]  # 多行列表
    elif isinstance(rows, slice):
        selected_df = df.iloc[rows]  # 切片（连续行）
    else:
        raise ValueError("rows参数仅支持：None/整数/列表/切片")

    # 转为字典列表（orient='records'表示按行转字典）
    dict_list = selected_df.to_dict(orient='records')

    return dict_list


def get_symbols_from_excel():
    """
    从Excel文件中提取所有启用的股票信息（'on' 字段为 True）

    Returns:
        list: 字典列表，每个字典代表一行启用的股票数据
    """
    data = excel_to_dict_list('data/tr_data.xlsx', 'symbols', rows=None)
    # 过滤掉 "on" 字段不为 True 的行
    return [row for row in data if row.get('on') is True]

def get_grid(t_symbols):
    data = excel_to_dict_list('data/tr_data.xlsx', 'grid', rows=None)
    result = {}
    for symbol in t_symbols:
        # 将 t_symbols 中的 symbol 和 data 中的 symbol 都转换为字符串进行比较
        # 这可以避免因为 Excel 单元格格式（数字 vs 文本）不同导致的匹配失败
        # 同时，统一使用字符串作为 result 的键，增加后续处理的稳定性
        key = str(symbol["symbol"])
        result[key] = [row for row in data if str(row["symbol"]) == key]
    return result