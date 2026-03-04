"""
================================================================================
策略编号: 01
策略名称: 开盘区间突破策略（Opening Range Breakout, ORB）
适用品种: 螺纹钢主力合约（SHFE.rb2510 或当前主力）
时间框架: 1分钟 K 线 / Tick 级触发
最后更新: 2026-03-02
================================================================================

【TqSdk 框架介绍】
TqSdk（天勤量化 SDK）是由信易科技推出的专业量化交易开发套件，支持期货、期权等
衍生品市场的程序化交易。TqSdk 提供了统一的行情订阅接口、历史数据回调、实盘/模
拟/回测三模式无缝切换能力，以及丰富的技术指标库（tqsdk.tafunc）。其核心编程范
式基于 Python asyncio 协程框架，通过 `api.wait_update()` 驱动事件循环，确保在
行情更新、成交回报、账户变动等各类事件触发时，策略逻辑能够以近实时速度响应。

TqSdk 的主要特点：
1. **行情订阅**：`api.get_quote(symbol)` 获取 Tick 行情；`api.get_kline_serial`
   获取 K 线序列，支持从 1 秒到日线的任意周期。
2. **下单交易**：`api.insert_order()` 实现市价/限价委托，配合 `api.wait_update()`
   监听成交状态，保证订单状态的实时感知。
3. **账户与持仓**：`api.get_account()` 获取资金账户；`api.get_position(symbol)` 
   获取某品种当前持仓，精确感知多空方向及手数。
4. **目标持仓接口**：`api.set_target_volume()` 配合 `TargetPosTask` 实现自动化
   的目标持仓管理，避免重复下单、超量开仓等常见错误。
5. **回测与实盘切换**：仅需更改 `TqApi` 的 `backtest` 参数，即可在历史行情回测
   与实盘账户之间无缝切换，代码逻辑完全一致。
6. **风控机制**：通过内置的持仓检查、资金检查和撤单接口，可以方便地构建多层次的
   风控体系，保障账户安全。

【策略思路】
开盘区间突破（ORB）是一种经典的日内趋势捕捉策略。其核心逻辑如下：
- 在每个交易日，记录开盘后前 15 分钟（即 09:00~09:14）内所有 1 分钟 K 线的最
  高价和最低价，构成「开盘区间」（Opening Range）。
- 09:15 之后，若价格向上突破区间最高价，视为多头动能确立，开多仓；若价格向下
  跌破区间最低价，视为空头动能确立，开空仓。
- 止损设置在区间对侧边界，止盈采用 ATR 倍数目标价；若触发止损，当日不再交易。
- 无论持仓方向，在 14:50 进行强制平仓，确保不持隔夜头寸。

【关键风控点】
1. 每日仅允许单次突破方向入场（多突破开多、空突破开空，不重复开仓）。
2. 止损设在区间对侧（多单止损=区间低点，空单止损=区间高点），单边风险固定。
3. 14:50 之前若已触止损，当日不再新开仓，防止连续亏损。
4. 使用 TargetPosTask 管理目标持仓，避免重复下单导致超仓。
5. 仓位控制：单次开仓固定 1 手，可根据账户余额动态调整（预留接口）。

【注意事项】
- 螺纹钢（rb）上午开盘时间为 09:00，注意区间时间窗口的准确性。
- 本策略运行前需在 TqApi 中配置真实账户或使用 TqSim() 模拟账户。
- 回测时建议使用 TqBacktest 模式验证策略表现后再进行实盘。
- 夜盘行情（21:00~23:00）不参与，策略仅在日盘运行。
================================================================================
"""

import asyncio
import datetime
from tqsdk import TqApi, TqAuth, TqSim, TargetPosTask
from tqsdk.tafunc import time_to_datetime

# ──────────────────────────────────────────────────────────────────────────────
# 全局配置参数
# ──────────────────────────────────────────────────────────────────────────────

# 交易品种：螺纹钢主力合约（运行时可替换为 SHFE.rb2510 等具体月份）
SYMBOL = "SHFE.rb2510"

# 开盘区间采样分钟数：前 N 根 1 分钟 K 线
ORB_MINUTES = 15                    # 09:00 ~ 09:14 共 15 根

# 强制平仓时间（14:50 之前收盘强平，螺纹钢收盘 15:00）
FORCE_CLOSE_HOUR = 14
FORCE_CLOSE_MINUTE = 50

# 早盘开始时间（区间采样起点）
DAY_SESSION_HOUR = 9
DAY_SESSION_MINUTE = 0

