# bot.py

import discord
from resources import settings

from discord.ext import commands


intents = discord.Intents.none()
intents.guilds = True   # for on_guild_join() and all guild objects
intents.messages = True
intents.reactions = True # for reading pin reactions

if settings.DEBUG_MODE == 'ON':
    bot = commands.Bot(help_command=None, case_insensitive=True, intents=intents,
                       debug_guilds=settings.DEV_GUILDS, owner_id=619879176316649482)
else:
    bot = commands.Bot(help_command=None, case_insensitive=True, intents=intents,
                       owner_id=619879176316649482)

EXTENSIONS = [
    'cogs.main',
    'cogs.dev',
    'cogs.pins',
    'cogs.rooms',
]
if __name__ == '__main__':
    for extension in EXTENSIONS:
        bot.load_extension(extension)

bot.run(settings.TOKEN)