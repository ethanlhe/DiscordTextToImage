import discord 
from discord.ext import commands
import asyncio

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # no warnings

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all(), application_id="1013232498249043969")

@bot.event
async def on_ready():
    print("Bot is online")
    await bot.change_presence(activity=discord.Game('/image | /text'))

async def main():
    await bot.load_extension('prompt')

asyncio.run(main())
bot.run('MTAxMzIzMjQ5ODI0OTA0Mzk2OQ.G7lWRf.KDjo1IZ5M8y3zaxK7PJ6pkNH4H5uU1rR4Pu-eY')