"""discord api connection"""

import asyncio
import logging
import os

import discord
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession

from config import load_config
from database.connection import DatabaseSingleton
from logger import setup_logger
from utils.create_channels import (
    get_create_channel,
)
from utils.server_settings import add_guild, has_guild
from utils.voice_channels import (
    add_voice_channel,
    get_voice_channel,
    remove_voice_channel,
)

env_config = load_config()

logger = logging.getLogger("bot")
setup_logger(logger)


class JoinToCreateBot(commands.AutoShardedBot):
    """Bot setup class."""

    def __init__(self, *args, **kwargs):
        self.logger = logger
        self.config = env_config
        self.db = DatabaseSingleton(env_config.db)
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.db.init_db()
        self.remove_command("help")
        await self.load_cogs()
        async with self.db.create_session() as session:
            async for guild in self.fetch_guilds():
                if not await has_guild(session, guild.id):
                    await add_guild(session, guild, {})
                    logger.info(f'Added guild "{guild.name}"')

        logger.info("Bot started")

    async def load_cogs(self):
        for file in os.listdir(os.path.dirname(__file__) + "/cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                await bot.load_extension(f"cogs.{name}")
                self.logger.info(f"Loaded cog: {name}")


intents = discord.Intents.default()
intents.voice_states = True
bot = JoinToCreateBot(command_prefix="!", intents=intents)


async def on_voice_channel_join(
    session: AsyncSession, member: discord.Member, after: discord.VoiceState
):
    if after.channel is None:
        return

    category = after.channel.category
    if category is None:
        return

    create_channel = await get_create_channel(
        session, member.guild.id, after.channel.id
    )
    if create_channel is None:
        return

    new_channel = await category.create_voice_channel(
        f"{member.display_name}'s channel", position=after.channel.position
    )
    await add_voice_channel(session, member.guild.id, new_channel.id)
    await member.move_to(new_channel, reason="Moved user to generated channel")


async def on_voice_channel_leave(
    session: AsyncSession, member: discord.Member, before: discord.VoiceState
):
    if before.channel is None:
        return

    db_channel = await get_voice_channel(session, member.guild.id, before.channel.id)
    if db_channel is None:
        return

    total_users = len(before.channel.members)
    if total_users <= 0:
        await remove_voice_channel(session, member.guild.id, before.channel.id)
        await before.channel.delete()


@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState | None,
    after: discord.VoiceState | None,
):
    async with bot.db.create_session() as session:
        if member.guild.id is None:
            return
        if before.channel is None and after.channel is not None:  # join
            await on_voice_channel_join(session, member, after)

        if before.channel is not None and after.channel is None:  # leave
            await on_voice_channel_leave(session, member, before)

        if (
            before.channel is not None
            and after.channel is not None
            and before.channel.id != after.channel.id
        ):
            await on_voice_channel_leave(session, member, before)
            await on_voice_channel_join(session, member, after)


@bot.event
async def on_guild_join(guild: discord.Guild):
    async with bot.db.create_session() as session:
        if not await has_guild(session, guild.id):
            await add_guild(session, guild, {})
            logger.info(f'Added guild "{guild.name}"')


@bot.event
async def on_command_error(ctx, error):
    """dont give a error if a command doesn't exist"""
    if isinstance(
        error,
        (
            commands.CommandNotFound,
            commands.MissingRequiredArgument,
            commands.MissingRole,
        ),
    ):
        return
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            color=0xE74C3C, description="Your not allowed to use this command"
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.NoPrivateMessage):
        embed = discord.Embed(
            color=0xE74C3C,
            description="This command can only be used within a community, not in DM",
        )
        await ctx.send(embed=embed)
    else:
        raise error


@bot.event
async def on_ready():
    """After bot is logged into discord"""
    await bot.tree.sync()


async def main() -> None:
    async with bot:
        await bot.start(env_config.bot.discord_bot_token)


if __name__ == "__main__":
    asyncio.run(main())
