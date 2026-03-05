#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略11 - 日内RSI超卖反转策略
原理：
    RSI指标在日内交易中寻找超卖/超买反转信号

参数：
    - 合约：SHFE.rb2505
    - 周期：5分钟
    - RSI周期：14
    - 超卖阈值：30
    - 超买阈值：70

适用行情：震荡行情
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth, TqSim, TargetPosTask
import numpy as np

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2505"           # 螺纹钢
KLINE_DURATION = 5 * 60          # 5分钟K线
RSI_PERIOD = 14                  # RSI周期
RSI_OVERSOLD = 30                # 超卖阈值
RSI_OVERBOUGHT = 70              # 超买阈值
VOLUME = 1                       # 每次交易手数
DATA_LENGTH = 100                # 历史K线数量


def calc_rsi(close, period):
    """计算RSI"""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def main():
    api = TqApi(account=TqSim(), auth=TqAuth("账号", "密码"))
    print("启动：日内RSI超卖反转策略")
    
    klines = api.get_kline_serial(SYMBOL, KLINE_DURATION, DATA_LENGTH)
    target_pos = TargetPosTask(api, SYMBOL)
    
    position = 0  # 0: 空仓, 1: 多, -1: 空
    
    while True:
        api.wait_update()
        
        if api.is_changing(klines.iloc[-1], "datetime"):
            close = klines["close"]
            rsi = calc_rsi(close, RSI_PERIOD)
            
            price = close.iloc[-1]
            rsi_val = rsi.iloc[-1]
            
            print(f"价格: {price:.2f}, RSI: {rsi_val:.1f}")
            
            if position == 0:
                # RSI超卖且开始回升
                if rsi_val < RSI_OVERSOLD:
                    print(f"[开仓] RSI超卖={rsi_val:.1f}，做多")
                    target_pos.set_target_volume(VOLUME)
                    position = 1
                # RSI超买且开始回落
                elif rsi_val > RSI_OVERBOUGHT:
                    print(f"[开仓] RSI超买={rsi_val:.1f}，做空")
                    target_pos.set_target_volume(-VOLUME)
                    position = -1
                    
            elif position == 1 and rsi_val > RSI_OVERBOUGHT:
                print(f"[平仓] RSI进入超买区域")
                target_pos.set_target_volume(0)
                position = 0
            elif position == -1 and rsi_val < RSI_OVERSOLD:
                print(f"[平仓] RSI进入超卖区域")
                target_pos.set_target_volume(0)
                position = 0
    
    api.close()


if __name__ == "__main__":
    main()
