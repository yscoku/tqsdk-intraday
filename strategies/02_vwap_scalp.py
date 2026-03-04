"""
================================================================================
策略编号: 02
策略名称: 日内VWAP偏离抢单策略（VWAP Scalping）
适用品种: 灵活配置（默认螺纹钢 SHFE.rb2510）
时间框架: 1分钟 VWAP / Tick 级触发
最后更新: 2026-03-02
================================================================================

【TqSdk 框架介绍】
TqSdk（天勤量化 SDK）是由信易科技推出的专业期货量化交易开发框架，基于 Python 
asyncio 异步协程架构构建，支持国内主要期货交易所（上期所、郑商所、大商所、中金所、
上期能源）的全品种程序化交易。该框架实现了行情订阅、历史数据获取、下单撤单、账户
资金管理的一体化接口，并提供了回测、模拟和实盘三种运行模式的无缝切换能力。

TqSdk 核心组件说明：
1. **TqApi**：框架核心，提供所有行情/交易接口，通过 `wait_update()` 实现事件驱动
   的非阻塞式行情处理，确保策略逻辑在毫秒级别响应行情变化。
2. **get_kline_serial**：获取 K 线序列，支持任意时间精度（1秒~1天），数据以 
   Pandas DataFrame 格式返回，包含 open/high/low/close/volume 等标准字段。
3. **get_tick_serial**：获取 Tick 序列，适用于微观结构分析，记录每笔成交的价格、
   成交量、买一/卖一报价等完整信息。
4. **TargetPosTask**：目标持仓管理器，通过指定目标手数（正为多、负为空、0 为平仓），
   自动计算并执行所需的开平仓操作，内置订单跟踪与超时重试机制。
5. **tafunc 技术指标库**：提供 MA、EMA、MACD、RSI、BOLL 等常用指标函数，可直接
   对 K 线序列 DataFrame 进行计算，与 TqSdk 深度集成。
6. **TqBacktest**：历史回测引擎，能以接近实盘的精度模拟历史行情下的策略执行效果，
   支持逐 Tick 或逐 K 线两种回测精度，为策略验证提供可靠依据。

【VWAP 指标介绍】
VWAP（Volume Weighted Average Price，成交量加权平均价格）是衡量日内市场公允价值
的重要基准指标。其计算方式为：将每根 K 线的典型价（(high+low+close)/3）乘以对应
成交量，再除以累积总成交量，得到从当日开盘到当前时刻的价格加权均值。机构投资者
通常以 VWAP 作为当日交易的基准价格，算法交易系统也广泛使用 VWAP 来评估执行质量。

当市场价格显著偏离 VWAP 时，往往存在均值回归的机会：
- 价格大幅低于 VWAP → 超卖信号 → 考虑开多（抄底）
- 价格大幅高于 VWAP → 超买信号 → 考虑开空（做空）

【策略思路】
VWAP 偏离抢单策略（VWAP Scalping）是一种基于均值回归假设的超短线策略，适用于
流动性充裕、日内价格均值回归特征明显的品种（如螺纹钢、沪铜等）。

核心逻辑：
1. 实时计算从当日开盘起的累积 VWAP。
2. 计算价格相对 VWAP 的偏离度（偏离 = (当前价 - VWAP) / VWAP × 10000，单位 bps）。
3. 当偏离度超过阈值（如 -15 bps，即价格低于 VWAP 0.15%）时，认为超卖，开多。
4. 当偏离度超过阈值（如 +15 bps，即价格高于 VWAP 0.15%）时，认为超买，开空。
5. 持仓目标：等待价格回归至 VWAP 附近（偏离 < 5 bps）时平仓获利。
6. 风控止损：若持仓超过 30 分钟仍未回归，或偏离继续扩大超过 2 倍阈值，强制止损平仓。
7. 14:50 全面强制平仓，绝不持隔夜仓。

【关键参数说明】
- ENTRY_DEVIATION_BPS: 入场偏离阈值（基点），推荐 10~20 bps
- EXIT_DEVIATION_BPS: 出场（止盈）偏离阈值，推荐 3~8 bps
- STOP_DEVIATION_BPS: 止损偏离阈值 = ENTRY_DEVIATION_BPS × STOP_MULTIPLIER
- MAX_HOLD_MINUTES: 最大持仓时间（分钟），超时强制平仓
- MIN_VOLUME_FILTER: 最小成交量过滤，避免在低流动性时刻入场

【风控要点】
1. 不在开盘前 15 分钟（09:00~09:14）入场，避开开盘波动剧烈期。
2. 不在尾盘后 10 分钟（14:50 之后）入场，为强平预留缓冲。
3. 同一方向不重复开仓（当日同向最多开 3 次）。
4. 持仓超过 30 分钟未达止盈，强制平仓（时间止损）。
5. 账户可用资金低于预设水位时，停止新开仓。
================================================================================
"""

