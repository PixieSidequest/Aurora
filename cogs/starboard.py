import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


def get_env_int(name: str, default: int | None = None) -> int:
    value = os.getenv(name)

    if value is None:
        if default is not None:
            return default
        raise ValueError(f"Missing required environment variable: {name}")

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


class Starboard(commands.Cog):
    """Simple reaction-based starboard using ⭐ reactions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starboard_channel_id = get_env_int("STARBOARD_CHANNEL_ID")
        self.star_threshold = get_env_int("STARBOARD_THRESHOLD", 3)

        # In-memory tracking for this first version.
        # key = original message ID, value = starboard message ID
        self.posted_messages: dict[int, int] = {}

    def build_embed(self, message: discord.Message, star_count: int) -> discord.Embed:
        embed = discord.Embed(
            description=message.content or "*No text content*",
            color=discord.Color.gold()
        )

        embed.set_author(
            name=str(message.author),
            icon_url=message.author.display_avatar.url
        )

        embed.add_field(
            name="Source",
            value=f"{message.channel.mention} | [Jump to message]({message.jump_url})",
            inline=False
        )

        embed.set_footer(text=f"⭐ {star_count} | Message ID: {message.id}")

        # Attach first image if present in embeds/attachments
        if message.attachments:
            first_attachment = message.attachments[0]
            if first_attachment.content_type and first_attachment.content_type.startswith("image"):
                embed.set_image(url=first_attachment.url)

        return embed

    async def get_star_count(self, message: discord.Message) -> int:
        for reaction in message.reactions:
            if str(reaction.emoji) == "⭐":
                return reaction.count
        return 0

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "⭐":
            return

        if payload.guild_id is None:
            return

        if payload.channel_id == self.starboard_channel_id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return

        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        except discord.Forbidden:
            return
        except discord.HTTPException:
            return

        if message.author.bot:
            return

        if message.id in self.posted_messages:
            return

        star_count = await self.get_star_count(message)
        if star_count < self.star_threshold:
            return

        starboard_channel = self.bot.get_channel(self.starboard_channel_id)
        if starboard_channel is None:
            return

        if not isinstance(starboard_channel, discord.TextChannel):
            return

        embed = self.build_embed(message, star_count)

        try:
            sent_message = await starboard_channel.send(
                content=f"⭐ **{star_count}** | {message.channel.mention}",
                embed=embed
            )
            self.posted_messages[message.id] = sent_message.id
        except discord.Forbidden:
            print("Missing permission to send messages in the starboard channel.")
        except discord.HTTPException as exc:
            print(f"Failed to post to starboard: {exc}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Starboard(bot))