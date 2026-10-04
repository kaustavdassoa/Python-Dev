"""
Vectorized Backtesting Engine.
Computes portfolio equity curve, CAGR, Sharpe ratio, Max Drawdown,
and benchmark comparison against Buy & Hold.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 100000.0,
        risk_free_rate: float = 0.065,  # 6.5% typical RBI repo/risk-free rate
        commission_rate: float = 0.001  # 0.1% per trade transaction friction
    ):
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        self.commission_rate = commission_rate

    def run_backtest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Simulate trading execution using vectorized returns.
        Assumes signals at day t execute at the close or next open.
        Position is shifted by 1 to prevent look-ahead bias.
        """
        data = df.copy()
        data["Market_Return"] = data["Close"].pct_change().fillna(0.0)

        # Strategy returns: executed using previous day's decided position
        # Shift(1) guarantees no look-ahead bias
        data["Strategy_Return"] = data["Market_Return"] * data["Position"].shift(1).fillna(0.0)

        # Subtract trading commission on trade transitions (Position changes)
        trades = (data["Position"].diff().abs().fillna(0.0) > 0).astype(int)
        data["Strategy_Return"] = data["Strategy_Return"] - (trades * self.commission_rate)

        # Cumulative equity curves
        data["Strategy_Equity"] = (1.0 + data["Strategy_Return"]).cumprod() * self.initial_capital
        data["Buy_Hold_Equity"] = (1.0 + data["Market_Return"]).cumprod() * self.initial_capital

        # High-water marks and Drawdowns
        strategy_peak = data["Strategy_Equity"].cummax()
        strategy_drawdown = (data["Strategy_Equity"] - strategy_peak) / strategy_peak
        max_drawdown = float(strategy_drawdown.min())

        buy_hold_peak = data["Buy_Hold_Equity"].cummax()
        buy_hold_drawdown = (data["Buy_Hold_Equity"] - buy_hold_peak) / buy_hold_peak
        buy_hold_max_drawdown = float(buy_hold_drawdown.min())

        # Total Returns
        strategy_final_value = float(data["Strategy_Equity"].iloc[-1])
        buy_hold_final_value = float(data["Buy_Hold_Equity"].iloc[-1])

        strategy_total_return = ((strategy_final_value - self.initial_capital) / self.initial_capital) * 100.0
        buy_hold_total_return = ((buy_hold_final_value - self.initial_capital) / self.initial_capital) * 100.0

        # Annualized metrics (CAGR)
        total_days = (data.index[-1] - data.index[0]).days
        years = max(total_days / 365.25, 0.1)

        strategy_cagr = ((strategy_final_value / self.initial_capital) ** (1.0 / years) - 1.0) * 100.0
        buy_hold_cagr = ((buy_hold_final_value / self.initial_capital) ** (1.0 / years) - 1.0) * 100.0

        # Sharpe Ratio (annualized, 252 trading days)
        daily_rf = (1.0 + self.risk_free_rate) ** (1.0 / 252.0) - 1.0
        excess_daily_returns = data["Strategy_Return"] - daily_rf
        
        std_dev = excess_daily_returns.std()
        if std_dev > 0:
            sharpe_ratio = float(np.sqrt(252.0) * (excess_daily_returns.mean() / std_dev))
        else:
            sharpe_ratio = 0.0

        # Trade Count & Win Rate analysis
        trade_logs = []
        in_trade = False
        entry_price = 0.0
        entry_date = None

        for idx, row in data.iterrows():
            pos_diff = row.get("Position_Diff", 0)
            if pos_diff == 1:  # Buy
                in_trade = True
                entry_price = row["Close"]
                entry_date = idx
            elif pos_diff == -1 and in_trade:  # Sell
                exit_price = row["Close"]
                ret_pct = ((exit_price - entry_price) / entry_price) * 100.0
                trade_logs.append({
                    "entry_date": str(entry_date.date()) if hasattr(entry_date, "date") else str(entry_date),
                    "exit_date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "return_pct": ret_pct,
                    "won": ret_pct > 0
                })
                in_trade = False

        total_trades = len(trade_logs)
        winning_trades = sum(1 for t in trade_logs if t["won"])
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "strategy_final_value": strategy_final_value,
            "buy_hold_final_value": buy_hold_final_value,
            "strategy_total_return_pct": strategy_total_return,
            "buy_hold_total_return_pct": buy_hold_total_return,
            "strategy_cagr_pct": strategy_cagr,
            "buy_hold_cagr_pct": buy_hold_cagr,
            "max_drawdown_pct": max_drawdown * 100.0,
            "buy_hold_max_drawdown_pct": buy_hold_max_drawdown * 100.0,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate_pct": win_rate,
            "years_tested": round(years, 2),
            "trade_logs": trade_logs[-5:]  # Include last 5 closed trades
        }
