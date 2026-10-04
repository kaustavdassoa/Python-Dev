"""
Beginner-friendly formatter module for stock analysis.
Translates quantitative technical indicators and P/E valuation metrics
into plain-English scorecards, traffic-light verdicts, confidence scores,
and real-money backtest summaries.
"""

from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def calculate_beginner_health_score(latest_eval: Dict[str, Any], valuation: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Computes a 0-100 Stock Health / Strength Score and a Confidence Level (0-100%)
    based on deterministic quantitative indicators combined with P/E fundamental valuation.
    """
    score = 0
    checks = []

    # 1. Trend Factor (Weight: 30 points)
    ema_20 = latest_eval["ema_20"]
    ema_50 = latest_eval["ema_50"]
    close = latest_eval["close_price"]

    if close > ema_20 > ema_50:
        score += 30
        checks.append(("Short-Term Trend", "Strongly Rising", "Price is steadily climbing above recent averages", "✅ Positive"))
    elif ema_20 > ema_50:
        score += 22
        checks.append(("Short-Term Trend", "Moderately Rising", "Trend is positive, price undergoing mild pullback", "✅ Positive"))
    elif close < ema_20 < ema_50:
        score += 5
        checks.append(("Short-Term Trend", "Strongly Falling", "Price is sliding down below recent averages", "❌ Negative"))
    else:
        score += 12
        checks.append(("Short-Term Trend", "Choppy / Neutral", "Market is moving sideways without clear direction", "⚠️ Neutral"))

    # 2. Buying vs Selling Pressure (RSI 14) (Weight: 20 points)
    rsi = latest_eval["rsi"]
    if 45 <= rsi <= 65:
        score += 20
        checks.append(("Buying Pressure", "Healthy & Balanced", "Steady accumulation without being overheated", "✅ Positive"))
    elif rsi > 70:
        score += 8
        checks.append(("Buying Pressure", "Overheated (Too Expensive)", "Price ran up too fast; risk of sudden pullback", "⚠️ High Risk"))
    elif rsi < 30:
        score += 10
        checks.append(("Buying Pressure", "Heavy Selling (Cheap)", "Deep discount zone; waiting for buyers to return", "⚠️ Oversold"))
    else:
        score += 14
        checks.append(("Buying Pressure", "Moderate / Recovering", "Balanced interest between buyers and sellers", "ℹ️ Neutral"))

    # 3. Momentum (MACD) (Weight: 20 points)
    macd = latest_eval["macd"]
    macd_sig = latest_eval["macd_signal"]

    if macd > macd_sig and macd > 0:
        score += 20
        checks.append(("Speed & Momentum", "Strong Upward Momentum", "Speed of price rise is accelerating", "✅ Positive"))
    elif macd > macd_sig:
        score += 15
        checks.append(("Speed & Momentum", "Turning Positive", "Early signs of buyers stepping in", "✅ Positive"))
    elif macd < macd_sig and macd < 0:
        score += 4
        checks.append(("Speed & Momentum", "Downward Momentum", "Sellers are currently driving the speed of decline", "❌ Negative"))
    else:
        score += 10
        checks.append(("Speed & Momentum", "Slowing Down", "Momentum is weakening", "⚠️ Neutral"))

    # 4. Volatility & Safety Range (Bollinger Bands) (Weight: 10 points)
    bb_lower = latest_eval["bb_lower"]
    bb_upper = latest_eval["bb_upper"]

    if bb_lower <= close <= bb_upper:
        score += 10
        checks.append(("Price Stability", "Normal Volatility Band", f"Trading safely between ₹{bb_lower:,.2f} and ₹{bb_upper:,.2f}", "✅ Stable"))
    elif close < bb_lower:
        score += 5
        checks.append(("Price Stability", "Unusually Low", "Pushed below regular volatility floor", "⚠️ Volatile Low"))
    else:
        score += 5
        checks.append(("Price Stability", "Stretched High", "Pushed above regular volatility ceiling", "⚠️ Volatile High"))

    # 5. Fundamental Valuation (P/E Ratio vs Sector & History) (Weight: 20 points)
    if valuation and valuation.get("trailing_pe") is not None:
        t_pe = valuation["trailing_pe"]
        s_pe = valuation.get("sector_pe", 20.0)
        h_pe = valuation.get("historical_avg_pe", s_pe)
        ref_pe = h_pe if h_pe else s_pe

        if t_pe < ref_pe * 0.80:
            score += 20
            checks.append(("P/E Valuation", f"Attractive / Undervalued (P/E {t_pe:.1f})", f"Trading well below sector ({s_pe:.1f}) & 5-yr avg ({h_pe:.1f})", "✅ Bargain"))
        elif t_pe <= ref_pe * 1.15:
            score += 15
            checks.append(("P/E Valuation", f"Fair Value (P/E {t_pe:.1f})", f"Priced in line with industry average ({s_pe:.1f})", "✅ Fair"))
        elif t_pe <= ref_pe * 1.40:
            score += 8
            checks.append(("P/E Valuation", f"Moderately Premium (P/E {t_pe:.1f})", f"Trading above industry average ({s_pe:.1f})", "⚠️ Premium"))
        else:
            score += 3
            checks.append(("P/E Valuation", f"Expensive / Stretched (P/E {t_pe:.1f})", f"Significantly above 5-yr avg ({h_pe:.1f}) & sector ({s_pe:.1f})", "❌ Overvalued"))
    else:
        # Fallback if P/E unavailable (scale existing 80 pts to 100)
        score = int(score * 1.25)
        checks.append(("P/E Valuation", "Data Unavailable", "Earnings multiple not applicable or unlisted", "ℹ️ Neutral"))

    # Calculate Signal Confidence Score (0-100%)
    sig = latest_eval["signal"]
    pos = latest_eval["current_position"]

    if sig == "BUY":
        confidence = min(max(int(score * 1.05), 60), 95)
    elif sig == "SELL":
        confidence = min(max(int((100 - score) * 1.05), 65), 95)
    else:  # HOLD
        if "CASH" in pos:
            confidence = min(max(int((100 - score) * 0.95), 50), 90)
        else:
            confidence = min(max(int(score * 0.95), 50), 90)

    # Health Rating Label
    if score >= 75:
        health_label = "Very Strong"
        health_color = "bold green"
    elif score >= 55:
        health_label = "Constructive / Moderate"
        health_color = "green"
    elif score >= 40:
        health_label = "Neutral / Watch Closely"
        health_color = "yellow"
    else:
        health_label = "Weak / Cautious"
        health_color = "bold red"

    return {
        "score": score,
        "health_label": health_label,
        "health_color": health_color,
        "confidence_pct": confidence,
        "checks": checks
    }


def render_beginner_summary(
    console: Console,
    display_name: str,
    ticker: str,
    latest_eval: Dict[str, Any],
    backtest: Dict[str, Any],
    valuation: Dict[str, Any] = None
):
    """
    Renders an intuitive, jargon-free beginner dashboard with confidence score
    and P/E valuation context.
    """
    health_info = calculate_beginner_health_score(latest_eval, valuation)
    sig = latest_eval["signal"]
    pos = latest_eval["current_position"]
    close = latest_eval["close_price"]
    score = health_info["score"]
    confidence = health_info["confidence_pct"]

    # 1. Plain-English Verdict & Action
    if sig == "BUY":
        verdict_badge = "[bold white on green] 🟢 BUY SIGNAL: GOOD OPPORTUNITY TO ENTER [/bold white on green]"
        buyer_advice = "The technical setup turned bullish. Favorable risk/reward for new positions."
        owner_advice = "Hold and let your profits run. Protect gains with a trailing mental stop."
        border_col = "green"
    elif sig == "SELL":
        verdict_badge = "[bold white on red] 🔴 SELL SIGNAL: TIME TO EXIT OR CUT LOSS [/bold white on red]"
        buyer_advice = "Do NOT buy. The stock has broken key support and is under selling pressure."
        owner_advice = "Consider booking profits or exiting to preserve your capital."
        border_col = "red"
    else:  # HOLD
        if "CASH" in pos:
            verdict_badge = "[bold black on yellow] 🟡 WAIT & WATCH (DO NOT BUY YET) [/bold black on yellow]"
            buyer_advice = "Be patient. The stock has not confirmed a clear upward turnaround yet."
            owner_advice = "If you are already holding, watch the lower support level closely."
        else:
            verdict_badge = "[bold black on yellow] 🟡 HOLD EXISTING SHARES (STAY INVESTED) [/bold black on yellow]"
            buyer_advice = "Existing trend remains okay, but wait for a fresh pullback before buying more."
            owner_advice = "Keep holding your current shares. No exit rule has been triggered yet."
        border_col = "yellow"

    # Beginner Top Card
    summary_text = (
        f"\n{verdict_badge}\n\n"
        f"• [bold]Current Share Price:[/bold] [yellow]₹{close:,.2f}[/yellow]\n"
        f"• [bold]Stock Overall Health Score:[/bold] [{health_info['health_color']}]{score}/100 ({health_info['health_label']})[/{health_info['health_color']}]\n"
        f"• [bold]Algorithm Confidence Score:[/bold] [bold cyan]{confidence}% Confidence[/bold cyan]\n\n"
        f"[bold]👉 If you are looking to BUY:[/bold] {buyer_advice}\n"
        f"[bold]👉 If you already OWN shares:[/bold] {owner_advice}"
    )

    console.print(Panel(
        summary_text,
        title=f"[bold]EASY SUMMARY FOR BEGINNERS: {display_name.upper()} ({ticker})[/bold]",
        expand=False,
        border_style=border_col
    ))

    # 2. Plain-English Factor Checklist
    console.print("\n[bold cyan]🔍 Plain-English Breakdown of Key Factors:[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Factor", style="bold")
    table.add_column("Status")
    table.add_column("What This Means in Simple Terms")
    table.add_column("Impact", justify="center")

    for factor, status, meaning, impact in health_info["checks"]:
        table.add_row(factor, status, meaning, impact)

    console.print(table)

    # 3. Real-Money Backtest Results (What happened in ₹1 Lakh terms)
    c_initial = backtest["initial_capital"]
    c_final_strat = backtest["strategy_final_value"]
    c_final_bh = backtest["buy_hold_final_value"]
    profit_strat = c_final_strat - c_initial
    profit_bh = c_final_bh - c_initial
    win_rate = backtest["win_rate_pct"]
    mdd = abs(backtest["max_drawdown_pct"])

    p_color = "green" if profit_strat >= 0 else "red"
    sign_str = "+" if profit_strat >= 0 else ""

    money_summary = (
        f"• [bold]If you started with:[/bold] ₹{c_initial:,.0f} three years ago\n"
        f"• [bold]Your money today using this strategy:[/bold] [{p_color}]₹{c_final_strat:,.0f}[/{p_color}] ({sign_str}₹{profit_strat:,.0f} / {sign_str}{backtest['strategy_total_return_pct']:.1f}%)\n"
        f"• [bold]If you just bought & never touched it (Buy & Hold):[/bold] ₹{c_final_bh:,.0f} ({'+' if profit_bh>=0 else ''}₹{profit_bh:,.0f})\n"
        f"• [bold]Trade Success Rate:[/bold] [bold]{win_rate:.0f}%[/bold] of closed trades made money ({backtest['winning_trades']} out of {backtest['total_trades']} trades won)\n"
        f"• [bold]Risk Protection:[/bold] The worst temporary drop was [bold red]-{mdd:.1f}%[/bold red] (Compared to [red]-{abs(backtest['buy_hold_max_drawdown_pct']):.1f}%[/red] for Buy & Hold)"
    )

    console.print(Panel(
        money_summary,
        title="[bold]💰 Historical Results in Real Money Terms (Last 3 Years on ₹1,00,000)[/bold]",
        expand=False,
        border_style="cyan"
    ))
