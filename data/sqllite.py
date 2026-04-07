import sqlite3
import threading
from datetime import datetime, timedelta
import decimal  # 量化用decimal避免浮点数精度问题
from unittest import result

from config.app_config import appConfig

# 使用 threading.local() 为每个线程创建独立的数据库连接
db_local = threading.local()

def get_db_connection():
    """为当前线程获取或创建数据库连接"""
    if not hasattr(db_local, 'conn'):
        db_local.conn = sqlite3.connect(
            database="data/trade_robot.db",
            check_same_thread=False  # 每个线程独享连接，无需检查
        )
        db_local.conn.row_factory = sqlite3.Row
    return db_local.conn

def close_db_connection():
    """关闭当前线程的数据库连接"""
    if hasattr(db_local, 'conn'):
        db_local.conn.close()
        del db_local.conn

# 初始化数据库表
def init_tables():
    """初始化数据库表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # 1. 创建tbl_pending_order（挂单表）
    create_order_table_sql = """
        create table if not exists tbl_pending_orders
        (
            symbol          TEXT    not null,
            qty             REAL    not null,
            price           REAL    not null,
            timestamp       REAL not null,
            id              integer not null
                constraint tbl_pending_order_pk
                    primary key,
            direction       TEXT    not null
        );
    """
    cursor.execute(create_order_table_sql)

    # 2. 创建tbl_symbols（股票代码表）
    # ... (此处省略，与原代码相同)

    # 3. 创建tbl_bar_data（K线数据表）
    create_bar_data_table_sql = """
        create table if not exists tbl_bar_data
        (
            id           integer           not null
        primary key autoincrement,
        symbol       TEXT              not null,
        timestamp    REAL           not null,
        price        REAL              not null,
        pre_close    REAL              not null,
        open         REAL              not null,
        highest      REAL              not null,
        lowest       REAL              not null,
        volume       REAL              not null,
        value        REAL              not null,
        total_volume REAL default 0    not null,
        total_value  REAL default 0    not null,
        date         TEXT default DATE not null,
        time         TEXT default TIME not null
        );
    """
    cursor.execute(create_bar_data_table_sql)

    # 4. 创建tbl_filled_orders
    create_filled_orders_table_sql = """
    create table if not exists tbl_filled_orders
    (
        id         integer        not null
            constraint tbl_filled_orders_pk
                primary key autoincrement,
        timestamp  REAL        not null,
        symbol     TEXT           not null,
        quantity   REAL        not null,
        price      REAL           not null,
        pos_qty    REAL           not null,
        cleared    INT  default 0 not null,
        amount     REAL default 0 not null,
        commission real default 0 not null
    );
        """
    cursor.execute(create_filled_orders_table_sql)
    conn.commit()

    # 5. 创建tbl_bar_history
    create_bar_history_table_sql = """
    create table if not exists tbl_bar_history
    (
        symbol  TEXT not null,
        open    REAL not null,
        highest REAL not null,
        lowest  REAL not null,
        close   REAL not null,
        volume  REAL not null,
        value   REAL not null,
        date    text not null,
        constraint tbl_bar_history_pk
            primary key (symbol, date)
    );
    """
    cursor.execute(create_bar_history_table_sql)
    conn.commit()

    print("✅ 数据库表初始化成功")

# 在程序启动时，可以先初始化一次
init_tables()

def get_previous_time_timestamp(target_time_str):
    now = datetime.now()
    hour, minute = map(int, target_time_str.split(":"))
    target_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now >= target_today:
        target_datetime = target_today
    else:
        target_datetime = target_today - timedelta(days=1)
    return target_datetime.timestamp()

def refresh_tbl_pending_order():
    """刷新挂单表，删除所有数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = get_previous_time_timestamp(appConfig["start_time"])
    cursor.execute("DELETE FROM tbl_pending_orders WHERE timestamp < ?", (timestamp,))
    conn.commit()
    print("✅ 挂单表已刷新，删除所有数据")

def refresh_tbl_bar_data():
    """刷新K线数据表，删除所有数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = get_previous_time_timestamp(appConfig["start_time"])-60*60
    cursor.execute("DELETE FROM tbl_bar_data WHERE timestamp < ?", (timestamp,))
    conn.commit()
    print("✅ 盘口数据表已刷新，删除所有数据")

def get_pending_orders(t_symbols):
    """获取所有挂单"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_pending_orders")
    rows = cursor.fetchall()
    result={}
    for symbol_info in t_symbols:
        result[symbol_info["symbol"]]=[dict(row) for row in rows if row["symbol"]==symbol_info["symbol"]]
    return result

def get_pending_orders_symbol(symbol:str):
    """获取指定股票的所有挂单"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_pending_orders WHERE symbol=?", (symbol,))
    rows = cursor.fetchall()
    rows = [dict(row) for row in rows]
    return rows

def get_filled_orders(t_symbols):
    """获取所有成交记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_filled_orders WHERE cleared=0 order by timestamp desc")
    rows = cursor.fetchall()
    result={}
    for symbol_info in t_symbols:
        result[symbol_info["symbol"]]=[dict(row) for row in rows if row["symbol"]==symbol_info["symbol"]]
    return result

