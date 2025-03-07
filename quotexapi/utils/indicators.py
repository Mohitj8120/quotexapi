import numpy as np
from typing import List, Dict


class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calculates the Relative Strength Index (RSI)."""
        if len(prices) < period + 1:
            return []

        deltas = np.diff(prices)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.concatenate(([np.mean(gain[:period])], gain[period:]))
        avg_loss = np.concatenate(([np.mean(loss[:period])], loss[period:]))

        for i in range(1, len(avg_gain)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[period + i - 1]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[period + i - 1]) / period

        rs = avg_gain / np.where(avg_loss == 0, 0.00001, avg_loss)
        rsi = 100 - (100 / (1 + rs))
        return [round(x, 2) for x in rsi.tolist()]

    @staticmethod
    def calculate_keltner_channel(prices: List[float], highs: List[float], lows: List[float], ema_period: int = 20, atr_period: int = 10, multiplier: float = 1) -> Dict[str, List[float]]:
        """Calculates the Keltner Channel."""
        if len(prices) < ema_period or len(highs) < atr_period or len(lows) < atr_period:
            return {"upper": [], "middle": [], "lower": []}

        ema = TechnicalIndicators.calculate_ema(prices, ema_period)
        atr = TechnicalIndicators.calculate_atr(highs, lows, prices, atr_period)

        upper_band = [ema[i] + (atr[i] * multiplier) for i in range(len(ema))]
        lower_band = [ema[i] - (atr[i] * multiplier) for i in range(len(ema))]

        return {
            "upper": [round(x, 2) for x in upper_band],
            "middle": [round(x, 2) for x in ema],
            "lower": [round(x, 2) for x in lower_band],
            "current": {
                "upper": upper_band[-1] if upper_band else None,
                "middle": ema[-1] if ema else None,
                "lower": lower_band[-1] if lower_band else None
            }
        }

    @staticmethod
    def calculate_moving_average(prices: List[float], period: int, ma_type: str = "SMA") -> List[float]:
        """Calculates the Moving Average."""
        if len(prices) < period:
            return []

        if ma_type == "SMA":
            return TechnicalIndicators.calculate_sma(prices, period)
        else:
            raise ValueError(f"Unsupported moving average type: {ma_type}")

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """Calculates the Simple Moving Average (SMA)."""
        if len(prices) < period:
            return []

        sma_values = []
        for i in range(len(prices) - period + 1):
            sma = sum(prices[i:(i + period)]) / period
            sma_values.append(round(sma, 2))
        return sma_values

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """Calculates the Exponential Moving Average (EMA)."""
        if len(prices) < period:
            return []

        multiplier = 2 / (period + 1)
        ema_values = [sum(prices[:period]) / period]

        for price in prices[period:]:
            ema = (price * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(round(ema, 2))
        return ema_values

    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 10) -> List[float]:
        """Calculates the Average True Range (ATR)."""
        if len(highs) < period:
            return []

        true_ranges = []
        for i in range(1, len(highs)):
            high = highs[i]
            low = lows[i]
            prev_close = closes[i - 1]

            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)

        atr_values = [sum(true_ranges[:period]) / period]

        for i in range(period, len(true_ranges)):
            atr = (atr_values[-1] * (period - 1) + true_ranges[i]) / period
            atr_values.append(round(atr, 2))

        return atr_values