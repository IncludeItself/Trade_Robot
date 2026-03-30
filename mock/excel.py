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


# ------------------- 测试示例 -------------------
if __name__ == "__main__":
    # 假设Excel文件（test.xlsx）内容如下：
    # side   price  volume
    # buy    105    50
    # buy    98     30
    # sell   110    20
    # buy    95     40

    # 1. 提取所有行
    all_rows = excel_to_dict_list("test.xlsx")
    print("所有行转为字典列表：")
    print(all_rows)

    # 2. 提取单行（第1行，对应Excel第二行，索引0）
    single_row = excel_to_dict_list("test.xlsx", rows=0)
    print("\n提取单行（索引0）：")
    print(single_row)

    # 3. 提取多行（索引0、1、3）
    multi_rows = excel_to_dict_list("test.xlsx", rows=[0, 1, 3])
    print("\n提取指定多行：")
    print(multi_rows)

    # 4. 提取连续行（索引0到2，即前3行）
    continuous_rows = excel_to_dict_list("test.xlsx", rows=slice(0, 3))
    print("\n提取连续行（0-2）：")
    print(continuous_rows)