def get_filled_orders_symbol(symbol:str):
    """获取指定股票的所有成交记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_filled_orders WHERE symbol=? and cleared=0 order by timestamp desc", (symbol,))
    rows = cursor.fetchall()
    rows=[dict(row) for row in rows]
    return rows

def get_bar_data(symbol,start_time,end_time):
    conn = get_db_connection()
    cursor = conn.cursor()
    select_sql = """
    SELECT * FROM tbl_bar_data WHERE symbol=? and timestamp>=? and timestamp<=? order by timestamp
    """
    cursor.execute(select_sql, (symbol,start_time,end_time))
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return rows

def get_last_bar_data(symbol:str):
    """获取指定股票的最新K线数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    select_sql = """
    SELECT * FROM tbl_bar_data WHERE symbol=? order by timestamp desc limit 1
    """
    cursor.execute(select_sql, (symbol,))
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return rows[0] if rows else None

def get_last_bar_datas(t_symbols):
    """获取所有股票的最新K线数据"""
    result={}
    for symbol_info in t_symbols:
        result[symbol_info["symbol"]]=get_last_bar_data(symbol_info["symbol"])
    return result

def get_last_day_bar(symbol:str):
    """获取历史日K线数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # 获取今天日期的前的天的日期
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    select_sql = """
        SELECT * FROM tbl_bar_history WHERE symbol=? and date=? limit 1
                 """
    cursor.execute(select_sql, (symbol,yesterday_str))
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return rows[0] if rows else None

def insert_bar_data(bar_data):
    """插入K线数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    insert_sql = """
    INSERT INTO tbl_bar_data 
    (symbol, timestamp,date,time, price, pre_close, open, highest, lowest, volume, value,total_volume,total_value)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?,?,?)
    """
    cursor.execute(
        insert_sql,
        (bar_data["code"], bar_data["timestamp"],bar_data["date"],str(bar_data["time"]), bar_data["price"], bar_data["pre_close"], bar_data["open"], bar_data["highest"], bar_data["lowest"], bar_data["volume"], bar_data["value"],bar_data["total_volume"],bar_data["total_value"])
    )
    conn.commit()
    # print(f"✅ 插入K线数据 {bar_data['symbol']} {bar_data['timestamp']} 成功")

