import os
import asyncio
import random
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get Discord Token from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Debug print to confirm it's loading
print(f"DISCORD_TOKEN Loaded: {DISCORD_TOKEN[:5]}*****" if DISCORD_TOKEN else "❌ DISCORD_TOKEN NOT FOUND")

# Set up bot with NO text prefix (slash commands only)
bot = commands.Bot(command_prefix=None, intents=discord.Intents.all())

async def change_status():
    """Cycles through different statuses every 10 minutes."""
    await bot.wait_until_ready()  # 🔹 Ensure bot is fully online before changing presence
    statuses = [
        discord.Game(name="VRChat ✨"),
        discord.Activity(type=discord.ActivityType.listening, name="Golden Hour by JVKE 🎶"),
        discord.Activity(type=discord.ActivityType.watching, name="the simulation 🖥️"),
        discord.Game(name="with the limits of AI 🤖"),
        discord.Activity(type=discord.ActivityType.competing, name="in a hotdog eating contest."),
        discord.Activity(type=discord.ActivityType.watching, name="Intersteller."),
    ]
    while not bot.is_closed():
        new_status = random.choice(statuses)
        await bot.change_presence(activity=new_status)
        print(f"🔄 Changing status to: {new_status.name}")  # Debug print
        await asyncio.sleep(600)  # Changes every 10 minutes

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} is online and ready!")

    # Load cogs dynamically (ONLY LOAD IF NOT ALREADY LOADED)
    async def load_cogs():
        cog_directory = "cogs"
        for filename in os.listdir(cog_directory):
            if filename.endswith(".py"):
                cog_name = f"{cog_directory}.{filename[:-3]}"
                if cog_name not in bot.extensions:  # Prevent duplicate loading
                    try:
                        await bot.load_extension(cog_name)
                        print(f"✅ Loaded cog: {filename}")
                    except Exception as e:
                        print(f"❌ Failed to load {filename}: {e}")

    await load_cogs()

# 🚨 TEMPORARY COMMAND CLEARING (Run once, if needed)
#    try:
#        await bot.tree.sync()  # Sync commands before clearing
#        bot.tree.clear_commands(guild=None)  # Reset command tree
#        await bot.tree.sync()  # Sync empty commands
#        print("🗑️ Cleared all commands from Discord!")
#    except Exception as e:
#        print(f"❌ Failed to clear commands: {e}")


    try:
        await bot.tree.sync()
        print("✅ Synced all commands with Discord!")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    bot.loop.create_task(change_status())  # Start status cycle

# Properly run the bot asynchronously
async def main():
    async with bot:
        await bot.start(DISCORD_TOKEN)

# Run the bot
asyncio.run(main())