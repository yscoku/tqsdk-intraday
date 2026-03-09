#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略16 - 波动率策略：热卷期货日内波动率突破策略
原理：
    日内交易使用ATR（平均真实波幅）来衡量市场波动程度。
    当ATR向上突破其移动平均线时，认为波动加大，顺势开仓。

参数：
    - 合约：上期所HC2505
    - K线周期：5分钟
    - ATR周期：20
    - ATR MA周期：10
    - 止损：0.7% 
    - 止盈：1.4%

适用行情：日内波动加剧行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
from tqsdk.ta import ATR, MA
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.hc2505"          # 热卷
KLINE_DURATION = 5 * 60        # 5分钟K线
ATR_PERIOD = 20                 # ATR周期
ATR_MA_PERIOD = 10              # ATR移动平均周期
STOP_LOSS = 0.007              # 0.7%止损
TAKE_PROFIT = 0.014             # 1.4%止盈

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：热卷期货日内波动率突破策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=ATR_PERIOD + ATR_MA_PERIOD + 10)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            if len(klines) < ATR_PERIOD + ATR_MA_PERIOD:
                continue
                
            current_price = klines['close'].iloc[-1]
            
            # 计算ATR
            atr = ATR(klines, ATR_PERIOD).iloc[-1]
            atr_ma = MA(ATR(klines, ATR_PERIOD), ATR_MA_PERIOD).iloc[-1]
            atr_prev = ATR(klines, ATR_PERIOD).iloc[-2]
            atr_ma_prev = MA(ATR(klines, ATR_PERIOD), ATR_MA_PERIOD).iloc[-2]
            
            current_time = klines['datetime'].iloc[-1]
            
            # 每天14:55后不再开仓
            hour = int(current_time[11:13])
            minute = int(current_time[14:16])
            is_near_close = (hour == 14 and minute >= 55) or hour >= 15
            
            print(f"价格: {current_price}, ATR: {atr:.2f}, ATR均线: {atr_ma:.2f}")
            
            if position == 0 and not is_near_close:
                # 做多信号：ATR向上突破均线，且价格站上20周期高点
                if atr_prev <= atr_ma_prev and atr > atr_ma:
                    recent_high = klines['high'].iloc[-20:].max()
                    if current_price > recent_high * 0.998:  # 接近20周期高点
                        position = 1
                        entry_price = current_price
                        print(f"[买入] ATR突破+价格强势: {current_price}")
                        
                # 做空信号：ATR向上突破均线，且价格跌破20周期低点
                elif atr_prev <= atr_ma_prev and atr > atr_ma:
                    recent_low = klines['low'].iloc[-20:].min()
                    if current_price < recent_low * 1.002:  # 接近20周期低点
                        position = -1
                        entry_price = current_price
                        print(f"[卖出] ATR突破+价格弱势: {current_price}")
                    
            elif position == 1:
                pnl_pct = (current_price - entry_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # ATR回落或接近收盘
                elif atr < atr_ma or is_near_close:
                    print(f"[平仓] ATR回落或收盘")
                    position = 0
                    
            elif position == -1:
                pnl_pct = (entry_price - current_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # ATR回落或接近收盘
                elif atr < atr_ma or is_near_close:
                    print(f"[平仓] ATR回落或收盘")
                    position = 0
            
            # 临近收盘强制平仓
            if is_near_close and position != 0:
                print(f"[收盘平仓] 价格: {current_price}")
                position = 0
    
    api.close()

if __name__ == "__main__":
    main()
