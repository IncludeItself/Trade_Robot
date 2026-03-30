## 数据库设计
### tbl_pending_orders
```sql
create table if not exists tbl_pending_orders
    (
        symbol          TEXT    not null,
        qty             REAL    not null,
        price           REAL    not null,
        order_id_to_clr integer,
        timestamp       integer not null,
        id              integer not null
            constraint tbl_pending_order_pk
                primary key,
        direction       TEXT    not null
    );
```

### tbl_symbols
```sql
create table if not exists tbl_symbols
(
    symbol        TEXT    not null
        constraint tbl_symbols_pk
            primary key,
    platform      TEXT    not null,
    exchange      TEXT    not null,
    core_position REAL    not null
);
```

### tbl_bar_data
```sql
create table if not exists tbl_bar_data
    (
        id             integer        not null
            primary key autoincrement,
        symbol         TEXT           not null,
        timestamp      integer        not null,
        price          REAL           not null,
        pre_close      REAL           not null,
        open           REAL           not null,
        highest        REAL           not null,
        lowest         REAL           not null,
        volume         REAL           not null,
        turnover       REAL           not null,
        total_volume   REAL default 0 not null,
        total_turnover REAL default 0 not null
    );
```

### tbl_filled_orders
```sql
create table if not exists tbl_filled_orders
    (
        id        integer not null
            constraint tbl_filled_orders_pk
                primary key autoincrement,
        timestamp integer not null,
        symbol    TEXT    not null,
        quantity  integer not null,
        price     REAL    not null,
        pos_qty   REAL    not null
    );
```