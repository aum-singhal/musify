import discord
from discord.ext import commands
from random import choice

client = commands.Bot(command_prefix=commands.when_mentioned_or(">"), description='Relatively simple music bot example')


def colour():
  l = [
    1752220, 3066993, 3447003, 10181046, 15844367,
    15105570, 15158332, 3426654, 1146986, 2067276,
    2123412, 7419530, 12745742, 11027200, 10038562,
    2899536, 16580705, 12320855
  ]
  return choice(l)

class MODs(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def ping(self, ctx):
    em = discord.Embed(
      title = f"Pong: {abs( client.latency * 1000)}ms",
      colour = colour()
    )
    await ctx.send(embed = em)
  
  @commands.command()
  async def help(self, ctx):
    em = discord.Embed(
      title = "Help",
      description = "This is the normal message",
      colour = colour()
    )
    await ctx.send(embed=em)