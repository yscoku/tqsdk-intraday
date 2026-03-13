#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略19 - 焦炭日内布林带趋势策略
原理：
    焦炭期货(J)使用布林带结合日内趋势进行交易。
    价格突破布林带上轨且短期趋势向上时做多，下轨且趋势向下时做空。
    日内交易，尾盘平仓。

参数：
    - 合约：大商所J2505
    - K线周期：15分钟
    - 布林带周期：20，标准差：2
    - 止损：2%
    - 止盈：4%
    - 平仓时间：14:45

适用行情：日内趋势明显的行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from tqsdk.ta import BOLL
from datetime import datetime
import numpy as np

# ============ 参数配置 ============
SYMBOL = "DCE.J2505"            # 焦炭期货
KLINE_DURATION = 60 * 15        # 15分钟K线
BOLL_PERIOD = 20                # 布林带周期
BOLL_STD = 2                   # 标准差倍数
STOP_LOSS = 0.02               # 2%止损
TAKE_PROFIT = 0.04             # 4%止盈
CLOSE_TIME = 14                 # 收盘时间（小时）

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：焦炭日内布林带趋势策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=BOLL_PERIOD + 30)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        # 检查是否到尾盘平仓时间
        current_hour = datetime.now().hour
        if current_hour >= CLOSE_TIME and position != 0:
            print(f"[尾盘平仓] 时间: {current_hour}:00")
            position = 0
            continue
            
        if api.is_changing(klines):
            if len(klines) < BOLL_PERIOD + 20:
                continue
                
            close_prices = klines['close']
            current_price = close_prices.iloc[-1]
            
            # 计算布林带
            boll = BOLL(close_prices, period=BOLL_PERIOD, dev=BOLL_STD)
            upper = boll['up'].iloc[-1]
            lower = boll['down'].iloc[-1]
            
            # 计算短期趋势（5周期均线）
            ma5 = close_prices.rolling(5).mean().iloc[-1]
            ma5_prev = close_prices.rolling(5).mean().iloc[-2]
            
            print(f"价格: {current_price}, 上轨: {upper:.2f}, 下轨: {lower:.2f}")
            
            if position == 0:
                # 做多信号：价格突破上轨且均线上升
                if current_price > upper and ma5 > ma5_prev:
                    position = 1
                    entry_price = current_price
                    print(f"[买入] 价格突破上轨: {current_price}")
                # 做空信号：价格突破下轨且均线下行
                elif current_price < lower and ma5 < ma5_prev:
                    position = -1
                    entry_price = current_price
                    print(f"[卖出] 价格突破下轨: {current_price}")
                    
            elif position == 1:
                pnl_pct = (current_price - entry_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 趋势反转平仓
                elif ma5 < ma5_prev:
                    print(f"[平仓] 趋势反转")
                    position = 0
                    
            elif position == -1:
                pnl_pct = (entry_price - current_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 趋势反转平仓
                elif ma5 > ma5_prev:
                    print(f"[平仓] 趋势反转")
                    position = 0
    
    api.close()


if __name__ == "__main__":
    main()
