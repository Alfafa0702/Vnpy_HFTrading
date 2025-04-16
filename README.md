# Vnpy_HFTrading
This is MFE5210 25Spring Project

## Get Spot Data from Binance
利用Binance的binance-public-data获取比特币历史(2017.7)以来的快照(Klines)数据，数据频率为1m、3m、5m、15m，数据为24h连续数据，快照数据包括：
| Open time | Open | High | Low | Close | Volume | Close time | Quote asset volume | Number of trades | Taker buy base asset volume | Taker buy quote asset volume | Ignore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 时间戳(Text) | Real | Real | Real | Real | Real   | 时间戳(Text) | Real | INTEGER | Real | Real | Real |
| 1735689600000000 | 4.15070000 | 4.15870000 | 4.15060000 | 4.15540000 | 539.23000000 | 1735693199999999 | 2240.39860900 | 13 | 401.82000000 | 1669.98121300 | 0 |

获取数据并创建数据库bitcoin_data.db，包含表bitcoin_data_1m，bitcoin_data_3m，bitcoin_data_5m，bitcoin_data_15m。
```bash
python database.py
```
从数据库中获取数据示例，从SQLite数据库中获取bitcoin 2024年1月11号早上8点到下午16点的1m快照数据

```python
import sqlite3
import datetime
import pandas as pd

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
```
## Reference
b站：vnpy数字货币高频交易视频教程[bilibili](https://www.bilibili.com/video/BV1ze4y1G743/)  
网易云课程：51bitquant最新版的[《VNPY数字货币量化交易从零到实盘》](https://study.163.com/course/introduction/1210904816.htm?inLoc=ss_sslx_VNPY%E6%95%B0%E5%AD%97%E8%B4%A7%E5%B8%81%E9%87%8F%E5%8C%96%E4%BA%A4%E6%98%93%E4%BB%8E%E9%9B%B6%E5%88%B0%E5%AE%9E%E7%9B%98&from=study)  

Binance 永续合约 策略：[构建针对短周期预测模型+强化学习](https://github.com/jinwukong/btc_-perpetual)  
vnpy_binance的框架：
- [Binance trading gateway for VeighNa Evo](https://github.com/veighna-global/vnpy_binance)
- [数据下载+环境安装](https://blog.csdn.net/m0_58598240/article/details/127700332)
