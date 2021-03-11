import discord
from discord.ext import commands
from math import round


client = commands.Bot(command_prefix=commands.when_mentioned_or(">"), description='Relatively simple music bot example')

class Music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def ping(self, ctx):
    em = discord.Embed(
      title = f"Pong: {round(client.latency *1000)}ms",
    )
    ctx.send(embed=em)