import subprocess
import os
import zipfile
import pandas as pd
import sqlite3
from tqdm import tqdm

# # 从binance中下载数据
# subprocess.run(["./get_data.sh"],check=True)

data_freq =['1m','3m','5m','15m'] 
for freq in data_freq:
    table_name = 'bitcoin_data_'+freq
    print(f'存储{freq}数据...')

    # 连接到SQLite数据库，如果不存在则创建
    conn = sqlite3.connect('bitcoin_data.db')
    cursor = conn.cursor()

    # 创建表
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        Open_time TEXT,
        Open REAL,
        High REAL,
        Low REAL,
        Close REAL,
        Volume REAL,
        Close_time TEXT,
        Quote_asset_volume REAL,
        Number_of_trades INTEGER,
        Taker_buy_base_asset_volume REAL,
        Taker_buy_quote_asset_volume REAL,
        Ignore REAL
    )
    """
    cursor.execute(create_table_query)

    # 定义数据所在目录路径
    data_dir = "binance-public-data/python/data/spot/monthly/klines/BTCUSDT/"+freq

    # 存储所有zip文件及其对应的最后6位数字
    zip_files_with_dates = []

    # 遍历目录下的zip文件
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.zip'):
                # 提取文件名中最后6位数字
                date_str = file[-10:-4].replace('-', '')
                zip_file_path = os.path.join(root, file)
                zip_files_with_dates.append((date_str, zip_file_path))

    # 按最后6位数字从小到大排序
    zip_files_with_dates.sort(key=lambda x: x[0])

    # 手动指定列名
    columns = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
            'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume',
            'Taker_buy_quote_asset_volume', 'Ignore']

    # 按排序后的顺序读取数据文件并存入sqlite
    for _, zip_file_path in tqdm(zip_files_with_dates):
        csv_file_name = os.path.basename(zip_file_path).replace('.zip', '.csv')
        # 解压zip文件
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extract(csv_file_name, os.path.dirname(zip_file_path))
        csv_file_path = os.path.join(os.path.dirname(zip_file_path), csv_file_name)
        # 使用pandas读取csv文件
        df = pd.read_csv(csv_file_path,header=None, names=columns)
        # 将数据插入到SQLite表中
        df.to_sql(table_name, conn, if_exists='append', index=False)
        # 删除解压后的csv文件
        os.remove(csv_file_path)

    # 提交事务并关闭连接
    conn.commit()
    conn.close()
    
