from numpy import float64
from vnpy_novastrategy import (
    StrategyTemplate,
    BarData, TickData,
    TradeData, OrderData,
    ArrayManager, Interval,
    Parameter, Variable,
    datetime, Direction
)

import lightgbm as lgb
import joblib
import numpy as np

model_path = r'lgbm_model_selected.txt'

class LgbmStrategy(StrategyTemplate):
    """LGBM strategy"""

    author: str = "Group X"

    '''参数'''
    trading_size: float = Parameter(0.02)
    test: bool = Parameter(False)
    trading_stats_interval: int = Parameter(10)

    trading_symbol: str = Variable("")
    cum_interval: int = Variable(0)
    buy_orders: list = Variable([])
    sell_orders: list = Variable([])
    trading_target: int = Variable(0)
    trading_pos: int = Variable(0)
    PnL_long: float = Variable(0.0)
    PnL_short: float = Variable(0.0)

    def on_init(self) -> None:
        """Callback when strategy is inited"""
        self.is_inited = False
        self.trading_symbol: str = self.vt_symbols[0]
        self.bar_dt: datetime = None
        self.am: ArrayManager = ArrayManager(size=24*4*4*4*4)
        '''初始化策略时加载的K线长度'''
        self.load_bars(days=5, interval=Interval.MINUTE)

        '''加载模型'''
        self.model = lgb.Booster(model_file=model_path)
        self.is_inited = True
        self.write_log("Strategy is inited.")

    def on_start(self) -> None:
        """Callback when strategy is started"""
        self.write_log("Strategy is started.")

    def on_stop(self) -> None:
        """Callback when strategy is stoped"""
        self.write_log("Strategy is stopped.")

    def on_tick(self, tick: TickData) -> None:
        """Callback of tick data update"""
        bar: BarData = tick.extra.get("bar", None)
        if not bar:
            return
        self.write_log(str(bar))

        bar_dt: datetime = bar.datetime
        if self.bar_dt and bar_dt == self.bar_dt:
            return
        self.bar_dt = bar_dt

        bars: dict = {bar.vt_symbol: bar}
        self.on_bars(bars)

    def on_bars(self, bars: dict[str, BarData]) -> None:
        """Callback of candle bar update"""
        #self.cancel_all()
        self.cum_interval += 1
        bar: BarData = bars[self.trading_symbol]

        '''接收到新K线后先进先出更新'''
        self.am.update_bar(bar)
        if not self.am.inited or not self.is_inited:
            return

        '''特征的计算'''
        # 1.sma特征, 对应特征编号2, 3, 4, 5
        fast_windows = [12*4*4, 12*4*4*4, 12*4*4*4*4]
        slow_windows = [24*4*4, 24*4*4*4, 24*4*4*4*4]
        fast_ma = np.array([
            self.am.sma(fast_windows[0]),
            self.am.sma(fast_windows[1]),
            self.am.sma(fast_windows[2]),
            self.am.sma_volume(fast_windows[0])
        ])
        slow_ma = np.array([
            self.am.sma(slow_windows[0]),
            self.am.sma(slow_windows[1]),
            self.am.sma(slow_windows[2]),
            self.am.sma_volume(slow_windows[0])
        ])
        sma_diff = (slow_ma - fast_ma) / fast_ma

        # 2. atr特征, 对应特征编号7
        atr_window = 14 * 4 * 4 * 4
        atr = self.am.atr(atr_window) 

        # 3.DI特征, 列表内分别对应特征9, 10, 11
        di_window = [14 * 4, 14 * 4 *4 *4]
        di = [self.am.minus_di(di_window[1]), self.am.plus_di(di_window[0]), self.am.plus_di(di_window[1])]

        # 4.布林带特征, 对应20
        boll_window = 5 * 4 * 4 * 4
        dev = 1
        boll = self.am.boll(boll_window, dev)
        boll_signal = (boll[0] - self.am.close[-1]) / boll[1]
        
        '''信号的计算'''
        features = []
        features.append(sma_diff[0])
        features.append(di[2])
        features.append(sma_diff[3])
        features.append(sma_diff[2])
        features.append(sma_diff[1])
        features.append(atr)
        features.append(di[0])
        features.append(boll_signal)
        features.append(di[1])
        X = np.array(features).reshape(1, -1)
        y_pred = self.model.predict(X)
        signal = y_pred[-1] + self.am.trend_signal_offset()

        if signal > 0.00015:
            signal = 1
        elif signal < -0.00015:
            signal = -1
        else:
            signal = 0
        '''下单'''
        if signal == 0:
            pass
        elif signal == 1:
            self.cancel_all()
            self.trading_target = self.trading_size * signal
            trading_volume: float = self.trading_target - self.trading_pos
            order_info = {"price": bar.close_price * 1.01, "volume": 0, "time": str(bar.datetime)}
            self.buy_orders.append(order_info)
            if abs(trading_volume) > 2e-3:
                self.buy(self.trading_symbol, order_info["price"], abs(trading_volume))
        elif signal == -1:
            self.cancel_all()
            self.trading_target = self.trading_size * signal
            trading_volume: float = self.trading_target - self.trading_pos
            order_info = {"price": bar.close_price * 0.99, "volume": 0, "time": str(bar.datetime)}
            self.sell_orders.append(order_info)
            if abs(trading_volume) > 2e-3:
                self.short(self.trading_symbol, order_info["price"], abs(trading_volume))
        elif signal == 0:
            # 仅取消订单, 不做平仓处理
            self.cancel_all()
        if self.cum_interval >= self.trading_stats_interval:
            self.stat_orders()
            self.cum_interval = 0

        self.put_event()

    def on_trade(self, trade: TradeData) -> None:
        """Callback of trade update"""
        self.trading_pos = self.get_pos(self.trading_symbol)
        if trade.direction == Direction.LONG and self.buy_orders:
            self.buy_orders[-1]["volume"] += trade.volume
        elif trade.direction == Direction.SHORT and self.sell_orders:
            self.sell_orders[-1]["volume"] += trade.volume

        self.put_event()

    def on_order(self, order: OrderData) -> None:
        """Callback of order update"""
        pass

    def stat_orders(self):
        vwap = self.am.vwap(self.trading_stats_interval)
        Pavg_long = sum((x['price'] * x['volume']) for x in self.buy_orders) / (sum(x['volume'] for x in self.buy_orders) + 1e-6)
        Pavg_short = sum((x['price'] * x['volume']) for x in self.sell_orders) / (sum(x['volume'] for x in self.sell_orders) + 1e-6)
        if Pavg_long != 0:
            PnL_long = -1 * (Pavg_long - vwap) / vwap * 10000
        else:
            PnL_long = 0
        if Pavg_short!= 0:
            PnL_short = 1 * (Pavg_short - vwap) / vwap * 10000
        else:
            PnL_short = 0
        self.write_log(f"Trading PnL during last {self.trading_stats_interval} K bars:\nPnL_long in BPs: {PnL_long}, PnL_short in BPs: {PnL_short}")
        self.PnL_long = PnL_long
        self.PnL_short = PnL_short
        # 只保留最后一行订单，其余删除，并将volume清零
        if len(self.buy_orders) > 1:
            self.buy_orders = [self.buy_orders[-1]]
        if self.buy_orders:
            self.buy_orders[-1]["volume"] = 0

        if len(self.sell_orders) > 1:
            self.sell_orders = [self.sell_orders[-1]]
        if self.sell_orders:
            self.sell_orders[-1]["volume"] = 0

