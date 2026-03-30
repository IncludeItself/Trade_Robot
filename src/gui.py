import tkinter as tk
from tkinter import ttk, messagebox


# 1. 定义表格界面的核心逻辑（封装成函数/类，避免代码混乱）
def create_main_window():
    """创建主窗口并配置表格界面"""
    # 初始化主窗口
    root = tk.Tk()
    root.title("holding symbols")
    root.geometry("700x500")  # 窗口大小：宽x高
    root.resizable(True, True)  # 允许用户调整窗口大小

    # ===== 表格配置 =====
    # 定义列名
    columns = ["symbol", "platform", "exchange", "least_trade_qty"]
    # 创建表格组件
    tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
    # 设置列标题和宽度
    col_widths = [150, 100, 100, 200]  # 对应每列的宽度
    for idx, col in enumerate(columns):
        tree.heading(col, text=col)
        tree.column(col, width=col_widths[idx], anchor="center")  # 文字居中

    # ===== 按钮配置 =====
    # 按钮框架（让按钮排版更整齐）
    btn_frame = ttk.Frame(root)

    # 添加行按钮
    def add_row():
        tree.insert("", "end", values=["", "", "", ""])

    btn_add = ttk.Button(btn_frame, text="添加行", command=add_row)

    # 删除行按钮
    def delete_row():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选中要删除的行！")
            return
        tree.delete(selected)

    btn_delete = ttk.Button(btn_frame, text="删除选中行", command=delete_row)

    # 保存数据按钮
    def save_data():
        data = []
        for item in tree.get_children():
            data.append(tree.item(item)["values"])
        messagebox.showinfo("成功", f"保存{len(data)}行数据！")
        # 实际项目中可替换为写入文件/数据库的逻辑
        print("保存的数据：", data)

    btn_save = ttk.Button(btn_frame, text="保存数据", command=save_data)

    # ===== 布局（把组件放到窗口里） =====
    tree.pack(padx=10, pady=10, fill="both", expand=True)
    btn_add.pack(side="left", padx=20, pady=5)
    btn_delete.pack(side="left", padx=20, pady=5)
    btn_save.pack(side="left", padx=20, pady=5)
    btn_frame.pack(fill="x", padx=10, pady=5)

    # ===== 初始化示例数据 =====
    tree.insert("", "end", values=["服务器IP", "127.0.0.1", "字符串", "本地测试"])
    tree.insert("", "end", values=["端口号", "8080", "整数", "应用端口"])
    tree.insert("", "end", values=["超时时间", "30", "整数", "单位：秒"])

    return root



