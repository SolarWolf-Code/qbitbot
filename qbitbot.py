import discord
from discord import app_commands
import qbittorrentapi
import os
from typing import Callable, Optional

# Global variables
HOST = os.environ.get('HOST')
PORT = os.environ.get('PORT')
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
GUILD_ID = os.environ.get('GUILD_ID')
TOKEN = os.environ.get('TOKEN')
ELEMENTS_PER_PAGE = int(os.environ.get('ELEMENTS_PER_PAGE'))


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

class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, get_page: Callable):
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 1
        super().__init__(timeout=100)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navigate(self):
        emb, self.total_pages = await self.get_page(self.index)
        if self.total_pages == 1:
            await self.interaction.response.send_message(embed=emb)
        elif self.total_pages > 1:
            self.update_buttons()
            await self.interaction.response.send_message(embed=emb, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        # Disable the start and previous buttons if we're on the first page
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == 1

        # Disable the next and end buttons if we're on the last page
        self.children[2].disabled = self.index == self.total_pages
        self.children[3].disabled = self.index == self.total_pages

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.Button):
        self.index = 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def end(self, interaction: discord.Interaction, button: discord.Button):
        self.index = self.total_pages
        await self.edit_page(interaction)

    async def on_timeout(self):
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(total_results: int, results_per_page: int) -> int:
        return ((total_results - 1) // results_per_page) + 1



@tree.command(name="status", description="Checks the downloads status of requested movies and shows currently downloading", guild=discord.Object(id=GUILD_ID))
async def get_downloads(interaction):
    sending_embed = False

    torrents = {}

    for torrent in qbt_client.torrents_info():
        if torrent.state != 'stalledUP' and torrent.state != "uploading":
            sending_embed = True
            state_emote = ":green_square:"
            if torrent.state != "downloading":
                state_emote = ":red_square:"
            torrents[torrent.name] = {
                "progress": str(round(torrent.progress*100,2)),
                "eta": f"{str(round(torrent.progress*100,2))}% | ETA: {convert_time(torrent.eta)}",
                "state": state_emote
            }

    if sending_embed:
        async def get_page(page: int):
            emb = discord.Embed(title="Downloads", color=0x00ff00)
            offset = (page-1) * ELEMENTS_PER_PAGE
            for torrent in list(torrents.keys())[offset:offset+ELEMENTS_PER_PAGE]:
                emb.add_field(name=torrent, value=f"{torrents[torrent]['state']} | {torrents[torrent]['eta']}", inline=False)

            n = Pagination.compute_total_pages(len(torrents), ELEMENTS_PER_PAGE)
            emb.set_footer(text=f"Page {page}/{n}")
            return emb, n
        await Pagination(interaction, get_page).navigate()
    else:
        await interaction.response.send_message("No downloads currently in progress.")



@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("qBitBot is online!")


if __name__ == "__main__":
    print(f"Logging into qBitTorrent @ {HOST}:{PORT} with username {USERNAME}")
    client.run(TOKEN)
