#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略12 - 日内波动率突破策略
原理：
    开盘后等待价格突破日内波动区间，确认趋势后入场

参数：
    - 合约：SHFE.rb2505
    - 周期：15分钟
    - 区间形成周期：4根K线（约1小时）
    - 突破系数：0.8

适用行情：趋势行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth, TqSim, TargetPosTask
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2505"           # 螺纹钢
KLINE_DURATION = 15 * 60         # 15分钟K线
FORMATION_BARS = 4               # 区间形成K线数
BREAKOUT_FACTOR = 0.8            # 突破系数
VOLUME = 1                       # 每次交易手数
DATA_LENGTH = 50                 # 历史K线数量


def main():
    api = TqApi(account=TqSim(), auth=TqAuth("账号", "密码"))
    print("启动：日内波动率突破策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, DATA_LENGTH)
    target_pos = TargetPosTask(api, SYMBOL)
    
    # 初始化区间
    range_high = None
    range_low = None
    breakout_confirmed = False
    position = 0
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines.iloc[-1], "datetime"):
            high = klines["high"]
            low = klines["low"]
            close = klines["close"]
            
            # 形成区间
            if not breakout_confirmed and len(klines) >= FORMATION_BARS:
                range_high = high.iloc[-FORMATION_BARS:].max()
                range_low = low.iloc[-FORMATION_BARS:].min()
                range_mid = (range_high + range_low) / 2
                range_size = range_high - range_low
                
                price = close.iloc[-1]
                
                print(f"区间: {range_low:.2f}~{range_high:.2f}, 价格: {price:.2f}")
                
                # 突破上轨
                if price > range_high + range_size * BREAKOUT_FACTOR and position == 0:
                    print(f"[开仓] 突破上轨，做多")
                    target_pos.set_target_volume(VOLUME)
                    position = 1
                    breakout_confirmed = True
                # 突破下轨
                elif price < range_low - range_size * BREAKOUT_FACTOR and position == 0:
                    print(f"[开仓] 突破下轨，做空")
                    target_pos.set_target_volume(-VOLUME)
                    position = -1
                    breakout_confirmed = True
                    
            elif position == 1 and close.iloc[-1] < range_low:
                print(f"[平仓] 回到区间下方")
                target_pos.set_target_volume(0)
                position = 0
                breakout_confirmed = False
            elif position == -1 and close.iloc[-1] > range_high:
                print(f"[平仓] 回到区间上方")
                target_pos.set_target_volume(0)
                position = 0
                breakout_confirmed = False
    
    api.close()


if __name__ == "__main__":
    main()
