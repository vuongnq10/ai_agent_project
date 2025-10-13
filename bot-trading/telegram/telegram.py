import os
import aiohttp
import asyncio
from datetime import datetime
import json

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


# async def listen_to_messages():
#     offset = 0  # update_id offset so we don't re-read old messages

#     async with aiohttp.ClientSession() as session:
#         while True:
#             try:
#                 url = f"https://api.telegram.org/bot{token}/getUpdates"
#                 params = {"offset": offset, "timeout": 30}  # long polling
#                 async with session.get(url, params=params) as resp:
#                     data = await resp.json()

#                     if data.get("ok") and data.get("result"):
#                         for update in data["result"]:
#                             offset = update["update_id"] + 1
#                             if "message" in update:
#                                 chat_id = update["message"]["chat"]["id"]
#                                 text = update["message"].get("text", "")

#                                 print(f"Received from {chat_id}: {text}")

#                                 # Example: respond to user
#                                 await telegram_bot(
#                                     f"You said: {text}", more={"chat_id": chat_id}
#                                 )
#             except Exception as e:
#                 print("Error while polling:", e)
#                 await asyncio.sleep(3)  # wait before retrying


# # ✅ Run listener
# if __name__ == "__main__":
#     asyncio.run(listen_to_messages())
