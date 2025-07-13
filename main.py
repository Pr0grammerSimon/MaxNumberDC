import asyncio
import discord
from discord.ext import commands
import logging
import dotenv
import os

from game import PosChoiceView, CardChoiceView, PlayerChoiceView
import game

### .ENV TOKEN ###
dotenv.load_dotenv('.env')

### LOGI ###
logging.basicConfig(level=logging.INFO)  # albo DEBUG
logger = logging.getLogger("discord")

handler = logging.FileHandler(filename='discord_bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

logger.addHandler(handler)
####

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

async def main():
    async with bot:
        # 1) załaduj cog z /room
        await bot.load_extension("rooms")
        # 2) zsynchronizuj wszystkie komendy (slash + grupa room)
        synced = await bot.tree.sync()
        logger.info(f"Slash commands zsynchronizowane! ({len(synced)})")
        # 3) uruchom bota
        await bot.start(os.getenv("TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
