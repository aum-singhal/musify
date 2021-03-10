import discord
from discord.ext import commands, tasks
from random import choice, randrange
import json
import os
import praw

client = commands.Bot(command_prefix=commands.when_mentioned_or(">"), description='Relatively simple music bot example')


client.run(os.environ['token'])