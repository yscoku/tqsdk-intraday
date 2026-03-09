#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略15 - 支撑阻力策略：螺纹钢日内支撑阻力策略
原理：
    日内交易使用关键支撑阻力位判断价格走势。
    价格突破阻力位时做多，跌破支撑位时做空。

参数：
    - 合约：上期所RB2505
    - K线周期：15分钟
    - 周期数：20根K线
    - 止损：0.6% 
    - 止盈：1.2%

适用行情：日内趋势行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2505"          # 螺纹钢
KLINE_DURATION = 15 * 60         # 15分钟K线
LOOKBACK_PERIOD = 20            # 周期数
STOP_LOSS = 0.006              # 0.6%止损
TAKE_PROFIT = 0.012             # 1.2%止盈

# ============ 主策略 ============
def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print("启动：螺纹钢日内支撑阻力策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=LOOKBACK_PERIOD + 10)
    quote = api.get_quote(SYMBOL)
    
    position = 0
    entry_price = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines):
            if len(klines) < LOOKBACK_PERIOD:
                continue
                
            current_price = klines['close'].iloc[-1]
            
            # 计算支撑阻力位
            recent_high = klines['high'].iloc[-LOOKBACK_PERIOD:].max()
            recent_low = klines['low'].iloc[-LOOKBACK_PERIOD:].min()
            
            # 阻力位和支撑位
            resistance = recent_high
            support = recent_low
            
            # 额外支撑阻力：中间价位
            mid_price = (resistance + support) / 2
            
            current_time = klines['datetime'].iloc[-1]
            
            # 每天14:55后不再开仓
            hour = int(current_time[11:13])
            minute = int(current_time[14:16])
            is_near_close = (hour == 14 and minute >= 55) or hour >= 15
            
            print(f"价格: {current_price}, 阻力位: {resistance:.2f}, 支撑位: {support:.2f}")
            
            if position == 0 and not is_near_close:
                # 做多信号：突破阻力位
                if current_price > resistance:
                    position = 1
                    entry_price = current_price
                    print(f"[买入] 突破阻力位: {current_price}")
                # 做空信号：跌破支撑位
                elif current_price < support:
                    position = -1
                    entry_price = current_price
                    print(f"[卖出] 跌破支撑位: {current_price}")
                    
            elif position == 1:
                pnl_pct = (current_price - entry_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 跌破支撑位或接近收盘
                elif current_price < support or is_near_close:
                    print(f"[平仓] 跌破支撑位或收盘")
                    position = 0
                    
            elif position == -1:
                pnl_pct = (entry_price - current_price) / entry_price
                
                if pnl_pct < -STOP_LOSS:
                    print(f"[止损] 价格: {current_price}, 亏损: {pnl_pct*100:.2f}%")
                    position = 0
                elif pnl_pct > TAKE_PROFIT:
                    print(f"[止盈] 价格: {current_price}, 盈利: {pnl_pct*100:.2f}%")
                    position = 0
                # 突破阻力位或接近收盘
                elif current_price > resistance or is_near_close:
                    print(f"[平仓] 突破阻力位或收盘")
                    position = 0
            
            # 临近收盘强制平仓
            if is_near_close and position != 0:
                print(f"[收盘平仓] 价格: {current_price}")
                position = 0
    
    api.close()

if __name__ == "__main__":
    main()
