"""
Fundamental Valuation Module for Indian Equities.
Fetches Current P/E (TTM), Forward P/E, Sector, Industry, and historical average P/E context
using direct authenticated Yahoo Finance quoteSummary session.
"""

import requests
from typing import Dict, Any, Optional

# Benchmark Indian Sector / Industry Average P/E Ratios (NSE / Nifty Sectors)
SECTOR_PE_BENCHMARKS = {
    "Energy": 12.5,
    "Oil & Gas Refining & Marketing": 9.5,
    "Oil & Gas Integrated": 14.0,
    "Financial Services": 18.0,
    "Banks - Diversified": 16.5,
    "Banks - Regional": 12.0,
    "Information Technology": 27.5,
    "Software - IT Services": 28.0,
    "Consumer Defensive": 52.0,
    "Packaged Foods": 55.0,
    "Household & Personal Products": 58.0,
    "Auto Manufacturers": 24.0,
    "Consumer Cyclical": 32.0,
    "Healthcare": 34.0,
    "Drug Manufacturers - Specialty & Generic": 31.0,
    "Basic Materials": 16.0,
    "Steel": 12.0,
    "Industrials": 35.0,
    "Utilities": 17.0,
    "Communication Services": 30.0,
    "Real Estate": 38.0,
}

# Historical 5-Year Average P/E estimates for popular Indian market leaders
HISTORICAL_AVG_PE_MAP = {
    "IOC.NS": 7.8,
    "RELIANCE.NS": 26.5,
    "TCS.NS": 30.2,
    "INFY.NS": 26.8,
    "HDFCBANK.NS": 21.0,
    "ICICIBANK.NS": 19.5,
    "SBIN.NS": 11.2,
    "BHARTIARTL.NS": 42.0,
    "ITC.NS": 24.5,
    "TATAMOTORS.NS": 18.0,
    "TATASTEEL.NS": 10.5,
    "WIPRO.NS": 20.5,
    "MARUTI.NS": 28.0,
    "LT.NS": 32.0,
    "AXISBANK.NS": 15.0,
    "BAJFINANCE.NS": 38.0,
    "HINDUNILVR.NS": 58.0,
}


class FundamentalValuationLoader:
    def __init__(self, ticker: str):
        self.ticker = ticker

    def fetch_valuation(self) -> Dict[str, Any]:
        """
        Fetches live valuation metrics (Trailing P/E, Forward P/E, EPS, Sector)
        via authenticated session with crumb support.
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        }

        trailing_pe: Optional[float] = None
        forward_pe: Optional[float] = None
        trailing_eps: Optional[float] = None
        sector: str = "Unknown"
        industry: str = "Unknown"
        price_to_book: Optional[float] = None

        try:
            sess = requests.Session()
            sess.headers.update(headers)
            sess.get("https://fc.yahoo.com", timeout=10)
            crumb_resp = sess.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=10)
            crumb = crumb_resp.text.strip()

            if crumb and not crumb.startswith("<"):
                url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{self.ticker}?modules=summaryDetail,defaultKeyStatistics,assetProfile&crumb={crumb}"
                resp = sess.get(url, timeout=12)
                if resp.status_code == 200:
                    data = resp.json().get("quoteSummary", {}).get("result", [{}])[0]
                    sd = data.get("summaryDetail", {})
                    ap = data.get("assetProfile", {})
                    ks = data.get("defaultKeyStatistics", {})

                    if "trailingPE" in sd and isinstance(sd["trailingPE"], dict):
                        trailing_pe = sd["trailingPE"].get("raw")
                    if "forwardPE" in sd and isinstance(sd["forwardPE"], dict):
                        forward_pe = sd["forwardPE"].get("raw")
                    if "trailingEps" in ks and isinstance(ks["trailingEps"], dict):
                        trailing_eps = ks["trailingEps"].get("raw")
                    if "priceToBook" in sd and isinstance(sd["priceToBook"], dict):
                        price_to_book = sd["priceToBook"].get("raw")

                    sector = ap.get("sector", "Diversified")
                    industry = ap.get("industry", "Indian Equities")
        except Exception:
            pass

        # Lookup Benchmark Sector P/E
        sector_pe = SECTOR_PE_BENCHMARKS.get(
            industry,
            SECTOR_PE_BENCHMARKS.get(sector, 22.0)
        )

        # Lookup 5-Year Historical Average P/E
        hist_pe = HISTORICAL_AVG_PE_MAP.get(self.ticker)
        if hist_pe is None and trailing_pe is not None:
            # Heuristic default if unlisted in map: slightly higher or lower based on sector
            hist_pe = round((trailing_pe + sector_pe) / 2.0, 1)

        # Determine Valuation Category
        status = "Fairly Valued"
        color = "yellow"
        if trailing_pe is not None:
            comparison_base = hist_pe if hist_pe else sector_pe
            discount_pct = ((trailing_pe - comparison_base) / comparison_base) * 100.0

            if discount_pct <= -20.0:
                status = f"Undervalued / Attractive ({abs(discount_pct):.0f}% below benchmark)"
                color = "green"
            elif discount_pct >= 25.0:
                status = f"Expensive / Overvalued (+{discount_pct:.0f}% above benchmark)"
                color = "red"
            else:
                status = f"Fairly Valued (Near historical/sector norm)"
                color = "yellow"
        else:
            status = "P/E Data Unavailable (Loss-making or financial firm)"

        return {
            "trailing_pe": trailing_pe,
            "forward_pe": forward_pe,
            "trailing_eps": trailing_eps,
            "price_to_book": price_to_book,
            "sector": sector,
            "industry": industry,
            "sector_pe": sector_pe,
            "historical_avg_pe": hist_pe,
            "valuation_status": status,
            "valuation_color": color
        }
