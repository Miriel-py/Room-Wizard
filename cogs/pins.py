# main.py
"""Contains events and commands to pin and unpin messages"""

import discord
from discord.commands import message_command
from discord.ext import commands


class PinsCog(commands.Cog):
    """Cog with events and commands to pin and unpin messages"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Commands
    @message_command(name="Pin Message")
    @commands.bot_has_permissions(read_message_history=True, manage_messages=True)
    async def pin(self, ctx: discord.ApplicationContext, message: discord.Message) -> None:
        if message.pinned:
            await ctx.respond('This message is already pinned.', ephemeral=True)
            return
        await message.pin()
        await ctx.respond('Message pinned!', ephemeral=True)

    @message_command(name="Unpin Message")
    @commands.bot_has_permissions(read_message_history=True, manage_messages=True)
    async def unpin(self, ctx: discord.ApplicationContext, message: discord.Message) -> None:
        if not message.pinned:
            await ctx.respond('This message is not pinned.', ephemeral=True)
            return
        await message.unpin()
        await ctx.respond('Message unpinned!', ephemeral=True)

     # Events
    @commands.Cog.listener()
    @commands.bot_has_permissions(send_messages=True, read_message_history=True, manage_messages=True)
    async def on_raw_reaction_add(self, event):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(event.channel_id)
        message = await channel.fetch_message(event.message_id)
        if str(event.emoji) == "📌":
            await message.pin()

    @commands.Cog.listener()
    @commands.bot_has_permissions(send_messages=True, read_message_history=True, manage_messages=True)
    async def on_raw_reaction_remove(self, event):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(event.channel_id)
        message = await channel.fetch_message(event.message_id)
        if str(event.emoji) == "📌":
            if not ":pushpin:" in [event.emoji for reaction in message.reactions]:
                await message.unpin()


# Initialization
def setup(bot):
    bot.add_cog(PinsCog(bot))