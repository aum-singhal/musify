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


#Pause the song
  @commands.command()
  async def pause(self, ctx):
    if not ctx.voice_client.is_playing():
      embed = discord.Embed(
        title = 'Opps!',
        description = 'I am not playing anything already.',
        colour = discord.Colour.red()
        )
      await ctx.send(embed=embed)
    else:
      await ctx.voice_client.pause()


#Resume the song
  @commands.command()
  async def resume(self, ctx):
    if not ctx.voice_client.is_playing():
      await ctx.voice_client.resume()
    else:
      embed = discord.Embed(
        title = 'Opps!',
        description = 'I am already playing.',
        colour = discord.Colour.red()
        )
      await ctx.send(embed=embed)


#Stops then song
  @commands.command()
  async def stop(self, ctx):
    if not ctx.voice_client.is_playing():
      embed = discord.Embed(
        title = 'Opps!',
        description = 'I am not playing anything already.',
        colour = discord.Colour.red()
      )
      await ctx.send(embed=embed)
    else:
      await ctx.voice_client.stop()
      

#Disconnect the bot from 
  @commands.command()
  async def disconnect(self, ctx):
    await ctx.voice_client.disconnect()