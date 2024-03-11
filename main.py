import main
import discord
from discord.ext import commands
from discord import Intents
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
import os
from dotenv import load_dotenv

load_dotenv()

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Event listener for when the bot has switched from offline to online
@bot.event
async def on_ready():
    guild_count = 0
    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
        guild_count += 1
    print(f"SampleDiscordBot is in {guild_count} guilds.")

@bot.command(name='j')
async def join_voice_channel(ctx, url):
    if ctx.author.voice is None:
        await ctx.send("You are not connected to a voice channel.")
    else:
        voice_channel = ctx.author.voice.channel
        voice_client = await voice_channel.connect()
        if voice_client.is_connected():
            await ctx.send("I have joined the voice channel.")
        else:
            await ctx.send("I was unable to join the voice channel.")

        with YoutubeDL({'format': 'bestaudio'}) as ydl:
            info = ydl.extract_info(url, download=False)
            URL = info['formats'][0]['url']
            voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=URL))
            await ctx.send('Şu anda müzik caliniyor!')

@bot.command(name='q')
async def quit_voice_channel(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send("I have left the voice channel.")
    else:
        await ctx.send("I am not connected to a voice channel.")
@bot.event
async def on_message(message):
    print(message.content)
    await bot.process_commands(message)

bot.run(os.environ["BOT_TOKEN"])