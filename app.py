# app.py

import os
import sys
import json
import time
import random
import asyncio
import pyfiglet
import requests
from datetime import datetime, timezone, timedelta
from quotexapi.utils.indicators import TechnicalIndicators  # Corrected import statement
from pathlib import Path
from quotexapi.expiration import (
    timestamp_to_date,
    get_timestamp_days_ago
)
from quotexapi.config import credentials
from quotexapi.stable_api import Quotex
from quotexapi.utils.processor import process_candles, get_color

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

# After the first access, the user's credentials will be available in this function.
email, password = credentials()

client = Quotex(
    email=email,
    password=password,
    lang="pt",  # Default pt -> Português.
)


# client.debug_ws_enable = True


def get_all_options():
    return """Available options:
    - test_connection
    - get_profile
    - get_balance
    - get_signal_data
    - trade_and_monitor
    - get_payment
    - get_payout
    - get_payout_by_asset
    - get_candle
    - get_candle_v2
    - get_candle_progressive
    - get_realtime_candle
    - get_candles_all_asset
    - get_realtime_sentiment
    - get_realtime_price
    - assets_open
    - get_all_assets
    - buy_simple
    - buy_and_check_win
    - buy_multiple
    - buy_pending
    - balance_refill
    - help
    """


async def connect(attempts=5):
    check, reason = await client.connect()
    if not check:
        attempt = 0
        while attempt <= attempts:
            if not await client.check_connect():
                check, reason = await client.connect()
                if check:
                    print("Reconnected successfully!!!")
                    break
                else:
                    print("Error when reconnecting.")
                    attempt += 1
                    if Path(os.path.join(".", "session.json")).is_file():
                        Path(os.path.join(".", "session.json")).unlink()
                    print(f"Reconnecting, attempt {attempt} de {attempts}")
            elif not check:
                attempt += 1
            else:
                break

            await asyncio.sleep(5)

        return check, reason

    print(reason)

    return check, reason


async def test_connection():
    check_connect, message = await client.connect()
    is_connected = await client.check_connect()
    if not is_connected:
        check_connect, message = await client.connect()
        if check_connect:
            print(f"Reconnected successfully!!!")
        else:
            print("Error when reconnecting.")
    else:
        print(f"Connected: {is_connected}")

    print("Exiting...")

    client.close()


async def get_balance():
    check_connect, message = await client.connect()
    if check_connect:
        client.change_account("PRACTICE")
        print("Current Balance: ", await client.get_balance())

    print("Exiting...")

    client.close()


async def buy_simple():
    check_connect, message = await client.connect()
    if check_connect:
        client.change_account("PRACTICE")
        amount = 50
        asset = "BRLUSD_otc"  # "EURUSD_otc"
        direction = "call"
        duration = 180  # in seconds
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        print(asset_name, asset_data)
        if asset_data[2]:
            print("OK: Asset is open.")
            status, buy_info = await client.buy(amount, asset_name, direction, duration, time_mode="TIME")
            print(status, buy_info)
        else:
            print("ERRO: Asset is closed.")

        print("Current Balance: ", await client.get_balance())

    print("Exiting...")

    client.close()


async def get_result():
    check_connect, reason = await client.connect()
    if check_connect:
        status, operation_info = await client.get_result('3ca7d99f-744e-4d5b-9780-27e50575290d')
        print(status, operation_info)
    print("Exiting...")

    client.close()


async def get_profile():
    check_connect, message = await client.connect()
    if check_connect:
        client.change_account("REAL")
        client.set_account_mode("PRACTICE")
        profile = await client.get_profile()
        description = (
            f"\nUser: {profile.nick_name}\n"
            f"Demo Balance: {profile.demo_balance}\n"
            f"Real Balance: {profile.live_balance}\n"
            f"ID: {profile.profile_id}\n"
            f"Avatar: {profile.avatar}\n"
            f"Country: {profile.country_name}\n"
            f"Timezone: {profile.offset}"
        )
        print(description)

    print("Exiting...")

    client.close()


