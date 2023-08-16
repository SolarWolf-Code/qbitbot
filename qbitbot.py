import discord
from discord import app_commands
import qbittorrentapi
import os
import datetime

# Global variables
HOST = os.environ.get('HOST')
PORT = os.environ.get('PORT')
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
GUILD_ID = os.environ.get('GUILD_ID')
TOKEN = os.environ.get('TOKEN')


# qBitTorrent client
qbt_client = qbittorrentapi.Client(HOST, PORT, USERNAME, PASSWORD)

# Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def convert_time(seconds):
    intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),    # 60 * 60 * 24
        ('hours', 3600),    # 60 * 60
        ('minutes', 60),
        ('seconds', 1),)
    if seconds != 8640000:
        result = []
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:])
    else:
        return "inf"


def get_downloading_torrents():
    sending_embed = False

    embed = discord.Embed(
            title="Download Status",
            description="",
            color=discord.Color.purple()
    )
        
    for torrent in qbt_client.torrents_info():
        state = torrent.state
        if state != 'stalledUP' and state != "uploading":
            sending_embed = True
            embed.add_field(name="Name", value=torrent.name, inline=True)
            embed.add_field(name="Progress/ETA", value=f"{str(round(torrent.progress*100,2))}% | {convert_time(torrent.eta)} ", inline=True)

            if state != "downloading":
                embed.add_field(name="State", value=":red_square:", inline=True)
            else:
                embed.add_field(name="State", value=":green_square:", inline=True)

    return embed, sending_embed


@tree.command(name="status", description="Checks the downloads status of requested movies and shows currently downloading", guild=discord.Object(id=GUILD_ID))
async def get_downloads(interaction):
    # print the timestamp and the user that sent the command
    print(f"{datetime.datetime.now()} - {interaction.user.name}#{interaction.user.discriminator} sent /status in #{interaction.channel.name} on {interaction.guild.name}")

    # print the timestamp and say that you're deleting old bot messages
    print(f"{datetime.datetime.now()} - Deleting old bot messages in #{interaction.channel.name} on {interaction.guild.name}")
    await interaction.channel.purge(limit=100, check=lambda m: m.author == client.user)

    try:
        embed, send_embed = get_downloading_torrents()
        if send_embed:
            await interaction.response.send_message(embed=embed)
            # print the timestamp and say the message you sent
            print(f"{datetime.datetime.now()} - Sent embedded message in #{interaction.channel.name} on {interaction.guild.name}")
        else:
            # print the timestamp and say the message you sent
            print(f"{datetime.datetime.now()} - Sent 'There are no active downloads!' in #{interaction.channel.name} on {interaction.guild.name}")
            await interaction.response.send_message("There are no active downloads!")
    except Exception as e:
        # print the timestamp and say the error that occurred
        print(f"{datetime.datetime.now()} - An error occurred: {e}")
        await interaction.response.send_message(f"An error occurred: {e}")


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("qBitBot is online!")


if __name__ == "__main__":
    print(f"Logging into qBitTorrent @ {HOST}:{PORT} with username {USERNAME}")
    client.run(TOKEN)
