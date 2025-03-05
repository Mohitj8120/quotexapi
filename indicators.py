# indicators.py (Indicators Calculation)
import numpy as np
import pandas as pd
import asyncio

async def fetch_candles(client, asset, period=1, count=20):
    """Fetch recent candle data for an asset."""
    end_time = int(pd.Timestamp.utcnow().timestamp())
    candles = await client.get_candles(asset, end_time, count * period, period)
    return pd.DataFrame(candles)

def calculate_sma(data, period=10):
    """Calculate Simple Moving Average (SMA)."""
    return data["close"].rolling(window=period).mean()

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index (RSI)."""
    delta = data["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_keltner_channel(data, ema_period=20, atr_period=10, multiplier=1):
    """Calculate Keltner Channel (Upper, Middle, Lower)."""
    ema = data["close"].ewm(span=ema_period).mean()
    atr = data["high"] - data["low"]
    atr = atr.rolling(window=atr_period).mean()
    upper = ema + (multiplier * atr)
    lower = ema - (multiplier * atr)
    return upper, ema, lower

async def check_trade_signal(client, asset):
    """Check if a buy/sell signal is present."""
    df = await fetch_candles(client, asset)
    if df.empty:
        return None

    df["SMA"] = calculate_sma(df)
    df["RSI"] = calculate_rsi(df)
    df["Keltner_Upper"], df["Keltner_Mid"], df["Keltner_Lower"] = calculate_keltner_channel(df)

    last_row = df.iloc[-1]

    # Buy Condition
    if (
        last_row["close"] > last_row["SMA"] and
        (last_row["close"] > last_row["Keltner_Upper"] or last_row["close"] > last_row["Keltner_Mid"]) and
        last_row["RSI"] >= 70
    ):
        return "BUY", last_row["RSI"]

    # Sell Condition
    if (
        last_row["close"] < last_row["SMA"] and
        (last_row["close"] < last_row["Keltner_Lower"] or last_row["close"] < last_row["Keltner_Mid"]) and
        last_row["RSI"] <= 30
    ):
        return "SELL", last_row["RSI"]

    return None