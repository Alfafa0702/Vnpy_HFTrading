# 以下是一个示例
# 从SQLite数据库中获取bitcoin 2024年1月11号早上8点到下午16点的1m快照数据

import sqlite3
import datetime
import pandas as pd
<<<<<<< HEAD

=======
'''
>>>>>>> 49a73e33990c0b5106c005b2e6e1c365890485a6
# 查看db中的表和表字段
import sqlite3

# 连接到 SQLite 数据库
conn = sqlite3.connect('bitcoin_data.db')
cursor = conn.cursor()

# 查询所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# 遍历每个表
for table in tables:
    table_name = table[0]
    print(f"表名: {table_name}")
    # 查询该表的所有字段名
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for column in columns:
        column_name = column[1]
        print(f"  字段名: {column_name}")

# 关闭数据库连接
conn.close()
'''

# 连接到 SQLite 数据库
conn = sqlite3.connect('bitcoin_data.db')
cursor = conn.cursor()

# 定义查询的时间范围
start_time = datetime.datetime(2024, 1, 11, 8, 0, 0)
end_time = datetime.datetime(2024, 1, 11, 16, 0, 0)

# 将时间转换为时间戳(毫秒)
start_timestamp = int(start_time.timestamp())* 1000
end_timestamp = int(end_time.timestamp())* 1000

# 执行 SQL 查询
query = f"SELECT * FROM bitcoin_data_1m WHERE CAST(Open_time AS INTEGER) >= {start_timestamp} AND CAST(Open_time AS INTEGER) < {end_timestamp}"

# a. 获取查询结果（列表)
cursor.execute(query)
results = cursor.fetchall()
print(len(results))

# b. df格式
df = pd.read_sql(query, conn)
print(df.head())

# 关闭数据库连接
conn.close()
<<<<<<< HEAD
'''
=======
>>>>>>> 49a73e33990c0b5106c005b2e6e1c365890485a6
