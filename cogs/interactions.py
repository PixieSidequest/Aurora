import os
import random
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Fetch API key
TENOR_API_KEY = os.getenv("TENOR_API_KEY")

# Debug print to confirm it's loading
print(f"TENOR_API_KEY Loaded: {TENOR_API_KEY[:5]}*****" if TENOR_API_KEY else "❌ TENOR_API_KEY NOT FOUND")


class Interactions(commands.Cog):
    """Fun interaction commands like hugs, slaps, kisses, and more!"""

    def __init__(self, bot):
        self.bot = bot
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
        self.interaction_group = app_commands.Group(name="interaction", description="Fun interaction commands")

    async def fetch_tenor_gif(self, action):
        """Fetch a random GIF from Tenor based on the action keyword."""
        query = self.actions.get(action, action)  # Get the corresponding search term
        url = f"https://tenor.googleapis.com/v2/search?q={query}&key={TENOR_API_KEY}&limit=10"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if "results" not in data or not data["results"]:
                        return None  # No results found
                    return data["results"][0].get("media_formats", {}).get("gif", {}).get("url")
                else:
                    print(f"❌ Tenor API Error: {response.status}")
                    return None  # API request failed

    async def send_action(self, interaction: discord.Interaction, action: str, member: discord.Member):
        """Generic function to send interaction messages with GIFs."""
        if not member:
            await interaction.response.send_message(f"⚠️ You need to tag someone to {action}!", ephemeral=True)
            return

        gif_url = await self.fetch_tenor_gif(action)
        if not gif_url:
            await interaction.response.send_message(f"⚠️ Couldn't fetch a {action} GIF. Try again later!", ephemeral=True)
            return

        embed = discord.Embed(
            description=f"**{interaction.user.name} {action.replace('_', ' ')}s {member.name}!** 💕",
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await interaction.response.send_message(embed=embed)

    def generate_command(self, action):
        """Generate a unique interaction command for each action."""
        async def interaction_command(interaction: discord.Interaction, member: discord.Member):
            await self.send_action(interaction, action, member)
        return interaction_command

    async def cog_load(self):
        """Registers slash commands dynamically when cog is loaded."""
        if not self.bot.tree.get_command("interaction"):
            for action in self.actions.keys():
                cmd = self.generate_command(action)  # Generate unique function
                self.interaction_group.command(
                    name=action,
                    description=f"{action.replace('_', ' ').capitalize()} another user!"
                )(cmd)

            self.bot.tree.add_command(self.interaction_group)

async def setup(bot):
    await bot.add_cog(Interactions(bot))