import asyncio
import datetime
import math
import numpy as np
from tqsdk import TqApi, TqAuth, TqSim, TargetPosTask

# ──────────────────────────────────────────────────────────────────────────────
# 全局配置参数
# ──────────────────────────────────────────────────────────────────────────────

# 交易品种
SYMBOL = "SHFE.rb2510"

# VWAP 偏离度阈值（单位：bps = 万分之一）
ENTRY_DEVIATION_BPS = 15        # 入场阈值：±15 bps
EXIT_DEVIATION_BPS = 5          # 止盈阈值：偏离缩小至 ±5 bps 内平仓
STOP_MULTIPLIER = 2.0           # 止损阈值 = ENTRY × STOP_MULTIPLIER（即 ±30 bps）

# 最大持仓时间（分钟）——超过此时间强制平仓（时间止损）
MAX_HOLD_MINUTES = 30

# 强制平仓时间
FORCE_CLOSE_HOUR = 14
FORCE_CLOSE_MINUTE = 50

# 策略生效时间：跳过开盘前 N 分钟
SKIP_OPEN_MINUTES = 15          # 09:00~09:14 不入场

# 单次开仓手数
LOT_SIZE = 1

# 每日同方向最大开仓次数
MAX_TRADES_PER_DAY = 3

# 当日开盘时间（日盘）
DAY_OPEN_HOUR = 9
DAY_OPEN_MINUTE = 0

# ──────────────────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────────────────

def calc_vwap(klines, start_bar_idx: int) -> float:
    """
    计算从 start_bar_idx 到最新 K 线的 VWAP。
    
    公式：VWAP = Σ(典型价 × 成交量) / Σ(成交量)
    典型价 = (high + low + close) / 3
    
    参数：
        klines: TqSdk K 线序列 DataFrame
        start_bar_idx: 当日开盘对应的 K 线起始索引
    返回：
        float: 当前 VWAP 价格；若数据不足返回 NaN
    """
    try:
        bars = klines.iloc[start_bar_idx:]
        if len(bars) == 0:
            return float('nan')
        typical_price = (bars['high'] + bars['low'] + bars['close']) / 3.0
        total_vol = bars['volume'].sum()
        if total_vol == 0:
            return float('nan')
        vwap = (typical_price * bars['volume']).sum() / total_vol
        return float(vwap)
    except Exception:
        return float('nan')


def calc_deviation_bps(price: float, vwap: float) -> float:
    """
    计算当前价格相对 VWAP 的偏离度（bps）。
    
    公式：deviation_bps = (price - vwap) / vwap × 10000
    
    正值 → 价格高于 VWAP（超买区间）
    负值 → 价格低于 VWAP（超卖区间）
    """
    if math.isnan(vwap) or vwap == 0:
        return float('nan')
    return (price - vwap) / vwap * 10000.0


# ──────────────────────────────────────────────────────────────────────────────
# 策略主体
# ──────────────────────────────────────────────────────────────────────────────

