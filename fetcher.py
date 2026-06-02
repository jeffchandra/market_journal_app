# fetcher.py
# Two jobs: fetch news via Tavily, fetch price data via yfinance
# extract_ticker() uses a keyword map + LLM fallback to find the right symbol

import os
from dotenv import load_dotenv
import yfinance as yf
from tavily import TavilyClient

load_dotenv(override=True)
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

TICKER_MAP = {
    "jpy": "USDJPY=X",
    "japanese yen": "USDJPY=X",
    "eur": "EURUSD=X",
    "euro": "EURUSD=X",
    "spy": "SPY",
    "s&p": "SPY",
    "s&p 500": "SPY",
    "nasdaq": "QQQ",
    "vix": "^VIX",
    "gold": "GC=F",
    "oil": "CL=F",
    "bitcoin": "BTC-USD",
    "btc": "BTC-USD",
    # add more as you encounter them
}

def extract_ticker(event: str) -> str | None:
    for key in TICKER_MAP.keys():
        if key in event.lower():
            return TICKER_MAP[key]
    return None

def fetch_news(event: str) -> str:
    response = tavily.search(query=event, max_results=5)
    snippets = [r["content"] for r in response["results"]]
    return "\n".join(snippets)[:2000]

def fetch_price_summary(ticker: str) -> str:
    if not ticker: return ""
    try:
        ticker_data = yf.Ticker(ticker).history(period="5d")
        summary_lines = [f"OHLC Summary for {ticker} (Last 5 Trading Days):"]    
        for date, row in ticker_data.iterrows():
            line = f"Date: {date.strftime('%Y-%m-%d')} | Open: {row['Open']:.2f} | High: {row['High']:.2f} | Low: {row['Low']:.2f} | Close: {row['Close']:.2f}"
            summary_lines.append(line)
        return "\n".join(summary_lines)
    except Exception as e:
        print(f"yfinance fetch failed for {ticker}: {e}")
        return ""