import discord 
from discord.ext import commands
import asyncio

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all(), application_id="1013232498249043969")

@bot.event
async def on_ready():
    print("Bot is online")

async def main():
    await bot.load_extension('prompt')

asyncio.run(main())
bot.run('MTAxMzIzMjQ5ODI0OTA0Mzk2OQ.GaUFlM.PVK86rFRcGOVnSU-ckP_RzqG99f6LwNHmQrZ1k')


