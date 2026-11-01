import os
import random
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")


class Interactions(commands.Cog):
    """Fun interaction commands with anime GIFs."""

    def __init__(self, bot):
        self.bot = bot
        self.session = None

        self.actions = {
            "hugs": "anime hug",
            "slaps": "anime slap",
            "kisses": "anime kiss",
            "wave": "anime wave",
            "highfive": "anime high five",
            "blush": "anime blush",
            "pat": "anime pat",
            "cuddle": "anime cuddle",
            "poke": "anime poke",
            "stares": "anime stare",
            "dances": "anime dance",
            "boop": "anime boop",
            "snuggle": "anime snuggle",
            "headpat": "anime headpat",
            "smug": "anime smug",
            "bonk": "anime bonk",
            "wink": "anime wink",
            "shrug": "anime shrug",
            "cry": "anime cry"
        }

        self.interaction_group = app_commands.Group(
            name="interaction",
            description="Fun interaction commands"
        )

    async def fetch_gif(self, action):
        """Fetch a random GIF from GIPHY."""

        if not GIPHY_API_KEY:
            print("❌ GIPHY_API_KEY not configured")
            return None

        query = self.actions.get(action, action)

        url = "https://api.giphy.com/v1/gifs/search"

        params = {
            "api_key": GIPHY_API_KEY,
            "q": query,
            "limit": 25,
            "rating": "pg"
        }

        try:
            async with self.session.get(
                url, params=params
            ) as response:

                if response.status != 200:
                    error = await response.text()
                    print(
                        f"❌ GIPHY Error "
                        f"{response.status}: {error[:300]}"
                    )
                    return None

                data = await response.json()
                gifs = data.get("data", [])

                valid_gifs = [
                    gif["images"]["original"]["url"]
                    for gif in gifs
                    if gif.get("images", {})
                    .get("original", {})
                    .get("url")
                ]

                if not valid_gifs:
                    return None

                return random.choice(valid_gifs)

        except (aiohttp.ClientError, TimeoutError) as error:
            print(f"❌ GIF request failed: {error}")
            return None

    async def send_action(
        self,
        interaction: discord.Interaction,
        action: str,
        member: discord.Member
    ):
        """Send an interaction embed with a GIF."""

        await interaction.response.defer()

        gif_url = await self.fetch_gif(action)

        if not gif_url:
            await interaction.followup.send(
                f"⚠️ Couldn't fetch a {action} GIF. "
                "Try again later!",
                ephemeral=True
            )
            return

        # Avoid awkward grammar such as "hugss".
        verbs = {
            "hugs": "hugs",
            "slaps": "slaps",
            "kisses": "kisses",
            "stares": "stares",
            "dances": "dances"
        }

        verb = verbs.get(action, f"{action}s")

        embed = discord.Embed(
            description=(
                f"**{interaction.user.display_name} "
                f"{verb} {member.display_name}!** 💕"
            ),
            color=discord.Color.random()
        )

        embed.set_image(url=gif_url)

        await interaction.followup.send(embed=embed)

    def generate_command(self, action):
        """Create a slash command for an interaction."""

        async def interaction_command(
            interaction: discord.Interaction,
            member: discord.Member
        ):
            await self.send_action(
                interaction, action, member
            )

        return interaction_command

    async def cog_load(self):
        """Register commands and start HTTP session."""

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )

        try:
            if not self.bot.tree.get_command("interaction"):

                for action in self.actions:
                    cmd = self.generate_command(action)

                    self.interaction_group.command(
                        name=action,
                        description=(
                            f"{action.capitalize()} another user!"
                        )
                    )(cmd)

                self.bot.tree.add_command(
                    self.interaction_group
                )
        except Exception:
            await self.session.close()
            self.session = None
            raise

    async def cog_unload(self):
        """Close the HTTP session when unloaded."""

        if self.session:
            await self.session.close()


async def setup(bot):
    await bot.add_cog(Interactions(bot))