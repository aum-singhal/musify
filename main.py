import discord
from discord.ext import commands, tasks
from random import choice
from music import Music
from mods import MODs
import os

client = commands.Bot(command_prefix=commands.when_mentioned_or(">"), description='Relatively simple music bot example')
client.remove_command('help')
status = ['Listening to >help', 'Singing music 🎙', '🍩 Eating Doughnut']


def colour():
  l = [
    1752220, 3066993, 3447003, 10181046, 15844367,
    15105570, 15158332, 3426654, 1146986, 2067276,
    2123412, 7419530, 12745742, 11027200, 10038562,
    2899536, 16580705, 12320855
  ]
  return choice(l)


class starting(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.command()
  async def ping(self, ctx):
    em = discord.Embed(
      title = f"Pong! {round(client.latency, 1)}",
      colour = colour()
    )
    await ctx.send(embed=em)

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
client.add_cog(MODs(client))
client.add_cog(starting(client))

client.run(os.environ['token'])