async def balance_refill():
    check_connect, message = await client.connect()
    if check_connect:
        # client.change_account("REAL")
        result = await client.edit_practice_balance(5000)

        print(result)

    client.close()


async def buy_and_check_win():
    check_connect, message = await client.connect()
    if check_connect:
        # client.change_account("REAL")
        print("Current Balance: ", await client.get_balance())
        amount = 50
        asset = "EURUSD_otc"  # "EURUSD_otc"
        direction = "put"
        duration = 60  # in seconds
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        print(asset_name, asset_data)
        if asset_data[2]:
            print("OK: Asset is open.")
            status, buy_info = await client.buy(amount, asset_name, direction, duration)
            print(status, buy_info)
            if status:
                print("Waiting for result...")
                if await client.check_win(buy_info["id"]):
                    print(f"\nWin!!! \nWe won, buddy!!!\nProfit: R$ {client.get_profit()}")
                else:
                    print(f"\nLoss!!! \nWe lost, buddy!!!\nLoss: R$ {client.get_profit()}")
            else:
                print("Operation failed!!!")
        else:
            print("ERRO: Asset is closed.")

        print("Current Balance: ", await client.get_balance())

    print("Exiting...")

    client.close()


async def trade_and_monitor():
    # Attempt to connect to the client
    check_connect, message = await client.connect()
    if check_connect:
        # Define trade parameters
        amount = 50
        asset = "AUDCAD_otc"
        direction = "call"
        duration = 60  # in seconds

        # Check if the asset is available for trading
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        print(asset_name, asset_data)

        if asset_data[2]:  # If the asset is open for trading
            print("OK: Asset is open.")
            try:
                # Calculate the expiration time for the trade in UTC
                expiration_time = datetime.utcnow() + timedelta(seconds=duration)
                print(f"Expiration Time (UTC): {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}")

                # Attempt to execute the trade using UTC time
                status, buy_info = await client.buy(amount, asset_name, direction, duration, time_mode="TIME")
                if status:
                    # If the trade was successful, get the open price and close timestamp
                    open_price = buy_info.get('openPrice')
                    close_timestamp = buy_info.get('closeTimestamp')
                    print("Open Price:", open_price)

                    # Wait for the duration of the trade
                    await asyncio.sleep(duration)

                    # Start monitoring the real-time price of the asset
                    client.start_realtime_price(asset, 60)

                    # Get the real-time prices of the asset
                    prices = await client.get_realtime_price(asset_name)

                    if prices:
                        # Get the current price and timestamp
                        current_price = prices[-1]['price']
                        current_timestamp = prices[-1]['time']
                        print(f"Current Time: {int(current_timestamp)}, Close Time: {close_timestamp}")
                        print(f"Current Price: {current_price}, Open Price: {open_price}")

                        # Determine the result of the trade
                        if (direction == "call" and current_price > open_price) or (
                                direction == "put" and current_price < open_price):
                            print("Result: WIN")
                            return 'Win'
                        elif (direction == "call" and current_price <= open_price) or (
                                direction == "put" and current_price >= open_price):
                            print("Result: LOSS")
                            return 'Loss'
                        else:
                            print("Result: DOJI")
                            return 'Doji'
                    else:
                        print("Not a price direction.")
                else:
                    print("Operation failed!!!")
                    print("Buy Info:", buy_info)
            except Exception as e:
                print(f"An error occurred during the trade: {e}")
        else:
            print("ERRO: Asset is closed.")

    else:
        print("Unable to connect to client.")

    print("Exiting...")

    client.close()