# 止盈倍数：相对于区间宽度的止盈距离
PROFIT_RATIO = 1.5                  # 止盈 = 区间宽度 × 1.5

# 单次开仓手数
LOT_SIZE = 1

# ──────────────────────────────────────────────────────────────────────────────
# 策略主体
# ──────────────────────────────────────────────────────────────────────────────

async def run_orb_strategy(api: TqApi):
    """
    开盘区间突破策略主协程。
    
    逻辑流程：
    1. 订阅 1 分钟 K 线序列，等待开盘区间形成（前 15 根 K 线）。
    2. 区间确认后，监控 Tick 价格突破区间高低点。
    3. 突破方向开仓，设置目标持仓；同时追踪止损和止盈条件。
    4. 14:50 强制平仓，清零所有持仓。
    """

    print(f"[ORB] 策略启动，交易品种: {SYMBOL}")
    print(f"[ORB] 开盘区间窗口: {ORB_MINUTES} 分钟 | 强平时间: {FORCE_CLOSE_HOUR}:{FORCE_CLOSE_MINUTE:02d}")

    # ── 订阅 1 分钟 K 线（取最近 200 根，足够覆盖单日采样）
    klines = api.get_kline_serial(SYMBOL, 60, data_length=200)

    # ── 订阅 Tick 实时行情（用于精确判断突破价位）
    quote = api.get_quote(SYMBOL)

    # ── 获取账户信息（用于风控资金检查）
    account = api.get_account()

    # ── 创建目标持仓任务（TargetPosTask 自动管理开平仓）
    target_pos = TargetPosTask(api, SYMBOL)

    # ── 状态变量
    orb_high = None           # 开盘区间最高价
    orb_low = None            # 开盘区间最低价
    orb_confirmed = False     # 区间是否已锁定（前 15 根 K 线全部结束）
    position_opened = False   # 当日是否已开仓
    trade_direction = 0       # 当前持仓方向：+1 多，-1 空，0 无仓
    stop_price = None         # 当前止损价
    profit_price = None       # 当前止盈价
    today_done = False        # 当日交易是否结束（止损触发后不再开仓）

    print("[ORB] 等待行情就绪...")

    # ── 主循环：由 wait_update 驱动，每次行情/K线更新时触发
    async with api.register_update_notify() as update_chan:
        async for _ in update_chan:
            # ── 获取当前时间（使用服务器行情时间）
            now_dt = None
            if not api.is_changing(quote, "datetime"):
                pass
            # 直接使用 datetime 模块获取系统时间作为辅助判断
            now = datetime.datetime.now()
            current_hour = now.hour
            current_minute = now.minute

            # ── 强制平仓逻辑：到达 14:50 必须清仓
            if (current_hour > FORCE_CLOSE_HOUR or
                    (current_hour == FORCE_CLOSE_HOUR and current_minute >= FORCE_CLOSE_MINUTE)):
                if trade_direction != 0:
                    print(f"[ORB] ⚡ 14:50 强制平仓，当前方向: {'多' if trade_direction > 0 else '空'}")
                    target_pos.set_target_volume(0)
                    trade_direction = 0
                    today_done = True
                # 强平后等待下一交易日重置（实盘 24h 运行时需要跨日重置逻辑）
                # 此处简化：当日交易结束，退出主循环
                if today_done:
                    print("[ORB] 当日交易结束，策略挂起等待下一交易日。")
                    break
                continue

            # ── 跳过夜盘时段（21:00~23:59 和 00:00~08:59）
            if not (9 <= current_hour < 15):
                continue

            # ── 当日已完成（止损触发后不再交易）
            if today_done:
                continue

            # ────────────────────────────────────────────────
            # 阶段一：采集开盘区间（前 15 根 1 分钟 K 线）
            # ────────────────────────────────────────────────
            if not orb_confirmed:
                # 只处理 9:00 ~ 9:14 时段
                if current_hour == 9 and current_minute < ORB_MINUTES:
                    # 每次 K 线更新时刷新区间高低点
                    # klines.iloc[-1] 是当前未完成 K 线，需从已收盘的 K 线中取
                    # 找到今日 09:00 开始的 K 线
                    try:
                        # 收集今日日盘开始后的前 ORB_MINUTES 根 K 线
                        recent_high = klines.high.iloc[-ORB_MINUTES:].max()
                        recent_low = klines.low.iloc[-ORB_MINUTES:].min()
                        orb_high = recent_high
                        orb_low = recent_low
                    except Exception as e:
                        print(f"[ORB] 区间采样异常: {e}")
                    continue

                # 09:15 之后锁定区间
                if current_hour == 9 and current_minute >= ORB_MINUTES:
                    if orb_high is not None and not orb_confirmed:
                        orb_confirmed = True
                        range_width = orb_high - orb_low
                        print(f"[ORB] ✅ 区间锁定 | 高: {orb_high:.1f} | 低: {orb_low:.1f} | 宽: {range_width:.1f}")

            # ────────────────────────────────────────────────
            # 阶段二：突破判断与开仓
            # ────────────────────────────────────────────────
            if orb_confirmed and not position_opened and not today_done:
                last_price = quote.last_price
                if last_price != last_price:   # NaN 检查
                    continue

                range_width = orb_high - orb_low

                # ── 向上突破：开多
                if last_price > orb_high:
                    print(f"[ORB] 🔼 多头突破！价格 {last_price:.1f} > 区间高 {orb_high:.1f}")
                    target_pos.set_target_volume(LOT_SIZE)
                    trade_direction = 1
                    stop_price = orb_low                              # 止损：区间低点
                    profit_price = orb_high + range_width * PROFIT_RATIO  # 止盈
                    position_opened = True
                    print(f"[ORB] 开多 {LOT_SIZE} 手 | 止损: {stop_price:.1f} | 止盈: {profit_price:.1f}")

                # ── 向下突破：开空
                elif last_price < orb_low:
                    print(f"[ORB] 🔽 空头突破！价格 {last_price:.1f} < 区间低 {orb_low:.1f}")
                    target_pos.set_target_volume(-LOT_SIZE)
                    trade_direction = -1
                    stop_price = orb_high                             # 止损：区间高点
                    profit_price = orb_low - range_width * PROFIT_RATIO   # 止盈
                    position_opened = True
                    print(f"[ORB] 开空 {LOT_SIZE} 手 | 止损: {stop_price:.1f} | 止盈: {profit_price:.1f}")

            # ────────────────────────────────────────────────
            # 阶段三：持仓中的止损/止盈监控
            # ────────────────────────────────────────────────
            if position_opened and trade_direction != 0:
                last_price = quote.last_price
                if last_price != last_price:
                    continue

                # ── 多单止损检查
                if trade_direction == 1 and last_price <= stop_price:
                    print(f"[ORB] ❌ 多单触及止损 {stop_price:.1f}，平仓！")
                    target_pos.set_target_volume(0)
                    trade_direction = 0
                    today_done = True   # 当日不再开仓
                    print("[ORB] 止损后当日不再入场。")

                # ── 多单止盈检查
                elif trade_direction == 1 and last_price >= profit_price:
                    print(f"[ORB] ✅ 多单触及止盈 {profit_price:.1f}，平仓！")
                    target_pos.set_target_volume(0)
                    trade_direction = 0
                    today_done = True   # 止盈后当日不再入场

                # ── 空单止损检查
                elif trade_direction == -1 and last_price >= stop_price:
                    print(f"[ORB] ❌ 空单触及止损 {stop_price:.1f}，平仓！")
                    target_pos.set_target_volume(0)
                    trade_direction = 0
                    today_done = True

                # ── 空单止盈检查
                elif trade_direction == -1 and last_price <= profit_price:
                    print(f"[ORB] ✅ 空单触及止盈 {profit_price:.1f}，平仓！")
                    target_pos.set_target_volume(0)
                    trade_direction = 0
                    today_done = True

    print("[ORB] 策略协程退出。")


def main():
    """
    策略入口函数。
    
    使用说明：
    - 实盘模式：将 TqSim() 替换为真实账户 TqAccount("期货公司", "账号", "密码")
    - 回测模式：添加 backtest=TqBacktest(start_dt=..., end_dt=...) 参数
    - auth 参数：填入天勤量化的用户名和密码
    """
    # ── 初始化 TqApi（此处使用模拟账户，实盘需替换）
    api = TqApi(
        account=TqSim(),
        auth=TqAuth("your_tq_username", "your_tq_password")
    )

    try:
        # ── 启动策略主协程
        api.run_coro(run_orb_strategy(api))
    finally:
        # ── 关闭 API 连接（确保资源释放）
        api.close()
        print("[ORB] TqApi 已关闭，程序退出。")


if __name__ == "__main__":
    main()
