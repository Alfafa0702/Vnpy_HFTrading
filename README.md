# Vnpy_HFTrading
MFE5210 Project



## Reference
b站：vnpy数字货币高频交易视频教程[bilibili](https://www.bilibili.com/video/BV1ze4y1G743/)  
网易云课程：51bitquant最新版的[《VNPY数字货币量化交易从零到实盘》](https://study.163.com/course/introduction/1210904816.htm?inLoc=ss_sslx_VNPY%E6%95%B0%E5%AD%97%E8%B4%A7%E5%B8%81%E9%87%8F%E5%8C%96%E4%BA%A4%E6%98%93%E4%BB%8E%E9%9B%B6%E5%88%B0%E5%AE%9E%E7%9B%98&from=study)



## LGBM Model

使用BTC 1 min 快照数据进行特征工程和模型训练；

数据预处理部分：对毫秒级时间戳进行转换；前向填充处理缺失值；

特征工程部分：

1. **SMA 差分**：计算不同周期的简单移动平均线并归一化。

1. **布林带**：计算不同窗口下的布林带，现价离上轨距离与带宽的占比。
2. **RSI**：使用较长周期计算 RSI。
3. **NATR**：计算归一化真实波幅。
4. **DI+/DI-**：计算正向/负向动向指标。
5. **对数收益率**：计算现价与前一窗口价的对数差。
6. **上下影线占比**：计算上影线和下影线的占比。
7. **主动买入特征**：计算主动买入 BTC 和计价币的占比及强度差分。

模型训练与评估：

- **训练集**：2018.1.1 - 2024.1.9

- **测试集**：2024.1.10 - 2025.4.15

- **模型选择**：使用 LGBMRegressor 进行 3 折交叉验证，并通过 GridSearchCV 调参。

  训练集 RMSE: 0.0038197

  测试集 RMSE: 0.0028296

  训练集 Corr: 0.3616

  测试集 Corr: 0.0371
