# views.py
"""Contains views for components"""

from typing import Optional

import discord

from resources import emojis


class CustomButton(discord.ui.Button):
    """Custom Button"""
    def __init__(self, style: discord.ButtonStyle, custom_id: str, label: Optional[str],
                 emoji: Optional[discord.PartialEmoji] = None):
        super().__init__(style=style, custom_id=custom_id, label=label, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.custom_id
        await interaction.message.edit(view=None)
        self.view.stop()


class ConfirmCancelView(discord.ui.View):
    """View with confirm and cancel button.

    Args: ctx, labels: Optional[list[str]]

    Also needs the message with the view, so do view.message = await ctx.interaction.original_message().
    Without this message, buttons will not be disabled when the interaction times out.

    Returns 'confirm', 'cancel' or None (if timeout/error)
    """
    def __init__(self, ctx: discord.ApplicationContext, labels: Optional[list[str]] = [None,None],
                 message: Optional[discord.Message] = None):
        super().__init__(timeout=10)
        self.value = None
        self.message = message
        self.user = ctx.author
        self.label_confirm = labels[0]
        self.label_cancel = labels[1]
        self.add_item(CustomButton(style=discord.ButtonStyle.green,
                                    custom_id='confirm',
                                    label=self.label_confirm,
                                    emoji = emojis.CHECK_WHITE))
        self.add_item(CustomButton(style=discord.ButtonStyle.red,
                                    custom_id='cancel',
                                    label=self.label_cancel,
                                    emoji = emojis.CROSS_WHITE))


    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return False
        return True

    async def on_timeout(self):
        self.value = None
        if self.message is not None:
            await self.message.edit(view=None)
        self.stop()