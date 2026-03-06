#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略14 - VWAP策略：成交量加权价格回归策略
原理：
    日内交易使用成交量加权平均价格（VWAP）作为价值参考。
    价格偏离VWAP过多时预期回归，偏离少时顺势交易。

参数：
    - 合约：SHFE.hc2505
    - K线周期：5分钟
    - VWAP周期：50根K线
    - 止损：0.8% 
    - 止盈：1.6%

适用行情：日内震荡行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from tqsdk.ta import MA
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.hc2505"          # 热卷
KLINE_DURATION = 5 * 60         # 5分钟K线
VWAP_PERIOD = 50                # VWAP计算周期
STOP_LOSS = 0.008              # 0.8%止损
TAKE_PROFIT = 0.016             # 1.6%止盈
DEVIATION_THRESHOLD = 0.005     # 偏离阈值0.5%

# ============ 主策略 ============
def calculate_vwap(klines, period):
    """计算成交量加权平均价格"""
    typical_price = (klines['high'] + klines['low'] + klines['close']) / 3
    vwap = (typical_price * klines['volume']).rolling(window=period).sum() / klines['volume'].rolling(window=period).sum()
    return vwap

def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：成交量加权价格回归策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=VWAP_PERIOD + 10)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            if len(klines) < VWAP_PERIOD:
                continue
                
            current_price = klines['close'].iloc[-1]
            vwap = calculate_vwap(klines, VWAP_PERIOD).iloc[-1]
            vwap_prev = calculate_vwap(klines, VWAP_PERIOD).iloc[-2]
            
            # 计算偏离度
            deviation = (current_price - vwap) / vwap
            
            current_time = klines['datetime'].iloc[-1]
            
            # 每天14:55后不再开仓
            hour = int(current_time[11:13])
            minute = int(current_time[14:16])
            is_near_close = (hour == 14 and minute >= 55) or hour >= 15
            
            print(f"价格: {current_price}, VWAP: {vwap:.2f}, 偏离度: {deviation*100:.2f}%")
            
            if position == 0 and not is_near_close:
                # 做多信号：价格低于VWAP且偏离较大，或者价格上穿VWAP
                if deviation < -DEVIATION_THRESHOLD:
                    position = 1
                    entry_price = current_price
                    print(f"[买入] 价格偏离VWAP过多: {current_price}")
                elif deviation < 0 and deviation > -DEVIATION_THRESHOLD and vwap > vwap_prev:
                    position = 1
                    entry_price = current_price
                    print(f"[买入] 价格站上VWAP: {current_price}")
                    
            elif position == 1:
                pnl_pct = (current_price - entry_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 价格回归VWAP或接近收盘
                elif is_near_close or (deviation > 0 and deviation < DEVIATION_THRESHOLD):
                    print(f"[平仓] 价格回归VWAP或收盘")
                    position = 0
            
            # 临近收盘强制平仓
            if is_near_close and position != 0:
                print(f"[收盘平仓] 价格: {current_price}")
                position = 0
    
    api.close()

if __name__ == "__main__":
    main()
