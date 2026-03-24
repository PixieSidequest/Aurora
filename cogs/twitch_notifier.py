import os
import discord
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_FOLLOW_CHANNELS = os.getenv("TWITCH_FOLLOW_CHANNELS", "")
TWITCH_NOTIFICATION_CHANNEL_ID = int(os.getenv("TWITCH_NOTIFICATION_CHANNEL_ID", "0"))

# Convert comma-separated usernames into a clean list
TWITCH_USER_LIST = [
    user.strip() for user in TWITCH_FOLLOW_CHANNELS.split(",") if user.strip()
]

# Create a mapping of Twitch usernames -> Discord notification channel ID
TWITCH_CHANNELS = {
    username: TWITCH_NOTIFICATION_CHANNEL_ID
    for username in TWITCH_USER_LIST
}

# Debug prints
print(
    f"TWITCH_CLIENT_ID Loaded: {TWITCH_CLIENT_ID[:5]}*****"
    if TWITCH_CLIENT_ID else "❌ TWITCH_CLIENT_ID NOT FOUND"
)
print(
    f"TWITCH_CLIENT_SECRET Loaded: {TWITCH_CLIENT_SECRET[:5]}*****"
    if TWITCH_CLIENT_SECRET else "❌ TWITCH_CLIENT_SECRET NOT FOUND"
)

if not TWITCH_USER_LIST:
    print("⚠️ No Twitch channels set. Twitch notifications disabled.")

if not TWITCH_NOTIFICATION_CHANNEL_ID:
    print("⚠️ No Discord notification channel ID set.")


class TwitchNotifier(commands.Cog):
    """Sends Discord notifications when configured Twitch streamers go live."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.twitch = None
        self.live_streams = {}
        self.check_twitch_streams.start()

    async def get_twitch(self):
        """Authenticate with the Twitch API."""
        if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
            print("❌ Twitch credentials missing in .env")
            return

        self.twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
        await self.twitch.authenticate_app([])

    async def get_stream_data(self, username: str):
        """Fetch stream details for a given Twitch username."""
        if not self.twitch:
            return None

        user = await first(self.twitch.get_users(logins=[username]))
        if not user:
            return None

        async for stream in self.twitch.get_streams(user_id=[user.id]):
            return {
                "title": stream.title,
                "game": stream.game_name,
                "viewers": stream.viewer_count,
                "profile_image": user.profile_image_url,
                "url": f"https://twitch.tv/{username}"
            }

        return None

    async def is_live(self, username: str) -> bool:
        """Return True if the Twitch user is live."""
        stream_data = await self.get_stream_data(username)
        return stream_data is not None

    @commands.command()
    async def testnotify(self, ctx: commands.Context):
        """Test whether the bot can send a message in the configured channel."""
        if not TWITCH_NOTIFICATION_CHANNEL_ID:
            await ctx.send("❌ TWITCH_NOTIFICATION_CHANNEL_ID is not set in .env")
            return

        channel = self.bot.get_channel(TWITCH_NOTIFICATION_CHANNEL_ID)

        if channel:
            await channel.send("✅ Aurora has permission to send messages here!")
        else:
            await ctx.send("❌ Channel ID is incorrect or the bot lacks permissions.")

    @commands.command()
    async def check_live(self, ctx: commands.Context, username: str = None):
        """Manually check whether a configured Twitch user is live."""
        if not TWITCH_USER_LIST:
            await ctx.send("❌ No Twitch users are configured in .env")
            return

        username = username or TWITCH_USER_LIST[0]

        if username not in TWITCH_CHANNELS:
            await ctx.send(f"❌ {username} is not being monitored.")
            return

        is_live = await self.is_live(username)
        await ctx.send(
            f"✅ {username} is LIVE!" if is_live else f"❌ {username} is not live."
        )

    @tasks.loop(minutes=2)
    async def check_twitch_streams(self):
        """Check Twitch every 2 minutes for configured live streams."""
        if not TWITCH_CHANNELS:
            return

        if not self.twitch:
            await self.get_twitch()

        if not self.twitch:
            return

        for username, channel_id in TWITCH_CHANNELS.items():
            is_live = await self.is_live(username)

            if is_live and username not in self.live_streams:
                self.live_streams[username] = True
                await self.send_notification(username, channel_id)

            elif not is_live and username in self.live_streams:
                self.live_streams.pop(username)

    async def send_notification(self, username: str, channel_id: int):
        """Send a Discord embed when a Twitch streamer goes live."""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            print(f"❌ Could not find Discord channel with ID: {channel_id}")
            return

        stream_data = await self.get_stream_data(username)
        if not stream_data:
            return

        embed = discord.Embed(
            title=f"🔴 {username} is now LIVE!",
            description=(
                f"🎮 **Category:** {stream_data['game']}\n"
                f"👀 **Viewers:** {stream_data['viewers']}\n\n"
                f"📢 **Stream Title:** {stream_data['title']}"
            ),
            color=discord.Color.purple(),
            url=stream_data["url"]
        )
        embed.set_thumbnail(url=stream_data["profile_image"])
        embed.set_footer(text="Click the title to watch the stream!")

        await channel.send(embed=embed)

    @check_twitch_streams.before_loop
    async def before_check_twitch_streams(self):
        """Wait until the bot is ready before starting the Twitch check loop."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchNotifier(bot))