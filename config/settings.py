import asyncio
from core.websocket import get_otc_pairs

# ✅ API Credentials & Settings
EMAIL = "your_email@example.com"
PASSWORD = "your_password"

# ✅ Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

# ✅ Automatically fetch all available OTC pairs
OTC_PAIRS = asyncio.run(get_otc_pairs())  # ✅ Quotex API se live pairs fetch honge

# ✅ Trading Settings
TIMEFRAME = 60  # 1 min (Not Used Anymore Since We Fetch Live Data in Real-Time)

# ✅ Debugging: Print Fetched OTC Pairs
print(f"✅ Monitoring These OTC Pairs: {OTC_PAIRS}")
