"""
Ticker resolution module for Indian Equities (NSE/BSE).
Handles common corporate names, ticker cleanups, and automatic suffixing.
"""

from typing import Tuple

# Common name to NSE symbol mapping for Indian equities
INDIAN_TICKER_MAP = {
    "RELIANCE": "RELIANCE.NS",
    "RELIANCE INDUSTRIES": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "TATA CONSULTANCY SERVICES": "TCS.NS",
    "HDFC": "HDFCBANK.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS",
    "INFOSYS": "INFY.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "STATE BANK OF INDIA": "SBIN.NS",
    "SBI": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "BHARTI AIRTEL": "BHARTIARTL.NS",
    "AIRTEL": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "KOTAK MAHINDRA BANK": "KOTAKBANK.NS",
    "LT": "LT.NS",
    "LARSEN & TOUBRO": "LT.NS",
    "L&T": "LT.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "HINDUSTAN UNILEVER": "HINDUNILVR.NS",
    "AXISBANK": "AXISBANK.NS",
    "AXIS BANK": "AXISBANK.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "BAJAJ FINANCE": "BAJFINANCE.NS",
    "MARUTI": "MARUTI.NS",
    "MARUTI SUZUKI": "MARUTI.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "TATA MOTORS": "TATAMOTORS.NS",
    "TATASTEEL": "TATASTEEL.NS",
    "TATA STEEL": "TATASTEEL.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "SUN PHARMA": "SUNPHARMA.NS",
    "WIPRO": "WIPRO.NS",
    "NIFTY": "^NSEI",
    "NIFTY 50": "^NSEI",
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
}


def resolve_indian_ticker(query: str, default_exchange: str = "NS") -> Tuple[str, str]:
    """
    Resolve an input string (symbol or company name) to a valid Yahoo Finance ticker.
    
    Returns:
        (resolved_ticker, display_name)
    """
    clean_query = query.strip()
    upper_query = clean_query.upper()

    # Direct match in map
    if upper_query in INDIAN_TICKER_MAP:
        return INDIAN_TICKER_MAP[upper_query], clean_query

    # If user explicitly supplied suffix (.NS or .BO) or index prefix (^)
    if upper_query.endswith(".NS") or upper_query.endswith(".BO") or upper_query.startswith("^"):
        return upper_query, clean_query

    # Default to appending exchange suffix (.NS or .BO)
    exchange = default_exchange.upper().replace(".", "")
    if exchange not in ["NS", "BO"]:
        exchange = "NS"
        
    resolved = f"{upper_query}.{exchange}"
    return resolved, clean_query
