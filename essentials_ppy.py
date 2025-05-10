import discord
import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
HYPIXEL_API_KEY = os.getenv("HYPIXEL_API_KEY")

ESSENTIALS_CHANNEL_ID = 1132491975598280814
LOG_CHANNEL_ID = 907201334409826326

WIN_ROLES = [
    (50000, '1108326132379558038'),
    (49000, '1108326080890277938'),
    (48000, '1108326025840046141'),
    (47000, '1108325974107504691'),
    (46000, '1108325917459218503'),
    (45000, '1108325869002424400'),
    (44000, '1108325797237882991'),
    (43000, '1108325743672438854'),
    (42000, '1108325689515589632'),
    (41000, '1108325637392977962'),
    (40000, '1108325585576525885'),
    (39000, '1108325528194269204'),
    (38000, '1108325469083934810'),
    (37000, '1108325409063452692'),
    (36000, '1108325357909717035'),
    (35000, '1108325302880452668'),
    (34000, '1108325253748359218'),
    (33000, '1108325200682033262'),
    (32000, '1108325131056578581'),
    (31000, '1108325079122722886'),
    (30000, '1108325026110914581'),
    (29000, '1108324975540195348'),
    (28000, '1108324906816520232'),
    (27000, '1108324850835140608'),
    (26000, '1108324800344113213'),
    (25000, '1108324746233401375'),
    (24000, '1108324673244119131'),
    (23000, '1108324597490790432'),
    (22000, '1108324541496836107'),
    (21000, '1108324472387280976'),
    (20000, '1108324389872742452'),
    (19000, '1108324333790711838'),
    (18000, '1108324273891848192'),
    (17000, '1108324201233920100'),
    (16000, '1108324112889286666'),
    (15000, '1108324061618126848'),
    (14000, '1108323995033542666'),
    (13000, '1108315273192288337'),
    (12000, '1108313966901465100'),
    (11000, '1108309512701616130'),
    (10000, '1083073967138541589'),
    (9000, '1083073849215684679'),
    (8000, '1083073644185534535'),
    (7000, '1063160742091685939'),
    (6000, '1026199251434360832'),
    (5000, '1020364100733247509'),
    (4000, '1007981455969878036'),
    (3000, '952452597191704628'),
    (2000, '937363837303263263'),
    (1000, '904422116433231953'),
    (500, '901616321689681971'),
    (250, '900855705437888583'),
    (100, '900855548596088944'),
]

def get_uuid(name):
    res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}")
    if res.status_code == 200:
        return res.json().get("id")
    return None

def get_pixel_party_wins(uuid):
    url = f"https://api.hypixel.net/player?key={HYPIXEL_API_KEY}&uuid={uuid}"
    try:
        res = requests.get(url)
        if res.status_code == 429:
            return "__RATE_LIMITED__"
        if res.status_code != 200:
            return 0  # fallback for other errors
        data = res.json()
        arcade_stats = data.get("player", {}).get("stats", {}).get("Arcade", {})
        for key in ["pixel_party", "pixelParty"]:
            if key in arcade_stats:
                return arcade_stats[key].get("wins", 0)
        return arcade_stats.get("pixel_party_wins", 0)
    except:
        return 0

