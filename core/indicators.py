import numpy as np
import pandas as pd

def zigzag(data, deviation=5, depth=12, backstep=3):
    """✅ ZigZag Indicator (Support/Resistance)"""
    highs = data['high'].values
    lows = data['low'].values
    zigzag_points = np.full(len(data), np.nan)

    last_high = last_low = None
    for i in range(depth, len(data) - backstep):
        if highs[i] == max(highs[i - depth:i + 1]) and (last_high is None or highs[i] > last_high + deviation):
            last_high = highs[i]
            zigzag_points[i] = last_high

        if lows[i] == min(lows[i - depth:i + 1]) and (last_low is None or lows[i] < last_low - deviation):
            last_low = lows[i]
            zigzag_points[i] = last_low

    return zigzag_points

def sma(data, period=10):
    """✅ Simple Moving Average"""
    return data['close'].rolling(window=period).mean()

def keltner_channel(data, ema_period=20, atr_period=10, multiplier=1):
    """✅ Keltner Channel"""
    ema = data['close'].ewm(span=ema_period).mean()
    atr = data['high'].sub(data['low']).rolling(window=atr_period).mean()
    upper_band = ema + (multiplier * atr)
    lower_band = ema - (multiplier * atr)
    return upper_band, lower_band

def rsi(data, period=14):
    """✅ RSI Indicator"""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
