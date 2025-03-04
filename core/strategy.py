from core.indicators import sma, keltner_channel, rsi, zigzag
import datetime

def check_signal(data, asset):
    """✅ Final Strategy with ZigZag, SMA, Keltner, RSI + Timestamp"""
    sma_line = sma(data)
    upper_keltner, lower_keltner = keltner_channel(data)
    rsi_value = rsi(data)
    zigzag_points = zigzag(data)

    last_close = data['close'].iloc[-1]
    prev_close = data['close'].iloc[-2]
    last_zigzag = zigzag_points[-1]

    is_resistance = last_zigzag and last_close >= last_zigzag
    is_support = last_zigzag and last_close <= last_zigzag

    # ✅ Current UTC Time
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    # ✅ Buy Signal Condition
    if (prev_close < sma_line.iloc[-2] and last_close > sma_line.iloc[-1]) and \
       (prev_close < upper_keltner.iloc[-2] and last_close > upper_keltner.iloc[-1]) and \
       (rsi_value.iloc[-1] > 70) and is_support:
        return f"BUY SIGNAL on {asset} at {timestamp}"

    # ✅ Sell Signal Condition
    if (prev_close > sma_line.iloc[-2] and last_close < sma_line.iloc[-1]) and \
       (prev_close > lower_keltner.iloc[-2] and last_close < lower_keltner.iloc[-1]) and \
       (rsi_value.iloc[-1] < 30) and is_resistance:
        return f"SELL SIGNAL on {asset} at {timestamp}"

    return None
