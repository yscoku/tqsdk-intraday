#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略05 - 日内交易：ATR突破策略
原理：
    使用ATR（平均真实波幅）动态计算止损止盈。
    突破高点时做多，跌破低点时做空。

参数：
    - 合约：SHFE.rb2505
    - 周期：15分钟
    - ATR周期：20
    - 突破系数：0.5倍ATR
    - 止损：1倍ATR

适用行情：日内趋势行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from tqsdk.ta import ATR
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2505"          # 螺纹钢
KLINE_DURATION = 15 * 60        # 15分钟K线
ATR_PERIOD = 20                  # ATR周期
BREAKOUT_MULT = 0.5              # 突破系数
STOP_MULT = 1.0                  # 止损系数

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：ATR日内突破策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=ATR_PERIOD + 10)
    
    position = 0
    entry_price = 0
    stop_loss = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            if len(klines) < ATR_PERIOD:
                continue
                
            atr = ATR(klines, ATR_PERIOD).iloc[-1]
            high = klines['high'].iloc[-1]
            low = klines['low'].iloc[-1]
            
            current_price = klines['close'].iloc[-1]
            
            print(f"价格: {current_price}, ATR: {atr:.2f}, 高: {high:.2f}, 低: {low:.2f}")
            
            if position == 0:
                # 突破高点
                if current_price > high + BREAKOUT_MULT * atr:
                    position = 1
                    entry_price = current_price
                    stop_loss = current_price - STOP_MULT * atr
                    print(f"[买入] 价格: {current_price}, 止损: {stop_loss:.2f}")
                    
                # 跌破低点
                elif current_price < low - BREAKOUT_MULT * atr:
                    position = -1
                    entry_price = current_price
                    stop_loss = current_price + STOP_MULT * atr
                    print(f"[卖出] 价格: {current_price}, 止损: {stop_loss:.2f}")
                    
            elif position == 1:
                if current_price < stop_loss:
                    print(f"[止损] 价格: {current_price}")
                    position = 0
                # 收盘前平仓
                elif klines.iloc[-1]['datetime'][11:16] == "14:45":
                    print(f"[收盘平仓] 价格: {current_price}")
                    position = 0
                    
            elif position == -1:
                if current_price > stop_loss:
                    print(f"[止损] 价格: {current_price}")
                    position = 0
                elif klines.iloc[-1]['datetime'][11:16] == "14:45":
                    print(f"[收盘平仓] 价格: {current_price}")
                    position = 0
    
    api.close()

if __name__ == "__main__":
    main()
