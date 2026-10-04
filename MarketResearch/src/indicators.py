"""
Deterministic Technical Indicators Module.
Computes Moving Averages, RSI, MACD, and Bollinger Bands using pandas/numpy vectorized calculations.
Zero LLM, zero look-ahead bias.
"""

import pandas as pd
import numpy as np


class TechnicalIndicators:
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all standard indicators and returns a copy with added columns.
        """
        data = df.copy()
        close = data["Close"]

        # 1. Moving Averages
        data["EMA_20"] = close.ewm(span=20, adjust=False).mean()
        data["EMA_50"] = close.ewm(span=50, adjust=False).mean()
        data["SMA_50"] = close.rolling(window=50, min_periods=20).mean()
        data["SMA_200"] = close.rolling(window=200, min_periods=50).mean()

        # 2. Relative Strength Index (RSI 14) - Wilder's Smoothing
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        
        # Avoid zero division
        rs = avg_gain / avg_loss.replace(0, np.nan)
        data["RSI"] = 100 - (100 / (1 + rs))
        data["RSI"] = data["RSI"].fillna(50.0)

        # 3. MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        data["MACD"] = ema_12 - ema_26
        data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
        data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]

        # 4. Bollinger Bands (20, 2 std dev)
        data["BB_Middle"] = close.rolling(window=20, min_periods=10).mean()
        bb_std = close.rolling(window=20, min_periods=10).std()
        data["BB_Upper"] = data["BB_Middle"] + (2.0 * bb_std)
        data["BB_Lower"] = data["BB_Middle"] - (2.0 * bb_std)
        
        # Bollinger %B (location within bands: 0 = lower band, 1 = upper band)
        band_width = (data["BB_Upper"] - data["BB_Lower"]).replace(0, np.nan)
        data["BB_Pct"] = (close - data["BB_Lower"]) / band_width

        # 5. Average True Range (ATR 14) for volatility context
        high = data["High"]
        low = data["Low"]
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        data["ATR"] = true_range.ewm(alpha=1/14, adjust=False).mean()

        return data
