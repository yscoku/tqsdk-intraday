#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略03 - 隔夜缺口突破策略
原理：
    隔夜风险主要来自外盘收盘后到国内开盘前的价格波动。
    本策略捕捉隔夜缺口后的突破行情：
    
    1. 记录隔夜缺口（开盘价与昨日收盘价的差异）
    2. 缺口向上突破后回踩不补缺口，做多
    3. 缺口向下突破后回踩不补缺口，做空

参数：
    - 缺口比例：0.5%
    - 确认周期：3根K线

适用行情：隔夜缺口明显的品种
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth
import pandas as pd

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2405"       # 螺纹钢
KLINE_DURATION = 15 * 60     # 15分钟K线
GAP_RATIO = 0.005            # 缺口比例 0.5%
CONFIRM_BARS = 3             # 确认周期
LOT_SIZE = 1                 # 开仓手数

def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print(f"启动：隔夜缺口突破策略 | 合约: {SYMBOL}")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, data_length=100)
    
    # 记录昨日收盘价
    prev_close = None
    position = 0  # 1: 多头, -1: 空头, 0: 空仓
    
    while True:
        api.wait_update(klines)
        
        if len(klines) < 10:
            continue
        
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)
        
        # 每日开盘获取昨日收盘价
        current_bar = df.iloc[-1]
        current_open = current_bar['open']
        current_close = current_bar['close']
        
        # 获取上一根K线（昨日）
        if len(df) > 1:
            prev_bar = df.iloc[-2]
            prev_close = prev_bar['close']
        
        if prev_close is None:
            continue
        
        # 计算缺口
        gap = (current_open - prev_close) / prev_close
        
        # 尾盘平仓
        current_time = api.get_current_datetime()
        if current_time.hour >= 14 and current_time.minute >= 55:
            if position != 0:
                print(f"[{current_time}] 尾盘平仓")
                if position == 1:
                    api.insert_order(symbol=SYMBOL, direction="short", offset="close", volume=LOT_SIZE)
                else:
                    api.insert_order(symbol=SYMBOL, direction="long", offset="close", volume=LOT_SIZE)
                position = 0
            continue
        
        # 交易信号
        if position == 0:
            # 向上缺口：价格高开高走
            if gap > GAP_RATIO:
                # 等待回调确认
                if current_close < current_open * 1.002:
                    print(f"向上缺口突破 | 缺口: {gap:.2%} | 做多")
                    api.insert_order(symbol=SYMBOL, direction="long", offset="open", volume=LOT_SIZE)
                    position = 1
            
            # 向下缺口：价格低开低走
            elif gap < -GAP_RATIO:
                if current_close > current_open * 0.998:
                    print(f"向下缺口突破 | 缺口: {gap:.2%} | 做空")
                    api.insert_order(symbol=SYMBOL, direction="short", offset="open", volume=LOT_SIZE)
                    position = -1
        
        elif position == 1:
            # 缺口被回补，平仓
            if current_close < prev_close:
                print(f"缺口被回补 | 平多仓")
                api.insert_order(symbol=SYMBOL, direction="short", offset="close", volume=LOT_SIZE)
                position = 0
        
        elif position == -1:
            if current_close > prev_close:
                print(f"缺口被回补 | 平空仓")
                api.insert_order(symbol=SYMBOL, direction="long", offset="close", volume=LOT_SIZE)
                position = 0
    
    api.close()

if __name__ == "__main__":
    main()
