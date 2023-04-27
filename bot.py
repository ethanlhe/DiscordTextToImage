import discord 
from discord.ext import commands
import asyncio
import systemd.daemon

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # no warnings

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all(), application_id="1013232498249043969")

@bot.event
async def on_ready():
    print("Bot is online")
    await bot.change_presence(activity=discord.Game('/prompt'))

async def main():
    await bot.load_extension('prompt')

asyncio.run(main())

systemd.daemon.notify('READY=1')
bot.run('MTAxMzIzMjQ5ODI0OTA0Mzk2OQ.GfBz_V.gXxdl_YLck377QnfgjPXnUEiDzBt6j5TL2LJDk')