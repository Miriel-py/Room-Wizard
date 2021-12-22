# rooms.py
"""Contains room commands"""

from datetime import datetime, timedelta
import discord
from discord.commands import Option, SlashCommandGroup
from discord.ext import commands

import database


class RoomsCog(commands.Cog):
    """Cog with room commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    setting = SlashCommandGroup(
        "set",
        "Set various settings",
    )

    setting_room = setting.create_subgroup(
        "room", "Set room settings"
    )

    get_setting = SlashCommandGroup(
        "get",
        "Get various settings",
    )

    get_setting_room = get_setting.create_subgroup(
        "room", "Get room settings"
    )

    reset_setting = SlashCommandGroup(
        "reset",
        "Remove various settings",
    )

    reset_setting_room = reset_setting.create_subgroup(
        "room", "Reset room settings"
    )

    rename = SlashCommandGroup(
        "rename",
        "Rename settings",
    )

    # Commands
    @setting_room.command(name='owner')
    @commands.has_permissions(manage_guild=True)
    async def set_room_owner(
        self,
        ctx: discord.ApplicationContext,
        room: Option(discord.TextChannel, 'Room the owner is set for'),
        owner: Option(discord.Member, 'The new owner')
    ) -> None:
        """Set the owner of a room"""
        if owner.bot:
            await ctx.respond('You can not assign a bot as the owner. Duh.')
            return
        room_settings: database.Room = await database.get_room(ctx, room.id)
        await room_settings.update(ctx, owner_id=owner.id)
        await ctx.respond(f'Done. **{owner.name}** is now the new owner of the room `{room.name}`.')

    @get_setting_room.command(name='owner')
    async def get_room_owner(self, ctx: discord.ApplicationContext) -> None:
        """Check the owner the current room"""
        room_settings: database.Room = await database.get_room(ctx, ctx.channel.id)
        if room_settings.owner_id is None:
            await ctx.respond(f'This room doesn\'t have an owner set.')
        else:
            owner = await ctx.guild.fetch_member(room_settings.owner_id)
            await ctx.respond(f'The owner of this room is **{owner.name}**.')

    @reset_setting_room.command(name='owner')
    @commands.has_permissions(manage_guild=True)
    async def reset_room_owner(
        self,
        ctx: discord.ApplicationContext,
        room: Option(discord.TextChannel, 'Room to reset the owner for')
    ) -> None:
        """Set the owner of a room"""
        room_settings: database.Room = await database.get_room(ctx, room.id)
        await room_settings.update(ctx, owner_id=None)
        if room_settings.owner_id is None:
            await ctx.respond('Done. This room doesn\'t have an owner set anymore.')
        else:
            await ctx.respond(f'Oops, something went wrong here, couldn\'t reset the owner.')

    @rename.command(name='room')
    async def rename_room(
        self,
        ctx: discord.ApplicationContext,
        field: Option(str, 'What you want to rename', choices=('Name','Topic')),
        text: Option(str, 'The new name or topic')
    ) -> None:
        """Renames the name or topic of a room. Please note that you can only do 2 changes every 10 minutes."""
        user_permissions = ctx.channel.permissions_for(ctx.author)
        room_settings: database.Room = await database.get_room(ctx, ctx.channel.id)
        if not user_permissions.manage_channels and room_settings.owner_id != ctx.author.id:
            await ctx.respond(f'Sorry **{ctx.author.name}**, you are not allowed to rename this room.')
            return
        if field == 'Name' and len(text) > 100:
            await ctx.respond(f'Sorry **{ctx.author.name}**, a room name is limited to 100 characters.')
            return
        if field == 'Topic' and len(text) > 1024:
            await ctx.respond(f'Sorry **{ctx.author.name}**, a room topic is limited to 1024 characters.')
            return
        if room_settings.edit_count >= 2 and room_settings.last_edit_at > datetime.utcnow() - timedelta(minutes=10):
            last_edit_relative = datetime.utcnow().replace(microsecond=0) - room_settings.last_edit_at
            ten_minutes = timedelta(minutes=10)
            next_edit_possible = ten_minutes - last_edit_relative
            minutes, seconds = divmod(next_edit_possible.total_seconds(), 60)
            await ctx.respond(
                f'Sorry **{ctx.author.name}**, you can only do 2 changes every 10 minutes.\n'
                f'You have to wait another {int(minutes)} minutes and {int(seconds)} seconds.'
            )
            return
        await ctx.defer()
        if field == 'Name':
            await ctx.channel.edit(name=text)
        else:
            await ctx.channel.edit(topic=text)
        edit_count = 1 if room_settings.edit_count >= 2 else room_settings.edit_count + 1
        await room_settings.update(ctx, edit_count=edit_count, last_edit_at=datetime.utcnow().replace(microsecond=0))
        await ctx.respond(f'The room {field.lower()} has been updated.')


# Initialization
def setup(bot):
    bot.add_cog(RoomsCog(bot))