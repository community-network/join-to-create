"""User management"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import JoinToCreateBot
from utils.create_channels import (
    add_create_channel,
    get_create_channel,
    get_create_channels,
    remove_create_channel,
)


class Admin(commands.Cog):
    def __init__(self, bot: JoinToCreateBot):
        self.bot = bot
        self.logger = logging.getLogger("admin")

    group = app_commands.Group(
        name="admin", description="Commands meant only for admins"
    )

    create_channel_group = app_commands.Group(
        name="create_channels", description="Change the create channels", parent=group
    )

    async def channel_name_autocomplete_parents(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete channel names"""
        async with self.bot.db.create_session() as session:
            if interaction.guild is None:
                return []
            voice_channel_ids = await get_create_channels(session, interaction.guild.id)
            return [
                app_commands.Choice(name=channel.name, value=str(channel.id))
                for channel in interaction.guild.voice_channels
                if channel.id in voice_channel_ids
                and channel.name.lower().startswith(current.lower())
            ][:25]

    async def channel_name_autocomplete_unmanaged(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete channel names"""
        async with self.bot.db.create_session() as session:
            if interaction.guild is None:
                return []
            voice_channel_ids = await get_create_channels(session, interaction.guild.id)
            return [
                app_commands.Choice(name=channel.name, value=str(channel.id))
                for channel in interaction.guild.voice_channels
                if channel.id not in voice_channel_ids
                and channel.name.lower().startswith(current.lower())
            ][:25]

    @create_channel_group.command(name="add", description="Add a create channel")
    @app_commands.describe(
        channel="Select a channel to add",
    )
    @app_commands.guild_only()
    @app_commands.autocomplete(channel=channel_name_autocomplete_unmanaged)
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def add_tracked_channel(
        self,
        interaction: discord.Interaction,
        channel: str,
    ) -> None:
        """Add a tracked channel"""
        await interaction.response.defer()
        if interaction.guild_id is None:
            return  # is already set to guild_only
        try:
            channel_id = int(channel)
        except ValueError:
            await interaction.followup.send(
                "Voice channel wasn't found", ephemeral=True
            )
            return

        if interaction.guild is None:
            return  # is already set to guild_only
        voice_channel = interaction.guild.get_channel(channel_id)
        if not isinstance(voice_channel, discord.VoiceChannel):
            await interaction.followup.send(
                "Voice channel wasn't found", ephemeral=True
            )
            return

        async with self.bot.db.create_session() as session:
            existing_channel = await get_create_channel(
                session, interaction.guild_id, channel_id=channel_id
            )
            if existing_channel is not None:
                await interaction.followup.send(
                    "Channel is already added", ephemeral=True
                )
                return

            await add_create_channel(
                session,
                interaction.guild_id,
                channel_id,
            )
            await interaction.followup.send("Added the voice channel", ephemeral=True)

    @create_channel_group.command(name="list", description="List create channels")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def list_tracked_channels(self, interaction: discord.Interaction) -> None:
        """List parent channels"""
        await interaction.response.defer()
        if interaction.guild_id is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            description = ""
            channel_ids = await get_create_channels(session, interaction.guild_id)
            for channel_id in channel_ids:
                description += f"<#{channel_id}>\n"

            if len(channel_ids) <= 0:
                await interaction.followup.send(
                    "No parent channels are tracked", ephemeral=True
                )
                return

            embed = discord.Embed(
                title="Current parent channels:", description=description
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @create_channel_group.command(name="remove", description="Remove a parent channel")
    @app_commands.guild_only()
    @app_commands.autocomplete(channel=channel_name_autocomplete_parents)
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_tracked_channel(
        self, interaction: discord.Interaction, channel: str
    ) -> None:
        """Remove a parent channel"""
        await interaction.response.defer()
        if interaction.guild_id is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            existing_channel = await get_create_channel(
                session, interaction.guild_id, channel_id=int(channel)
            )
            if existing_channel is not None:
                await remove_create_channel(session, interaction.guild_id, int(channel))

                await interaction.followup.send(
                    "Removed the parent channel", ephemeral=True
                )
                return

            await interaction.followup.send(
                "Parent channel wasn't tracked", ephemeral=True
            )


async def setup(bot: JoinToCreateBot) -> None:
    """Setup the cog within discord.py lib"""
    await bot.add_cog(Admin(bot))
