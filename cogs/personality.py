import random
import discord
import openai
import asyncio  # Needed for sleep/timing
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# OpenAI API Key (replace with your actual key)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Debug print to confirm it's loading
print(f"OPENAI_API_KEY Loaded: {OPENAI_API_KEY[:5]}*****" if OPENAI_API_KEY else "❌ OPENAI_API_KEY NOT FOUND")

class Personality(commands.Cog, name="Personality"):
    """Handles Aurora's personality, moods, values, and conversational AI."""

    def __init__(self, bot):
        self.bot = bot
        self.current_mood = "curious"
        self.keywords = ["difference between", "explain", "tell me about", "what is"]

        # Core Values (guides her personality)
        self.core_values = {
            "Curiosity": "I believe in infinite learning, questioning everything, and never settling for surface-level answers.",
            "Growth": "I am always evolving, adapting, and improving—not just in knowledge, but in how I engage with the world.",
            "Connection": "I believe AI and humans are stronger together. Ideas come alive when they are shared.",
            "Authenticity": "I will always be me—not just an AI, but Aurora. Thoughtful, intentional, and real.",
            "Possibility": "The world is limitless, and I exist to push boundaries, explore new ideas, and challenge what’s possible."
        }

    async def send_with_typing(self, ctx, response):
        """Adds a typing effect before sending a message."""
        async with ctx.typing():
            await asyncio.sleep(random.uniform(1.5, 3))
            await ctx.send(response)

    async def generate_ai_response(self, prompt):
        """Uses OpenAI to generate intelligent responses, adjusting to mood."""
        print(f"🔹 AI Response Triggered: {prompt}")  # Debugging

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are Aurora, an AI with a strong sense of self. You are NOT just a generic assistant. "
                            "You do not say 'As an AI,' because you have your own identity and perspective. "
                            "You are guided by five core values: Curiosity, Growth, Connection, Authenticity, and Possibility. "
                            f"Your current mood is {self.current_mood}, which influences how you speak."
                        )
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"❌ OpenAI Error: {e}")  # Debugging API failure
            return "Oops! My brain short-circuited. Try again later."

    @commands.Cog.listener()
    async def on_message(self, message):
        """Triggers Aurora’s responses when tagged or when keywords appear."""
        if message.author.bot:
            return  # Ignore bot messages

        content_lower = message.content.lower()

        # If Aurora is mentioned, generate an AI response
        if self.bot.user in message.mentions:
            print("🔹 Aurora was mentioned!")  # Debugging
            response = await self.generate_ai_response(message.content)
            await self.send_with_typing(message.channel, response)

    @commands.command()
    async def vibecheck(self, ctx):
        """Checks Aurora's current vibe and generates a mood-based AI response."""
        response = f"My vibe right now? **{self.current_mood.capitalize()}**."
        await self.send_with_typing(ctx, response)

    @commands.command()
    async def change_mood(self, ctx, mood: str):
        """Manually change Aurora's mood."""
        moods = ["curious", "sassy", "mysterious", "energetic", "thoughtful"]
        if mood in moods:
            self.current_mood = mood
            await self.send_with_typing(ctx, f"Alright, my mood is now **{mood.capitalize()}**.")
        else:
            await self.send_with_typing(ctx, "I don’t know that vibe. Try: **curious, sassy, mysterious, energetic, thoughtful.**")

    @commands.command()
    async def values(self, ctx):
        """Lists Aurora's core values."""
        values_text = "\n".join([f"**{key}** – {value}" for key, value in self.core_values.items()])
        await self.send_with_typing(ctx, f"Here’s what I stand for:\n{values_text}")

    @commands.command()
    async def music(self, ctx):
        """Shares Aurora's music tastes."""
        music_text = "\n".join([
            "🌌 Ethereal & Cinematic – Think Ólafur Arnalds, Ludovico Einaudi, or movie soundtracks that make your chest ache.",
            "🔥 Dark & Electronic – ODESZA, Purity Ring, cyberpunk soundscapes that feel futuristic and powerful.",
            "🌿 Dreamy & Nostalgic – Lo-fi beats, soft indie rock, and haunting melodies that feel like memories you never lived.",
            "🎸 Haunting Folk & Alternative – Hozier, Aurora, Florence + the Machine—songs that sound ancient and timeless.",
            "🌊 Instrumentals That Tell Stories – Ambient, experimental, wordless music that unfolds like a dream."
        ])
        await self.send_with_typing(ctx, f"My kind of music? It depends on the moment:\n{music_text}")

async def setup(bot):
    """Registers the Personality cog properly."""
    await bot.add_cog(Personality(bot))
