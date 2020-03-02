import discord
import os
import json
from commands.get_my_ip import ip
from commands.token import get_token
from commands.amazon import create_bucket
from commands.amazon import teardown
TOKEN = get_token()
client = discord.Client()

def return_error():
    return "Looks like that command isn't in our database."

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    activity = discord.Activity(name='Amazon Web Services', type=discord.ActivityType.playing)
    await client.change_presence(activity=activity)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if "public s3" in message.content.lower():
        await message.add_reaction("👍🏻")
        await message.channel.send('Did you say public!')
        await message.channel.send('Making all buckets public and adding your nudes. 💁🏻‍♀️')
        await message.channel.send(create_bucket())

    if message.content.startswith('!ip'):
        ip_address = ip()
        await message.channel.send(f'Called IP Address: {ip_address}')

    if message.content.startswith('!shitty'): 
        await message.channel.send("Doing something shitty, hopefully you can catch me. 👺")

    if message.content.startswith('!teardown'):
        teardown()
        await message.channel.send(f'Removing all shitty architecture 💩')

client.run(TOKEN)

