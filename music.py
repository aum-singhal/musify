import discord
from discord.ext import commands
from random import choice
from youtube_dl import YoutubeDL
from functools import partial
import asyncio
import urllib.parse, urllib.request, re
from async_timeout import timeout

client = commands.Bot(command_prefix=commands.when_mentioned_or(">"), description='Relatively simple music bot example')


def colour():
  l = [
    1752220, 3066993, 3447003, 10181046, 15844367,
    15105570, 15158332, 3426654, 1146986, 2067276,
    2123412, 7419530, 12745742, 11027200, 10038562,
    2899536, 16580705, 12320855
  ]
  return choice(l)


ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        await ctx.send(f'```ini\n[Added {data["title"]} to the Queue.]\n```')

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)



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


class MusicPlayer(commands.Cog):
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(f'**Now Playing:** `{source.title}` requested by '
                                               f'`{source.requester}`')
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))



class Music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.players = {}

  
  def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player



  @commands.command(aliases=["p"])
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
        player = self.get_player(ctx)

        source = await YTDLSource.create_source(ctx, url, loop=self.bot.loop, download=False)

        await player.queue.put(source)


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
  @commands.command(aliases=["dc"])
  async def disconnect(self, ctx):
    await ctx.voice_client.disconnect()


#Changes the Volume of the bot
  @commands.command(aliases=["vol"])
  async def volume(self, ctx, volume: int):
    if ctx.voice_client is None:
      return await ctx.send("Not connected to a voice channel.")
    ctx.voice_client.source.volume = volume / 100
    await ctx.send("Changed volume to {}%".format(volume))