# 全局状态变量，用于标记核心任务是否正在运行
is_task_running = False
is_in_a_period = False
is_in_h_period = False
is_in_us_period = False

t_symbols = []
t_pending_orders={}
# t_bar_data=[]
t_filled_orders={}
t_grid={}

# 最近的成交记录
t_last_bar_data={}



