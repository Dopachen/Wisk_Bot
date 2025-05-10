import discord
from discord.ext import commands
from dotenv import load_dotenv
from verify_arcade import send_verify_message_arcade
from verify_ppy import send_verify_message_ppy
from essentials_ppy import send_essentials_message
from ppy_status import track_queue_status
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class MyBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix="/", intents=discord.Intents.all(), **kwargs)

    async def setup_hook(self):
        await self.load_extension("command")

    async def on_ready(self):
        print(f'Running on "{self.user}"')
        await self.tree.sync()
        await send_verify_message_arcade(bot)
        await send_verify_message_ppy(bot)
        await send_essentials_message(bot)
        bot.loop.create_task(track_queue_status(bot))
        print("Bot is ready")

bot = MyBot()
bot.run(TOKEN)
