import os
import discord
from discord.ext import commands
from discord import Intents
from youtube_dl import YoutubeDL
from dotenv import load_dotenv
from googleapiclient.discovery import build
from urllib.parse import urlparse
from collections import deque

# I KNOW THIS CODE SUCKS I WILL REFACTOR IT LATER ON. FOR NOW I AM MAKING IT SURE THAT BOT WORKS
song_dequeue = deque()

# FFMPEG OPTIONS TO KEEP MUSIC PLAYING UNTIL THE END
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

load_dotenv()

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Event listener for when the bot has switched from offline to online
@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
    print(f"This Bot is in {len(bot.guilds)} guilds.")

@bot.command(name='j')
async def join_voice_channel(ctx, *,query):
    if ctx.author.voice is None:
        return await ctx.send("You are not connected to a voice channel.")
    
    voice_channel = ctx.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # Check if the bot is connected to a voice channel
    await add_music_to_queue(ctx,query)

    if voice_client and voice_client.is_connected():
        await ctx.send("I am already connected to a voice channel.")
    else:
        voice_client = await voice_channel.connect()

    if not voice_client.is_playing():
        source = song_dequeue.popleft()
        voice_client.play(source, after=lambda e: play_next_music(ctx,voice_client,e))

async def add_music_to_queue(ctx, query):
    parsed = urlparse(query)
    if all([parsed.scheme, parsed.netloc]):
        video_url = query
    else:
        video_url = search_youtube(query)

    print(f"Audio stream URL: {video_url}")  # Print the audio stream URL
    with YoutubeDL({'format': 'bestaudio'}) as ydl:
        info = ydl.extract_info(video_url, download=False)
        audio_source = discord.FFmpegPCMAudio(info["formats"][0]["url"],**FFMPEG_OPTIONS)
        song_dequeue.append(audio_source)
        await ctx.send('Music is in queue now!')

@bot.command(name='s')
async def skip_music(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_playing():
        voice_client.stop()
        if song_dequeue:  # Check if there are songs in the queue
            next_song = song_dequeue.popleft()  # Get the next song
            voice_client.play(next_song, after=lambda e: play_next_music(ctx, voice_client, e))  # Play the next song

def play_next_music(ctx,voice_client,error=None):
    if error:
        print(f"Player error: {error}")
    if not song_dequeue:
        print("The song queue is empty.")
        return
    source = song_dequeue.popleft()
    ctx.guild.voice_client.source = discord.PCMVolumeTransformer(ctx.guild.voice_client.source)
    ctx.guild.voice_client.source.volume = 1
    voice_client.play(source, after=lambda e: play_next_music(ctx,voice_client,e))

def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey='AIzaSyBj0bWtxZZVd7ThjJhHytwM-tNGo6-ocMM')
    request = youtube.search().list(
        part='snippet',
        maxResults=1,
        q=query,
        type='video',
        order='relevance'
    )
    response = request.execute()
    video_id = response['items'][0]['id']['videoId']
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    return video_url

@bot.command(name='q')
async def quit_voice_channel(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        song_dequeue.clear()
        await ctx.send("I have left the voice channel.")
    else:
        await ctx.send("I am not connected to a voice channel.")

@bot.event
async def on_message(message):
    print(message.content)
    await bot.process_commands(message)

bot.run(os.environ["BOT_TOKEN"])