# bot.py

import os
import discord
import sqlite3
import shutil
import asyncio
import global_data
import emojis
import logging
import logging.handlers
import itertools

from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime
from discord.ext.commands import CommandNotFound

# Check if log file exists, if not, create empty one
log_dir = global_data.log_dir
logfile = global_data.logfile

if not os.path.exists(log_dir):
    os.mkdir(log_dir)
if not os.path.isfile(logfile):
    open(logfile, 'a').close()

# Initialize logger
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(filename=logfile,when='D',interval=1, encoding='utf-8', utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Read the bot token from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set name of database files
dbfile = global_data.dbfile

# Open connection to the local database
pinbot_db = sqlite3.connect(dbfile, isolation_level=None)

# Mixed Case prefix
async def mixedCase(*args):
  mixed_prefixes = []
  for string in args:
    all_prefixes = map(''.join, itertools.product(*((c.upper(), c.lower()) for c in string)))
    for prefix in list(all_prefixes):
        mixed_prefixes.append(prefix)

  return list(mixed_prefixes)


# --- Database: Get Data ---

# Check database for stored prefix, if none is found, a record is inserted and the default prefix - is used, return all bot prefixes
async def get_prefix_all(bot, ctx):

    try:
        cur=pinbot_db.cursor()
        cur.execute('SELECT * FROM settings_guild where guild_id=?', (ctx.guild.id,))
        record = cur.fetchone()

        if record:
            prefix_db = record[1].replace('"','')
            prefix_db_mixed_case = await mixedCase(prefix_db)
            prefixes = []
            for prefix in prefix_db_mixed_case:
                prefixes.append(prefix)
        else:
            prefix_mixed_case = await mixedCase(global_data.default_prefix)
            cur.execute('INSERT INTO settings_guild VALUES (?, ?)', (ctx.guild.id, global_data.default_prefix,))
            prefixes = []
            for prefix in prefix_mixed_case:
                prefixes.append(prefix)
    except sqlite3.Error as error:
        await log_error(ctx, error)

    return commands.when_mentioned_or(*prefixes)(bot, ctx)

# Check database for stored prefix, if none is found, the default prefix - is used, return only the prefix (returning the default prefix this is pretty pointless as the first command invoke already inserts the record)
async def get_prefix(bot, ctx, guild_join=False):

    if guild_join == False:
        guild = ctx.guild
    else:
        guild = ctx

    try:
        cur=pinbot_db.cursor()
        cur.execute('SELECT * FROM settings_guild where guild_id=?', (guild.id,))
        record = cur.fetchone()

        if record:
            prefix = record[1]
        else:
            prefix = global_data.default_prefix
    except sqlite3.Error as error:
        if guild_join == False:
            await log_error(ctx, error)
        else:
            await log_error(ctx, error, True)

    return prefix

# Get user count
async def get_user_number(ctx):

    try:
        cur=pinbot_db.cursor()
        cur.execute('SELECT COUNT(*) FROM settings_user')
        record = cur.fetchone()

        if record:
            user_number = record
        else:
            await log_error(ctx, 'No user data found in database.')
    except sqlite3.Error as error:
        await log_error(ctx, error)

    return user_number



# --- Database: Write Data ---

# Set new prefix
async def set_prefix(bot, ctx, new_prefix):

    try:
        cur=pinbot_db.cursor()
        cur.execute('SELECT * FROM settings_guild where guild_id=?', (ctx.guild.id,))
        record = cur.fetchone()

        if record:
            cur.execute('UPDATE settings_guild SET prefix = ? where guild_id = ?', (new_prefix, ctx.guild.id,))
        else:
            cur.execute('INSERT INTO settings_guild VALUES (?, ?)', (ctx.guild.id, new_prefix,))
    except sqlite3.Error as error:
        await log_error(ctx, error)


# --- Error Logging ---

# Error logging
async def log_error(ctx, error, guild_join=False):

    if guild_join == False:
        try:
            cur=pinbot_db.cursor()
            cur.execute('INSERT INTO errors VALUES (?, ?, ?)', (ctx.message.created_at, ctx.message.content, str(error)))
        except sqlite3.Error as db_error:
            print(print(f'Error inserting error (ha) into database.\n{db_error}'))
    else:
        try:
            cur=pinbot_db.cursor()
            cur.execute('INSERT INTO errors VALUES (?, ?, ?)', (datetime.now(), 'Error when joining a new guild', str(error)))
        except sqlite3.Error as db_error:
            print(print(f'Error inserting error (ha) into database.\n{db_error}'))



# --- Command Initialization ---

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=get_prefix_all, help_command=None, case_insensitive=True)



