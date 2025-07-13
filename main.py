import asyncio
import discord
from discord.ext import commands
import logging
import dotenv
import os


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

@bot.event
async def on_ready():
    logger.info(f"Bot działa jako {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Slash commands zsynchronizowane! ({len(synced)})")
    except Exception as e:
        logger.error(f"Wystąpił błąd w synchronizacji: {e}")

async def main():
    async with bot:
        await bot.load_extension("rooms")
        await bot.start(os.getenv("TOKEN"))

asyncio.run(main())
