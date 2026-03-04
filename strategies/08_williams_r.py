#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略08 - 日内交易：威廉姆斯%R超买超卖策略
原理：
    威廉姆斯%R是超买超卖指标，数值在-100到0之间。
    当数值低于-80超卖买入，高于-20超买卖出。

参数：
    - 合约：SHFE.rb2505
    - 周期：5分钟
    - 威廉姆斯%R周期：14
    - 止损：0.4%

适用行情：区间震荡行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from tqsdk.ta import WR
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2505"          # 螺纹钢
KLINE_DURATION = 5 * 60         # 5分钟K线
WR_PERIOD = 14                  # 威廉姆斯%R周期
OVERBOUGHT = -20                # 超买阈值
OVERSOLD = -80                  # 超卖阈值
STOP_LOSS = 0.004               # 0.4%止损

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：威廉姆斯%R超买超卖策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=50)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            if len(klines) < WR_PERIOD:
                continue
                
            wr = WR(klines, WR_PERIOD).iloc[-1]
            current_price = klines['close'].iloc[-1]
            
            print(f"价格: {current_price}, %R: {wr:.2f}")
            
            if position == 0:
                # 超卖时做多
                if wr < OVERSOLD:
                    position = 1
                    entry_price = current_price
                    print(f"[买入超卖] 价格: {current_price}, %R: {wr:.2f}")
                # 超买时做空
                elif wr > OVERBOUGHT:
                    position = -1
                    entry_price = current_price
                    print(f"[卖出超买] 价格: {current_price}, %R: {wr:.2f}")
                    
            elif position == 1:
                # 回到超买区域或触及止损则平仓
                if wr > OVERBOUGHT * 0.5:
                    print(f"[平仓] 回到中性区域, 价格: {current_price}")
                    position = 0
                elif current_price < entry_price * (1 - STOP_LOSS):
                    print(f"[止损] 价格: {current_price}")
                    position = 0
                    
            elif position == -1:
                # 回到超卖区域或触及止损则平仓
                if wr < OVERSOLD * 0.5:
                    print(f"[平仓] 回到中性区域, 价格: {current_price}")
                    position = 0
                elif current_price > entry_price * (1 + STOP_LOSS):
                    print(f"[止损] 价格: {current_price}")
                    position = 0
    
    api.close()

if __name__ == "__main__":
    main()
