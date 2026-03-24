import os
import random
import discord
import aiohttp
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

# Load .env file
load_dotenv()


class Memes(commands.Cog):
    """Fetches memes from the internet!"""

    def __init__(self, bot):
        self.bot = bot
        self.TENOR_API_KEY = os.getenv("TENOR_API_KEY")

        # Define slash command group
        self.meme_group = app_commands.Group(
            name="memes",
            description="Meme-related commands"
        )

    async def fetch_tenor_gif(self, query):
        """Fetch a random meme GIF from Tenor."""
        if not self.TENOR_API_KEY:
            print("❌ TENOR_API_KEY not found in .env")
            return None

        url = f"https://tenor.googleapis.com/v2/search?q={query}&key={self.TENOR_API_KEY}&limit=10"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    if "results" not in data or not data["results"]:
                        print(f"⚠️ Tenor API returned no results for '{query}'")
                        return None

                    random_gif = random.choice(data["results"])
                    return random_gif.get("media_formats", {}).get("gif", {}).get("url")

                else:
                    print(f"❌ Tenor API Error: {response.status}")
                    return None

    async def random_command(self, interaction: discord.Interaction):
        """Fetches a random meme GIF."""
        await interaction.response.defer()

        gif_url = await self.fetch_tenor_gif("funny meme")
        if not gif_url:
            await interaction.followup.send(
                "⚠️ Couldn't fetch a meme. Try again later!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Here's a random meme for you!",
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)
        await interaction.followup.send(embed=embed)

    async def wholesome_command(self, interaction: discord.Interaction):
        """Fetches a wholesome meme GIF."""
        await interaction.response.defer()

        gif_url = await self.fetch_tenor_gif("wholesome meme")
        if not gif_url:
            await interaction.followup.send(
                "⚠️ Boooo.. I couldn't fetch a wholesome meme. Try again later!",
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
        """Registers the slash command group dynamically."""
        if not self.bot.tree.get_command("memes"):
            self.meme_group.command(
                name="random",
                description="Posts a random GIF meme."
            )(self.random_command)

            self.meme_group.command(
                name="wholesome",
                description="Posts a random wholesome GIF meme."
            )(self.wholesome_command)

            self.bot.tree.add_command(self.meme_group)


async def setup(bot):
    await bot.add_cog(Memes(bot))