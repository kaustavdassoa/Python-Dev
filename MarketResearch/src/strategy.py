"""
Multi-Condition Composite Strategy & Signal Engine.
Evaluates trend, momentum, MACD, and Bollinger Bands deterministically.
Outputs discrete 'BUY', 'SELL', or 'HOLD' states along with detailed rationales.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


class MultiConditionStrategy:
    def __init__(
        self,
        rsi_oversold: float = 35.0,
        rsi_overbought: float = 70.0,
        enable_bollinger: bool = True
    ):
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.enable_bollinger = enable_bollinger

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluates deterministic technical indicators row-by-row / vector-wise
        to determine the target position (1 for Long, 0 for Flat/Cash)
        and outputs discrete BUY, SELL, or HOLD transitions.
        """
        data = df.copy()

        # Conditions
        trend_bullish = data["EMA_20"] > data["EMA_50"]
        trend_bearish = data["EMA_20"] < data["EMA_50"]

        macd_bullish = data["MACD"] > data["MACD_Signal"]
        macd_bearish = data["MACD"] < data["MACD_Signal"]

        rsi_healthy_buy = (data["RSI"] >= self.rsi_oversold) & (data["RSI"] <= 65.0)
        rsi_overheated = data["RSI"] >= self.rsi_overbought
        rsi_collapsed = data["RSI"] < 25.0

        bb_reversal_buy = data["Close"] <= data["BB_Lower"] * 1.01
        bb_upper_rejection = data["Close"] >= data["BB_Upper"]

        # Composite Buy Condition:
        # 1. Primary: Bullish trend (EMA20 > EMA50) + positive MACD + non-overbought RSI
        # 2. Or Mean Reversion: Oversold bounce (Price at lower BB with RSI recovering)
        buy_condition = (
            (trend_bullish & macd_bullish & rsi_healthy_buy) |
            (bb_reversal_buy & (data["RSI"] > data["RSI"].shift(1)) & (data["RSI"] < 40))
        )

        # Composite Sell Condition:
        # Bearish trend cross OR MACD death cross with dropping RSI OR severe overbought exhaustion
        sell_condition = (
            (trend_bearish & macd_bearish) |
            (rsi_overheated & bb_upper_rejection) |
            (trend_bearish & (data["RSI"] < 45.0))
        )

        # Build position state: 1 = In Market, 0 = Out of Market
        position = pd.Series(0, index=data.index)
        current_state = 0
        
        # Iterate over bars to maintain state continuity
        for i in range(len(data)):
            if buy_condition.iloc[i]:
                current_state = 1
            elif sell_condition.iloc[i]:
                current_state = 0
            position.iloc[i] = current_state

        data["Position"] = position
        
        # State transitions
        # +1 means transition from 0 to 1 -> BUY
        # -1 means transition from 1 to 0 -> SELL
        # 0 means continuation -> HOLD
        data["Position_Diff"] = data["Position"].diff().fillna(0)

        signals = []
        for diff in data["Position_Diff"]:
            if diff == 1:
                signals.append("BUY")
            elif diff == -1:
                signals.append("SELL")
            else:
                signals.append("HOLD")

        data["Signal"] = signals
        return data

    def evaluate_latest_bar(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extracts the latest bar's deterministic metrics and builds human-readable rationales.
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        signal = latest["Signal"]
        current_pos = latest["Position"]

        reasons: List[str] = []

        # 1. Trend Analysis
        if latest["EMA_20"] > latest["EMA_50"]:
            reasons.append(f"Bullish Trend: 20 EMA ({latest['EMA_20']:.2f}) > 50 EMA ({latest['EMA_50']:.2f})")
        else:
            reasons.append(f"Bearish Trend: 20 EMA ({latest['EMA_20']:.2f}) < 50 EMA ({latest['EMA_50']:.2f})")

        # 2. RSI Analysis
        rsi_val = latest["RSI"]
        if rsi_val > 70:
            reasons.append(f"RSI is Overbought ({rsi_val:.1f})")
        elif rsi_val < 35:
            reasons.append(f"RSI is Oversold ({rsi_val:.1f})")
        else:
            reasons.append(f"RSI is Neutral/Constructive ({rsi_val:.1f})")

        # 3. MACD Analysis
        if latest["MACD"] > latest["MACD_Signal"]:
            reasons.append(f"MACD Bullish: MACD Line ({latest['MACD']:.2f}) above Signal ({latest['MACD_Signal']:.2f})")
        else:
            reasons.append(f"MACD Bearish: MACD Line ({latest['MACD']:.2f}) below Signal ({latest['MACD_Signal']:.2f})")

        # 4. Bollinger Bands Context
        close_p = latest["Close"]
        if close_p >= latest["BB_Upper"]:
            reasons.append(f"Price ({close_p:.2f}) touching/exceeding Upper Bollinger Band ({latest['BB_Upper']:.2f})")
        elif close_p <= latest["BB_Lower"]:
            reasons.append(f"Price ({close_p:.2f}) touching/below Lower Bollinger Band ({latest['BB_Lower']:.2f})")
        else:
            reasons.append(f"Price ({close_p:.2f}) trading within Bollinger Bands ({latest['BB_Lower']:.2f} - {latest['BB_Upper']:.2f})")

        # Contextual summary for HOLD
        if signal == "HOLD":
            if current_pos == 1:
                status_summary = "HOLD (In Long Position - Existing trend remains intact)"
            else:
                status_summary = "HOLD (In Cash - Awaiting clearer entry confirmation)"
        elif signal == "BUY":
            status_summary = "BUY (New Bullish Entry Triggered)"
        else:
            status_summary = "SELL (Exit / Profit-taking Triggered)"

        return {
            "date": str(latest.name.date()) if hasattr(latest.name, "date") else str(latest.name),
            "signal": signal,
            "status_summary": status_summary,
            "current_position": "LONG (Invested)" if current_pos == 1 else "CASH (Uninvested)",
            "close_price": float(latest["Close"]),
            "ema_20": float(latest["EMA_20"]),
            "ema_50": float(latest["EMA_50"]),
            "rsi": float(latest["RSI"]),
            "macd": float(latest["MACD"]),
            "macd_signal": float(latest["MACD_Signal"]),
            "bb_lower": float(latest["BB_Lower"]),
            "bb_upper": float(latest["BB_Upper"]),
            "rationales": reasons
        }
