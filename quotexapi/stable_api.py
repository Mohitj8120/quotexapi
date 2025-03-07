import time
import logging
import asyncio
import requests
import csv
import os
from datetime import datetime, timezone, timedelta
from . import expiration
from . import global_value
from .api import QuotexAPI
from .utils.services import truncate
from .utils.processor import (
    calculate_candles,
    process_candles_v2,
    merge_candles
)
from .config import (
    load_session,
    update_session,
    resource_path,
    credentials
)
from .utils.indicators import TechnicalIndicators
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

__version__ = "1.0.0"
logger = logging.getLogger(__name__)

LOG_FILE = "trades_log.csv"

class Quotex:

    def __init__(
            self,
            email=None,
            password=None,
            lang="pt",
            user_agent="Quotex/1.0",
            root_path=".",
            user_data_dir="browser",
            asset_default="EURUSD",
            period_default=60
    ):
        self.size = [
            1,
            5,
            10,
            15,
            30,
            60,
            120,
            300,
            600,
            900,
            1800,
            3600,
            7200,
            14400,
            86400,
        ]
        self.email = email
        self.password = password
        self.lang = lang
        self.resource_path = root_path
        self.user_data_dir = user_data_dir
        self.asset_default = asset_default
        self.period_default = period_default
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        self.account_is_demo = 1
        self.suspend = 0.2
        self.codes_asset = {}
        self.api = None
        self.duration = None
        self.websocket_client = None
        self.websocket_thread = None
        self.debug_ws_enable = False
        self.resource_path = resource_path(root_path)
        session = load_session(user_agent)
        self.session_data = session
        if not email or not password:
            self.email, self.password = credentials()
        self.last_trade_time = 0  # Track the last trade time

    @property
    def websocket(self):
        """Property to get websocket.
        :returns: The instance of :class:`WebSocket <websocket.WebSocket>`.
        """
        return self.websocket_client.wss

    @staticmethod
    async def check_connect():
        await asyncio.sleep(2)
        if global_value.check_accepted_connection == 1:
            return True

        return False

    def set_session(self, user_agent: str, cookies: str = None, ssid: str = None):
        session = {
            "cookies": cookies,
            "token": ssid,
            "user_agent": user_agent
        }
        self.session_data = update_session(session)

    async def re_subscribe_stream(self):
        try:
            for ac in self.subscribe_candle:
                sp = ac.split(",")
                await self.start_candles_one_stream(sp[0], sp[1])
        except:
            pass
        try:
            for ac in self.subscribe_candle_all_size:
                await self.start_candles_all_size_stream(ac)
        except:
            pass
        try:
            for ac in self.subscribe_mood:
                await self.start_mood_stream(ac)
        except:
            pass

    async def get_instruments(self):
        while self.check_connect and self.api.instruments is None:
            await asyncio.sleep(0.2)
        return self.api.instruments or []

    def get_all_asset_name(self):
        if self.api.instruments:
            return [[i[1], i[2].replace("\n", "")] for i in self.api.instruments]

    async def get_available_asset(self, asset_name: str, force_open: bool = False):
        asset_open = await self.check_asset_open(asset_name)
        if force_open and (not asset_open or not asset_open[2]):
            condition_otc = "otc" not in asset_name
            refactor_asset = asset_name.replace("_otc", "")
            asset_name = f"{asset_name}_otc" if condition_otc else refactor_asset
            asset_open = await self.check_asset_open(asset_name)
        return asset_name, asset_open

    async def check_asset_open(self, asset_name: str):
        instruments = await self.get_instruments()
        for i in instruments:
            if asset_name == i[1]:
                self.api.current_asset = asset_name
                return i[0], i[2].replace("\n", ""), i[14]

    async def get_all_assets(self):
        instruments = await self.get_instruments()
        for i in instruments:
            if i[0] != "":
                self.codes_asset[i[1]] = i[0]

        return self.codes_asset

    async def get_candles(self, asset, end_from_time, offset, period, progressive=False):
        if end_from_time is None:
            end_from_time = time.time()
        index = expiration.get_timestamp()
        self.api.candles.candles_data = None
        self.start_candles_stream(asset, period)
        self.api.get_candles(asset, index, end_from_time, offset, period)
        while True:
            while self.check_connect and self.api.candles.candles_data is None:
                await asyncio.sleep(0.1)
            if self.api.candles.candles_data is not None:
                break

        candles = self.prepare_candles(asset, period)
        if progressive:
            return self.api.historical_candles.get("data", {})

        return candles

    async def get_history_line(self, asset, end_from_time, offset):
        if end_from_time is None:
            end_from_time = time.time()
        index = expiration.get_timestamp()
        self.api.current_asset = asset
        self.api.historical_candles = None
        self.start_candles_stream(asset)
        self.api.get_history_line(self.codes_asset[asset], index, end_from_time, offset)
        while True:
            while self.check_connect and self.api.historical_candles is None:
                await asyncio.sleep(0.2)
            if self.api.historical_candles is not None:
                break
        return self.api.historical_candles

    async def get_candle_v2(self, asset, period):
        self.api.candle_v2_data[asset] = None
        self.start_candles_stream(asset, period)
        while self.api.candle_v2_data[asset] is None:
            await asyncio.sleep(0.2)
        candles = self.prepare_candles(asset, period)
        return candles

    async def get_realtime_candles(self, asset, period):
        self.api.realtime_price[asset] = []
        self.start_candles_stream(asset, period)
        while True:
            if self.api.realtime_price.get(asset):
                return self.api.realtime_price[asset]
            await asyncio.sleep(1)

    def prepare_candles(self, asset: str, period: int):
        """
        Prepare candles data for a specified asset.

        Args:
            asset (str): Asset name.
            period (int): Period for fetching candles.

        Returns:
            list: List of prepared candles data.
        """
        candles_data = calculate_candles(self.api.candles.candles_data, period)
        candles_v2_data = process_candles_v2(self.api.candle_v2_data, asset, candles_data)
        new_candles = merge_candles(candles_v2_data)

        return new_candles

    async def connect(self):
        self.api = QuotexAPI(
            "qxbroker.com",
            self.email,
            self.password,
            self.lang,
            resource_path=self.resource_path,
            user_data_dir=self.user_data_dir
        )
        self.close()
        self.api.trace_ws = self.debug_ws_enable
        self.api.session_data = self.session_data
        self.api.current_asset = self.asset_default
        self.api.current_period = self.period_default
        global_value.SSID = self.session_data.get("token")

        if not self.session_data.get("token"):
            await self.api.authenticate()

        check, reason = await self.api.connect(self.account_is_demo)

        if not await self.check_connect():
            logger.debug("Reconnecting on websocket")
            return await self.connect()

        return check, reason

    async def reconnect(self):
        await self.api.authenticate()

    def set_account_mode(self, balance_mode="PRACTICE"):
        """Set active account `real` or `practice`"""
        if balance_mode.upper() == "REAL":
            self.account_is_demo = 0
        elif balance_mode.upper() == "PRACTICE":
            self.account_is_demo = 1
        else:
            logger.error("ERROR doesn't have this mode")
            exit(1)

    def change_account(self, balance_mode: str):
        """Change active account `real` or `practice`"""
        self.account_is_demo = 0 if balance_mode.upper() == "REAL" else 1
        self.api.change_account(self.account_is_demo)

    async def edit_practice_balance(self, amount=None):
        self.api.training_balance_edit_request = None
        self.api.edit_training_balance(amount)
        while self.api.training_balance_edit_request is None:
            await asyncio.sleep(0.2)
        return self.api.training_balance_edit_request

    async def get_balance(self):
        while self.api.account_balance is None:
            await asyncio.sleep(0.2)
        balance = self.api.account_balance.get("demoBalance") \
            if self.api.account_type > 0 else self.api.account_balance.get("liveBalance")
        return float(f"{truncate(balance + self.get_profit(), 2):.2f}")

    def get_profit(self):
        return self.api.profit_in_operation or 0

    async def get_profile(self):
        settings = self.api.get_settings()
        user_settings = settings.get("data")
        self.api.profile.nick_name = user_settings["nickname"]
        self.api.profile.profile_id = user_settings["id"]
        self.api.profile.demo_balance = user_settings["demoBalance"]
        self.api.profile.live_balance = user_settings["liveBalance"]
        self.api.profile.avatar = user_settings["avatar"]
        self.api.profile.currency_code = user_settings["currencyCode"]
        self.api.profile.country = user_settings["country"]
        self.api.profile.country_name = user_settings["countryName"]
        self.api.profile.currency_symbol = user_settings["currencySymbol"]
        self.api.profile.offset = user_settings.get("timeOffset")
        return self.api.profile

    def start_signals_data(self):
        self.api.signals_subscribe()

    async def auto_trade(self, strategy):
        """ Automatically trade based on strategy """
        await self.synchronize_time()
        while True:
            assets = await self.get_all_assets()
            for asset in assets:
                if "otc" in asset:
                    candles = await self.get_realtime_candles(asset, 60)
                    close_prices = [candle['price'] for candle in candles]
                    if strategy(asset, close_prices):
                        current_time = time.time()
                        if current_time - self.last_trade_time > 60:  # 60 seconds cooldown
                            await self.buy(10, asset, "call", duration=60)
                            self.last_trade_time = current_time
                            send_telegram_message(f"Trade executed on {asset} based on strategy")
            await asyncio.sleep(1)  # Fetch data every second

    async def synchronize_time(self):
        """Continuously synchronize local time with Quotex server time and display both times"""
        while True:
            server_time = self.api.timesync.server_timestamp
            local_time = time.time()
            time_difference = server_time - local_time
            print(f"Local time before sync: {datetime.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Server time (UTC): {datetime.fromtimestamp(server_time, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
            if abs(time_difference) > 1:
                print(f"Synchronizing time: adjusting by {time_difference} seconds")
                if time_difference > 0:
                    time.sleep(time_difference)
                else:
                    # Adjust local time forward
                    await asyncio.sleep(abs(time_difference))
            print(f"Local time after sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(1)  # Synchronize every second

            # Display real-time UTC time
            utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"Current UTC Time: {utc_time}", end="\r")

    async def buy(self, amount: float, asset: str, direction: str, duration: int, time_mode: str = "TIMER"):
        """Buy Binary option"""
        self.api.buy_id = None
        request_id = expiration.get_timestamp()
        is_fast_option = True if time_mode.upper() == "TIME" else False
        self.start_candles_stream(asset, duration)
        print(f"Executing trade at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.api.buy(amount, asset, direction, duration, request_id, is_fast_option)

        count = 0.1
        while self.api.buy_id is None:
            count += 0.1
            if count > duration:
                status_buy = False
                break
            await asyncio.sleep(0.2)
            if global_value.check_websocket_if_error:
                return False, global_value.websocket_error_reason
        else:
            status_buy = True

        return status_buy, self.api.buy_successful

    def start_candles_stream(self, asset, period=0):
        self.api.current_asset = asset
        self.api.subscribe_realtime_candle(asset, period)
        self.api.follow_candle(asset)

    async def monitor_assets(self):
        """ Monitor all assets and apply strategy """
        while True:
            await self.auto_trade(self.strategy)
            await asyncio.sleep(60)

    def close(self):
        if self.websocket_client:
            self.websocket_client.wss.close()
            self.websocket_thread.join()
        if hasattr(self, 'utc_task'):
            self.utc_task.cancel()
        return True

def send_telegram_message(message):
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

def initialize_csv():
    """ Creates a CSV file with headers if it doesn't exist """
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Asset", "Trade Type", "Amount", "Result", "Profit/Loss"])

def log_trade(timestamp, asset, trade_type, amount, result, profit_loss):
    """ Logs trade details into a CSV file """
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, asset, trade_type, amount, result, profit_loss])

async def display_utc_time():
    """Display the current UTC time"""
    while True:
        utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Current UTC Time: {utc_time}", end="\r")
        await asyncio.sleep(1)
