import discord
from discord.ext import commands, tasks
from random import choice
from music import Music
import os

client = commands.Bot(command_prefix=commands.when_mentioned_or(">"), description='Relatively simple music bot example')
status = ['Listening to >help', 'Singing music 🎙', '🍩 Eating Doughnut']



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
