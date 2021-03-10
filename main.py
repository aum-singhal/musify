import discord
from discord.ext import commands, tasks
from random import choice, randrange
import json
import os
import youtube_dl
import asyncio
import urllib.parse, urllib.request, re

client = commands.Bot(command_prefix=commands.when_mentioned_or(">"), description='Relatively simple music bot example')
status = ['Listening to >help','Singing music 🎙','🍩 Eating Doughnut']

def colour():
  l = [
    1752220, 3066993, 3447003, 10181046, 15844367,
    15105570, 15158332, 3426654, 1146986, 2067276,
    2123412, 7419530, 12745742, 11027200, 10038562,
    2899536, 16580705, 12320855
  ]
  return choice(l)


youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
  'format': 'bestaudio/best',
  'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
  'restrictfilenames': True,
  'noplaylist': True,
  'nocheckcertificate': True,
  'ignoreerrors': False,
  'logtostderr': False,
  'quiet': True,
  'no_warnings': True,
  'default_search': 'auto',
  'source_address': '0.0.0.0'
}

ffmpeg_options = {
  'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
  def __init__(self, source, *, data, volume=0.5):
    super().__init__(source, volume)

    self.data = data

    self.title = data.get('title')
    self.url = data.get('url')

  @classmethod
  async def from_url(cls, url, *, loop=None, stream=False):
    loop = loop or asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

    if 'entries' in data:
        # take first item from a playlist
        data = data['entries'][0]

    filename = data['url'] if stream else ytdl.prepare_filename(data)
    return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'), data=data)


class Music(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

#sends the ping
  @commands.command()
  async def ping(self, ctx):
    embed = discord.Embed(
        title = f'Latency: {round(client.latency *1000)}ms',
        colour = colour()
        )
    await ctx.send(embed=embed)




@client.event
async def on_ready():
  change_status.start()
  print("The Bot is online!")


@tasks.loop(seconds=10)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))


client.add_cog(Music(client))

client.run(os.environ['token'])