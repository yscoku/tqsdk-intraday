#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略07 - 日内交易：开盘区间突破策略
原理：
    开盘30分钟内形成的价格区间具有较强的支撑阻力作用。
    突破该区间时顺势交易。

参数：
    - 合约：SHFE.rb2505
    - 周期：15分钟
    - 开盘区间：前30分钟
    - 止损：0.5%
    - 止盈：1%

适用行情：日内趋势行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2505"          # 螺纹钢
KLINE_DURATION = 15 * 60        # 15分钟K线
OPEN_RANGE_BARS = 2             # 开盘区间K线数（2*15=30分钟）
STOP_LOSS = 0.005               # 0.5%止损
TAKE_PROFIT = 0.01              # 1%止盈

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：开盘区间突破策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=50)
    
    position = 0
    entry_price = 0
    range_high = 0
    range_low = 0
    range_formed = False
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            current_price = klines['close'].iloc[-1]
            
            # 形成开盘区间
            if not range_formed and len(klines) >= OPEN_RANGE_BARS:
                range_high = klines['high'].iloc[-(OPEN_RANGE_BARS+1):-1].max()
                range_low = klines['low'].iloc[-(OPEN_RANGE_BARS+1):-1].min()
                range_formed = True
                print(f"[区间形成] 区间: {range_low:.2f} - {range_high:.2f}")
                
            if range_formed:
                print(f"价格: {current_price}, 区间: {range_low:.2f} - {range_high:.2f}")
                
                if position == 0:
                    # 突破区间上沿做多
                    if current_price > range_high:
                        position = 1
                        entry_price = current_price
                        print(f"[买入突破] 价格: {current_price}, 突破上沿")
                    # 突破区间下沿做空
                    elif current_price < range_low:
                        position = -1
                        entry_price = current_price
                        print(f"[卖出突破] 价格: {current_price}, 突破下沿")
                        
                elif position == 1:
                    pnl_pct = (current_price - entry_price) / entry_price
                    
                    if pnl_pct < -STOP_LOSS:
                        print(f"[止损] 价格: {current_price}")
                        position = 0
                    elif pnl_pct > TAKE_PROFIT:
                        print(f"[止盈] 价格: {current_price}")
                        position = 0
                        
                elif position == -1:
                    pnl_pct = (entry_price - current_price) / entry_price
                    
                    if pnl_pct < -STOP_LOSS:
                        print(f"[止损] 价格: {current_price}")
                        position = 0
                    elif pnl_pct > TAKE_PROFIT:
                        print(f"[止盈] 价格: {current_price}")
                        position = 0
    
    api.close()

if __name__ == "__main__":
    main()
