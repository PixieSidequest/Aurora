import os
import asyncio
import discord
import yt_dlp
import requests
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

load_dotenv()


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.queue: list[tuple[str, str]] = []
        self.is_playing = False

    ytdl_options = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "source_address": "0.0.0.0",
    }

    ffmpeg_before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    ffmpeg_options = "-vn"

    music_group = app_commands.Group(
        name="music",
        description="Music player commands"
    )

    async def search_youtube(self, query: str):
        print(f"🔍 search_youtube called with query: {query}")

        if not self.youtube_api_key:
            print("❌ YOUTUBE_API_KEY not found in .env")
            return None, None

        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "key": self.youtube_api_key,
            "maxResults": 5,
            "type": "video",
            "videoCategoryId": "10",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                print(f"⚠️ No YouTube API results for: {query}")
                return None, None

            first_video = items[0]
            video_id = first_video["id"]["videoId"]
            title = first_video["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            print(f"✅ YouTube API result: {title}")
            return video_url, title

        except Exception as e:
            print(f"❌ YouTube API search error: {type(e).__name__}: {e}")
            return None, None

    async def extract_audio(self, video_url: str):
        print(f"🎧 extract_audio called with URL: {video_url}")
        loop = asyncio.get_running_loop()

        def run_extract():
            with yt_dlp.YoutubeDL(self.ytdl_options) as ydl:
                return ydl.extract_info(video_url, download=False)

        try:
            info = await loop.run_in_executor(None, run_extract)
            if not info:
                return None, None

            audio_url = info.get("url")
            title = info.get("title", "Unknown Title")

            if not audio_url:
                return None, None

            print(f"✅ Audio extracted: {title}")
            return audio_url, title

        except Exception as e:
            print(f"❌ yt-dlp extraction error: {type(e).__name__}: {e}")
            return None, None

    async def join_voice(self, interaction: discord.Interaction, announce: bool = True) -> bool:
        if not interaction.guild:
            return False

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ Join a voice channel first!", ephemeral=True)
            return False

        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client

        try:
            if vc and vc.is_connected():
                if vc.channel != channel:
                    await vc.move_to(channel)
                    if announce:
                        await interaction.followup.send(f"🔊 Moved to **{channel.name}**.")
                else:
                    print(f"🔊 Already in {channel.name}")
                return True

            await channel.connect(timeout=20.0, reconnect=False, self_deaf=True)
            if announce:
                await interaction.followup.send(f"🔊 Joined **{channel.name}**.")
            return True

        except Exception as e:
            print(f"❌ Voice error: {type(e).__name__}: {e}")
            await interaction.followup.send(
                f"❌ Voice connection failed.\n`{type(e).__name__}: {e}`",
                ephemeral=True
            )
            return False

    async def play_song(self, interaction: discord.Interaction, query: str):
        print(f"🎵 play_song called with query: {query}")

        voice_client = interaction.guild.voice_client if interaction.guild else None

        if not voice_client or not voice_client.is_connected():
            await interaction.followup.send("❌ I'm not connected to a voice channel.")
            return

        if self.is_playing or voice_client.is_playing():
            self.queue.append((query, query))
            await interaction.followup.send(
                f"🎶 Added **{query}** to the queue. Position: {len(self.queue)}"
            )
            return

        await self.start_playback(interaction, query)

    async def start_playback(self, interaction: discord.Interaction, query: str, title_hint: str | None = None):
        print(f"▶️ start_playback called with query: {query}")

        voice_client = interaction.guild.voice_client if interaction.guild else None
        if not voice_client or not voice_client.is_connected():
            self.is_playing = False
            await interaction.followup.send("❌ I’m not connected to a voice channel.")
            return

        video_url, api_title = await self.search_youtube(query)
        if not video_url:
            self.is_playing = False
            await interaction.followup.send("❌ Could not find a YouTube result for that.")
            await self.play_next(interaction)
            return

        audio_url, extracted_title = await self.extract_audio(video_url)
        if not audio_url:
            self.is_playing = False
            await interaction.followup.send("❌ Could not extract audio from that video.")
            await self.play_next(interaction)
            return

        final_title = title_hint or extracted_title or api_title or query
        self.is_playing = True
        await interaction.followup.send(f"🎵 Now playing: **{final_title}**")

        def after_playing(error):
            if error:
                print(f"❌ Playback error: {error}")
            self.bot.loop.create_task(self.play_next(interaction))

        try:
            source = discord.FFmpegPCMAudio(
                audio_url,
                before_options=self.ffmpeg_before_options,
                options=self.ffmpeg_options,
            )
            voice_client.play(source, after=after_playing)
            print("✅ Playback started")

        except Exception as e:
            print(f"❌ FFmpeg playback error: {type(e).__name__}: {e}")
            self.is_playing = False
            await interaction.followup.send(
                f"❌ Playback failed.\n`{type(e).__name__}: {e}`"
            )
            await self.play_next(interaction)

    async def play_next(self, interaction: discord.Interaction):
        self.is_playing = False
        voice_client = interaction.guild.voice_client if interaction.guild else None

        if not voice_client or not voice_client.is_connected():
            return

        if self.queue:
            next_query, next_title = self.queue.pop(0)
            await self.start_playback(interaction, next_query, next_title)
        else:
            print("📭 Queue is empty.")

    @music_group.command(name="join", description="Join your voice channel.")
    async def join_command(self, interaction: discord.Interaction):
        print("🔊 /music join called")
        await interaction.response.defer(ephemeral=True)
        await self.join_voice(interaction, announce=True)

    @music_group.command(name="play", description="Play music")
    async def play_command(self, interaction: discord.Interaction, query: str):
        print(f"🎵 /music play called with query: {query}")
        await interaction.response.defer(thinking=True)

        # Quietly ensure Aurora is in voice.
        if not await self.join_voice(interaction, announce=False):
            return

        await self.play_song(interaction, query)

    @music_group.command(name="skip", description="Skip the current song.")
    async def skip_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        voice_client = interaction.guild.voice_client if interaction.guild else None
        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
                await interaction.followup.send("⏭ Skipped the current song.")
            else:
                await interaction.followup.send("⚠️ Nothing is currently playing.")
        else:
            await interaction.followup.send("❌ I’m not in a voice channel!")

    @music_group.command(name="leave", description="Leave the voice channel.")
    async def leave_command(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client if interaction.guild else None

        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            self.queue.clear()
            self.is_playing = False
            await interaction.response.send_message("👋 Left the voice channel.")
        else:
            await interaction.response.send_message("❌ I’m not connected to a voice channel.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if self.bot.user and member.id == self.bot.user.id:
            print(
                f"🔊 Bot voice state update | "
                f"before: {getattr(before.channel, 'name', None)} "
                f"-> after: {getattr(after.channel, 'name', None)}"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))