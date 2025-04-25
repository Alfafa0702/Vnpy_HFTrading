from datetime import datetime
import pandas as pd
import numpy as np
import pickle
import os
import lightgbm as lgb
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from pathlib import Path

from vnpy.trader.constant import (
    Direction,
    Offset,
    Exchange,
    Interval,
    Status
)
from vnpy.trader.object import TickData, BarData, TradeData, OrderData

from vnpy_ctastrategy.template import CtaTemplate
from vnpy_ctastrategy.backtesting import BacktestingEngine as BaseEngine
from vnpy_ctastrategy.base import StopOrder
from vnpy.trader.utility import BarGenerator, ArrayManager

# 设置日志
def setup_logger(name: str = "BitcoinStrategy"):
    """设置日志"""
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    log_file = log_path / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.INFO)
    
    # 格式化
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    return logger

class BacktestingEngine(BaseEngine):
    """扩展的回测引擎，支持直接加载K线数据"""
    
    def __init__(self) -> None:
        """初始化"""
        super().__init__()
        self.history_data = []
        
    def load_bars(self, bars: list[BarData] | int) -> None:
        """加载K线数据
        
        参数:
            bars: 如果是list[BarData]，则直接加载这些K线数据
                         如果是int，则加载指定天数的历史数据
        """
        if isinstance(bars, list):
            # 直接加载K线数据列表
            self.history_data.clear()  # 清除之前的数据
            self.history_data.extend(bars)
            print(f"成功加载{len(bars)}条K线数据")
        else:
            # 加载指定天数的历史数据
            days = bars
            print(f"加载{days}天的历史数据")

