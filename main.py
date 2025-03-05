# main.py (Quotex Bot Controller)
import asyncio
import logging
from quotexapi.stable_api import Quotex
from indicators import check_trade_signal
from telegram_bot import send_telegram_message
from config import EMAIL, PASSWORD, TRADE_AMOUNT

logging.basicConfig(level=logging.INFO)  # Set logging level to INFO

class QuotexBot:
    def __init__(self):
        self.client = Quotex(email=EMAIL, password=PASSWORD)
        self.running = True

    async def fetch_otc_assets(self):
        """Fetch the list of available OTC assets."""
        assets = await self.client.get_all_assets()
        otc_assets = [asset for asset in assets if 'otc' in asset.lower()]  # Filter OTC assets
        return otc_assets

    async def monitor_asset(self, asset):
        """Monitor a single asset for trade signals."""
        while self.running:
            try:
                signal = await check_trade_signal(self.client, asset)
                if signal:
                    direction, confidence = signal
                    message = f"🚀 {direction.upper()} Signal for {asset}! Confidence: {confidence:.2f}%"
                    logging.info(message)
                    send_telegram_message(message)

                    # Place trade (Optional)
                    # trade_id, result = await self.client.buy(amount=TRADE_AMOUNT, asset=asset, direction=direction, duration=60)
                    # logging.info(f"Trade {direction} on {asset}, Result: {result}")

            except Exception as e:
                logging.error(f"Error checking {asset}: {e}")

            await asyncio.sleep(1)  # Check every second

    async def start(self):
        """Start the bot and continuously monitor the market."""
        await self.client.connect()
        logging.info("Bot started! Fetching OTC pairs...")

        otc_assets = await self.fetch_otc_assets()
        logging.info(f"Monitoring {len(otc_assets)} OTC pairs...")

        tasks = [self.monitor_asset(asset) for asset in otc_assets]
        await asyncio.gather(*tasks)

        await self.client.close()

    def stop(self):
        """Stop the bot."""
        self.running = False
        logging.info("Stopping bot...")

if __name__ == "__main__":
    bot = QuotexBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        bot.stop()
