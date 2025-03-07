import numpy as np
import pandas as pd
from typing import List, Dict, Union, Tuple


class TechnicalIndicators:
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """Calcula la Media Móvil Simple (SMA)"""
        if len(prices) < period:
            return []

        sma = np.convolve(prices, np.ones(period) / period, mode='valid')
        return np.concatenate((np.array([None] * (len(prices) - len(sma))), sma)).tolist()

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calcula el Índice de Fuerza Relativa (RSI)"""
        if len(prices) < period:
            return []

        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.zeros_like(prices)
        avg_loss = np.zeros_like(prices)

        avg_gain[period] = np.mean(gain[:period])
        avg_loss[period] = np.mean(loss[:period])

        for i in range(period + 1, len(prices)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i - 1]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i - 1]) / period

        rs = np.where(avg_loss == 0, 100, avg_gain / (avg_loss + 1e-10))
        rsi = 100 - (100 / (1 + rs))

        return np.concatenate((np.array([None] * period), rsi[period:])).tolist()

    @staticmethod
    def calculate_keltner_channel(prices: List[float], ema_period: int = 20, atr_period: int = 10, multiplier: int = 1) -> Dict[str, List[float]]:
        """Calcula el Keltner Channel (Middle, Upper, Lower)"""
        if len(prices) < max(ema_period, atr_period):
            return {"middle": [], "upper": [], "lower": []}

        df = pd.DataFrame({"close": prices})
        
        df["ema"] = df["close"].ewm(span=ema_period, adjust=False).mean()

        df["prev_close"] = df["close"].shift(1)
        df["tr"] = np.maximum(df["close"] - df["prev_close"], np.abs(df["prev_close"] - df["close"]))

        df["atr"] = df["tr"].rolling(atr_period).mean()
        
        df["upper"] = df["ema"] + (multiplier * df["atr"])
        df["lower"] = df["ema"] - (multiplier * df["atr"])

        return {
            "middle": df["ema"].values.tolist(),
            "upper": df["upper"].values.tolist(),
            "lower": df["lower"].values.tolist()
        }