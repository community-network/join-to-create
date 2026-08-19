"""Non-grouped commands"""

import discord
from discord import app_commands
from discord.ext import commands

from bot import JoinToCreateBot


class OtherCommands(commands.Cog):
    """Other commands"""

    def __init__(self, bot: JoinToCreateBot):
        self.bot = bot

    @app_commands.command(name="help", description="See more info about the bot")
    async def help_command(self, interaction: discord.Interaction):
        """Main help command"""
        await interaction.response.defer()
        embed = discord.Embed(
            color=0xFFA500,
            title="Help for the Join-to-create bot",
            description="This bot will automatically can track specific voice channels you make. "
            'And if a user joins it, it will create a channel named "user\'s channel".'
            "And it will automatically remove the user's channel if empty."
            'To set up the bot, use "/admin create_channels add" to add a voice channel.',
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: JoinToCreateBot) -> None:
    """Setup the cog within discord.py lib"""
    await bot.add_cog(OtherCommands(bot))
