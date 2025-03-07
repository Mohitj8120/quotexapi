# app.py

import os
import sys
import json
import time
import random
import asyncio
import pyfiglet
import logging
import requests
from pathlib import Path
from quotexapi.expiration import (
    timestamp_to_date,
    get_timestamp_days_ago,
    get_expiration_time_quotex
)
from quotexapi.config import credentials
from quotexapi.stable_api import Quotex
from quotexapi.utils.processor import process_candles, get_color
from quotexapi.utils.indicators import TechnicalIndicators  # Add this line to import TechnicalIndicators

__author__ = "Cleiton Leonel Creton"
__version__ = "1.0.0"

__message__ = f"""
Use in moderation, because management is everything!
Support: cleiton.leonel@gmail.com or +55 (27) 9 9577-2291
"""

USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

custom_font = pyfiglet.Figlet(font="ansi_shadow")
ascii_art = custom_font.renderText("PyQuotex")
art_effect = f"""{ascii_art}

        author: {__author__} versão: {__version__}
        {__message__}
"""

print(art_effect)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



# After the first access, the user's credentials will be available in this function.
email, password = credentials()

client = Quotex(
    email=email,
    password=password,
    lang="pt",  # Default pt -> Português.
)

# Telegram bot setup
TELEGRAM_BOT_TOKEN = 
TELEGRAM_CHAT_ID = 

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

async def connect(attempts=5):
    check, reason = await client.connect()
    if not check:
        attempt = 0
        while attempt <= attempts:
            if not await client.check_connect():
                check, reason = await client.connect()
                if check:
                    logger.debug("Reconnected successfully!!!")
                    break
                else:
                    logger.debug("Error when reconnecting.")
                    attempt += 1
                    if Path(os.path.join(".", "session.json")).is_file():
                        Path(os.path.join(".", "session.json")).unlink()
                    logger.debug(f"Reconnecting, attempt {attempt} de {attempts}")
            elif not check:
                attempt += 1
            else:
                break

            await asyncio.sleep(5)

        return check, reason

    logger.debug(reason)
    send_telegram_message("Bot connected successfully")
    return check, reason

async def monitor_otc_pairs():
    logger.debug("Starting to monitor OTC pairs...")
    check_connect, message = await client.connect()
    if check_connect:
        codes_asset = await client.get_all_assets()
        otc_assets = [asset for asset in codes_asset.keys() if "otc" in asset]

        async def monitor_asset(asset):
            while True:
                logger.debug(f"Fetching candles for {asset}...")
                candles = await client.get_candles(asset, time.time(), 60, 60)
                if candles:
                    prices = [float(candle["close"]) for candle in candles]
                    highs = [float(candle["high"]) for candle in candles]
                    lows = [float(candle["low"]) for candle in candles]

                    indicators = TechnicalIndicators()
                    sma = indicators.calculate_sma(prices, 10)
                    keltner = indicators.calculate_keltner_channel(prices, highs, lows, 20, 10, 1)
                    rsi = indicators.calculate_rsi(prices, 14)

                    if len(sma) > 0 and len(keltner["middle"]) > 0 and len(rsi) > 0:
                        last_price = prices[-1]
                        last_sma = sma[-1]
                        last_keltner_upper = keltner["upper"][-1]
                        last_keltner_middle = keltner["middle"][-1]
                        last_keltner_lower = keltner["lower"][-1]
                        last_rsi = rsi[-1]

                        # Buy signal
                        if last_price > last_sma and (last_price > last_keltner_upper or last_price > last_keltner_middle or last_price > last_keltner_lower) and last_rsi >= 70:
                            logger.debug(f"Buy signal for {asset} at {last_price}")
                            send_telegram_message(f"Buy signal for {asset} at {last_price}")

                        # Sell signal
                        if last_price < last_sma and (last_price < last_keltner_upper or last_price < last_keltner_middle or last_price < last_keltner_lower) and last_rsi <= 30:
                            logger.debug(f"Sell signal for {asset} at {last_price}")
                            send_telegram_message(f"Sell signal for {asset} at {last_price}")

                await asyncio.sleep(1)

        tasks = [monitor_asset(asset) for asset in otc_assets]
        await asyncio.gather(*tasks)

    logger.debug("Exiting...")

    client.close()

async def trade_asset(asset):
    check_connect, message = await client.connect()
    if check_connect:
        client.set_account_mode("PRACTICE")  # Ensure the trade is in the demo account
        amount = 1.0  # Amount to trade
        direction = "call"  # Buy direction
        duration = 60  # 1-minute time frame
        expiration_time = get_expiration_time_quotex(duration)  # Set future expiration timestamp
        max_retries = 5  # Maximum number of retries
        retry_delay = 2  # Delay between retries in seconds

        for attempt in range(max_retries):
            status, result = await client.buy(amount, "USDINR_otc", direction, expiration_time)
            if status:
                send_telegram_message(f"Trade executed for USD/INR (OTC): {result}")
                break
            elif isinstance(result, dict) and result.get("error") == "expiration":
                logger.debug(f"Trade failed due to expiration error. Retrying... ({attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                send_telegram_message(f"Trade failed for USD/INR (OTC): {result}")
                break
        else:
            send_telegram_message(f"Trade failed for USD/INR (OTC) after {max_retries} attempts due to expiration error.")
    client.close()

async def get_balance():
    check_connect, message = await client.connect()
    if check_connect:
        balance = await client.get_balance()
        print(f"Current balance: {balance}")
        send_telegram_message(f"Current balance: {balance}")
    client.close()

async def get_profile():
    check_connect, message = await client.connect()
    if check_connect:
        profile = await client.get_profile()
        print(f"Profile: {profile.__dict__}")
        send_telegram_message(f"Profile: {profile.__dict__}")
    client.close()

def get_all_options():
    return ["monitor_otc_pairs", "get_balance", "get_profile", "help", "trade"]

async def execute(argument):
    if argument.startswith("trade_"):
        asset = "USDINR_otc"  # Always trade USD/INR (OTC)
        return await trade_asset(asset)
    match argument:
        case "monitor_otc_pairs":
            return await monitor_otc_pairs()
        case "get_balance":
            return await get_balance()
        case "get_profile":
            return await get_profile()
        case "help":
            print(f"Use: {'./app' if getattr(sys, 'frozen', False) else 'python app.py'} <option>")
            return print(get_all_options())
        case _:
            return print("Invalid option. Use 'help' to get a list of options.")

async def main():
    if len(sys.argv) != 2:
        return

    option = sys.argv[1]
    await execute(option)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.debug("Closing at program.")
    finally:
        loop.close()
