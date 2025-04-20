# Vnpy_HFTrading
MFE5210 Project



## Reference
b站：vnpy数字货币高频交易视频教程[bilibili](https://www.bilibili.com/video/BV1ze4y1G743/)  
网易云课程：51bitquant最新版的[《VNPY数字货币量化交易从零到实盘》](https://study.163.com/course/introduction/1210904816.htm?inLoc=ss_sslx_VNPY%E6%95%B0%E5%AD%97%E8%B4%A7%E5%B8%81%E9%87%8F%E5%8C%96%E4%BA%A4%E6%98%93%E4%BB%8E%E9%9B%B6%E5%88%B0%E5%AE%9E%E7%9B%98&from=study)



Kaggle：Crypto Forcasting Using LGBM

https://www.kaggle.com/code/h1yung/crypto-forecasting-using-lgbm



数据：

* **train.csv :**  加密货币的分钟级交易数据，包括时间戳、资产ID、交易次数、开盘价、最高价、最低价、收盘价、交易量、成交量加权平均价（VWAP）和目标值。

- **asset_details.csv**：提供每种加密货币的名称和权重。

- **example_test.csv**：时间序列API数据结构的示例。



数据加载和特征提取

构建新特征



模型训练，训练集和验证集。

超参调优，网格搜索

目标是预测加密货币未来收益，残差对数收益率作为目标值。



————————————————————————————

github：

https://github.com/redjules/LGBM-LightGBM-Model-on-TimeSeries-Data-of-Cryptocurrency-Price

Bitcoin Price Prediction with FB Prophet.ipynb

使用Facebook Prophet模型预测比特币价格
\- 包含时间序列分解（趋势、季节项）与置信区间分析



Bitcoin_Price_Prediction_FBPROPHET_outperform_ARIMAX_ XGBOOST_LSTM

对比Prophet、ARIMAX、XGBoost、LSTM性能
\- 提供模型评估指标（MAE、RMSE）对比



Feature_Engineering_with_Stock_Exchange-Dataset LGBM

展示如何构造滞后特征、移动平均等时序特征
\- LightGBM参数调优示例



Historic_Crypto.ipynb

加密货币历史数据获取与清洗（如CoinGecko API）
\- 波动率计算与相关性热力图分析

——————————————————————————

vnpy_bina

https://github.com/veighna-global/vnpy_binance
