#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略04 - 盘口厚度突破策略
原理：
    盘口厚度反映市场深度，大单集中处形成"厚墙"。
    当价格突破厚墙时，往往伴随快速行情：
    
    1. 统计盘口各价位的挂单量
    2. 找出挂单密集区（厚墙）
    3. 价格突破厚墙后顺势交易

参数：
    - 统计深度：10档
    - 厚墙阈值：平均量的2倍

适用行情：流动性好的主力合约
作者：yscoku / tqsdk-intraday
"""

from tqsdk import TqApi, TqAuth

# ============ 参数配置 ============
SYMBOL = "SHFE.rb2405"       # 螺纹钢
DEPTH = 10                   # 盘口深度
WALL_RATIO = 2.0             # 厚墙阈值
LOT_SIZE = 1                 # 开仓手数

def main():
    api = TqApi(auth=TqAuth("账号", "密码"))
    
    print(f"启动：盘口厚度突破策略 | 合约: {SYMBOL}")
    
    quote = api.get_quote(SYMBOL)
    
    position = 0  # 1: 多头, -1: 空头, 0: 空仓
    
    while True:
        api.wait_update(quote)
        
        # 获取盘口数据
        bids = quote.bids  # 买盘 [price, volume]
        asks = quote.asks # 卖盘 [price, volume]
        
        if not bids or not asks or len(bids) < DEPTH or len(asks) < DEPTH:
            continue
        
        # 统计挂单量
        bid_volumes = [b[1] for b in bids[:DEPTH]]
        ask_volumes = [a[1] for a in asks[:DEPTH]]
        
        avg_bid = sum(bid_volumes) / len(bid_volumes)
        avg_ask = sum(ask_volumes) / len(ask_volumes)
        
        # 找出厚墙
        bid_walls = [i for i, v in enumerate(bid_volumes) if v > avg_bid * WALL_RATIO]
        ask_walls = [i for i, v in enumerate(ask_volumes) if v > avg_ask * WALL_RATIO]
        
        # 当前价格
        last_price = quote.last_price
        
        # 交易信号
        if position == 0:
            # 向上突破卖盘厚墙
            if ask_walls and min(ask_walls) <= 2:
                wall_price = asks[min(ask_walls)][0]
                if last_price > wall_price:
                    print(f"突破卖盘厚墙 | 价格: {last_price} > 厚墙: {wall_price} | 做多")
                    api.insert_order(symbol=SYMBOL, direction="long", offset="open", volume=LOT_SIZE)
                    position = 1
            
            # 向下突破买盘厚墙
            elif bid_walls and min(bid_walls) <= 2:
                wall_price = bids[min(bid_walls)][0]
                if last_price < wall_price:
                    print(f"突破买盘厚墙 | 价格: {last_price} < 厚墙: {wall_price} | 做空")
                    api.insert_order(symbol=SYMBOL, direction="short", offset="open", volume=LOT_SIZE)
                    position = -1
        
        elif position == 1:
            # 价格回落平仓
            if bid_walls:
                wall_price = bids[min(bid_walls)][0]
                if last_price < wall_price:
                    print(f"回落平多仓")
                    api.insert_order(symbol=SYMBOL, direction="short", offset="close", volume=LOT_SIZE)
                    position = 0
        
        elif position == -1:
            if ask_walls:
                wall_price = asks[min(ask_walls)][0]
                if last_price > wall_price:
                    print(f"反弹平空仓")
                    api.insert_order(symbol=SYMBOL, direction="long", offset="close", volume=LOT_SIZE)
                    position = 0
    
    api.close()

if __name__ == "__main__":
    main()