class BitcoinLgbStrategy(CtaTemplate):
    """基于LGBM的比特币CTA策略"""
    
    author = "ZHOU Yixin"

    # 定义参数
    threshold = 0.0003         # 预测阈值
    min_holding_minutes = 30     # 最小持仓时间（分钟）
    
    # 定义变量
    current_pos = 0              # 当前持仓
    last_entry_time = None       # 最近开仓时间
    last_trade_time = None       # 最近交易时间（包括开仓和平仓）

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 设置日志记录器
        self.logger = setup_logger()
        
        # 加载LGBM模型
        self.model = None  # 显式初始化
        try:
            print("开始加载LGBM模型...")
            self.model = lgb.Booster(model_file='lgbm_model.txt')
            print(f"模型类型: {type(self.model)}")
            print("成功加载LGBM模型")
            self.logger.info("成功加载LGBM模型")
        except Exception as e:
            print(f"加载LGBM模型失败: {str(e)}")
            raise Exception("请确保lgbm_model.txt文件存在且可访问")
        
        # 加载特征数据
        try:
            features_path = os.path.join('all_test_features', 'all_test_features.csv')
            self.features_df = pd.read_csv(features_path)
            trend_path = os.path.join('all_test_features', 'test_trend.csv')
            self.trend_df = pd.read_csv(trend_path)
            self.trend_df['datetime'] = pd.to_datetime(self.trend_df['datetime'], format='%Y/%m/%d %H:%M').dt.strftime('%Y-%m-%d %H:%M:%S')
            self.features_df = pd.merge(self.features_df,self.trend_df,on='datetime', how='inner')
            self.features_df['datetime'] = pd.to_datetime(self.features_df['datetime'])
            self.features_df.set_index('datetime', inplace=True)
            print("成功加载特征数据")
            
            # 获取特征列名（feature1到feature23）
            self.feature_columns = [f'feature{i}' for i in range(1, 24)]
            
            # 验证所有特征列都存在
            missing_features = [col for col in self.feature_columns if col not in self.features_df.columns]
            if missing_features:
                raise Exception(f"缺少特征列: {missing_features}")
                
            # 验证价格列存在
            required_columns = ['Open','High', 'Low', 'Close']
            missing_columns = [col for col in required_columns if col not in self.features_df.columns]
            if missing_columns:
                raise Exception(f"缺少价格列: {missing_columns}")
                
            print(f"成功识别{len(self.feature_columns)}个特征")
            
        except Exception as e:
            print(f"加载特征数据失败: {str(e)}")
            raise Exception("请确保特征数据文件存在且格式正确")
        
        # K线生成器
        self.bg = BarGenerator(self.on_bar)
        
        # 时间序列
        self.am = ArrayManager()
        
    def load_bars(self, days: int) -> None:
        """加载指定天数的历史数据"""
        self.cta_engine.load_bars(days)
        
    def on_init(self):
        """策略初始化"""
        print("策略初始化")
        self.load_bars(1)  # 加载1天的历史数据用于初始化
        
    def on_start(self):
        """策略启动"""
        print("策略启动")
    
    def on_stop(self):
        """策略停止"""
        print("策略停止")

    def get_features(self, bar: BarData) -> np.ndarray:
        """获取特征数据"""
        try:
            # 将bar的datetime转换为与features_df索引相同的格式
            dt = pd.Timestamp(bar.datetime).floor('min')  # 将时间向下取整到分钟
            
            # 获取当前时间点的特征
            try:
                current_data = self.features_df.loc[dt]
                
                # 更新bar的价格数据
                bar.open_price = current_data['Open']
                bar.high_price = current_data['High']
                bar.low_price = current_data['Low']
                bar.close_price = current_data['Close']
                
                # 只获取特征列的数据并确保格式正确
                feature_values = current_data[self.feature_columns].values
                feature_values = feature_values.reshape(1, -1).astype(np.float32)
                return feature_values, current_data['trend']
                
            except KeyError:
                print(f"警告：在特征数据中找不到时间点 {dt}")
                return None
                
        except Exception as e:
            print(f"获取特征时发生错误: {str(e)}")
            return None

    def get_trading_volume(self, price): # 先弃用
        """计算可交易数量"""
        capital = self.cta_engine.capital # !!这里的capital根本不对，并不是balance
        # 使用50%的资金进行交易，留50%作为缓冲
        available_capital = capital * 0.5
        volume = available_capital / price
        return volume

    def can_trade(self, bar: BarData) -> bool:
        """检查是否可以交易"""
        if self.last_trade_time is None:
            return True
            
        # 计算距离上次交易的时间（分钟）
        minutes_since_last_trade = (bar.datetime - self.last_trade_time).total_seconds() / 60
        
        if minutes_since_last_trade < self.min_holding_minutes:
            self.logger.info(f"距离上次交易仅{minutes_since_last_trade:.1f}分钟，小于最小间隔{self.min_holding_minutes}分钟，暂不交易")
            return False
            
        return True

    def on_bar(self, bar: BarData):
        """K线更新回调"""
        self.am.update_bar(bar)
        self.trading_target = 0.02
        if not self.am.inited:
            return
            
        # 获取特征并预测
        features,trend = self.get_features(bar)
        if features is not None:
            try:
                if self.model is None:
                    raise ValueError("模型未正确加载！")
                prediction = self.model.predict(features)[0] + trend
                
                # 输出预测信号
                signal = "看多" if prediction > self.threshold else "看空" if prediction < -self.threshold else "震荡"
                msg = f"预测信号 >>> 时间: {bar.datetime}, 预测值: {prediction:.6f}, 信号: {signal}"
                self.logger.info(msg)
                
                # 检查是否可以交易
                # if not self.can_trade(bar):
                #     return
                
                # 计算交易数量
                trading_volume = self.trading_target - self.current_pos
                
                # 交易逻辑
                if prediction > self.threshold and self.current_pos <= 0:
                    # 预测上涨，做多
                    if self.current_pos < 0:
                        self.cover(bar.close_price, abs(self.current_pos))  # 平空
                        self.buy(bar.close_price, abs(trading_volume))  # 做多
                    else:
                        self.buy(bar.close_price, trading_volume)  # 做多
                    self.last_entry_time = bar.datetime  # 记录开仓时间
                    self.last_trade_time = bar.datetime  # 记录交易时间
                    
                elif prediction < -self.threshold and self.current_pos >= 0:
                    # 预测下跌，做空
                    if self.current_pos > 0:
                        self.sell(bar.close_price, abs(self.current_pos))  # 平多
                        self.short(bar.close_price, abs(trading_volume))  # 做空
                    else:
                        self.short(bar.close_price, trading_volume)  # 做空
                    self.last_entry_time = bar.datetime  # 记录开仓时间
                    self.last_trade_time = bar.datetime  # 记录交易时间
                    
                elif abs(prediction) < self.threshold and self.current_pos != 0:
                    # 预测震荡，平仓
                    if self.current_pos > 0:
                        self.sell(bar.close_price, abs(self.current_pos)) # 平多
                    else:
                        self.cover(bar.close_price, abs(self.current_pos)) # 平空
                    self.last_entry_time = None  # 清除开仓时间
                    self.last_trade_time = bar.datetime  # 记录交易时间
                    
            except Exception as e:
                print(f"预测过程中发生错误: {str(e)}")
                print(f"特征数据形状: {features.shape}")
                print(f"特征数据类型: {features.dtype}")

    def on_order(self, order: OrderData):
        """委托更新回调"""
        pass

    def on_trade(self, trade: TradeData):
        """成交更新回调"""
        # 更新持仓
        if trade.direction == Direction.LONG:
            self.current_pos += trade.volume
        else:
            self.current_pos -= trade.volume
            
        # 添加详细的交易日志
        trade_type = "开多" if trade.direction == Direction.LONG and trade.offset == Offset.OPEN else \
                    "开空" if trade.direction == Direction.SHORT and trade.offset == Offset.OPEN else \
                    "平多" if trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE else "平空"
        
        msg = f"交易提醒 >>> 时间: {trade.datetime}, 交易类型: {trade_type}, " \
              f"成交价: {trade.price:.4f}, 成交量: {trade.volume:.3f}, " \
              f"当前持仓: {self.current_pos:.3f}"
        print(msg)
        self.logger.info(msg)

