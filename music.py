import discord
from discord.ext import commands
from random import choice
import youtube_dl
import asyncio
import urllib.parse, urllib.request, re

client = commands.Bot(command_prefix=commands.when_mentioned_or(">"), description='Relatively simple music bot example')


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

ffmpeg_options = {'options': '-vn'}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=1):
		super().__init__(source, volume)

		self.data = data

		self.title = data.get('title')
		self.url = data.get('url')

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=False):
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor( None, lambda: ytdl.extract_info(url, download=not stream))

		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]

		filename = data['url']
		return cls(discord.FFmpegPCMAudio(
      filename,
      **ffmpeg_options,
      before_options= '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'),
      data=data
    )

async def join(ctx):
    author = ctx.author.voice
    if not author:
      em = discord.Embed(
        title = 'Opps! 😥',
        description = 'You are not connected to any voice channel. \nTry again after connecting to a voice channel.',
        colour = discord.Colour.red()
      )
      await ctx.send(embed=em)
      return 1
    else:
      author = ctx.author.voice.channel
      voiceClient = ctx.voice_client
      if not voiceClient:
        await author.connect()
      else:
        await ctx.send("**Already connected to :**" + author)
      return 0


async def search(ctx, url=""):
  if 'http://www.youtube.com' in url:
    return url
  else:
    l = url.split(' ')
    j = ''
    for i in l:
      j += i
      j += '+'
    url = j
    htm_content = urllib.request.urlopen(
      'http://www.youtube.com/results?search_query=' + url
    )
    search_results = re.findall(r"watch\?v=(\S{11})", htm_content.read().decode())
    std = 'http://www.youtube.com/watch?v='
    url = str(std) + str(search_results[0])
    return url

class Music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def play(self, ctx, *, url=""):
    w = await join(ctx)
    if w == 1:
      print("User not connected")
    else:
      if url == '':
        embed = discord.Embed(
          title = 'Opps! 😥',
          description = "You didn't specified any song to play. \nPlease try again but this time specify a song name or url to play.",
          colour = discord.Colour.orange()
        )
        await ctx.send(embed=embed)
      else:
        url = await search(ctx, url)

        async with ctx.typing():
          player = await YTDLSource.from_url(url, loop= ctx.bot.loop, stream=True)  # before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
          ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        await ctx.send('Now playing: {}'.format(player.title))


#Pause the song
  @commands.command()
  async def pause(self, ctx):
    if not ctx.voice_client.is_playing():
      embed = discord.Embed(
        title = 'Opps!',
        description = 'I am not playing anything already.',
        colour = colour()
        )
      await ctx.send(embed=embed)
    else:
      ctx.voice_client.pause()


#Resume the song
  @commands.command()
  async def resume(self, ctx):
    if not ctx.voice_client.is_playing():
      ctx.voice_client.resume()
    else:
      embed = discord.Embed(
        title = 'Opps!',
        description = 'I am already playing.',
        colour = colour()
        )
      await ctx.send(embed=embed)


#Stops then song
  @commands.command()
  async def stop(self, ctx):
    if not ctx.voice_client.is_playing():
      embed = discord.Embed(
        title = 'Opps!',
        description = 'I am not playing anything already.',
        colour = colour()
        )
      await ctx.send(embed=embed)
    else:
      await ctx.voice_client.stop()
      

#Disconnect the bot from 
  @commands.command()
  async def disconnect(self, ctx):
    await ctx.voice_client.disconnect()