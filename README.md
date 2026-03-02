# tqsdk-intraday 日内高频策略库

> 基于 [TqSdk（天勤量化）](https://doc.shinnytech.com/tqsdk/latest/) 的高频日内期货策略集合。  
> 所有策略**当日必须平仓，不持隔夜头寸**。

---

## 📋 策略列表

| 编号 | 文件名 | 策略名称 | 品种 | 核心思路 | 强平时间 | 上线日期 |
|------|--------|----------|------|----------|----------|----------|
| 01 | [01_orb_rb.py](strategies/01_orb_rb.py) | 开盘区间突破（ORB） | 螺纹钢 rb | 开盘后15分钟高低点作为突破区间，向上突破开多，向下突破开空 | 14:50 | 2026-03-02 |
| 02 | [02_vwap_scalp.py](strategies/02_vwap_scalp.py) | 日内VWAP偏离抢单 | 螺纹钢 rb | 基于1分钟VWAP偏离度的超短线均值回归，最大持仓30分钟 | 14:50 | 2026-03-02 |

---

## 🏗️ 仓库结构

```
tqsdk-intraday/
├── README.md                  # 本文档
└── strategies/                # 策略文件目录
    ├── 01_orb_rb.py           # 开盘区间突破策略（ORB）
    └── 02_vwap_scalp.py       # 日内VWAP偏离抢单策略
```

---

## 🚀 策略详情

### 01 · 开盘区间突破（ORB）

**适用品种**：螺纹钢主力合约（SHFE.rb2510）  
**时间框架**：1分钟 K 线 / Tick 级触发  

**策略逻辑**：
- 记录开盘后前 **15 分钟**（09:00~09:14）内的最高价和最低价，构成「开盘区间」
- 09:15 之后，价格**突破区间高点** → 开多；**跌破区间低点** → 开空
- 止损设在区间对侧，止盈为区间宽度的 1.5 倍
- **14:50 强制平仓**，不持隔夜

**关键参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ORB_MINUTES` | 15 | 开盘区间采样分钟数 |
| `PROFIT_RATIO` | 1.5 | 止盈倍数（相对区间宽度） |
| `LOT_SIZE` | 1 | 单次开仓手数 |

---

### 02 · 日内VWAP偏离抢单（VWAP Scalping）

**适用品种**：螺纹钢主力合约（SHFE.rb2510，可替换）  
**时间框架**：1分钟 VWAP / Tick 级触发  

**策略逻辑**：
- 实时计算当日累积 VWAP（成交量加权均价）
- 价格低于 VWAP **15 bps** 以上 → 超卖，开多；高于 **15 bps** → 超买，开空
- 持仓后等价格回归 VWAP 附近（偏离 < 5 bps）止盈平仓
- **最大持仓 30 分钟**，超时强制时间止损平仓
- **14:50 强制平仓**，不持隔夜

**关键参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ENTRY_DEVIATION_BPS` | 15 | 入场偏离阈值（bps） |
| `EXIT_DEVIATION_BPS` | 5 | 止盈偏离阈值（bps） |
| `STOP_MULTIPLIER` | 2.0 | 止损倍数（止损=入场阈值×2.0） |
| `MAX_HOLD_MINUTES` | 30 | 最大持仓时间（分钟） |
| `MAX_TRADES_PER_DAY` | 3 | 每日同方向最大开仓次数 |

---

## ⚙️ 使用方法

### 安装依赖

```bash
pip install tqsdk
```

### 运行策略（模拟账户）

```python
# 直接运行策略文件
python strategies/01_orb_rb.py
python strategies/02_vwap_scalp.py
```

### 切换实盘账户

将策略文件中的 `TqSim()` 替换为真实账户：

```python
from tqsdk import TqAccount
api = TqApi(
    account=TqAccount("期货公司名称", "账号", "密码"),
    auth=TqAuth("天勤用户名", "天勤密码")
)
```

### 回测模式

```python
from tqsdk import TqBacktest
import datetime
api = TqApi(
    account=TqSim(),
    auth=TqAuth("天勤用户名", "天勤密码"),
    backtest=TqBacktest(
        start_dt=datetime.date(2025, 1, 1),
        end_dt=datetime.date(2025, 12, 31)
    )
)
```

---

## ⚠️ 风险提示

> **本仓库内策略仅供学习研究使用，不构成任何投资建议。**  
> 期货交易存在较高风险，请在充分了解品种特性和策略逻辑后，  
> 先通过**模拟账户**或**历史回测**验证，再考虑实盘运行。  
> 实盘亏损由交易者自行承担，作者不对任何损失负责。

---

## 📅 更新日志

| 日期 | 变更 |
|------|------|
| 2026-03-02 | 初始化仓库，上传 ORB 开盘突破策略和 VWAP 偏离抢单策略 |

---

*Powered by [TqSdk](https://doc.shinnytech.com/tqsdk/latest/) · 天勤量化*
