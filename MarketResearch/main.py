"""
Entry point for Indian Stock Deterministic Signal & Backtesting Application.
Displays an intuitive Beginner-Friendly Summary (with Traffic-Light Verdict,
Confidence Score, Factor Checklist including P/E Valuation, and Real-Money Results)
alongside the detailed quantitative and valuation tables.
"""

import sys
import os
import argparse

# Ensure src is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ticker_resolver import resolve_indian_ticker
from src.data_loader import HistoricalDataLoader
from src.indicators import TechnicalIndicators
from src.strategy import MultiConditionStrategy
from src.backtester import BacktestEngine
from src.fundamentals import FundamentalValuationLoader
from src.formatters import render_beginner_summary

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def display_advanced_results(ticker: str, display_name: str, latest_eval: dict, backtest_results: dict, valuation: dict):
    """
    Renders the quantitative, technical indicator tables, fundamental P/E valuation, and backtest metrics.
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print(f"[bold cyan]📊 DETAILED QUANTITATIVE ANALYSIS & METRICS (Zero LLM, Pure Math)[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════════[/bold cyan]")

    # 1. Fundamental Valuation Table (P/E Ratio, Sector P/E, Historical Avg P/E)
    val_table = Table(show_header=True, header_style="bold yellow", title="[bold yellow]Fundamental Valuation Metrics[/bold yellow]")
    val_table.add_column("Valuation Metric", style="dim")
    val_table.add_column("Value")
    val_table.add_column("Benchmark / Context")

    t_pe = f"{valuation['trailing_pe']:.2f}" if valuation.get("trailing_pe") else "N/A"
    f_pe = f"{valuation['forward_pe']:.2f}" if valuation.get("forward_pe") else "N/A"
    s_pe = f"{valuation['sector_pe']:.1f}"
    h_pe = f"{valuation['historical_avg_pe']:.1f}" if valuation.get("historical_avg_pe") else "N/A"
    eps = f"₹{valuation['trailing_eps']:.2f}" if valuation.get("trailing_eps") else "N/A"
    sector_info = f"{valuation['sector']} ({valuation['industry']})"

    val_table.add_row("Current P/E (TTM)", t_pe, f"[{valuation['valuation_color']}]{valuation['valuation_status']}[/]")
    val_table.add_row("Forward P/E", f_pe, "Next 12-month earnings projection")
    val_table.add_row("Sector Average P/E", s_pe, f"Benchmark for: {sector_info}")
    val_table.add_row("5-Year Historical Avg P/E", h_pe, "Stock's long-term median valuation multiple")
    val_table.add_row("Trailing 12M EPS", eps, "Net profit earned per share")

    console.print(val_table)

    # 2. Deterministic Technical Rationales
    console.print("\n[bold cyan]Technical Indicators & Signal State:[/bold cyan]")
    ind_table = Table(show_header=True, header_style="bold magenta")
    ind_table.add_column("Indicator", style="dim")
    ind_table.add_column("Value")
    ind_table.add_column("Evaluation / Context")

    # EMA
    trend_state = "Bullish" if latest_eval['ema_20'] > latest_eval['ema_50'] else "Bearish"
    ind_table.add_row(
        "20 EMA / 50 EMA",
        f"₹{latest_eval['ema_20']:.2f} / ₹{latest_eval['ema_50']:.2f}",
        f"[{'green' if trend_state == 'Bullish' else 'red'}]{trend_state} crossover[/]"
    )
    # RSI
    rsi_color = "red" if latest_eval['rsi'] > 70 or latest_eval['rsi'] < 30 else "green"
    ind_table.add_row(
        "RSI (14)",
        f"{latest_eval['rsi']:.1f}",
        f"[{rsi_color}]{'Overbought' if latest_eval['rsi']>70 else ('Oversold' if latest_eval['rsi']<35 else 'Constructive')}[/]"
    )
    # MACD
    macd_color = "green" if latest_eval['macd'] > latest_eval['macd_signal'] else "red"
    ind_table.add_row(
        "MACD (12, 26, 9)",
        f"{latest_eval['macd']:.2f} (Sig: {latest_eval['macd_signal']:.2f})",
        f"[{macd_color}]{'Bullish' if latest_eval['macd'] > latest_eval['macd_signal'] else 'Bearish'}[/]"
    )
    # Bollinger Bands
    ind_table.add_row(
        "Bollinger Bands (20,2)",
        f"Lower: ₹{latest_eval['bb_lower']:.2f} | Upper: ₹{latest_eval['bb_upper']:.2f}",
        "Dynamic Volatility Bounds"
    )

    console.print(ind_table)

    # 3. Backtest Performance Metrics Table
    bt = backtest_results
    console.print(f"\n[bold cyan]Historical Backtesting Performance ({bt['years_tested']} Years):[/bold cyan]")
    bt_table = Table(show_header=True, header_style="bold blue")
    bt_table.add_column("Metric", style="dim")
    bt_table.add_column("Strategy (Multi-Condition)", justify="right")
    bt_table.add_column("Buy & Hold Benchmark", justify="right")

    strat_color = "green" if bt["strategy_total_return_pct"] >= 0 else "red"
    bh_color = "green" if bt["buy_hold_total_return_pct"] >= 0 else "red"

    bt_table.add_row("Initial Capital", f"₹{bt['initial_capital']:,.2f}", f"₹{bt['initial_capital']:,.2f}")
    bt_table.add_row("Final Equity", f"₹{bt['strategy_final_value']:,.2f}", f"₹{bt['buy_hold_final_value']:,.2f}")
    bt_table.add_row("Total Return (%)", f"[{strat_color}]{bt['strategy_total_return_pct']:.2f}%[/]", f"[{bh_color}]{bt['buy_hold_total_return_pct']:.2f}%[/]")
    bt_table.add_row("CAGR (%)", f"{bt['strategy_cagr_pct']:.2f}%", f"{bt['buy_hold_cagr_pct']:.2f}%")
    bt_table.add_row("Max Drawdown (%)", f"[red]{bt['max_drawdown_pct']:.2f}%[/red]", f"[red]{bt['buy_hold_max_drawdown_pct']:.2f}%[/red]")
    bt_table.add_row("Sharpe Ratio (Rf=6.5%)", f"{bt['sharpe_ratio']:.2f}", "-")
    bt_table.add_row("Total Completed Trades", f"{bt['total_trades']}", "1")
    bt_table.add_row("Win Rate (%)", f"{bt['win_rate_pct']:.1f}%", "-")

    console.print(bt_table)

    # Recent Closed Trades if any
    if bt.get("trade_logs"):
        console.print("\n[bold cyan]Recent Completed Trades:[/bold cyan]")
        t_table = Table(show_header=True, header_style="bold green")
        t_table.add_column("Entry Date")
        t_table.add_column("Exit Date")
        t_table.add_column("Entry Price", justify="right")
        t_table.add_column("Exit Price", justify="right")
        t_table.add_column("Trade Return", justify="right")

        for tr in bt["trade_logs"]:
            t_color = "green" if tr["won"] else "red"
            t_table.add_row(
                tr["entry_date"],
                tr["exit_date"],
                f"₹{tr['entry_price']:.2f}",
                f"₹{tr['exit_price']:.2f}",
                f"[{t_color}]{tr['return_pct']:+.2f}%[/]"
            )
        console.print(t_table)


def run_pipeline(query: str, period: str = "3y", exchange: str = "NS", show_advanced: bool = True):
    resolved_ticker, display_name = resolve_indian_ticker(query, default_exchange=exchange)
    console.print(f"\n[cyan]Fetching market & valuation data for [bold]{display_name}[/bold] -> [yellow]{resolved_ticker}[/yellow] ({period})...[/cyan]")

    try:
        loader = HistoricalDataLoader(ticker=resolved_ticker, period=period)
        raw_df = loader.fetch_data()
    except Exception as e:
        console.print(f"[bold red]Data Fetch Error:[/bold red] {e}")
        return

    # Fetch Fundamental P/E Valuation Metrics
    val_loader = FundamentalValuationLoader(ticker=resolved_ticker)
    valuation_data = val_loader.fetch_valuation()

    # Compute Indicators
    df_ind = TechnicalIndicators.add_all_indicators(raw_df)

    # Apply Multi-Condition Composite Strategy
    strategy = MultiConditionStrategy()
    df_signals = strategy.generate_signals(df_ind)
    latest_eval = strategy.evaluate_latest_bar(df_signals)

    # Run Vectorized Backtest
    backtester = BacktestEngine(initial_capital=100000.0)
    backtest_results = backtester.run_backtest(df_signals)

    # 1. Render Beginner-Friendly Summary (with P/E Valuation incorporated)
    render_beginner_summary(console, display_name, resolved_ticker, latest_eval, backtest_results, valuation_data)

    # 2. Render Advanced Quantitative & Valuation Details
    if show_advanced:
        display_advanced_results(resolved_ticker, display_name, latest_eval, backtest_results, valuation_data)


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic Indian Stock Signal Generator & Backtester with P/E Valuation (NSE/BSE)"
    )
    parser.add_argument(
        "--symbol", "-s",
        type=str,
        help="Stock symbol or name (e.g., RELIANCE, TCS, INFY, TATAMOTORS, HDFCBANK, IOC)"
    )
    parser.add_argument(
        "--period", "-p",
        type=str,
        default="3y",
        help="Historical lookback period (default: 3y). Options: 6mo, 1y, 2y, 3y, 5y"
    )
    parser.add_argument(
        "--exchange", "-e",
        type=str,
        default="NS",
        help="Default exchange suffix if omitted: NS (NSE) or BO (BSE)"
    )
    parser.add_argument(
        "--hide-advanced",
        action="store_true",
        help="Show only the beginner-friendly summary and hide technical tables"
    )

    args = parser.parse_args()

    show_adv = not args.hide_advanced

    if args.symbol:
        run_pipeline(args.symbol, period=args.period, exchange=args.exchange, show_advanced=show_adv)
    else:
        console.print("[bold yellow]=== Deterministic Indian Stock Signal & Backtest Analyzer ===[/bold yellow]")
        query = console.input("[bold green]Enter Indian Stock Name or Symbol (e.g. RELIANCE, TCS, IOC, INFY): [/bold green]")
        if query.strip():
            run_pipeline(query.strip(), period=args.period, exchange=args.exchange, show_advanced=show_adv)
        else:
            console.print("[red]No stock symbol provided. Exiting.[/red]")


if __name__ == "__main__":
    main()
