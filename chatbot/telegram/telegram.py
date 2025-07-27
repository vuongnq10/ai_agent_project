import os
import aiohttp
from datetime import datetime

token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHATID")
env = os.getenv("ENV", "Unknown")


async def telegram_bot(message: str, more=None):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"""
                  {env}: {message}
                  {more or ''}
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
