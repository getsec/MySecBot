import discord
import os

from commands.get_my_ip import ip
from commands.token import get_token



TOKEN = get_token()
client = discord.Client()

def return_error():
    return "Looks like that command isn't in our database."

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!ip'):
        ip_address = ip()
        await message.channel.send(f'Called IP Address: {ip_address}')

    else:
        await message.channel.send(return_error())

client.run(TOKEN)

