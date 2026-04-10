import os
import asyncio
import aiohttp
from datetime import datetime
import json
import config

token = config.TELEGRAM_TOKEN
chat_id = config.TELEGRAM_CHATID
env = config.ENV


async def telegram_bot(message: str, more=None):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"""
                {env}: {message}
                {json.dumps(more, indent=4) if more else ''}
                at: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}
                """,
            "parse_mode": "HTML",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error! status: {response.status}")
                data = await response.json()
                return data

    except Exception as e:
        return {"ok": False, "description": str(e)}


async def listen_messages():
    """Long-poll Telegram for new messages and print their text.

    Handles both private/group 'message' updates and channel 'channel_post' updates.
    """
    offset = None
    url = f"https://api.telegram.org/bot{token}/getUpdates"

    print("[Telegram] Listener started, waiting for messages...")

    async with aiohttp.ClientSession() as session:
        while True:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset

            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=35)) as response:
                    data = await response.json()

                if not data.get("ok"):
                    print(f"[Telegram] getUpdates error: {data}")
                    await asyncio.sleep(3)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1

                    # Private chat or group message
                    msg = update.get("message") or update.get("channel_post")
                    if msg:
                        text = msg.get("text")
                        if text:
                            print(f"[Telegram] {text}")

            except Exception as e:
                print(f"[Telegram] polling error: {e}")
                await asyncio.sleep(3)