def get_linked_discord(uuid):
    url = f"https://api.hypixel.net/player?key={HYPIXEL_API_KEY}&uuid={uuid}"
    try:
        res = requests.get(url)
        if res.status_code != 200:
            return "__API_ERROR__"
        data = res.json()
        return data.get("player", {}).get("socialMedia", {}).get("links", {}).get("DISCORD")
    except:
        return "__API_ERROR__"

    new_name = discord.ui.TextInput(label="Your new ingame name")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ign = self.new_name.value
        uuid = get_uuid(ign)
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)

        if not uuid:
            embed = discord.Embed(
                title="❌ Invalid IGN",
                description=f"`{ign}` is not a valid Minecraft username.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            if log_channel:
                await log_channel.send(f"[Nickname Change] ❌ `{interaction.user}` tried to set invalid IGN: `{ign}`")
            return

        linked = get_linked_discord(uuid)
        if linked != str(interaction.user):
            embed = discord.Embed(
                title="❌ Verification Failed",
                description="Your Discord tag doesn't match the IGN's linked account on Hypixel.",
                color=discord.Color.red()
            )
            embed.add_field(name="Entered IGN", value=f"`{ign}`", inline=False)
            embed.add_field(name="Linked Discord", value=f"`{linked or 'None'}`", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            if log_channel:
                await log_channel.send(f"[Nickname Change] ❌ `{interaction.user}` tried to verify with `{ign}` but tag didn't match (`{linked}`)")
            return

        try:
            await interaction.user.edit(nick=ign)
            embed = discord.Embed(
                title="✅ Nickname Updated",
                description=f"Your server nickname is now `{ign}`.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            if log_channel:
                await log_channel.send(f"[Nickname Change] ✅ `{interaction.user}` successfully changed nickname to `{ign}`")
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Nickname Change Failed",
                description="I don't have permission to change your nickname.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            if log_channel:
                await log_channel.send(f"[Nickname Change] ❌ `{interaction.user}` attempted to change nickname to `{ign}`, but I lacked permission.")

class NicknameModal(discord.ui.Modal, title="Change Ingame Name"):
    new_name = discord.ui.TextInput(label="Your new ingame name")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ign = self.new_name.value
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)

        try:
            uuid = get_uuid(ign)
        except Exception:
            uuid = None

        if uuid is None:
            try:
                test_res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{ign}")
                if test_res.status_code != 200:
                    raise Exception()
            except Exception:
                embed = discord.Embed(
                    title="⚠️ Service Unavailable",
                    description="Mojang API is currently not responding.\nTry again in a few minutes.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

                log = discord.Embed(
                    title="⚠️ Nickname Update Failed",
                    description="Mojang API failed to respond or rate-limited.",
                    color=discord.Color.orange()
                )
                log.add_field(name="User", value=interaction.user.mention, inline=True)
                log.add_field(name="Submitted IGN", value=f"`{ign}`", inline=True)
                await log_channel.send(embed=log)
                return

            embed = discord.Embed(
                title="❌ Invalid IGN",
                description=f"`{ign}` is not a valid Minecraft username.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="❌ Nickname Update Failed",
                description="Invalid Minecraft name submitted.",
                color=discord.Color.red()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="Submitted IGN", value=f"`{ign}`", inline=True)
            await log_channel.send(embed=log)
            return

        linked = get_linked_discord(uuid)
        if linked == "__API_ERROR__":
            embed = discord.Embed(
                title="⚠️ Service Unavailable",
                description="Hypixel API is currently not responding or rate-limited.\nTry again later.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="⚠️ Nickname Update Failed",
                description="Could not fetch linked Discord from Hypixel API.",
                color=discord.Color.orange()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="IGN", value=f"`{ign}`", inline=True)
            await log_channel.send(embed=log)
            return

        if linked != str(interaction.user):
            embed = discord.Embed(
                title="❌ Couldn’t Update Nickname",
                description="Your Discord tag doesn't match the one linked to that Minecraft name.",
                color=discord.Color.red()
            )
            embed.add_field(name="Submitted IGN", value=f"`{ign}`", inline=False)
            embed.add_field(name="IGN's Linked Discord", value=f"`{linked or 'None'}`", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="❌ Nickname Update Failed",
                description="Discord tag didn't match the linked account on Hypixel.",
                color=discord.Color.red()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="Submitted IGN", value=f"`{ign}`", inline=True)
            log.add_field(name="IGN's Linked Discord", value=f"`{linked or 'None'}`", inline=True)
            await log_channel.send(embed=log)
            return

        current_nick = interaction.user.nick or interaction.user.name
        if current_nick == ign:
            embed = discord.Embed(
                title="Nickname Already Set",
                description=f"Your server nickname is already `{ign}`.",
                color=discord.Color.blurple()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="Nickname Not Updated",
                description="User attempted to set the same nickname they already have.",
                color=discord.Color.blurple()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="IGN", value=f"`{ign}`", inline=True)
            await log_channel.send(embed=log)
            return

        try:
            await interaction.user.edit(nick=ign)
            embed = discord.Embed(
                title="✅ Nickname Updated",
                description=f"Your nickname was successfully changed to `{ign}`.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="✅ Nickname Updated",
                description="User successfully updated their server nickname.",
                color=discord.Color.green()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="New Nickname", value=f"`{ign}`", inline=True)
            await log_channel.send(embed=log)
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Couldn’t Change Nickname",
                description="I don’t have permission to update your nickname.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="❌ Nickname Update Failed",
                description="Bot lacks permission to update the user's nickname.",
                color=discord.Color.red()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="Attempted Nickname", value=f"`{ign}`", inline=True)
            await log_channel.send(embed=log)

class EssentialsButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Wins", style=discord.ButtonStyle.blurple)
    async def wins_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        member = interaction.guild.get_member(interaction.user.id)
        ign = member.nick or member.name

        uuid = get_uuid(ign)
        if not uuid:
            embed = discord.Embed(
                title="❌ Invalid IGN",
                description=f"`{ign}` is not a valid Minecraft username.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="❌ Win Role Assignment Failed",
                description="Could not find valid Minecraft account for nickname.",
                color=discord.Color.red()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="Submitted Nickname", value=f"`{ign}`", inline=True)
            await log_channel.send(embed=log)
            return

        wins = get_pixel_party_wins(uuid)
        if wins == "__RATE_LIMITED__":
            embed = discord.Embed(
                title="⚠️ Rate Limited",
                description="The Hypixel API is currently rate-limiting me. Try again in a bit.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="⚠️ API Rate Limit Hit",
                description="Could not fetch wins due to Hypixel API rate limiting.",
                color=discord.Color.orange()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="IGN", value=f"`{ign}`", inline=True)
            await log_channel.send(embed=log)
            return

        granted_roles = []
        for threshold, role_id in WIN_ROLES:
            if wins >= threshold:
                await member.add_roles(discord.Object(id=role_id), reason="Pixel Party win role assignment")
                granted_roles.append(threshold)

        if granted_roles:
            embed = discord.Embed(
                title="✅ Roles Granted",
                description=f"{len(granted_roles)} roles assigned for `{wins}` wins.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="✅ Win Roles Assigned",
                description="User received win-based roles.",
                color=discord.Color.green()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="IGN", value=f"`{ign}`", inline=True)
            log.add_field(name="Wins", value=f"`{wins}`", inline=True)
            log.add_field(name="Roles Given", value=f"{len(granted_roles)}", inline=True)
            await log_channel.send(embed=log)
        else:
            embed = discord.Embed(
                title="No Roles Given",
                description=f"You have `{wins}` Pixel Party wins — no new roles unlocked.",
                color=discord.Color.blurple()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log = discord.Embed(
                title="No Win Roles Assigned",
                description="User did not meet any thresholds.",
                color=discord.Color.blurple()
            )
            log.add_field(name="User", value=interaction.user.mention, inline=True)
            log.add_field(name="IGN", value=f"`{ign}`", inline=True)
            log.add_field(name="Wins", value=f"`{wins}`", inline=True)
            await log_channel.send(embed=log)

    @discord.ui.button(label="Nickname", style=discord.ButtonStyle.green)
    async def nickname_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NicknameModal())

async def send_essentials_message(bot):
    channel = bot.get_channel(ESSENTIALS_CHANNEL_ID)
    if not channel:
        return

    async for msg in channel.history(limit=1):
        if msg.author == bot.user:
            await msg.delete() # Delete the previous message when the bot starts up

    embed = discord.Embed(
        title="Pixel Party Essentials",
        description=(
            "Use the buttons below to manage your roles and name.\n\n"
            "➤ **Wins**: Grants you roles based on your Pixel Party wins (based on your server nickname).\n"
            "➤ **Nickname**: If you recently changed your in-game name, click below to update your server nickname."
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="Essentials System • Pixel Party Community")

    await channel.send(embed=embed, view=EssentialsButtonView())
