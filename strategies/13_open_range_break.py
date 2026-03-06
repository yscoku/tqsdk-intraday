#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略13 - 开盘区间策略：日内开盘区间突破策略
原理：
    日内交易使用开盘30分钟的高低点作为区间参考。
    价格突破开盘区间上沿做多，突破下沿做空。

参数：
    - 合约：SHFE.rb2505
    - K线周期：15分钟
    - 开盘区间：30分钟
    - 止损：1% 
    - 止盈：2%

适用行情：日内趋势明显的行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from datetime import datetime, time
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2505"          # 螺纹钢
KLINE_DURATION = 15 * 60        # 15分钟K线
OPEN_RANGE_MIN = 30             # 开盘区间分钟数
STOP_LOSS = 0.01                # 1%止损
TAKE_PROFIT = 0.02              # 2%止盈

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：日内开盘区间突破策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=100)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    range_high = 0
    range_low = 0
    range_defined = False
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            current_price = klines['close'].iloc[-1]
            current_time = datetime.now().time()
            
            # 每天9:00-9:30定义开盘区间
            if not range_defined and current_time >= time(9, 0) and current_time <= time(9, 35):
                if len(klines) >= 2:
                    range_high = klines['high'].iloc[-2:]
                    range_low = klines['low'].iloc[-2:]
                    range_high = range_high.max()
                    range_low = range_low.min()
                    range_defined = True
                    print(f"[开盘区间] 高点: {range_high}, 低点: {range_low}")
            
            # 每天11:30和15:00清仓
            if current_time >= time(11, 30) or current_time >= time(15, 0):
                if position != 0:
                    print(f"[收盘平仓] 价格: {current_price}")
                    position = 0
                    range_defined = False
            
            if range_defined:
                print(f"价格: {current_price}, 区间高点: {range_high}, 区间低点: {range_low}")
                
                if position == 0:
                    # 做多信号：突破区间高点
                    if current_price > range_high:
                        position = 1
                        entry_price = current_price
                        print(f"[买入] 突破区间高点: {current_price}")
                    # 做空信号：跌破区间低点
                    elif current_price < range_low:
                        position = -1
                        entry_price = current_price
                        print(f"[卖出] 跌破区间低点: {current_price}")
                        
                elif position == 1:
                    pnl_pct = (current_price - entry_price) / entry_price
                    
                    if pnl_pct < -STOP_LOSS:
                        print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                        position = 0
                    elif pnl_pct > TAKE_PROFIT:
                        print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                        position = 0
                        
                elif position == -1:
                    pnl_pct = (entry_price - current_price) / entry_price
                    
                    if pnl_pct < -STOP_LOSS:
                        print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                        position = 0
                    elif pnl_pct > TAKE_PROFIT:
                        print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                        position = 0
    
    api.close()

if __name__ == "__main__":
    main()
