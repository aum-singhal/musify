import discord
from discord.ext import commands, tasks
from random import choice, randrange
import json
import os
import youtube_dl
import asyncio
import urllib.parse, urllib.request, re

client = commands.Bot(command_prefix=commands.when_mentioned_or(">"),
                      description='Relatively simple music bot example')
status = ['Listening to >help', 'Singing music 🎙', '🍩 Eating Doughnut']


def colour():
	l = [
    1752220, 3066993, 3447003, 10181046, 15844367, 15105570, 15158332,
    3426654, 1146986, 2067276, 2123412, 7419530, 12745742, 11027200,
    10038562, 2899536, 16580705, 12320855
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
	def __init__(self, source, *, data, volume=0.5):
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

		filename = data['url'] if stream else ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(
      filename,
      **ffmpeg_options,
      before_options= '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'),
      data=data
    )


async def join(ctx):
	author = ctx.author.voice
	if not author:
		embed = discord.Embed(
		    title='Opps! 😥',
		    description=
		    'You are not connected to any voice channel. \nTry again after connecting to a voice channel.',
		    colour=discord.Colour.red())
		await ctx.send(embed=embed)
	else:
		author = ctx.author.voice.channel
		voiceClient = ctx.voice_client
		if not voiceClient:
			await author.connect()


async def search(url=""):
	if 'http://www.youtube.com' in url:
		return url
	else:
		l = url.split(' ')
		j = ""
		for i in l:
			j += i
			j += '+'
		url = j
		htm_content = urllib.request.urlopen( 'http://www.youtube.com/results?search_query=' + url)
		search_results = re.findall(r"watch\?v=(\S{11})", htm_content.read().decode())
		std = 'http://www.youtube.com/watch?v='
		url = str(std) + str(search_results[0])
		return url


class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot


#sends the ping

	@commands.command()
	async def ping(self, ctx):
		embed = discord.Embed(
		  title=f'Latency: {round(client.latency *1000)}ms',
      colour=colour()
    )
		await ctx.send(embed=embed)

	@commands.command()
	async def invite(self, ctx):
		embed = discord.Embed(
      title='Invite me to your server',
		  colour=colour()
    )
		embed.add_field(
		  name='Click here to invite',
		  value= 'https://discord.com/api/oauth2/authorize?client_id=819233568621854760&permissions=4294967287&scope=bot'
		)
		await ctx.send(embed=embed)

	@commands.command(aliases=["p"])
	async def play(self, ctx, *, url=""):
		await join(ctx)
		print(url)
		url = await search(url)
		print(url)

		async with ctx.typing():
			player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
			ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
		await ctx.send('Now playing: {}'.format(player.title))


@client.event
async def on_ready():
	change_status.start()
	print("The Bot is online!")


@tasks.loop(seconds=10)
async def change_status():
	await client.change_presence(activity=discord.Game(choice(status)))


@client.event
async def on_command_error(ctx, error):
	await ctx.send(f"```{error}```")


client.add_cog(Music(client))

client.run(os.environ['token'])
