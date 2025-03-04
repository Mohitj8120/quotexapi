import asyncio
import websockets
import json
from quotexapi.stable_api import Quotex
from config.settings import EMAIL, PASSWORD

# ✅ Quotex WebSocket Client Setup
client = Quotex(email=EMAIL, password=PASSWORD)

async def get_otc_pairs():
    """✅ Quotex API se dynamically saare available OTC pairs fetch karega"""
    await client.connect()
    all_assets = await client.get_all_assets()
    otc_pairs = [pair for pair in all_assets if "_otc" in pair]  # ✅ Sirf OTC pairs filter karna
    return otc_pairs

async def fetch_market_data(asset):
    """✅ Real-time Market Data Fetching for a given asset"""
    async with websockets.connect(client.wss_url) as ws:
        await ws.send(json.dumps({"action": "subscribe", "asset": asset}))  # ✅ WebSocket request bhejna
        
        while True:
            data = await ws.recv()  # ✅ Live data receive karna
            parsed_data = json.loads(data)  # ✅ JSON format me convert karna
            return parsed_data  # ✅ Data return karega jo indicators analyze karenge