async def buy_multiple(orders=10):
    order_list = [
        {"amount": 5, "asset": "EURUSD", "direction": "call", "duration": 60},
        {"amount": 10, "asset": "AUDCAD_otc", "direction": "put", "duration": 60},
        {"amount": 15, "asset": "AUDJPY_otc", "direction": "call", "duration": 60},
        {"amount": 20, "asset": "AUDUSD_otc", "direction": "put", "duration": 60},
        {"amount": 25, "asset": "CADJPY", "direction": "call", "duration": 60},
        {"amount": 30, "asset": "EURCHF_otc", "direction": "put", "duration": 60},
        {"amount": 35, "asset": "EURGBP_otc", "direction": "call", "duration": 60},
        {"amount": 40, "asset": "EURJPY", "direction": "put", "duration": 60},
        {"amount": 45, "asset": "GBPAUD_otc", "direction": "call", "duration": 60},
        {"amount": 50, "asset": "GBPJPY_otc", "direction": "put", "duration": 60},
    ]
    check_connect, message = await client.connect()
    for i in range(0, orders):
        print("\n/", 80 * "=", "/", end="\n")
        print(f"OPEND ORDER: {i + 1}")
        order = random.choice(order_list)
        print(order)
        if check_connect:
            # client.change_account("REAL")
            asset_name, asset_data = await client.get_available_asset(order['asset'], force_open=True)
            print(asset_name, asset_data)
            if asset_data[2]:
                print("OK: Asset is open.")
                status, buy_info = await client.buy(**order)
                print(status, buy_info)
            else:
                print("ERRO: Asset is closed.")
            print("Current Balance: ", await client.get_balance())
            await asyncio.sleep(2)

    print("\n/", 80 * "=", "/", end="\n")

    print("Exiting...")

    client.close()


async def buy_pending():
    check_connect, message = await client.connect()
    if check_connect:
        # client.change_account("REAL")
        amount = 50
        asset = "AUDCAD"  # "EURUSD_otc"
        direction = "call"
        duration = 60  # in seconds

        # Format d/m h:m
        open_time = "17/12 22:23" # If None, then this will be set to the equivalent of one minute in duration

        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        print(asset_name, asset_data)
        if asset_data[2]:
            print("OK: Asset is open.")
            status, buy_info = await client.open_pending(amount, asset_name, direction, duration, open_time)
            print(status, buy_info)
        else:
            print("ERRO: Asset is closed.")

        print("Current Balance: ", await client.get_balance())

    print("Exiting...")

    client.close()


async def sell_option():
    check_connect, message = await client.connect()
    if check_connect:
        # client.change_account("REAL")
        amount = 30
        asset = "EURUSD_otc"  # "EURUSD_otc"
        direction = "put"
        duration = 1000  # in seconds
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        print(asset_name, asset_data)
        if asset_data[2]:
            print("OK: Asset is open.")
            status, buy_info = await client.buy(amount, asset_name, direction, duration)
            print(status, buy_info)
            await client.sell_option(buy_info["id"])

        print("Current Balance: ", await client.get_balance())

    print("Exiting...")

    client.close()


def asset_parse(asset: str):
    new_asset = f"{asset[:3]}/{asset[3:]}"
    if "_otc" in asset:
        return new_asset.replace("_otc", " (OTC)")

    return new_asset


async def assets_open():
    check_connect, reason = await client.connect()
    if check_connect:
        print("Asset Open")
        for i in client.get_all_asset_name():
            print(i[1])
            print(i[1], await client.check_asset_open(i[0]))

    print("Exiting...")

    client.close()


async def get_all_assets():
    """
    Continuously fetches and prints all asset.

    This function connects to the client, checks if the asset.
    It waits for a specified interval between requests.
    """
    check_connect, message = await client.connect()
    if check_connect:
        codes_asset = await client.get_all_assets()
        print(codes_asset)


async def get_candle():
    candles_color = []
    check_connect, message = await client.connect()
    if check_connect:
        asset = "CHFJPY_otc"
        offset = 3600  # in seconds
        period = 60  # in seconds [5, 10, 15, 30, 60, 120, 180, 240, 300, 600, 900, 1800, 3600, 14400, 86400]
        end_from_time = time.time()
        candles = await client.get_candles(asset, end_from_time, offset, period)
        candles_data = candles
        if len(candles_data) > 0:

            if not candles_data[0].get("open"):
                candles = process_candles(candles_data, period)
                candles_data = candles

            print(asset, candles_data[-1])

            for candle in candles_data:
                color = get_color(candle)
                candles_color.append(color)

            # print(candles)
            # print(candles_color if len(candles_color) > 0 else "")
        else:
            print("No candles.")

    print("Exiting...")

    client.close()


