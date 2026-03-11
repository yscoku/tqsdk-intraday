#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略18 - 日内突破策略：焦炭日内突破策略
原理：
    焦炭（J）使用日内突破判断趋势方向。
    价格突破日内高点做多，跌破日内低点做空。

参数：
    - 合约：大商所j2505
    - K线周期：15分钟
    - 周期数：16根K线
    - 止损：0.6% 
    - 止盈：1.2%

适用行情：日内突破行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
import numpy as np

# ============ 参数配置 ============
SYMBOL = "DCE.j2505"            # 焦炭
KLINE_DURATION = 15 * 60        # 15分钟K线
LOOKBACK_PERIOD = 16            # 周期数
STOP_LOSS = 0.006               # 0.6%止损
TAKE_PROFIT = 0.012             # 1.2%止盈

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：焦炭日内突破策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=LOOKBACK_PERIOD + 10)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            if len(klines) < LOOKBACK_PERIOD:
                continue
            
            current_price = klines['close'].iloc[-1]
            current_time = klines['datetime'].iloc[-1]
            
            # 解析时间
            hour = int(current_time[11:13])
            minute = int(current_time[14:16])
            
            # 14:55后不再开仓
            is_near_close = (hour == 14 and minute >= 55) or hour >= 15
            
            # 计算日内高低点
            day_open = klines['open'].iloc[0]
            day_high = klines['high'].iloc[-LOOKBACK_PERIOD:].max()
            day_low = klines['low'].iloc[-LOOKBACK_PERIOD:].min()
            
            # 计算突破阈值
            breakout_pct = 0.3 / 100  # 0.3%
            
            print(f"时间: {current_time}, 价格: {current_price}, 日内高点: {day_high:.2f}, 日内低点: {day_low:.2f}")
            
            # 尾盘强制平仓
            if hour == 14 and minute >= 55:
                if position != 0:
                    print(f"[尾盘平仓] 时间: {current_time}")
                    position = 0
                continue
            
            if position == 0 and not is_near_close:
                # 做多信号：突破日内高点
                if current_price > day_high * (1 + breakout_pct):
                    position = 1
                    entry_price = current_price
                    print(f"[买入] 突破日内高点: {current_price}")
                # 做空信号：跌破日内低点
                elif current_price < day_low * (1 - breakout_pct):
                    position = -1
                    entry_price = current_price
                    print(f"[卖出] 跌破日内低点: {current_price}")
                    
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
                    print(f"[平仓] 跌破日内低点: {current_price}")
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
                    print(f"[平仓] 突破日内高点: {current_price}")
                    position = 0

if __name__ == "__main__":
    main()
