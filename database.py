# database.py
"""Access to the database"""

from datetime import datetime
import sqlite3
from typing import NamedTuple, Optional, Union

import discord

from resources import logs, settings


PINBOT_DB = sqlite3.connect(settings.DB_FILE, isolation_level=None)


INTERNAL_ERROR_SQLITE3 = 'Error executing SQL.\nError: {error}\nTable: {table}\nFunction: {function}\SQL: {sql}'
INTERNAL_ERROR_LOOKUP = 'Error assigning values.\nError: {error}\nTable: {table}\nFunction: {function}\Records: {record}'
INTERNAL_ERROR_NO_ARGUMENTS = 'You need to specify at least one keyword argument.\nTable: {table}\nFunction: {function}'


class Channel(NamedTuple):
    channe_id: int
    owner_id: int


async def log_error(error: Union[Exception, str], ctx: Optional[discord.ApplicationContext] = None):
    """Logs an error to the database and the logfile

    Arguments
    ---------
    error: Exception or a simple string.
    ctx: If context is available, the function will log the user input, the message timestamp
    and the user settings. If not, current time is used, settings and input are logged as "N/A".

    Raises
    ------
    sqlite3.Error when something goes wrong in the database. Also logs this error to the log file.
    """
    table = 'errors'
    function_name = 'log_error'
    sql = 'INSERT INTO errors VALUES (?, ?, ?, ?)'
    if ctx is not None:
        command_name = f'{ctx.command.full_parent_name} {ctx.command.name}'.strip()
        timestamp = ctx.author.created_at
        user_options = str(ctx.interaction.data)
    else:
        timestamp = datetime.utcnow()
        user_options = 'N/A'
    try:
        cur = PINBOT_DB.cursor()
        cur.execute(sql, (timestamp, command_name, user_options, str(error)))
    except sqlite3.Error as error:
        logs.logger.error(
            INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
            ctx
        )
        raise


# --- Database: Get Data ---
async def get_channel(ctx: Union[discord.ApplicationContext, discord.Guild]) -> Channel:
    """Gets all channel settings.

    Returns
    -------
    Channel object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'settings_channel'
    function_name = 'get_channel'
    sql = 'SELECT * FROM settings_channel where channel_id=?'
    channel_id = ctx.channel.id
    try:
        cur = PINBOT_DB.cursor()
        cur.row_factory = sqlite3.Row
        cur.execute(sql, (channel_id,))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await log_error(
            INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
            ctx
        )
        raise
    if not record:
        sql = 'INSERT INTO settings_channel (guild_id, owner_id) VALUES (?, ?)'
        try:
            cur.execute(sql, (channel_id, 0))
            sql = 'SELECT * FROM settings_guild where guild_id=?'
            cur.execute(sql, (channel_id,))
            record = cur.fetchone()
        except sqlite3.Error as error:
            await log_error(
                INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
                ctx
            )
            raise
    try:
        channel_settings = Channel(
            channel_id = record['channel_id'],
            owner_id = record['owner_id'],
        )
    except Exception as error:
        await log_error(
            INTERNAL_ERROR_LOOKUP.format(error=error, table=table, function=function_name, record=record),
            ctx
        )
        raise LookupError

    return channel_settings



# --- Database: Write Data ---
async def update_channel(ctx: discord.ApplicationContext, **kwargs) -> None:
    """Updates guild settings.

    Arguments
    ---------
    ctx: Context.
    kwargs (column=value):
        channel_id: int
        owner_id: int

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if not kwargs are passed (need to pass at least one)
    Also logs all error to the database.
    """
    table = 'settings_channel'
    function_name = 'update_channel'
    channel_id = ctx.channel.id
    if not kwargs:
        await log_error(
            INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name),
            ctx
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    await get_channel(ctx) # Makes sure the user exists in the database
    try:
        cur = PINBOT_DB.cursor()
        sql = 'UPDATE settings_channel SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['channel_id'] = channel_id
        sql = f'{sql} WHERE channel_id = :channel_id'
        cur.execute(sql, kwargs)
    except sqlite3.Error as error:
        await log_error(
            INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
            ctx
        )
        raise