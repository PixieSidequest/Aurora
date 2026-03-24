import random
import time
import discord
from discord.ext import commands
from discord import app_commands

class EightBall(commands.Cog):
    """Magic 8-Ball command with mood and annoyance tracking"""

    def __init__(self, bot):
        self.bot = bot
        self.user_8ball_requests = {}  # Tracks how often users ask

    @app_commands.command(name="8ball", description="Ask Aurora a question and receive a mystical answer!")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        """Ask the Magic 8-Ball a question and get a cryptic answer"""
        
        user_id = interaction.user.id
        current_time = time.time()

        # Track requests per user
        if user_id not in self.user_8ball_requests:
            self.user_8ball_requests[user_id] = []
        
        self.user_8ball_requests[user_id].append(current_time)

        # Remove old requests (older than 60 seconds)
        self.user_8ball_requests[user_id] = [
            t for t in self.user_8ball_requests[user_id] if current_time - t < 60
        ]

        # Annoyed responses if they spam too much
        if len(self.user_8ball_requests[user_id]) > 4:
            annoyed_responses = [
                "Ugh, again? Just flip a coin at this point. 🙄",
                "Really? Another one? You’re testing my patience...",
                "I'm not your personal life coach. Figure it out. 😒",
                "Maybe I should start charging you per question. 💰",
                "I'm ignoring you now. *poof* ✨",
            ]
            response = random.choice(annoyed_responses)
        else:
            # Normal 8ball responses
            responses = [
                "It is certain.", "Without a doubt.", "Yes – definitely.", "You may rely on it.",
                "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
                "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
                "Cannot predict now.", "Concentrate and ask again.",
                "Don't count on it.", "My reply is no.", "Outlook not so good.",
                "Very doubtful.", "Absolutely not.",
                "Do you really need a magic ball to tell you that?", "Hmm... let me think... nah.",
                "Are you sure you want to know?", "Wouldn't you like to know? 😉",
                "Ask me after a coffee.", "Oh honey, you already know the answer.",
                "If I had a dollar for every time someone asked me that..."
            ]

            mood_cog = interaction.client.get_cog("Mood")
            mood = mood_cog.mood if mood_cog else "curious"

            # Modify response based on GoldieLex's mood
            if mood == "sassy":
                response = random.choice(responses[-6:])  # Pick from the sassier responses
            else:
                response = random.choice(responses)  # Pick from all responses

        await interaction.response.send_message(f"🎱 **{response}**")

async def setup(bot):
    await bot.add_cog(EightBall(bot))