---
name: backtesting-engine
description: Best practices, guidelines, and quantitative patterns for building rule-based, deterministic backtesting engines and stock signal generators in Python without LLM dependencies, with specialized support for Indian equities (NSE/BSE).
---

# Backtesting Engine & Stock Signal Generator Skill

This skill provides standards, mathematical definitions, Indian market conventions, and architectural patterns for creating deterministic, non-LLM Python stock analysis and backtesting applications.

---

## 1. Core Principles

1. **Zero LLM Dependency for Signals:** All trading decisions ("Buy", "Sell", "Hold") must derive strictly from deterministic mathematical indicators and rule-based quantitative formulas.
2. **Strict Prevention of Look-Ahead Bias:** Signals generated for time $t$ must only use information available strictly up to time $t$. Indicator calculations must never use future data points or global backward adjustments.
3. **Indian Market Ticker Handling:**
   - National Stock Exchange (NSE) tickers require the `.NS` suffix (e.g., `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`).
   - Bombay Stock Exchange (BSE) tickers require the `.BO` suffix (e.g., `RELIANCE.BO`).
   - Benchmark comparisons should default to Nifty 50 (`^NSEI`) or Sensex (`^BSESN`).
4. **Vectorized Operations:** Leverage `pandas` and `numpy` for fast historical series computation before falling back to event-driven loops.

---

## 2. Signal Definitions & Output Schema

Every trading bar must deterministically evaluate to one of three discrete categorical signals:

* **`Buy`**: Bullish condition triggered (e.g., Fast MA crosses above Slow MA, or RSI recovers above 30 from oversold territory).
* **`Sell`**: Bearish condition triggered (e.g., Fast MA crosses below Slow MA, RSI drops below 70 from overbought territory, or stop-loss/take-profit limit breached).
* **`Hold`**: Neutral state or continuation of existing position with no state-change trigger.

---

## 3. Mathematical Indicator Formulas

### Simple & Exponential Moving Averages (SMA / EMA)
$$\text{SMA}_n(t) = \frac{1}{n} \sum_{i=0}^{n-1} P_{t-i}$$

$$\text{EMA}_n(t) = P_t \cdot \left(\frac{2}{n+1}\right) + \text{EMA}_n(t-1) \cdot \left(1 - \frac{2}{n+1}\right)$$

### Relative Strength Index (RSI - Cutler / Wilder)
$$\text{RSI} = 100 - \left( \frac{100}{1 + \text{RS}} \right), \quad \text{RS} = \frac{\text{EMA}(\text{Gain}, 14)}{\text{EMA}(\text{Loss}, 14)}$$

### Moving Average Convergence Divergence (MACD)
$$\text{MACD Line} = \text{EMA}_{12}(P) - \text{EMA}_{26}(P)$$
$$\text{Signal Line} = \text{EMA}_9(\text{MACD Line})$$
$$\text{MACD Histogram} = \text{MACD Line} - \text{Signal Line}$$

### Bollinger Bands
$$\text{Middle Band} = \text{SMA}_{20}(P)$$
$$\text{Upper Band} = \text{Middle Band} + 2 \cdot \sigma_{20}(P)$$
$$\text{Lower Band} = \text{Middle Band} - 2 \cdot \sigma_{20}(P)$$

---

## 4. Key Performance & Risk Metrics

When backtesting historical performance, compute the following deterministic metrics:

- **Total Return (%):**
  $$\text{Total Return} = \frac{V_{\text{final}} - V_{\text{initial}}}{V_{\text{initial}}} \times 100$$

- **Compound Annual Growth Rate (CAGR):**
  $$\text{CAGR} = \left( \frac{V_{\text{final}}}{V_{\text{initial}}} \right)^{\frac{365}{N_{\text{days}}}} - 1$$

- **Sharpe Ratio (Annualized, $\text{Risk-Free Rate } R_f \approx 6.5\%$ for India):**
  $$\text{Sharpe} = \sqrt{252} \cdot \frac{\mathbb{E}[R_p - R_f/252]}{\sigma_p}$$

- **Maximum Drawdown (MDD):**
  $$\text{MDD} = \max_{t} \left( \frac{\text{Peak}_t - V_t}{\text{Peak}_t} \right)$$

---

## 5. Reference Architecture Pattern

```python
import pandas as pd
import numpy as np
import yfinance as yf

class IndianStockAnalyzer:
    def __init__(self, symbol: str, start_date: str = None, period: str = "1y", initial_capital: float = 100000.0):
        # Automatically append .NS if no exchange suffix is provided
        if not (symbol.upper().endswith(".NS") or symbol.upper().endswith(".BO")):
            self.symbol = f"{symbol.upper()}.NS"
        else:
            self.symbol = symbol.upper()
            
        self.period = period
        self.start_date = start_date
        self.initial_capital = initial_capital
        self.data = None

    def fetch_data(self) -> pd.DataFrame:
        """Fetch historical price data without look-ahead bias."""
        kwargs = {"period": self.period} if not self.start_date else {"start": self.start_date}
        df = yf.download(self.symbol, progress=False, **kwargs)
        if df.empty:
            raise ValueError(f"No data found for symbol: {self.symbol}")
        
        # Flatten MultiIndex columns if returned by newer yfinance versions
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        self.data = df
        return df

    def compute_indicators(self) -> pd.DataFrame:
        """Compute technical indicators deterministically."""
        df = self.data.copy()
        close = df['Close']

        # Moving Averages
        df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
        df['EMA_50'] = close.ewm(span=50, adjust=False).mean()
        df['SMA_200'] = close.rolling(window=200).mean()

        # RSI (14)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        df['MACD'] = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        self.data = df
        return df

    def generate_signals(self) -> pd.DataFrame:
        """Evaluate deterministic rules to produce BUY / SELL / HOLD."""
        df = self.data.copy()
        df['Position'] = 0

        # Bullish: EMA 20 > EMA 50 and RSI between 35 and 70
        bullish = (df['EMA_20'] > df['EMA_50']) & (df['RSI'] > 35) & (df['RSI'] < 70)
        # Bearish: EMA 20 < EMA 50 or RSI > 75 (overbought) or RSI < 30 (breakdown)
        bearish = (df['EMA_20'] < df['EMA_50']) | (df['RSI'] > 75)

        df.loc[bullish, 'Position'] = 1
        df.loc[bearish, 'Position'] = 0

        # Discrete trigger points
        df['Trigger'] = df['Position'].diff()
        df['Signal'] = 'HOLD'
        df.loc[df['Trigger'] == 1, 'Signal'] = 'BUY'
        df.loc[df['Trigger'] == -1, 'Signal'] = 'SELL'

        self.data = df
        return df

    def get_latest_recommendation(self) -> dict:
        """Return the current actionable recommendation."""
        last_row = self.data.iloc[-1]
        return {
            "symbol": self.symbol,
            "date": str(self.data.index[-1].date()),
            "close_price": float(last_row['Close']),
            "signal": last_row['Signal'],
            "rsi": float(last_row['RSI']),
            "ema_20": float(last_row['EMA_20']),
            "ema_50": float(last_row['EMA_50'])
        }
```
