# tqsdk-intraday

> 基于 **TqSdk** 的高频日内策略，持续更新中。

## 项目简介

本仓库专注于**日内高频量化策略**，涵盖Tick级别、开盘突破、隔夜缺口等策略。  
所有策略使用 [天勤量化 TqSdk](https://github.com/shinnytech/tqsdk-python) 实现。

## 策略列表

| # | 策略名称 | 类型 | 品种 | 文件 |
|---|---------|------|------|------|
| 01 | 开盘区间突破策略 | 突破策略 | SHFE.rb | [01_orb_rb.py](strategies/01_orb_rb.py) |
| 02 | VWAP scalping策略 | 日内策略 | 期货 | [02_vwap_scalp.py](strategies/02_vwap_scalp.py) |
| 03 | 隔夜缺口突破策略 | 缺口策略 | 期货 | [03_gap_break.py](strategies/03_gap_break.py) |
| 04 | 盘口厚度突破策略 | 盘口策略 | 期货 | [04_orderbook_wall.py](strategies/04_orderbook_wall.py) |

## 更新日志

- 2026-03-03: 新增策略03（隔夜缺口）、策略04（盘口厚度）
