#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略17 - 日内动量策略：铁矿石日内动量策略
原理：
    铁矿石（I）使用日内动量判断趋势方向。
    动量持续向上做多，向下做空，尾盘平仓。

参数：
    - 合约：大商所i2505
    - K线周期：10分钟
    - 动量周期：6
    - 止损：0.6% 
    - 止盈：1.2%

适用行情：日内趋势行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
import numpy as np

# ============ 参数配置 ============
SYMBOL = "DCE.i2505"            # 铁矿石
KLINE_DURATION = 10 * 60        # 10分钟K线
MOMENTUM_PERIOD = 6             # 动量周期
STOP_LOSS = 0.006               # 0.6%止损
TAKE_PROFIT = 0.012             # 1.2%止盈

# ============ 主策略 ============
def calculate_momentum(klines, period):
    """计算动量"""
    close = klines['close']
    momentum = close.iloc[-1] - close.iloc[-period]
    return momentum

def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：铁矿石日内动量策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=MOMENTUM_PERIOD + 10)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            if len(klines) < MOMENTUM_PERIOD:
                continue
            
            current_price = klines['close'].iloc[-1]
            current_time = klines['datetime'].iloc[-1]
            
            # 解析时间
            hour = int(current_time[11:13])
            minute = int(current_time[14:16])
            
            # 14:55后不再开仓
            is_near_close = (hour == 14 and minute >= 55) or hour >= 15
            
            # 计算动量
            momentum = calculate_momentum(klines, MOMENTUM_PERIOD)
            
            print(f"时间: {current_time}, 价格: {current_price}, 动量: {momentum:.2f}")
            
            # 尾盘强制平仓
            if hour == 14 and minute >= 55:
                if position != 0:
                    print(f"[尾盘平仓] 时间: {current_time}")
                    position = 0
                continue
            
            if position == 0 and not is_near_close:
                # 做多信号：动量向上
                if momentum > 0:
                    position = 1
                    entry_price = current_price
                    print(f"[买入] 动量向上: {current_price}")
                # 做空信号：动量向下
                elif momentum < 0:
                    position = -1
                    entry_price = current_price
                    print(f"[卖出] 动量向下: {current_price}")
                    
            elif position == 1:
                pnl_pct = (current_price - entry_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 动量转负平仓
                elif momentum < 0:
                    print(f"[平仓] 动量转负: {current_price}")
                    position = 0
                    
            elif position == -1:
                pnl_pct = (entry_price - current_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 动量转正平仓
                elif momentum > 0:
                    print(f"[平仓] 动量转正: {current_price}")
                    position = 0

if __name__ == "__main__":
    main()
