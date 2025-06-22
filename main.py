import asyncio
import discord
from discord.ext import commands

from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot działa jako {bot.user}")

    try:
        synced = await bot.tree.sync()
        print("Slash commends zsynchronizowane!", len(synced))
    except Exception as e:
        print("Wystąpił błąd w synchronizacji:", e)


async def main():
    async with bot:
        await bot.load_extension("rooms")
        await bot.start(TOKEN)



asyncio.run(main())