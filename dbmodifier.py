import sqlite3
 
def transfer_data(db_path: str):
    """将数据从bitcoin_data_1m转换并存入dbbardata表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建新表（如果不存在）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dbbardata (
            datetime TIMESTAMP,
            symbol TEXT,
            exchange TEXT,
            interval TEXT,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume REAL,
            turnover REAL,
            open_interest REAL,
            close_time INTEGER,
            quote_asset_volume REAL,
            number_of_trades INTEGER,
            taker_buy_base_volume REAL,
            taker_buy_quote_volume REAL,
            ignore INTEGER
        )
        """)
        
        # 转换并插入数据
        cursor.execute("""
        INSERT INTO dbbardata 
        SELECT 
            datetime(Open_time/1000, 'unixepoch') AS datetime,
            'BTC' AS symbol,
            'BINANCE' AS exchange,
            '1m' AS interval,
            Open AS open_price,
            High AS high_price,
            Low AS low_price,
            Close AS close_price,
            Volume AS volume,
            0 AS turnover,
            0 AS open_interest,
            Close_time,
            Quote_asset_volume,
            Number_of_trades,
            Taker_buy_base_asset_volume,
            Taker_buy_quote_asset_volume,
            Ignore
        FROM bitcoin_data_1m
        """)
        
        # 提交更改
        conn.commit()
        print("数据转换完成")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()
def add_id_column(db_path: str, table_name: str):
    """为指定表格添加自增id列"""
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取原表的所有数据
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        # 创建临时表
        columns_str = ", ".join(columns)
        cursor.execute(f"CREATE TABLE temp_table AS SELECT * FROM {table_name}")
        
        # 删除原表
        cursor.execute(f"DROP TABLE {table_name}")
        
        # 创建新表（包含id列）
        new_columns = ["id INTEGER"] + [f"{col} {get_column_type(cursor, 'temp_table', col)}" for col in columns]
        create_table_sql = f"CREATE TABLE {table_name} ({', '.join(new_columns)})"
        cursor.execute(create_table_sql)
        
        # 插入数据
        placeholders = ",".join(["?" for _ in range(len(columns) + 1)])
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        
        # 添加自增id并插入数据
        new_rows = [(i + 1, *row) for i, row in enumerate(rows)]
        cursor.executemany(insert_sql, new_rows)
        
        # 删除临时表
        cursor.execute("DROP TABLE temp_table")
        
        # 提交更改
        conn.commit()
        print(f"成功为表 {table_name} 添加id列")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

def get_column_type(cursor, table_name: str, column_name: str) -> str:
    """获取列的数据类型"""
    cursor.execute(f"SELECT typeof({column_name}) FROM {table_name} LIMIT 1")
    result = cursor.fetchone()
    return result[0].upper() if result else "TEXT"

if __name__ == "__main__":
    # 使用示例
    db_path = r"\.vntrader\bitcoin_data.db"
    table_name = "dbbardata"     # 替换为实际的表名
    transfer_data(db_path)
    add_id_column(db_path, table_name)