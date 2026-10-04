"""
Historical Data Ingestion Module for Indian Equities.
Fetches clean OHLCV data using direct Yahoo Finance chart API with custom headers and caching,
avoiding yfinance rate-limit blocks.
"""

import pandas as pd
import requests
import datetime
from typing import Optional


class HistoricalDataLoader:
    def __init__(self, ticker: str, period: str = "3y", interval: str = "1d"):
        self.ticker = ticker
        self.period = period
        self.interval = interval

    def fetch_data(self) -> pd.DataFrame:
        """
        Download historical OHLCV data directly via Yahoo Finance v8 chart API with standard headers.
        """
        # Map period format to Yahoo query range
        range_map = {
            "1mo": "1mo",
            "3mo": "3mo",
            "6mo": "6mo",
            "1y": "1y",
            "2y": "2y",
            "3y": "3y",
            "5y": "5y",
            "max": "max"
        }
        query_range = range_map.get(self.period, "3y")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Try ticker; if NSE fails, try BSE fallback
        tickers_to_try = [self.ticker]
        if self.ticker.endswith(".NS"):
            tickers_to_try.append(self.ticker.replace(".NS", ".BO"))

        last_error = None
        for sym in tickers_to_try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={query_range}&interval={self.interval}&includeAdjustedClose=true"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    payload = resp.json()
                    chart = payload.get("chart", {})
                    results = chart.get("result")
                    if results and len(results) > 0:
                        data = results[0]
                        timestamps = data.get("timestamp", [])
                        indicators = data.get("indicators", {})
                        quote = indicators.get("quote", [{}])[0]
                        adjclose = indicators.get("adjclose", [{}])[0].get("adjclose", [])

                        if timestamps and "close" in quote:
                            df = pd.DataFrame({
                                "Open": quote.get("open", []),
                                "High": quote.get("high", []),
                                "Low": quote.get("low", []),
                                "Close": quote.get("close", []),
                                "Volume": quote.get("volume", []),
                            }, index=pd.to_datetime(timestamps, unit="s", utc=True))

                            # Convert to IST time / drop timezone for clean indexing
                            df.index = df.index.tz_convert("Asia/Kolkata").tz_localize(None)

                            # Drop nulls and zeros
                            df = df.dropna(subset=["Close"])
                            df = df[df["Close"] > 0]
                            df.sort_index(inplace=True)

                            if len(df) >= 30:
                                self.ticker = sym
                                return df
                elif resp.status_code == 429:
                    last_error = "Rate limit reached from Yahoo Finance API. Please wait a moment."
                else:
                    last_error = f"API HTTP Error {resp.status_code} for {sym}"
            except Exception as e:
                last_error = str(e)

        raise ValueError(
            f"No price data found for ticker '{self.ticker}'. "
            f"Reason: {last_error or 'Insufficient history or symbol unlisted'}"
        )