async def get_candle_progressive():
    check_connect, reason = await client.connect()
    if check_connect:
        asset = "EURUSD_otc"
        offset = 3600  # in seconds
        period = 60  # in seconds [5, 10, 15, 30, 60, 120, 180, 240, 300, 600, 900, 1800, 3600, 14400, 86400]
        days_of_candle = 1
        list_candles = []
        size = days_of_candle * 24
        timestamp = get_timestamp_days_ago(days_of_candle)
        end_from_time = (int(timestamp) - int(timestamp) % period) + offset
        epoch_candle = timestamp_to_date(end_from_time)
        print(f"Searching for historical data from {epoch_candle} to now...")
        for i in range(size):
            epoch_candle = timestamp_to_date(end_from_time)
            # print(epoch_candle)
            candles = await client.get_candles(asset, end_from_time, offset, period, progressive=True)
            if candles:
                list_candles += candles
            if i >= size:
                offset *= 2
            end_from_time = end_from_time + offset

        lista_limpa = list({frozenset(d.items()): d for d in list_candles}.values())
        print(lista_limpa, len(lista_limpa))

    print("Exiting...")

    client.close()


async def get_payout():
    check_connect, reason = await client.connect()
    if check_connect:
        asset_data = await client.check_asset_open("EURUSD_otc")
        print(asset_data)

    print("Exiting...")

    client.close()


# Function suggested by https://t.me/Suppor_Mk in the message https://t.me/c/2215782682/1/2990
async def get_payout_by_asset():
    check_connect, reason = await client.connect()
    if check_connect:
        asset_data = client.get_payout_by_asset("AUDCAD_otc")
        print(asset_data)

    print("Exiting...")

    client.close()


async def get_payment():
    check_connect, message = await client.connect()
    if check_connect:
        all_data = client.get_payment()
        for asset_name in all_data:
            asset_data = all_data[asset_name]
            profit = f'\nProfit 1+ : {asset_data["profit"]["1M"]} | Profit 5+ : {asset_data["profit"]["5M"]}'
            status = " ==> Opened" if asset_data["open"] else " ==> Closed"
            print(asset_name, status, profit)
            print("-" * 35)

    print("Exiting...")

    client.close()


async def get_candle_v2():
    check_connect, message = await client.connect()
    if check_connect:
        asset = "EURUSD_otc"
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        print(asset_name, asset_data)
        if asset_data[2]:
            print("OK: Asset is open.")
            # 60 at 180 seconds
            candles = await client.get_candle_v2(asset_name, 60)
            print(candles)
        else:
            print("ERRO: Asset is closed.")

    print("Exiting...")

    client.close()


async def get_candles_all_asset():
    check_connect, message = await client.connect()
    if check_connect:
        offset = 3600  # in seconds
        period = 60  # in seconds
        codes_asset = await client.get_all_assets()
        for asset in codes_asset.keys():
            asset_name, asset_data = await client.get_available_asset(asset)
            if asset_data[2]:
                print(asset_name, asset_data)
                print("OK: Asset is open.")
                end_from_time = time.time()
                candles = await client.get_candles(asset, end_from_time, offset, period)
                print(candles)
            await asyncio.sleep(1)

    print("Exiting...")

    client.close()


async def get_realtime_candle():
    check_connect, message = await client.connect()
    if check_connect:
        period = 5  # in seconds [60, 120, 180, 240, 300, 600, 900, 1800, 3600, 14400, 86400]
        asset = "EURUSD_otc"
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        print(asset_name, asset_data)
        if asset_data[2]:
            print("Asset Open")
            client.start_candles_stream(asset_name, 60)
            while True:
                candles = await client.get_realtime_candles(asset_name, period)
                print(candles)
                """for _, candle in candles.items():
                    open_price = candle["open"]
                    print(f"Vela atual ({asset_name}): abertura = {open_price}", end="\r")"""
                await asyncio.sleep(1)
        else:
            print("ERRO: Asset is closed.")

    print("Exiting...")

    client.close()


