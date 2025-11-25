import discord

from hammond import mealie
from hammond.systemd_creds import SystemdCreds
from hammond.logger import logger

# Get Discord setup with permission to read message content
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DISCORD_CHANNELS = {
    "mealie-recipe": 1442643510166556733,
}


@client.event
async def on_ready():
    logger.info(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.channel.id == DISCORD_CHANNELS["mealie-recipe"]:
        await mealie.message_handler(message)

    # logging.info(message)
    # if message.content.startswith("$hello"):
    #     _ = await message.channel.send("Hello!")


def main():
    client.run(SystemdCreds().discord_token, log_handler=None)


if __name__ == "__main__":
    main()