# --- Ready & Join Events ---

# Set bot status when ready
@bot.event
async def on_ready():

    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='pinbot help'))

# Send message to system channel when joining a server
@bot.event
async def on_guild_join(guild):

    try:
        prefix = await get_prefix(bot, guild, True)

        welcome_message =   f'Hello **{guild.name}**! I\'m here to let users pin and unpin messages.\n\n'\
                            f'To pin: React with 📌 or use  {prefix}pin [message id].\n'\
                            f'To unpin: Remove reaction 📌 or use  {prefix}unpin [message id].'

        await guild.system_channel.send(welcome_message)
    except:
        return



# --- Error Handling ---

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    elif isinstance(error, (commands.MissingPermissions)):
        missing_perms = ''
        for missing_perm in error.missing_perms:
            missing_perm = missing_perm.replace('_',' ').title()
            if not missing_perms == '':
                missing_perms = f'{missing_perms}, `{missing_perm}`'
            else:
                missing_perms = f'`{missing_perm}`'
        await ctx.reply(f'Sorry **{ctx.author.name}**, you need the permission(s) {missing_perms} to use this command.', mention_author=False)
    elif isinstance(error, (commands.BotMissingPermissions)):
        missing_perms = ''
        for missing_perm in error.missing_perms:
            missing_perm = missing_perm.replace('_',' ').title()
            if not missing_perms == '':
                missing_perms = f'{missing_perms}, `{missing_perm}`'
            else:
                missing_perms = f'`{missing_perm}`'
        await ctx.send(f'Sorry **{ctx.author.name}**, I\'m missing the permission(s) {missing_perms} to work properly.')
    elif isinstance(error, (commands.NotOwner)):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f'You\'re missing some arguments.', mention_author=False)
    else:
        await log_error(ctx, error)



# --- Server Settings ---

# Command "setprefix" - Sets new prefix (if user has "manage server" permission)
@bot.command()
@commands.has_permissions(manage_guild=True)
@commands.bot_has_permissions(send_messages=True)
async def setprefix(ctx, *new_prefix):

    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        if new_prefix:
            if len(new_prefix)>1:
                await ctx.reply(f'The command syntax is `{ctx.prefix}setprefix [prefix]`.', mention_author=False)
            else:
                await set_prefix(bot, ctx, new_prefix[0])
                await ctx.reply(f'Prefix changed to `{await get_prefix(bot, ctx)}`.', mention_author=False)
        else:
            await ctx.reply(f'The command syntax is `{ctx.prefix}setprefix [prefix]`.', mention_author=False)

# Command "prefix" - Returns current prefix
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def prefix(ctx):

    if not ctx.prefix == 'rpg ':
        current_prefix = await get_prefix(bot, ctx)
        await ctx.reply(f'The prefix for this server is `{current_prefix}`\nTo change the prefix use `{current_prefix}setprefix [prefix]`.', mention_author=False)



# --- Main menus ---

# Main menu
@bot.command(aliases=('g','h',))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def help(ctx):

    prefix = ctx.prefix
    prefix = await get_prefix(bot, ctx)

    pin = (
        f'{emojis.bp} React to a message with 📌 (`:pushpin:`)\n'
        f'{emojis.blank} or\n'
        f'{emojis.bp} `{prefix}pin [message id]`'
    )

    unpin = (
        f'{emojis.bp} Remove reaction 📌 from message\n'
        f'{emojis.blank} or\n'
        f'{emojis.bp} `{prefix}unpin [message id]`'
    )

    server_settings = (
        f'{emojis.bp} `{prefix}prefix` : Check the bot prefix\n'
        f'{emojis.bp} `{prefix}setprefix` / `{prefix}sp` : Set the bot prefix'
    )

    embed = discord.Embed(
        color = global_data.color,
        title = 'PINBOT',
        description =   f'Heyo **{ctx.author.name}**, want to pin something?'
    )
    embed.set_footer(text=await global_data.default_footer(prefix))
    embed.add_field(name='HOW TO PIN A MESSAGE', value=pin, inline=False)
    embed.add_field(name='HOW TO UNPIN A MESSAGE', value=unpin, inline=False)
    embed.add_field(name='SERVER SETTINGS', value=server_settings, inline=False)

    await ctx.reply(embed=embed, mention_author=False)