async def get_realtime_sentiment():
    check_connect, message = await client.connect()
    if check_connect:
        asset = "EURUSD_otc"
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        if asset_data[2]:
            print("OK: Asset is open.")
            client.start_candles_stream(asset, 60)
            while True:
                print(await client.get_realtime_sentiment(asset_name), end="\r")
                await asyncio.sleep(0.5)
        else:
            print("ERRO: Asset is closed.")

    print("Exiting...")

    client.close()


async def get_realtime_price():
    check_connect, message = await client.connect()
    if check_connect:
        asset = "EURJPY_otc"
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        if asset_data[2]:
            print("OK: Asset is open.")
            await client.start_realtime_price(asset, 60)
            while True:
                candle_price = await client.get_realtime_price(asset_name)
                print(
                    f"Asset: {asset} "
                    f"Time: {candle_price[-1]['time']} "
                    f"Price: {candle_price[-1]['price']}",
                    end="\r"
                )
                await asyncio.sleep(0.1)
        else:
            print("ERRO: Asset is closed.")

    print("Exiting...")

    client.close()


async def get_signal_data():
    check_connect, message = await client.connect()
    if check_connect:
        client.start_signals_data()
        while True:
            signals = client.get_signal_data()
            if signals:
                print(json.dumps(signals, indent=4))
            await asyncio.sleep(1)

    print("Exiting...")

    client.close()


async def display_utc_time():
    while True:
        print(f"UTC Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}", end="\r")
        await asyncio.sleep(1)

from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

async def send_telegram_message(message):
    """ Sends a message to your Telegram bot """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("📩 Telegram Alert Sent!")
        else:
            print(f"⚠️ Telegram Error: {response.text}")
    except Exception as e:
        print(f"❌ Telegram Exception: {e}")

