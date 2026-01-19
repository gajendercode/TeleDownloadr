import os
from pyrogram import Client
from teledownloadr.config.settings import API_ID, API_HASH

class TelegramClient:
    def __init__(self):
        self.app = Client(
            "my_account",
            api_id=API_ID,
            api_hash=API_HASH,
            workdir=os.getcwd() # Save session file in current directory
        )

    async def start(self):
        await self.app.start()
        me = await self.app.get_me()
        print(f"Successfully logged in as: {me.first_name} (@{me.username})")
        return self.app

    async def stop(self):
        await self.app.stop()
