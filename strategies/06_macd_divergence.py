#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略06 - 日内交易：MACD背离策略
原理：
    当价格创新高/新低，但MACD没有同步时，出现背离。
    背离往往预示着趋势反转。

参数：
    - 合约：SHFE.rb2505
    - 周期：5分钟
    - MACD参数：12, 26, 9
    - 止损：0.5%

适用行情：趋势尾声出现背离时
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from tqsdk.ta import MACD
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2505"          # 螺纹钢
KLINE_DURATION = 5 * 60         # 5分钟K线
FAST = 12                       # 快线
SLOW = 26                       # 慢线
SIGNAL = 9                     # 信号线
STOP_LOSS = 0.005               # 0.5%止损

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：MACD背离策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=100)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            if len(klines) < 50:
                continue
                
            macd = MACD(klines, FAST, SLOW, SIGNAL)
            dif = macd['dif'].iloc[-1]
            dea = macd['dea'].iloc[-1]
            
            # 价格创新高
            recent_high = klines['high'].iloc[-10:].max()
            current_price = klines['close'].iloc[-1]
            
            # 检查底背离：价格创新低，MACD没有
            recent_low = klines['low'].iloc[-10:].min()
            macd_low = macd['macd'].iloc[-10:].min()
            
            print(f"价格: {current_price}, DIF: {dif:.4f}, DEA: {dea:.4f}")
            
            if position == 0:
                # 底背离做多
                if current_price < recent_low and macd['macd'].iloc[-1] > macd_low * 0.8:
                    position = 1
                    entry_price = current_price
                    print(f"[买入底背离] 价格: {current_price}")
                    
                # 顶背离做空
                elif current_price > recent_high and macd['macd'].iloc[-1] < macd_high * 0.8:
                    macd_high = macd['macd'].iloc[-10:].max()
                    position = -1
                    entry_price = current_price
                    print(f"[卖出顶背离] 价格: {current_price}")
                    
            elif position == 1:
                if current_price < entry_price * (1 - STOP_LOSS):
                    print(f"[止损] 价格: {current_price}")
                    position = 0
                    
            elif position == -1:
                if current_price > entry_price * (1 + STOP_LOSS):
                    print(f"[止损] 价格: {current_price}")
                    position = 0
    
    api.close()

if __name__ == "__main__":
    main()
