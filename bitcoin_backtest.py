from datetime import datetime
import polars as pl
import numpy as np
import lightgbm as lgb
from vnpy.trader.constant import Interval, Direction, Offset
from vnpy.trader.object import BarData
from vnpy.alpha.strategy.backtesting import BacktestingEngine
from vnpy.alpha.strategy.template import AlphaStrategy
from vnpy.alpha.lab import AlphaLab
import sqlite3
import pandas as pd

'''
改成ctastrategy的框架(单品种交易)
在trader的object.py里面注册symbol
在excel里面添加两列exchange symbol
在测试集上回测
'''

class BitcoinStrategy(AlphaStrategy):
    """比特币交易策略"""
    
    def __init__(self, engine, strategy_name, vt_symbols, setting):
        """初始化策略"""
        super().__init__(engine, strategy_name, vt_symbols, setting)
        
        # 加载LGBM模型
        try:
            self.model = lgb.Booster(model_file='lgbm_model.txt')
            self.write_log("成功加载LGBM模型")
        except Exception as e:
            self.write_log(f"加载LGBM模型失败: {str(e)}")
            raise Exception("请确保已经训练并保存了LGBM模型到lgbm_model.txt")
        
        # 加载特征数据
        try:
            self.features_df = pd.read_excel('features.xlsx', index_col='datetime')
            self.features_df.index = pd.to_datetime(self.features_df.index)
            self.write_log("成功加载特征数据")
        except Exception as e:
            self.write_log(f"加载特征数据失败: {str(e)}")
            raise Exception("请确保features.xlsx文件存在且格式正确")
        
        # 策略参数
        self.threshold = 0.5  # 预测概率阈值
        self.position_size = 0.1  # 每次交易数量
        
        # 策略变量
        self.bar_count = 0
        self.current_position = 0
        
    def on_init(self):
        """策略初始化"""
        self.write_log("策略初始化")
        
    def on_trade(self, trade):
        """成交回调"""
        self.write_log(f"成交：{trade.vt_symbol}, 方向：{trade.direction}, 价格：{trade.price}, 数量：{trade.volume}")
        
    def get_features(self, bar: BarData) -> np.ndarray:
        """获取特征数据"""
        try:
            # 获取当前时间点的特征
            current_features = self.features_df.loc[bar.datetime]
            return current_features.values.reshape(1, -1)
        except KeyError:
            self.write_log(f"警告：在特征数据中找不到时间点 {bar.datetime}")
            return None
        
    def on_bars(self, bars: dict[str, BarData]):
        """K线更新"""
        # 获取比特币K线数据
        bar = bars["BTCUSDT.BINANCE"]
        
        # 更新K线计数
        self.bar_count += 1
        
        # 获取特征
        features = self.get_features(bar)
        
        # 使用模型预测
        if features is not None:
            prediction = self.model.predict(features)[0]
            
            # 获取当前持仓
            pos = self.get_pos("BTCUSDT.BINANCE")
            
            # 交易信号
            if prediction > self.threshold and pos <= 0:
                # 预测上涨，做多
                self.send_order(
                    "BTCUSDT.BINANCE",
                    Direction.LONG,
                    Offset.OPEN,
                    bar.close_price,
                    self.position_size
                )
                self.current_position = 1
                
            elif prediction < -self.threshold and pos >= 0:
                # 预测下跌，做空
                self.send_order(
                    "BTCUSDT.BINANCE",
                    Direction.SHORT,
                    Offset.OPEN,
                    bar.close_price,
                    self.position_size
                )
                self.current_position = -1
                
            elif abs(prediction) < self.threshold and pos != 0:
                # 预测震荡，平仓
                if pos > 0:
                    self.send_order(
                        "BTCUSDT.BINANCE",
                        Direction.SHORT,
                        Offset.CLOSE,
                        bar.close_price,
                        abs(pos)
                    )
                else:
                    self.send_order(
                        "BTCUSDT.BINANCE",
                        Direction.LONG,
                        Offset.CLOSE,
                        bar.close_price,
                        abs(pos)
                    )
                self.current_position = 0

class BacktestingEngine(BacktestingEngine):
    """扩展的回测引擎，支持从Excel加载数据"""
    
    def __init__(self, lab: AlphaLab) -> None:
        super().__init__(lab)
        self.data_df = None
        
    def load_excel_data(self, file_path: str) -> None:
        """从Excel加载数据"""
        # 读取Excel数据
        self.data_df = pd.read_excel(file_path, index_col='datetime')
        self.data_df.index = pd.to_datetime(self.data_df.index)
        
        # 将数据转换为BarData对象
        for dt in self.data_df.index:
            row = self.data_df.loc[dt]
            bar = BarData(
                symbol="BTCUSDT",
                exchange=Exchange.BINANCE,
                datetime=dt,
                interval=Interval.MINUTE,
                volume=row['volume'],
                open_price=row['open'],
                high_price=row['high'],
                low_price=row['low'],
                close_price=row['close'],
                gateway_name=self.gateway_name
            )
            self.history_data[(dt, "BTCUSDT.BINANCE")] = bar
            self.dts.add(dt)

def main():
    """主函数"""
    # 创建回测引擎
    lab = AlphaLab("./lab_data")
    engine = BacktestingEngine(lab)
    
    # 设置回测参数
    engine.set_parameters(
        vt_symbols=["BTCUSDT.BINANCE"],  # 交易对
        interval=Interval.MINUTE,         # 时间周期
        start=datetime(2023, 1, 1),       # 开始时间
        end=datetime(2023, 12, 31),       # 结束时间
        capital=100000,                   # 初始资金
        risk_free=0,                      # 无风险利率
        annual_days=365                   # 年交易日数
    )
    
    # 设置合约参数
    vt_symbol = "BTCUSDT.BINANCE"
    long_rate = 0.0003    # 做多手续费率
    short_rate = 0.0003   # 做空手续费率
    size = 1              # 合约乘数
    pricetick = 0.01      # 价格精度
    
    # 添加合约设置
    lab.add_contract_setting(
        vt_symbol,
        long_rate,
        short_rate,
        size,
        pricetick
    )
    
    # 创建信号数据框
    signal_df = pl.DataFrame()
    
    # 添加策略
    engine.add_strategy(BitcoinStrategy, setting={}, signal_df=signal_df)
    
    # 从Excel加载数据
    engine.load_excel_data('price_data.xlsx')  # 假设价格数据在price_data.xlsx中
    
    # 运行回测
    engine.run_backtesting()
    
    # 计算回测结果
    engine.calculate_result()
    
    # 显示回测结果
    engine.show_chart()
    engine.show_performance("BTCUSDT.BINANCE")

if __name__ == "__main__":
    main() 