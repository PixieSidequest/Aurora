
import os
import random
import discord
import aiohttp

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

# Load environment variables
load_dotenv()


class Memes(commands.Cog):
    """Fetches random and wholesome GIF memes from GIPHY!"""

    def __init__(self, bot):
        self.bot = bot
        self.GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
        self.session = None

        # Define slash command group
        self.meme_group = app_commands.Group(
            name="memes",
            description="Meme-related commands"
        )

    async def fetch_giphy_gif(self, query):
        """Fetch a random GIF from GIPHY."""

        if not self.GIPHY_API_KEY:
            print("❌ GIPHY_API_KEY not found in .env")
            return None

        url = "https://api.giphy.com/v1/gifs/search"

        params = {
            "api_key": self.GIPHY_API_KEY,
            "q": query,
            "limit": 50,
            "rating": "pg"
        }

        try:
            async with self.session.get(
                url, params=params
            ) as response:

                if response.status != 200:
                    error = await response.text()
                    print(
                        f"❌ GIPHY API Error: "
                        f"{response.status} - {error[:300]}"
                    )
                    return None

                data = await response.json()
                gifs = data.get("data", [])

                # Collect GIFs with valid image URLs
                valid_gifs = []

                for gif in gifs:
                    images = gif.get("images", {})

                    gif_url = (
                        images.get("original", {}).get("url")
                        or images.get("fixed_height", {}).get("url")
                    )

                    if gif_url:
                        valid_gifs.append(gif_url)

                if not valid_gifs:
                    print(
                        f"⚠️ GIPHY returned no GIFs "
                        f"for '{query}'"
                    )
                    return None

                # Choose a random GIF
                return random.choice(valid_gifs)

        except (aiohttp.ClientError, TimeoutError) as error:
            print(f"❌ GIPHY request failed: {error}")
            return None

    async def random_command(
        self,
        interaction: discord.Interaction
    ):
        """Fetch a random funny meme GIF."""

        await interaction.response.defer()

        # Rotate search terms for more variety
        search_terms = [
            "funny meme",
            "reaction meme",
            "funny reaction gif",
            "internet meme",
            "comedy meme"
        ]

        query = random.choice(search_terms)
        gif_url = await self.fetch_giphy_gif(query)

        if not gif_url:
            await interaction.followup.send(
                "⚠️ Couldn't fetch a meme. Try again later!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Here's a random meme for you! 😂",
            color=discord.Color.random()
        )

        embed.set_image(url=gif_url)

        await interaction.followup.send(embed=embed)

    async def wholesome_command(
        self,
        interaction: discord.Interaction
    ):
        """Fetch a wholesome meme GIF."""

        await interaction.response.defer()

        search_terms = [
            "wholesome meme",
            "cute wholesome",
            "heartwarming reaction",
            "positive vibes",
            "you are amazing"
        ]

        query = random.choice(search_terms)
        gif_url = await self.fetch_giphy_gif(query)

        if not gif_url:
            await interaction.followup.send(
                "⚠️ Boooo.. I couldn't fetch a "
                "wholesome meme. Try again later!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Here's a wholesome meme! 💖",
            color=discord.Color.gold()
        )

        embed.set_image(url=gif_url)

        await interaction.followup.send(embed=embed)

    async def cog_load(self):
        """Register commands and initialize HTTP session."""

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )

        try:
            if not self.bot.tree.get_command("memes"):

                self.meme_group.command(
                    name="random",
                    description="Posts a random GIF meme."
                )(self.random_command)

                self.meme_group.command(
                    name="wholesome",
                    description="Posts a wholesome GIF meme."
                )(self.wholesome_command)

                self.bot.tree.add_command(self.meme_group)

        except Exception:
            await self.session.close()
            self.session = None
            raise

    async def cog_unload(self):
        """Close the HTTP session when the cog unloads."""

        if self.session:
            await self.session.close()


async def setup(bot):
    await bot.add_cog(Memes(bot))