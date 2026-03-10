#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略17 - 日内趋势突破策略：螺纹钢期货日内趋势突破策略
原理：
    螺纹钢期货（RB）使用日内高低点突破进行趋势交易。
    突破当日高点时做多，跌破当日低点时做空。

参数：
    - 合约：上期所RB2505
    - K线周期：15分钟
    - 止损：1.5% 
    - 止盈：3%
    - 收盘前平仓：是

适用行情：日内趋势明显的行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from datetime import datetime
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.RB2505"          # 螺纹钢期货
KLINE_DURATION = 15 * 60        # 15分钟K线
STOP_LOSS = 0.015               # 1.5%止损
TAKE_PROFIT = 0.03              # 3%止盈
CLOSE_TIME = 14                 # 收盘时间（小时）

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：螺纹钢期货日内趋势突破策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=100)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    day_high = 0
    day_low = float('inf')
    last_trading_date = None
    
    while True:
        api.wait_update()
        
        # 获取当前时间
        current_time = datetime.now()
        trading_date = current_time.strftime("%Y-%m-%d")
        
        # 新交易日重置
        if last_trading_date is not None and trading_date != last_trading_date:
            day_high = 0
            day_low = float('inf')
            position = 0
            
        last_trading_date = trading_date
        
        # 更新日内高低点
        if len(klines) > 0:
            current_high = klines['high'].iloc[-1]
            current_low = klines['low'].iloc[-1]
            
            if current_high > day_high:
                day_high = current_high
            if current_low < day_low:
                day_low = current_low
        
        if api.is_changing(klines):
            current_price = klines['close'].iloc[-1]
            
            print(f"价格: {current_price}, 日内高点: {day_high:.2f}, 日内低点: {day_low:.2f}")
            
            # 收盘前平仓
            if current_time.hour >= CLOSE_TIME and position != 0:
                print(f"[收盘平仓] 时间: {current_time}")
                position = 0
                continue
            
            if position == 0:
                # 做多信号：突破日内高点
                if day_high > 0 and current_price > day_high:
                    position = 1
                    entry_price = current_price
                    print(f"[买入] 突破日内高点: {current_price}, 高点: {day_high:.2f}")
                # 做空信号：跌破日内低点
                elif day_low < float('inf') and current_price < day_low:
                    position = -1
                    entry_price = current_price
                    print(f"[卖出] 跌破日内低点: {current_price}, 低点: {day_low:.2f}")
                    
            elif position == 1:
                pnl_pct = (current_price - entry_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 跌破日内低点平仓
                elif current_price < day_low:
                    print(f"[平仓] 跌破日内低点")
                    position = 0
                    
            elif position == -1:
                pnl_pct = (entry_price - current_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 突破日内高点平仓
                elif current_price > day_high:
                    print(f"[平仓] 突破日内高点")
                    position = 0
    
    api.close()

if __name__ == "__main__":
    main()
