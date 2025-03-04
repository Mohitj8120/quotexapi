import asyncio
from core.websocket import fetch_market_data, get_otc_pairs
from core.strategy import check_signal
from telegram.bot import send_telegram_message

async def monitor_asset(asset):
    """✅ Ek single asset ka continuously market data track karega"""
    while True:
        market_data = await fetch_market_data(asset)  # ✅ Live WebSocket Data Fetch
        signal = check_signal(market_data, asset)  # ✅ Strategy Apply Karega
        
        if signal:
            send_telegram_message(signal)  # ✅ Telegram pe signal turant bhejna

async def main():
    """✅ Saare OTC pairs ko **simultaneously** track karega"""
    otc_pairs = await get_otc_pairs()  # ✅ Saare OTC pairs dynamically fetch karna
    print(f"✅ Monitoring OTC Pairs: {otc_pairs}")

    tasks = [monitor_asset(asset) for asset in otc_pairs]  # ✅ Har asset ka alag async task run hoga
    await asyncio.gather(*tasks)  # ✅ Sab assets parallel monitor honge

if __name__ == "__main__":
    asyncio.run(main())