#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略20 - 焦煤日内区间突破策略
原理：
    焦煤期货(JM)使用日内区间突破进行交易。
    记录开盘后30分钟的价格区间，突破区间上沿做多，下沿做空。
    日内交易，尾盘平仓。

参数：
    - 合约：大商所JM2505
    - K线周期：5分钟
    - 区间形成周期：30分钟（6根5分钟K线）
    - 止损：1.5%
    - 止盈：3%
    - 平仓时间：14:45

适用行情：区间震荡后的突破行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from datetime import datetime
import numpy as np

# ============ 参数配置 ============
SYMBOL = "DCE.JM2505"            # 焦煤期货
KLINE_DURATION = 60 * 5         # 5分钟K线
RANGE_PERIOD = 6                 # 形成区间的K线数量（30分钟）
STOP_LOSS = 0.015               # 1.5%止损
TAKE_PROFIT = 0.03              # 3%止盈
CLOSE_TIME = 14                  # 收盘时间（小时）

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：焦煤日内区间突破策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=RANGE_PERIOD + 50)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    range_high = 0
    range_low = 0
    range_formed = False
    
    while True:
        api.wait_update()
        
        # 检查是否到尾盘平仓时间
        current_hour = datetime.now().hour
        if current_hour >= CLOSE_TIME and position != 0:
            print(f"[尾盘平仓] 时间: {current_hour}:00")
            position = 0
            range_formed = False
            continue
            
        if api.is_changing(klines):
            close_prices = klines['close']
            high_prices = klines['high']
            low_prices = klines['low']
            current_price = close_prices.iloc[-1]
            
            # 区间形成阶段
            if not range_formed and len(klines) >= RANGE_PERIOD:
                # 使用前30分钟的数据形成区间
                range_high = high_prices.iloc[-RANGE_PERIOD:-1].max()
                range_low = low_prices.iloc[-RANGE_PERIOD:-1].min()
                range_formed = True
                print(f"[区间形成] 区间: {range_low:.2f} - {range_high:.2f}")
                
            if not range_formed:
                continue
                
            print(f"价格: {current_price}, 区间: {range_low:.2f} - {range_high:.2f}")
            
            if position == 0:
                # 突破区间上沿做多
                if current_price > range_high:
                    position = 1
                    entry_price = current_price
                    print(f"[买入] 突破区间上沿: {current_price}")
                # 突破区间下沿做空
                elif current_price < range_low:
                    position = -1
                    entry_price = current_price
                    print(f"[卖出] 突破区间下沿: {current_price}")
                    
            elif position == 1:
                pnl_pct = (current_price - entry_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                    range_formed = False  # 重新形成区间
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                    range_formed = False
                # 回到区间内平仓
                elif current_price < range_high and current_price > range_low:
                    print(f"[平仓] 回到区间内")
                    position = 0
                    range_formed = False
                    
            elif position == -1:
                pnl_pct = (entry_price - current_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                    range_formed = False
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                    range_formed = False
                # 回到区间内平仓
                elif current_price < range_high and current_price > range_low:
                    print(f"[平仓] 回到区间内")
                    position = 0
                    range_formed = False
    
    api.close()


if __name__ == "__main__":
    main()