def delete_tbl_pending_orders(symbol_id):
    """删除一条记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    delete_sql = "DELETE FROM tbl_pending_orders WHERE id =?"
    cursor.execute(delete_sql, (symbol_id,))
    conn.commit()
    print(f"删除挂单表中的记录 {symbol_id}")


def insert_filled_order(filled_order):
    """插入成交记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    insert_sql = """
    INSERT INTO tbl_filled_orders 
    (timestamp, symbol, quantity, price, pos_qty,amount,commission)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(
        insert_sql,
        (filled_order["timestamp"], filled_order["symbol"], filled_order["quantity"], filled_order["price"], filled_order["pos_qty"],filled_order["amount"],filled_order["commission"])
    )
    conn.commit()
    print(f"✅ 插入成交记录 {filled_order['symbol']} {filled_order['timestamp']} 成功")

def insert_pending_order(pending_order):
    """插入挂单"""
    conn = get_db_connection()
    cursor = conn.cursor()
    insert_sql = """
    INSERT INTO tbl_pending_orders
    (symbol, qty, price, direction, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(
        insert_sql,
        (pending_order["symbol"], pending_order["qty"], pending_order["price"], pending_order["direction"], pending_order["timestamp"])
    )
    conn.commit()
    print(f"✅ 插入挂单 {pending_order['symbol']} {pending_order['timestamp']} 成功")

def update_tbl_filled_orders_symbol(filled_symbol):
    """更新成交记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    for filled_order in filled_symbol:
        update_sql = """
        UPDATE tbl_filled_orders 
        SET cleared=?, pos_qty=?, timestamp=?, quantity=?, price=?, symbol=?,amount=?,commission=? WHERE id=?
        """
        cursor.execute(
            update_sql,
            (filled_order["cleared"], filled_order["pos_qty"], filled_order["timestamp"], filled_order["quantity"], filled_order["price"], filled_order["symbol"],filled_order["amount"],filled_order["commission"], filled_order["id"])
        )
    conn.commit()
    print(f"✅ 更新成交记录 {filled_symbol[0]['symbol']} 成功")

def insert_bar_history(bar_history):
    conn = get_db_connection()
    cursor = conn.cursor()
    insert_sql = """
    INSERT OR REPLACE INTO tbl_bar_history
    (symbol, open, highest, lowest, close, volume, value, date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(
        insert_sql,
        (bar_history["symbol"], bar_history["open"], bar_history["highest"], bar_history["lowest"], bar_history["close"], float(bar_history["volume"]), float(bar_history["value"]), bar_history["date"])
    )
    conn.commit()
    print(f"✅ 更新历史数据： {bar_history['symbol']} {bar_history['date']} 成功")

def get_filled_timestamp(symbols):
    conn = get_db_connection()
    cursor = conn.cursor()
    select_sql="""
    SELECT symbol,max(timestamp) as timestamp FROM tbl_filled_orders group by symbol
    """
    cursor.execute(select_sql)
    rows = cursor.fetchall()
    dict_result={}
    for symbol in symbols:
        try:
            row=next(row for row in rows if row["symbol"] == symbol["symbol"])
            dict_result[symbol["symbol"]]=row["timestamp"] if row else 0
        except:
            dict_result[symbol["symbol"]]=0

    return dict_result


def insert_order(symbol, order_id, side, order_type, price, quantity, status):
    """插入订单数据，自动计算金额"""
    conn = get_db_connection()
    cursor = conn.cursor()
    insert_sql = """
    INSERT OR REPLACE INTO orders 
    (symbol, order_id, side, order_type, price, quantity, status, create_time, update_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    now = datetime.now()
    price_dec = decimal.Decimal(str(price))
    quantity_dec = decimal.Decimal(str(quantity))
    cursor.execute(
        insert_sql,
        (symbol, order_id, side, order_type, float(price_dec), float(quantity_dec), status, now, now)
    )
    conn.commit()
    print(f"✅ 插入订单 {order_id} 成功")

def insert_trade(symbol, trade_id, order_id, price, quantity, side, realized_pnl=0, commission=0, commission_asset='USDT', timestamp=None, position_side='BOTH', is_maker=False, is_buyer=False):
    """插入成交记录数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    insert_sql = """
    INSERT OR REPLACE INTO trades 
    (symbol, trade_id, order_id, price, quantity, side, realized_pnl, commission, commission_asset, timestamp, position_side, is_maker, is_buyer, create_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    now = datetime.now()
    if timestamp is None:
        timestamp = now
    elif isinstance(timestamp, int):
        timestamp = datetime.fromtimestamp(timestamp / 1000)
    
    price_dec = decimal.Decimal(str(price))
    quantity_dec = decimal.Decimal(str(quantity))
    realized_pnl_dec = decimal.Decimal(str(realized_pnl))
    commission_dec = decimal.Decimal(str(commission))
    
    cursor.execute(
        insert_sql,
        (
            symbol, trade_id, order_id, float(price_dec), float(quantity_dec), side, 
            float(realized_pnl_dec), float(commission_dec), commission_asset, 
            timestamp, position_side, is_maker, is_buyer, now
        )
    )
    conn.commit()
    print(f"✅ 插入成交记录 {trade_id} 成功")

def get_trades(symbol=None, limit=50, start_time=None, end_time=None):
    """查询成交记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    query_sql = "SELECT * FROM trades WHERE 1=1"
    params = []
    
    if symbol:
        query_sql += " AND symbol = ?"
        params.append(symbol)
    
    if start_time:
        query_sql += " AND timestamp >= ?"
        params.append(start_time)
    
    if end_time:
        query_sql += " AND timestamp <= ?"
        params.append(end_time)
    
    query_sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query_sql, params)
    return cursor.fetchall()

# 主线程退出时，可以考虑关闭所有线程的连接，但这通常不是必须的
# 因为守护线程会随主程序退出
def close_all_connections():
    # 这个函数在这里更多是概念性的，因为我们无法直接访问其他线程的db_local
    print("\n🔌 概念性关闭所有连接...实际应由各线程自行管理。")

if __name__ == "__main__":
    # 插入模拟数据
    insert_trade(
        symbol="ETHUSDT",
        trade_id="244444320",
        order_id="8443167746",
        price="1949.41",
        quantity="0.013",
        side="BUY",
        realized_pnl="0",
        commission="0.01013693",
        commission_asset="USDT",
        timestamp=1772432980175,
        position_side="BOTH",
        is_maker=False,
        is_buyer=True
    )
    
    insert_trade(
        symbol="ETHUSDT",
        trade_id="244444888",
        order_id="8443171859",
        price="1949.07",
        quantity="0.013",
        side="SELL",
        realized_pnl="-0.00442000",
        commission="0.01013516",
        commission_asset="USDT",
        timestamp=1772433084831,
        position_side="BOTH",
        is_maker=False,
        is_buyer=False
    )
    
    insert_trade(
        symbol="ETHUSDT",
        trade_id="244476093",
        order_id="8443317914",
        price="1940.09",
        quantity="0.013",
        side="BUY",
        realized_pnl="0",
        commission="0.01008846",
        commission_asset="USDT",
        timestamp=1772437385011,
        position_side="BOTH",
        is_maker=False,
        is_buyer=True
    )
    close_db_connection() # 在主线程的末尾关闭连接