import discord

from hammond.systemd_creds import SystemdCreds

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        _ = await message.channel.send("Hello!")


def main():
    client.run(SystemdCreds().discord_token)


if __name__ == "__main__":
    main()
