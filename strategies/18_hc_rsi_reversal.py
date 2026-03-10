#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略18 - 日内RSI反转策略：热卷期货日内RSI超买超卖策略
原理：
    热卷期货（HC）使用RSI指标进行日内超买超卖反转交易。
    RSI低于25时做多，高于75时做空，盘中来回操作。

参数：
    - 合约：上期所HC2505
    - K线周期：5分钟
    - RSI周期：14
    - 超买阈值：75
    - 超卖阈值：25
    - 止损：1% 
    - 止盈：2%
    - 收盘前平仓：是

适用行情：日内震荡行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from tqsdk.ta import RSI
from datetime import datetime
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.HC2505"          # 热卷期货
KLINE_DURATION = 5 * 60         # 5分钟K线
RSI_PERIOD = 14                 # RSI周期
RSI_OVERBOUGHT = 75             # 超买阈值
RSI_OVERSOLD = 25               # 超卖阈值
STOP_LOSS = 0.01                # 1%止损
TAKE_PROFIT = 0.02              # 2%止盈
CLOSE_TIME = 14                  # 收盘时间（小时）

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：热卷期货日内RSI反转策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=RSI_PERIOD + 20)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        # 获取当前时间
        current_time = datetime.now()
        
        # 收盘前平仓
        if current_time.hour >= CLOSE_TIME and position != 0:
            print(f"[收盘平仓] 时间: {current_time}")
            position = 0
            continue
        
        if api.is_changing(klines):
            if len(klines) < RSI_PERIOD + 10:
                continue
                
            current_price = klines['close'].iloc[-1]
            
            # 计算RSI
            rsi = RSI(klines['close'], period=RSI_PERIOD).iloc[-1]
            rsi_prev = RSI(klines['close'], period=RSI_PERIOD).iloc[-2]
            
            print(f"价格: {current_price}, RSI: {rsi:.2f}")
            
            if position == 0:
                # 做多信号：RSI从超卖区域回升
                if rsi_prev < RSI_OVERSOLD and rsi > RSI_OVERSOLD:
                    position = 1
                    entry_price = current_price
                    print(f"[买入] RSI从超卖回升: {current_price}, RSI: {rsi:.2f}")
                # 做空信号：RSI从超买区域回落
                elif rsi_prev > RSI_OVERBOUGHT and rsi < RSI_OVERBOUGHT:
                    position = -1
                    entry_price = current_price
                    print(f"[卖出] RSI从超买回落: {current_price}, RSI: {rsi:.2f}")
                    
            elif position == 1:
                pnl_pct = (current_price - entry_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # RSI进入超买区域平仓
                elif rsi > RSI_OVERBOUGHT:
                    print(f"[平仓] RSI进入超买区域")
                    position = 0
                    
            elif position == -1:
                pnl_pct = (entry_price - current_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # RSI进入超卖区域平仓
                elif rsi < RSI_OVERSOLD:
                    print(f"[平仓] RSI进入超卖区域")
                    position = 0
    
    api.close()

if __name__ == "__main__":
    main()