def run_backtesting():
    """运行回测"""
    # 创建引擎
    engine = BacktestingEngine()
    
    # 设置回测参数
    engine.set_parameters(
        vt_symbol="BTCUSDT.BINANCE",
        interval="1m",
        start=datetime(2025, 1, 10),
        end=datetime(2025, 4, 15),
        rate=3/10000,           # 手续费率
        slippage=0,            # 滑点
        size=1,                # 合约乘数
        pricetick=0.001,        # 价格精度
        capital=100000,        # 初始资金
    )
    
    # 加载特征数据并转换为K线数据
    features_path = os.path.join('all_test_features', 'all_test_features.csv')
    features_df = pd.read_csv(features_path)
    # 确保datetime列的格式正确
    features_df['datetime'] = pd.to_datetime(features_df['datetime']).dt.floor('min')  # 向下取整到分钟

    # 创建K线数据
    bars = []
    for _, row in features_df.iterrows():
        bar = BarData(
            symbol="BTCUSDT",
            exchange=Exchange.BINANCE,
            datetime=row['datetime'].to_pydatetime(),  # 转换为python datetime对象
            interval=Interval.MINUTE,
            volume=0,  # 如果没有成交量数据，设为0
            open_price=row['Open'],
            high_price=row['High'],
            low_price=row['Low'],
            close_price=row['Close'],
            gateway_name='BINANCE'
        )
        bars.append(bar)
    
    # 将K线数据加载到引擎中
    engine.load_bars(bars)
    
    # 添加策略
    strategy = BitcoinLgbStrategy
    engine.add_strategy(strategy, {})
    
    # 运行回测
    engine.run_backtesting()
    
    # 计算并显示结果
    df = engine.calculate_result()
    stats = engine.calculate_statistics()
    
    logger = setup_logger('BitcoinStrategy_stats')
    # 记录回测统计信息
    logger.info("\n" + "="*50 + "\n回测统计信息：")
    for key, value in stats.items():
        logger.info(f"{key}: {value}")
    
    # 显示图表
    fig = engine.show_chart(df)
    fig.show()
    
    return engine, df, stats

if __name__ == "__main__":
    engine, df, stats = run_backtesting()
    
    # 保存回测结果到csv文件
    df.to_csv(f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    # 保存统计数据到txt文件
    with open(f"backtest_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w', encoding='utf-8') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    
    print("回测完成")
    
    # 保持图表显示
    import matplotlib.pyplot as plt
    plt.show() 