# tqsdk-intraday

> 基于 **TqSdk** 的日内交易策略集合，持续更新中。

## 项目简介

本仓库专注于**日内交易策略**，涵盖突破策略、均值回归、量价分析等方向。  
所有策略使用 [天勤量化 TqSdk](https://github.com/shinnytech/tqsdk-python) 实现，可直接对接实盘账户。

## 策略列表

| # | 策略名称 | 类型 | 品种 | 文件 |
|---|---------|------|------|------|
| 01 | 开盘区间突破策略 | 突破策略 | SHFE.rb | [01_orb_rb.py](strategies/01_orb_rb.py) |
| 02 | VWAP  scalp 策略 |  scalping | SHFE.rb | [02_vwap_scalp.py](strategies/02_vwap_scalp.py) |
| 03 | 跳空突破策略 | 突破策略 | SHFE.rb | [03_gap_break.py](strategies/03_gap_break.py) |
| 04 | 订单簿挂单策略 | 订单簿策略 | SHFE.rb | [04_orderbook_wall.py](strategies/04_orderbook_wall.py) |
| 05 | ATR 突破策略 | 突破策略 | SHFE.rb | [05_atr_breakout.py](strategies/05_atr_breakout.py) |
| 06 | MACD 背离策略 | 背离策略 | SHFE.rb | [06_macd_divergence.py](strategies/06_macd_divergence.py) |
| 07 | 开盘区间突破策略 | 突破策略 | SHFE.rb | [07_open_range_break.py](strategies/07_open_range_break.py) |
| 08 | Williams %R 超买超卖策略 | 超买超卖 | SHFE.rb | [08_williams_r.py](strategies/08_williams_r.py) |
| 09 | 区间突破策略 | 突破策略 | SHFE.rb | [09_range_breakout.py](strategies/09_range_breakout.py) |
| 10 | 订单流策略 | 订单流 | SHFE.rb | [10_order_flow.py](strategies/10_order_flow.py) |
| 11 | RSI 反转策略 | RSI策略 | SHFE.rb | [11_rsi_reversal.py](strategies/11_rsi_reversal.py) |
| 12 | 波动率突破策略 | 波动率策略 | SHFE.rb | [12_volatility_breakout.py](strategies/12_volatility_breakout.py) |
| 13 | 日内区间突破策略 | 突破策略 | SHFE.rb | [13_open_range_break.py](strategies/13_open_range_break.py) |
| 14 | VWAP 回归策略 | VWAP策略 | SHFE.rb | [14_vwap_reversion.py](strategies/14_vwap_reversion.py) |
| 15 | 布林带 scalping 策略 | scalping | SHFE.rb | [15_boll_scalp.py](strategies/15_boll_scalp.py) |
| 16 | 动量日内策略 | 动量策略 | SHFE.rb | [16_intraday_momentum.py](strategies/16_intraday_momentum.py) |
| 17 | 成交量突破策略 | 成交量策略 | SHFE.rb | [17_volume_breakout.py](strategies/17_volume_breakout.py) |
| 18 | 均线支撑阻力策略 | 均线策略 | SHFE.rb | [18_ma_support_resistance.py](strategies/18_ma_support_resistance.py) |
| 19 | 突破回踩策略 | 突破策略 | SHFE.rb | [19_breakout_retest.py](strategies/19_breakout_retest.py) |
| 20 | 收盘价突破策略 | 突破策略 | SHFE.rb | [20_close_breakout.py](strategies/20_close_breakout.py) |

## 策略分类

### 💥 突破策略（Breakout）
基于价格突破关键位置进行交易。

### 📊 VWAP 策略
基于成交量加权平均价格进行交易。

### 🔄  scalping 策略
高频小额盈利的日内交易策略。

### 📈 动量策略
基于价格动量进行交易。

## 环境要求

```bash
pip install tqsdk numpy pandas
```

## 风险提示

- 日内交易频率较高，需注意手续费成本
- 极端行情可能导致流动性风险
- 本仓库策略仅供学习研究，不构成投资建议

---

**持续更新中，欢迎 Star ⭐ 关注**

*更新时间：2026-03-11*
