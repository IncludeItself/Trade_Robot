import threading

# 创建全局锁对象，用于保护tbl_filled_orders表格的访问
orders_lock = threading.Lock()