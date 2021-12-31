# database.py
"""Access to the database"""

from dataclasses import dataclass
from datetime import date, datetime
import sqlite3
from typing import Optional, Union

import discord

from resources import exceptions, logs, settings


PINBOT_DB = sqlite3.connect(settings.DB_FILE, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)


INTERNAL_ERROR_SQLITE3 = 'Error executing SQL.\nError: {error}\nTable: {table}\nFunction: {function}\SQL: {sql}'
INTERNAL_ERROR_LOOKUP = 'Error assigning values.\nError: {error}\nTable: {table}\nFunction: {function}\Records: {record}'
INTERNAL_ERROR_NO_ARGUMENTS = 'You need to specify at least one keyword argument.\nTable: {table}\nFunction: {function}'


@dataclass()
class Room():
    """Object that represents a record of the table "rooms"."""
    channel_id: int
    edit_count: int
    last_edit_at: datetime
    owner_id: int

    async def refresh(self, ctx: discord.ApplicationContext) -> None:
        """Refreshes clan data from the database.
        If the record doesn't exist anymore, "record_exists" will be set to False.
        All other values will stay on their old values before deletion (!).
        """
        new_settings = await get_room(ctx, self.channel_id)
        self.edit_count = new_settings.edit_count
        self.last_edit_at = new_settings.last_edit_at
        self.owner_id = new_settings.owner_id

    async def update(self, ctx: discord.ApplicationContext, **kwargs) -> None:
        """Updates the room record in the database. Also calls refresh().

        Arguments
        ---------
        kwargs (column=value):
            channel_id: int
            owner_id: int
            edit_count: int
            last_edit_at: datetime without microseconds

        Raises
        ------
        sqlite3.Error if something happened within the database.
        NoArgumentsError if no kwargs are passed (need to pass at least one).
        Also logs all errors to the database.
        """
        await _update_room(ctx, self.channel_id, **kwargs)
        await self.refresh(ctx)


async def log_error(error: Union[Exception, str], ctx: Optional[discord.ApplicationContext] = None):
    """Logs an error to the database and the log file

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
    sql = f'INSERT INTO {table} (date_time, command_name, command_data, error) VALUES (?, ?, ?, ?)'
    if ctx is not None:
        date_time = ctx.author.created_at
        command_name = f'{ctx.command.full_parent_name} {ctx.command.name}'.strip()
        command_data = str(ctx.interaction.data)
    else:
        date_time = datetime.utcnow()
        command_name = 'N/A'
        command_data = 'N/A'
    try:
        cur = PINBOT_DB.cursor()
        cur.execute(sql, (date_time, command_name, command_data, str(error)))
    except sqlite3.Error as error:
        if ctx is not None:
            logs.logger.error(
                INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
                ctx
            )
        else:
            logs.logger.error(INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql))
        raise


# --- Database: Get Data ---
async def get_room(ctx: discord.ApplicationContext, channel_id: int) -> Room:
    """Gets the settings of a room. If the room doesn't exist, a new record is created.

    Returns
    -------
    Room object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'rooms'
    function_name = 'get_room'
    sql = f'SELECT * FROM {table} WHERE channel_id=?'
    try:
        cur = PINBOT_DB.cursor()
        cur.row_factory = sqlite3.Row
        cur.execute(sql, (channel_id,))
        record = cur.fetchone()
        if not record:
            sql = f'INSERT INTO {table} (channel_id, last_edit_at) VALUES (?, ?)'
            cur.execute(sql, (channel_id, datetime.utcnow().replace(microsecond=0)))
            sql = f'SELECT * FROM {table} WHERE channel_id=?'
            cur.execute(sql, (channel_id,))
            record = cur.fetchone()
    except sqlite3.Error as error:
        await log_error(
            INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
            ctx
        )
        raise
    try:
        channel_settings = Room(
            channel_id = record['channel_id'],
            edit_count = record['edit_count'],
            last_edit_at = datetime.fromisoformat(record['last_edit_at']),
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
async def _update_room(ctx: discord.ApplicationContext, channel_id: int, **kwargs) -> None:
    """Updates room settings. Use Room.update() to trigger this.

    Arguments
    ---------
    ctx: Context.
    channel_id: int
    kwargs (column=value):
        channel_id: int
        edit_count: int
        last_edit_at: datetime without microseconds
        owner_id: int

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if not kwargs are passed (need to pass at least one)
    Also logs all error to the database.
    """
    table = 'rooms'
    function_name = 'update_room'
    if not kwargs:
        await log_error(
            INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name),
            ctx
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    await get_room(ctx, channel_id) # Makes sure the record exists
    try:
        cur = PINBOT_DB.cursor()
        sql = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['channel_id_old'] = channel_id
        sql = f'{sql} WHERE channel_id = :channel_id_old'
        cur.execute(sql, kwargs)
    except sqlite3.Error as error:
        await log_error(
            INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
            ctx
        )
        raise