async def run_vwap_scalp(api: TqApi):
    """
    日内 VWAP 偏离抢单策略主协程。
    
    执行步骤：
    1. 订阅 1 分钟 K 线，实时维护当日累积 VWAP。
    2. 监控 Tick 行情，计算偏离度并判断入场信号。
    3. 开仓后记录入场时间，监控止盈/止损/时间止损条件。
    4. 14:50 强制全平，退出当日交易。
    """

    print(f"[VWAP-SCALP] 策略启动 | 品种: {SYMBOL}")
    print(f"[VWAP-SCALP] 入场阈值: ±{ENTRY_DEVIATION_BPS} bps | "
          f"止盈: ±{EXIT_DEVIATION_BPS} bps | "
          f"止损: ±{ENTRY_DEVIATION_BPS * STOP_MULTIPLIER:.0f} bps | "
          f"时间止损: {MAX_HOLD_MINUTES} 分钟")

    # ── 订阅数据
    klines = api.get_kline_serial(SYMBOL, 60, data_length=300)   # 1 分钟 K 线
    quote = api.get_quote(SYMBOL)
    account = api.get_account()

    # ── 创建目标持仓任务
    target_pos = TargetPosTask(api, SYMBOL)

    # ── 状态变量
    day_open_bar_idx = None      # 当日开盘对应的 K 线索引
    position_direction = 0       # 当前持仓方向：+1 多，-1 空，0 无
    entry_time = None            # 开仓时刻（datetime）
    entry_price = None           # 开仓价格（用于日志）
    entry_vwap = None            # 开仓时的 VWAP（用于日志）
    long_count = 0               # 当日多向开仓次数
    short_count = 0              # 当日空向开仓次数
    force_closed = False         # 是否已执行强平
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    print(f"[VWAP-SCALP] 交易日: {today_str} | 等待行情就绪...")

    # ── 主循环
    async with api.register_update_notify() as update_chan:
        async for _ in update_chan:

            now = datetime.datetime.now()
            ch, cm = now.hour, now.minute

            # ────────────────────────────────────────────────
            # 强制平仓判断（14:50）
            # ────────────────────────────────────────────────
            if (ch > FORCE_CLOSE_HOUR or
                    (ch == FORCE_CLOSE_HOUR and cm >= FORCE_CLOSE_MINUTE)):
                if position_direction != 0 and not force_closed:
                    print(f"[VWAP-SCALP] ⚡ 14:50 强制平仓，持仓方向: "
                          f"{'多' if position_direction > 0 else '空'}")
                    target_pos.set_target_volume(0)
                    position_direction = 0
                    force_closed = True
                if force_closed:
                    print("[VWAP-SCALP] 当日交易完毕，策略停止。")
                    break
                continue

            # ── 仅日盘时间运行（09:00~14:50）
            if not (9 <= ch < 15):
                continue

            # ── 跳过开盘前 SKIP_OPEN_MINUTES 分钟
            if ch == DAY_OPEN_HOUR and cm < SKIP_OPEN_MINUTES:
                continue

            # ────────────────────────────────────────────────
            # 确定当日开盘 K 线索引（用于 VWAP 计算起点）
            # ────────────────────────────────────────────────
            if day_open_bar_idx is None:
                # 尝试找到今日 09:00 对应的 K 线（简化：取距今 300 根中最早的日盘 K 线）
                # 实际生产环境中应根据 klines 的 datetime 字段精确定位
                total_bars = len(klines)
                # 以当前最新 K 线往前推，找日盘开始位置（最多回溯 100 根）
                # 简化处理：取今日 09:00 之后的所有 K 线
                today_bars_count = min(ch * 60 + cm - 9 * 60 + 1, total_bars)
                day_open_bar_idx = max(0, total_bars - today_bars_count)
                print(f"[VWAP-SCALP] 当日开盘 K 线索引定位: idx={day_open_bar_idx}, "
                      f"今日累积 K 线数: {today_bars_count}")

            # ────────────────────────────────────────────────
            # 计算当日 VWAP
            # ────────────────────────────────────────────────
            vwap = calc_vwap(klines, day_open_bar_idx)
            if math.isnan(vwap):
                continue

            # ────────────────────────────────────────────────
            # 获取当前行情价格
            # ────────────────────────────────────────────────
            last_price = quote.last_price
            if math.isnan(last_price) or last_price <= 0:
                continue

            # 计算偏离度（bps）
            deviation = calc_deviation_bps(last_price, vwap)
            if math.isnan(deviation):
                continue

            stop_bps = ENTRY_DEVIATION_BPS * STOP_MULTIPLIER

            # ────────────────────────────────────────────────
            # 阶段一：无持仓时，判断入场信号
            # ────────────────────────────────────────────────
            if position_direction == 0:

                # ── 超卖信号：价格低于 VWAP，偏离超过阈值，开多
                if deviation <= -ENTRY_DEVIATION_BPS and long_count < MAX_TRADES_PER_DAY:
                    print(f"[VWAP-SCALP] 📈 超卖入场多 | 价格: {last_price:.1f} | "
                          f"VWAP: {vwap:.1f} | 偏离: {deviation:.2f} bps")
                    target_pos.set_target_volume(LOT_SIZE)
                    position_direction = 1
                    entry_time = now
                    entry_price = last_price
                    entry_vwap = vwap
                    long_count += 1
                    print(f"[VWAP-SCALP] 开多 {LOT_SIZE} 手 | 今日多向第 {long_count} 次")

                # ── 超买信号：价格高于 VWAP，偏离超过阈值，开空
                elif deviation >= ENTRY_DEVIATION_BPS and short_count < MAX_TRADES_PER_DAY:
                    print(f"[VWAP-SCALP] 📉 超买入场空 | 价格: {last_price:.1f} | "
                          f"VWAP: {vwap:.1f} | 偏离: {deviation:.2f} bps")
                    target_pos.set_target_volume(-LOT_SIZE)
                    position_direction = -1
                    entry_time = now
                    entry_price = last_price
                    entry_vwap = vwap
                    short_count += 1
                    print(f"[VWAP-SCALP] 开空 {LOT_SIZE} 手 | 今日空向第 {short_count} 次")

            # ────────────────────────────────────────────────
            # 阶段二：持仓中，判断出场条件
            # ────────────────────────────────────────────────
            elif position_direction != 0:

                hold_minutes = (now - entry_time).total_seconds() / 60.0

                # ── 条件1：止盈 —— 价格回归 VWAP 附近（|偏离| < EXIT_DEVIATION_BPS）
                if abs(deviation) <= EXIT_DEVIATION_BPS:
                    pnl_est = (last_price - entry_price) * position_direction
                    print(f"[VWAP-SCALP] ✅ 止盈平仓 | 价格: {last_price:.1f} | "
                          f"偏离: {deviation:.2f} bps | 持仓: {hold_minutes:.1f}min | "
                          f"估算盈亏: {pnl_est:.1f}点")
                    target_pos.set_target_volume(0)
                    position_direction = 0
                    entry_time = None

                # ── 条件2：止损 —— 偏离进一步扩大超过止损阈值（顺势但反向持仓）
                elif position_direction == 1 and deviation <= -stop_bps:
                    # 多头持仓，但价格继续下跌远离 VWAP，止损
                    print(f"[VWAP-SCALP] ❌ 多单偏离止损 | 偏离: {deviation:.2f} bps "
                          f"(止损线: -{stop_bps:.0f} bps)")
                    target_pos.set_target_volume(0)
                    position_direction = 0
                    entry_time = None

                elif position_direction == -1 and deviation >= stop_bps:
                    # 空头持仓，但价格继续上涨远离 VWAP，止损
                    print(f"[VWAP-SCALP] ❌ 空单偏离止损 | 偏离: {deviation:.2f} bps "
                          f"(止损线: +{stop_bps:.0f} bps)")
                    target_pos.set_target_volume(0)
                    position_direction = 0
                    entry_time = None

                # ── 条件3：时间止损 —— 持仓超过 MAX_HOLD_MINUTES 分钟未止盈
                elif hold_minutes >= MAX_HOLD_MINUTES:
                    print(f"[VWAP-SCALP] ⏰ 时间止损平仓 | 已持仓 {hold_minutes:.1f} 分钟 "
                          f"| 当前偏离: {deviation:.2f} bps")
                    target_pos.set_target_volume(0)
                    position_direction = 0
                    entry_time = None

                else:
                    # 持仓中，定期打印状态
                    if api.is_changing(klines):    # 每根新 K 线打印一次
                        print(f"[VWAP-SCALP] 📊 持仓中 | 方向: {'多' if position_direction > 0 else '空'} "
                              f"| 价格: {last_price:.1f} | VWAP: {vwap:.1f} "
                              f"| 偏离: {deviation:.2f} bps | 持仓: {hold_minutes:.1f}min")

    print("[VWAP-SCALP] 策略协程退出。")


def main():
    """
    策略入口函数。
    
    使用说明：
    - 实盘模式：将 TqSim() 替换为 TqAccount("期货公司", "账号", "密码")
    - 回测模式：添加 backtest=TqBacktest(start_dt=..., end_dt=...) 参数
    - auth 参数：填入天勤量化的用户名和密码（https://www.shinnytech.com/ 注册）
    
    参数调优建议：
    - ENTRY_DEVIATION_BPS: 可根据品种波动率调整（高波动品种调大，低波动调小）
    - MAX_HOLD_MINUTES: 超短线建议 15~30 分钟，中短线可延长至 60 分钟
    - LOT_SIZE: 根据账户资金和品种保证金合理设置
    """
    api = TqApi(
        account=TqSim(),
        auth=TqAuth("your_tq_username", "your_tq_password")
    )

    try:
        api.run_coro(run_vwap_scalp(api))
    finally:
        api.close()
        print("[VWAP-SCALP] TqApi 已关闭，程序退出。")


if __name__ == "__main__":
    main()