async def run_strategy():
    check_connect, message = await client.connect()
    if check_connect:
        asset = "XAUUSD_otc"
        amount = 10  # Define the trade amount
        direction = "call"  # Define the trade direction
        duration = 60  # 1 minute trade duration

        # Fetch the latest prices to calculate RSI
        prices = await client.get_realtime_candles(asset, 60)
        close_prices = [price['price'] for price in prices]
        print(f"Close prices for RSI calculation: {close_prices}")
        
        # Calculate RSI
        rsi_values = TechnicalIndicators.calculate_rsi(close_prices)
        if rsi_values and len(rsi_values) > 0:
            current_rsi = rsi_values[-1]
            print(f"Current RSI for {asset}: {current_rsi}")
        else:
            print("RSI calculation failed or not enough data.")

        # Calculate the expiration time for the trade in UTC
        expiration_time = datetime.now(timezone.utc) + timedelta(seconds=duration)
        print(f"Expiration Time (UTC): {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Execute the trade immediately after connecting
        status, buy_info = await client.buy(amount, asset, direction, duration, time_mode="TIME")
        if status:
            open_price = buy_info.get('openPrice')
            close_timestamp = buy_info.get('closeTimestamp')
            print(f"Trade executed on {asset} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("Open Price:", open_price)

            # Wait for the duration of the trade
            await asyncio.sleep(duration)

            # Get the real-time prices of the asset
            prices = await client.get_realtime_price(asset)

            if prices:
                current_price = prices[-1]['price']
                current_timestamp = prices[-1]['time']
                print(f"Current Time: {int(current_timestamp)}, Close Time: {close_timestamp}")
                print(f"Current Price: {current_price}, Open Price: {open_price}")

                # Determine the result of the trade
                if current_price > open_price:
                    print("Result: WIN")
                else:
                    print("Result: LOSS")
            else:
                print("Not a price direction.")
        else:
            print("Operation failed!!!")
            print("Buy Info:", buy_info)

    print("Exiting...")

    client.close()

async def synchronize_time():
    """Synchronize local time with Quotex server time."""
    server_time = client.api.timesync.server_timestamp
    local_time = time.time()
    time_difference = server_time - local_time
    if abs(time_difference) > 1:
        if time_difference > 0:
            time.sleep(time_difference)
        else:
            await asyncio.sleep(abs(time_difference))

async def test_strategy():
    check_connect, message = await client.connect()
    if check_connect:
        # Change the demo account balance to 5000
        await client.edit_practice_balance(5000)
        print("Demo account balance set to 5000")

        # Check if the asset is available
        asset = "XAUUSD_otc"
        asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
        if not asset_data[2]:
            print(f"Asset {asset} is not available.")
            return

        # Calculate the expiration time for the trade in UTC
        expiration_time = datetime.utcnow() + timedelta(seconds=60)
        print(f"Expiration Time (UTC): {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Execute the trade immediately after connecting
        status, buy_info = await client.buy(10, asset_name, "call", duration=60, time_mode="TIME")
        if status:
            open_price = buy_info.get('openPrice')
            close_timestamp = buy_info.get('closeTimestamp')
            print("Open Price:", open_price)

            # Wait for the duration of the trade
            await asyncio.sleep(60)

            # Start monitoring the real-time price of the asset
            client.start_realtime_price(asset, 60)

            # Get the real-time prices of the asset
            prices = await client.get_realtime_price(asset_name)

            if prices:
                current_price = prices[-1]['price']
                current_timestamp = prices[-1]['time']
                print(f"Current Time: {int(current_timestamp)}, Close Time: {close_timestamp}")
                print(f"Current Price: {current_price}, Open Price: {open_price}")

                # Determine the result of the trade
                if current_price > open_price:
                    print("Result: WIN")
                else:
                    print("Result: LOSS")
            else:
                print("Not a price direction.")
        else:
            print("Operation failed!!!")
            print("Buy Info:", buy_info)

        # Send a Telegram message with the trade execution time
        utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        await send_telegram_message(f"Trade executed on {asset_name} at {utc_time}")

    print("Exiting...")

    client.close()

async def execute(argument):
    match argument:
        case "test_connection":
            return await test_connection()
        case "get_profile":
            return await get_profile()
        case "get_balance":
            return await get_balance()
        case "get_signal_data":
            return await get_signal_data()
        case "trade_and_monitor":
            return await trade_and_monitor()
        case "get_payout":
            return await get_payout()
        case "get_payout_by_asset":
            return await get_payout_by_asset()
        case "get_payment":
            return await get_payment()
        case "assets_open":
            return await assets_open()
        case "get_all_assets":
            return await get_all_assets()
        case "get_candle":
            return await get_candle()
        case "get_candle_v2":
            return await get_candle_v2()
        case "get_candles_all_asset":
            return await get_candles_all_asset()
        case "get_candle_progressive":
            return await get_candle_progressive()
        case "get_realtime_candle":
            return await get_realtime_candle()
        case "get_realtime_sentiment":
            return await get_realtime_sentiment()
        case "get_realtime_price":
            return await get_realtime_price()
        case "buy_simple":
            return await buy_simple()
        case "get_result":
            return await get_result()
        case "buy_and_check_win":
            return await buy_and_check_win()
        case "buy_multiple":
            return await buy_multiple()
        case "buy_pending":
            return await buy_pending()
        case "balance_refill":
            return await balance_refill()
        case "run_strategy":
            return await run_strategy()
        case "test_strategy":
            return await test_strategy()
        case "help":
            print(f"Use: {'./app' if getattr(sys, 'frozen', False) else 'python app.py'} <option>")
            return print(get_all_options())
        case _:
            return print("Invalid option. Use 'help' to get a list of options.")


async def main():
    if len(sys.argv) != 2:
        # await test_connection()
        # await get_balance()
        # await get_profile()
        # await buy_simple()
        # await get_candle()
        # await get_candles_all_asset()
        return

    option = sys.argv[1]
    await execute(option)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Closing at program.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        loop.close()