# --- Reaction Events ---
# Add pin
@bot.event
@commands.bot_has_permissions(send_messages=True, read_message_history=True, manage_messages=True)
async def on_raw_reaction_add(event):
    await bot.wait_until_ready()
    channel = bot.get_channel(event.channel_id)
    message = await channel.fetch_message(event.message_id)
    if str(event.emoji) == "📌":
        await message.pin()

# Remove pin
@bot.event
@commands.bot_has_permissions(send_messages=True, read_message_history=True, manage_messages=True)
async def on_raw_reaction_remove(event):
    await bot.wait_until_ready()
    channel = bot.get_channel(event.channel_id)
    message = await channel.fetch_message(event.message_id)
    if str(event.emoji) == "📌":
        if not ":pushpin:" in [ event.emoji for reaction in  message.reactions]:
            await message.unpin()


# --- Commands ---
# Pin
@bot.command(aliases=('p',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True, manage_messages=True)
async def pin(ctx, *args):

    prefix = ctx.prefix

    syntax = f'The syntax is `{prefix}pin [message id]`'

    if args:
        if len(args) == 1:
            arg = args[0]
            if arg.isnumeric():
                try:
                    message_id = int(arg)
                    message = await ctx.fetch_message(message_id)
                    if not message == None:
                        if not message.pinned == True:
                            await message.pin()
                            return
                        else:
                            await ctx.reply('Message is already pinned.', mention_author=False)
                            return
                    else:
                        await ctx.send(
                            f'Could not find a message with this ID.\n'
                            f'Please note that you need to use this command in the channel the message was sent.'
                        )
                    return
                except:
                    await ctx.send('Invalid message ID.')
                    return
            else:
                await ctx.send(syntax)
                return
        else:
            await ctx.send(syntax)
            return
    else:
        await ctx.send(syntax)
        return

# Unpin
@bot.command(aliases=('u','up',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True, manage_messages=True)
async def unpin(ctx, *args):

    prefix = ctx.prefix

    syntax = f'The syntax is `{prefix}unpin [message id]`'

    if args:
        if len(args) == 1:
            arg = args[0]
            if arg.isnumeric():
                try:
                    message_id = int(arg)
                    message = await ctx.fetch_message(message_id)
                    if not message == None:
                        if not message.pinned == False:
                            await message.unpin()
                            await message.reply('Message unpinned!')
                            return
                        else:
                            await ctx.reply('Message is already unpinned.', mention_author=False)
                            return
                    else:
                        await ctx.send(
                            f'Could not find a message with this ID.\n'
                            f'Please note that you need to use this command in the channel the message was sent.'
                        )
                    return
                except:
                    await ctx.send('Invalid message ID.')
                    return
            else:
                await ctx.send(syntax)
                return
        else:
            await ctx.send(syntax)
            return
    else:
        await ctx.send(syntax)
        return



# --- Miscellaneous ---

# Statistics command
@bot.command(aliases=('statistic','statistics,','devstat','ping','about','info','stats'))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def devstats(ctx):
    """Shows some bot info"""
    start_time = datetime.utcnow()
    message = await ctx.send('Testing API latency...')
    end_time = datetime.utcnow()
    elapsed_time = end_time - start_time
    bot_status = (
        f'{emojis.bp} {len(bot.guilds):,} servers\n'
        f'{emojis.bp} Bot latency: {round(bot.latency*1000):,} ms\n'
        f'{emojis.bp} API latency: {round(elapsed_time.total_seconds()*1000):,} ms'
        )
    creator = f'{emojis.bp} Miriel#0001'
    embed = discord.Embed(color = global_data.color, title = 'ABOUT PINBOT')
    embed.add_field(name='BOT STATS', value=bot_status, inline=False)
    embed.add_field(name='CREATOR', value=creator, inline=False)
    await message.edit(content=None, embed=embed)



# --- Owner Commands ---

# Shutdown command (only I can use it obviously)
@bot.command()
@commands.is_owner()
@commands.bot_has_permissions(send_messages=True)
async def shutdown(ctx):

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        await ctx.reply(f'**{ctx.author.name}**, are you **SURE**? `[yes/no]`', mention_author=False)
        answer = await bot.wait_for('message', check=check, timeout=30)
        if answer.content.lower() in ['yes','y']:
            await ctx.send(f'Shutting down.')
            await ctx.bot.logout()
        else:
            await ctx.send(f'Phew, was afraid there for a second.')

bot.run(TOKEN)