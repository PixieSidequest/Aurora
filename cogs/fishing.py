import os
import random
import json
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# File to store fishing progress
DATA_FILE = "fishing_data.json"


class Fishing(commands.Cog):
    """Advanced Fishing simulator with achievements, tournaments, and unlockable gear"""

    def __init__(self, bot):
        self.bot = bot
        self.user_fishing_stats = {}
        self.load_data()  # Load saved fishing stats on startup

        # ✅ Define Slash Command Group for structured commands
        self.fishing_group = app_commands.Group(name="fishing", description="Fishing-related commands")

    def save_data(self):
        """Saves fishing stats to a JSON file"""
        with open(DATA_FILE, "w") as file:
            json.dump(self.user_fishing_stats, file, indent=4)

    def load_data(self):
        """Loads fishing stats from a JSON file"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as file:
                self.user_fishing_stats = json.load(file)
        else:
            self.user_fishing_stats = {}  # If no file exists, start fresh

    def get_fishing_stats(self, user_id):
        """Gets the user's current fishing level, XP, rod, and achievements"""
        if str(user_id) not in self.user_fishing_stats:
            self.user_fishing_stats[str(user_id)] = {
                "xp": 0, "level": 1, "rod": "Basic Rod", "achievements": []
            }
        return self.user_fishing_stats[str(user_id)]

    def add_fishing_xp(self, user_id, xp_amount):
        """Adds XP to the user and levels up if necessary"""
        stats = self.get_fishing_stats(user_id)

        # Bonus XP based on rod type
        rod_xp_boost = {
            "Basic Rod": 1.0, "Advanced Rod": 1.2, "Master Rod": 1.5, "Legendary Rod": 2.0
        }
        boost = rod_xp_boost.get(stats["rod"], 1.0)
        stats["xp"] += int(xp_amount * boost)

        # Level-up system (every 100 XP * level)
        while stats["xp"] >= stats["level"] * 100:
            stats["xp"] -= stats["level"] * 100
            stats["level"] += 1

        self.save_data()  # ✅ Save progress after XP gain!
        return stats["level"], stats["xp"]

    async def fish_command(self, interaction: discord.Interaction):
        """Cast your line and see what you catch!"""
        user_id = str(interaction.user.id)
        stats = self.get_fishing_stats(user_id)
        level = stats["level"]

        catches = {
            "Common Fish": ["🐟 A small trout", "🐠 A clownfish", "🎣 A bass", "🐡 A pufferfish"],
            "Uncommon Fish": ["🐙 An octopus!", "🦀 A crab", "🦑 A squid!", "🐠 A parrotfish"],
            "Rare Fish": ["🐋 A baby whale?!", "🦈 A shark!", "🐢 A sea turtle", "🐉 A sea dragon!!"],
            "Trash": ["🗑 A soggy boot", "🥤 A plastic bottle", "🦴 A fish skeleton"],
            "Treasure": ["💎 A diamond!", "👑 A pirate’s lost crown!", "💰 A sunken treasure chest!"],
            "Legendary Catch": ["🌊 **Poseidon's Trident!**", "🐉 **A mythical leviathan!!**", "🔥 **A golden phoenix fish?!**"]
        }

        chances = {
            "Common Fish": max(50 - level * 2, 20), "Uncommon Fish": min(25 + level, 40),
            "Rare Fish": min(10 + level // 2, 20), "Trash": max(10 - level // 3, 5),
            "Treasure": min(5 + level // 4, 15), "Legendary Catch": 1
        }

        catch_type = random.choices(list(chances.keys()), weights=list(chances.values()), k=1)[0]
        catch = random.choice(catches[catch_type])
        xp_gain = {"Common Fish": 10, "Uncommon Fish": 20, "Rare Fish": 50, "Trash": 5, "Treasure": 100, "Legendary Catch": 500}
        new_level, xp = self.add_fishing_xp(user_id, xp_gain[catch_type])

        await interaction.response.send_message(
            f"🎣 **{interaction.user.name} casts a line...**\n"
            f"🎣 **{catch}** (**{catch_type}**!)\n"
            f"📈 **Fishing XP:** {xp}/{new_level * 100} | 🎖 **Level {new_level}** | 🎣 **Rod: {stats['rod']}**"
        )

    async def leaderboard_command(self, interaction: discord.Interaction):
        """Shows the top fishers in the server"""
        sorted_users = sorted(self.user_fishing_stats.items(), key=lambda x: x[1]["level"], reverse=True)
        leaderboard_text = "**🎣 Fishing Leaderboard**\n"

        for i, (user_id, stats) in enumerate(sorted_users[:5], start=1):
            user = self.bot.get_user(int(user_id))  # Convert back to int
            leaderboard_text += f"🏆 **{i}. {user.name if user else 'Unknown'}** - Level {stats['level']} | XP: {stats['xp']}/{stats['level'] * 100}\n"

        await interaction.response.send_message(leaderboard_text)

    async def cog_load(self):
        """Registers the slash command group dynamically"""
        if not self.bot.tree.get_command("fishing"):
            # ✅ Add fishing commands dynamically
            self.fishing_group.command(name="fish", description="Cast your line and see what you catch!")(self.fish_command)
            self.fishing_group.command(name="leaderboard", description="Shows the top fishers in the server")(self.leaderboard_command)

            # ✅ Register the full command group
            self.bot.tree.add_command(self.fishing_group)

async def setup(bot):
    """Adds the Fishing cog to the bot"""
    await bot.add_cog(Fishing(bot))