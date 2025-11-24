import logging

import discord
import coloredlogs

from hammond.systemd_creds import SystemdCreds

# Setup pretty logging
logging.basicConfig(level=logging.INFO)
coloredlogs.install(level=logging.INFO)

# Get Discord setup with permission to read message content
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    logging.info(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        _ = await message.channel.send("Hello!")


def main():
    client.run(SystemdCreds().discord_token, log_handler=None)


if __name__ == "__main__":
    main()
