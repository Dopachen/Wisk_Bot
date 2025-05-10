import discord
import os
import requests
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta, timezone
import math

load_dotenv()
HYPIXEL_API_KEY = os.getenv("HYPIXEL_API_KEY")

VERIFY_CHANNEL_ID = 1131646078790406284 
LOGGING_CHANNEL_ID = 1131681873123356682 
REMOVE_ROLE_ID = 903769123471900732 
ADD_ROLE_IDS = [903547723918229534, 900847332617228338] 

def get_pixel_party_stats(uuid):
    url = f'https://api.hypixel.net/player?key={HYPIXEL_API_KEY}&uuid={uuid}'
    try:
        res = requests.get(url)
        data = res.json()
        arcade_stats = data.get("player", {}).get("stats", {}).get("Arcade", {})
        print("Arcade Stats:", json.dumps(arcade_stats, indent=2))
        
        if "pixel_party" in arcade_stats:
            return arcade_stats["pixel_party"]
        elif "pixelParty" in arcade_stats:
            return arcade_stats["pixelParty"]
        elif "pixel_party_wins" in arcade_stats:
            # make it return in same format
            return {"wins": arcade_stats["pixel_party_wins"]}
        else:
            return {"error": "No Pixel Party data — player probably hasn’t played yet"}
    except Exception as e:
        return {"error": f"api error: {e}"}

def get_pixel_party_stats_from_data(player_data):
    arcade_stats = player_data.get("stats", {}).get("Arcade", {})
    print("Arcade Stats:", json.dumps(arcade_stats, indent=2))

    # So the background behind this piece of art is that it just didn't work when I tried to make it as in command.py
    # I don't know why, but it just didn't work for specific usernames. So I just made it like this. (wasn't API rate-limited)
    if "pixel_party" in arcade_stats:
        return arcade_stats["pixel_party"]
    elif "pixelParty" in arcade_stats:
        return arcade_stats["pixelParty"]
    elif "pixel_party_wins" in arcade_stats:
        return {"wins": arcade_stats["pixel_party_wins"]}
    else:
        return {"error": "No Pixel Party data — player probably hasn’t played yet"}

def parse_duration(duration_str):
    unit = duration_str[-1]
    amount = int(duration_str[:-1])
    if unit == "d":
        return timedelta(days=amount)
    elif unit == "w":
        return timedelta(weeks=amount)
    elif unit == "m":
        return timedelta(days=30 * amount)
    elif unit == "y":
        return timedelta(days=365 * amount)
    else:
        raise ValueError("Invalid time unit in duration string")

def get_requirements():
    with open("values.json", "r") as f:
        values = json.load(f)
    return values["servers"]["PPY_COMMUNITY"]

def calculate_hypixel_level(network_exp):
    return max(1, round((math.sqrt(network_exp + 15312.5) - 125 / math.sqrt(2)) / (25 * math.sqrt(2)), 2)) # Hypixel level formula

class VerifyModal(discord.ui.Modal, title="Verify your Minecraft account"):
    minecraft_username = discord.ui.TextInput(label="Minecraft Username", placeholder="e.g. Notch")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        requirements = get_requirements()

        # ----- MC NAME NOT FOUND -----
        ign = self.minecraft_username.value
        uuid_res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{ign}")
        if uuid_res.status_code != 200:
            embed = discord.Embed(
                title="Minecraft Username Invalid",
                description=(
                    f"The username `{ign}` could not be found.\n"
                    "Please make sure it's typed correctly and that the account exists."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Verification Failed • Invalid Username")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Attempt Failed",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
                log_embed.add_field(name="Entered Username", value=ign, inline=False)
                log_embed.add_field(name="Reason", value="Invalid Minecraft username", inline=False)
                log_embed.set_footer(text="System Log")
                await log_channel.send(embed=log_embed)

            return


        uuid = uuid_res.json()["id"]

        # ----- API COOLDOWN -----
        hypixel_res = requests.get(f"https://api.hypixel.net/player?key={HYPIXEL_API_KEY}&uuid={uuid}")
        if hypixel_res.status_code != 200:
            embed = discord.Embed(
                title="Hypixel API Error",
                description=(
                    "I'm currently being rate-limited.\n"
                    "Please wait at least 2 minutes before trying again.\n"
                ),
                color=discord.Color.orange()
            )
            embed.set_footer(text="Verification Failed • Hypixel API Issue")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Error: Hypixel API Unavailable",
                    color=discord.Color.orange()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                log_embed.add_field(name="Reason", value="Hypixel API is on cooldown. The user needs to wait atleast 2 minutes before trying again.", inline=False)
                log_embed.set_footer(text="Verification Logger")
                await log_channel.send(embed=log_embed)

            return
        
        hypixel_data = hypixel_res.json()
        if not hypixel_data.get("success"):
            await interaction.followup.send("❌ Failed to fetch player data from Hypixel. Try again in a bit.", ephemeral=True)
            return
        
        # ----- NO PLAYER DATA -----
        player = hypixel_data.get("player")
        if not player:
            embed = discord.Embed(
                title="Hypixel Account Not Found",
                description=(
                    f"The account `{ign}` exists but hasn't joined Hypixel yet, or the data couldn't be retrieved.\n"
                    "Make sure the account has logged into Hypixel at least once."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Verification Failed • No Hypixel Data")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Error: No Hypixel Account",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                log_embed.add_field(name="Reason", value="No `player` field in Hypixel API response — likely never joined Hypixel", inline=False)
                log_embed.set_footer(text="Verification Logger")
                await log_channel.send(embed=log_embed)

            return

        # ----- NO DISCORD LINK -----
        linked_discord = player.get("socialMedia", {}).get("links", {}).get("DISCORD")
        if not linked_discord:
            embed = discord.Embed(
                title="No Discord Linked on Hypixel",
                description=(
                    f"The Minecraft account `{ign}` does not have a Discord account linked on Hypixel.\n"
                    "Please join Hypixel and link your Discord."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Verification Failed • Missing Discord Link")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Error: Missing Discord Link",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                log_embed.add_field(name="Reason", value="No Discord account linked on Hypixel profile", inline=False)
                log_embed.set_footer(text="Verification Logger")
                await log_channel.send(embed=log_embed)

            return


        user_tag = str(interaction.user)
        if linked_discord != user_tag:
            embed = discord.Embed(
                title="Discord Tag Mismatch",
                description=(
                    f"The Discord account linked to `{ign}` on Hypixel does not match your current tag.\n\n"
                    f"**Linked on Hypixel:** `{linked_discord}`\n"
                    f"**Your Discord tag:** `{user_tag}`\n\n"
                    "To fix this, join Hypixel and link the correct Discord account."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Verification Failed • Tag Mismatch")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Error: Discord Tag Mismatch",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                log_embed.add_field(name="Linked Discord", value=linked_discord or "None", inline=True)
                log_embed.add_field(name="User's Discord Tag", value=user_tag, inline=True)
                log_embed.add_field(name="Reason", value="Mismatch between user's Discord tag and what is linked on Hypixel", inline=False)
                log_embed.set_footer(text="Verification Logger")
                await log_channel.send(embed=log_embed)

            return

        guild = interaction.guild
        member = guild.get_member(interaction.user.id)

        network_exp = player.get("networkExp", 0)
        hypixel_level = calculate_hypixel_level(network_exp)

        if hypixel_level < requirements["least_hypixel_level"]:
            embed = discord.Embed(
                title="Insufficient Hypixel Level",
                description=(
                    f"Your Hypixel level is `{int(hypixel_level)}`, but the minimum required level is `{requirements['least_hypixel_level']}`.\n"
                    "Keep playing on Hypixel to level up, then try verifying again later."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Verification Failed • Hypixel Level Too Low")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Error: Hypixel Level Too Low",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                log_embed.add_field(name="Level", value=f"{int(hypixel_level)}", inline=True)
                log_embed.add_field(name="Required Level", value=f"{requirements['least_hypixel_level']}", inline=True)
                log_embed.add_field(name="Reason", value="Hypixel level does not meet requirement", inline=False)
                log_embed.set_footer(text="Verification Logger")
                await log_channel.send(embed=log_embed)

            return


        # Check hypixel account age
        first_login = player.get("firstLogin")
        if first_login is not None:
            first_login_date = datetime.utcfromtimestamp(first_login / 1000).replace(tzinfo=timezone.utc)
            min_hypixel_age = parse_duration(requirements["least_hypixel_account_age"])
            now = datetime.now(timezone.utc)

            if now - first_login_date < min_hypixel_age:
                embed = discord.Embed(
                    title="Hypixel Account Too New",
                    description=(
                        f"Your Hypixel account must be at least `{requirements['least_hypixel_account_age']}` old to verify.\n"
                        f"Current age: `{(now - first_login_date).days}` days."
                    ),
                    color=discord.Color.red()
                )
                embed.set_footer(text="Verification Failed • Account Age Too Low")
                await interaction.followup.send(embed=embed, ephemeral=True)

                log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
                if log_channel:
                    log_embed = discord.Embed(
                        title="Verification Error: Hypixel Account Too New",
                        color=discord.Color.red()
                    )
                    log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                    log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                    log_embed.add_field(name="Account Age", value=f"{(now - first_login_date).days} days", inline=True)
                    log_embed.add_field(name="Required Age", value=requirements["least_hypixel_account_age"], inline=True)
                    log_embed.add_field(name="Reason", value="Hypixel account age does not meet requirement", inline=False)
                    log_embed.set_footer(text="Verification Logger")
                    await log_channel.send(embed=log_embed)

                return

        else:
            embed = discord.Embed(
                title="Unable to Verify Hypixel Account Age",
                description=(
                    "We couldn't determine when this account first joined Hypixel.\n"
                    "Please ensure the account has logged into Hypixel at least once and try again later."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Verification Failed • Missing Join Date")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Error: Missing Hypixel Join Date",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                log_embed.add_field(name="Reason", value="No `firstLogin` timestamp in Hypixel data", inline=False)
                log_embed.set_footer(text="Verification Logger")
                await log_channel.send(embed=log_embed)

            return

        now = datetime.now(timezone.utc)
        created_at = interaction.user.created_at

        if not created_at:
            embed = discord.Embed(
                title="Unable to Verify Discord Account Age",
                description=(
                    "We couldn't determine the creation date of your Discord account.\n"
                    "Please try again later or contact an admin if this issue persists."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Verification Failed • Missing Account Date")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Error: Discord Account Age Unknown",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                log_embed.add_field(name="Reason", value="Discord `created_at` is None (couldn't determine account age)", inline=False)
                log_embed.set_footer(text="Verification Logger")
                await log_channel.send(embed=log_embed)

            return

        account_age = now - created_at
        min_discord_age = parse_duration(requirements["least_discord_account_age"])

        if account_age < min_discord_age:
            embed = discord.Embed(
                title="Discord Account Too New",
                description=(
                    f"Your Discord account must be at least `{requirements['least_discord_account_age']}` old to verify.\n"
                    f"Current age: `{account_age.days}` days."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Verification Failed • Discord Account Age Too Low")
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Verification Error: Discord Account Too New",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Attempted IGN", value=ign, inline=True)
                log_embed.add_field(name="Account Age", value=f"{account_age.days} days", inline=True)
                log_embed.add_field(name="Required Age", value=requirements["least_discord_account_age"], inline=True)
                log_embed.add_field(name="Reason", value="Discord account age does not meet requirement", inline=False)
                log_embed.set_footer(text="Verification Logger")
                await log_channel.send(embed=log_embed)

            return


        if member:
            await member.remove_roles(discord.Object(id=REMOVE_ROLE_ID))

            for rid in ADD_ROLE_IDS:
                await member.add_roles(discord.Object(id=rid))

            try:
                await member.edit(nick=ign)
            except discord.Forbidden:
                pass

            pixel_stats = get_pixel_party_stats_from_data(player)
            win_count = pixel_stats.get("wins", 0) if isinstance(pixel_stats, dict) else 0
            print(f"win_count: {win_count}")

            # Win roles thresholds when a user verifies
            win_roles = [
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

            for threshold, role_id in win_roles:
                if win_count >= threshold:
                    await member.add_roles(discord.Object(id=role_id))

            await interaction.followup.send(f"✅ You’ve been verified as `{ign}`!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Unexpected error occured.", ephemeral=True)

        log_channel = guild.get_channel(LOGGING_CHANNEL_ID)
        if log_channel:
            # data prep
            first_login_str = (
                datetime.utcfromtimestamp(first_login / 1000).strftime("%Y-%m-%d %H:%M:%S UTC")
                if first_login else "Unknown"
            )
            discord_creation = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            account_age_days = (datetime.now(timezone.utc) - created_at).days
            hypixel_level_display = round(hypixel_level, 2)
            avatar_url = f"https://minotar.net/helm/{uuid}/100"

            embed = discord.Embed(
                title="✅ New Verification Logged",
                description=f"User `{interaction.user}` has successfully verified as `{ign}`.",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=avatar_url)

            embed.add_field(name="Minecraft IGN", value=ign, inline=False)
            embed.add_field(name="UUID", value=uuid, inline=False)
            embed.add_field(name="Hypixel Level", value=f"{hypixel_level_display}", inline=False)
            embed.add_field(name="First Hypixel Join", value=first_login_str, inline=False)
            embed.add_field(name="Discord Tag", value=str(interaction.user), inline=False)
            embed.add_field(name="Discord ID", value=interaction.user.id, inline=False)
            embed.add_field(name="Discord Created", value=discord_creation, inline=False)
            embed.add_field(name="Account Age", value=f"{account_age_days} days", inline=False)

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            embed.set_footer(text=f"Verification Logger • {now_str}")

            await log_channel.send(embed=embed)

class VerifyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

async def send_verify_message_ppy(bot):
    channel = bot.get_channel(VERIFY_CHANNEL_ID)
    if not channel:
        return
    
    async for msg in channel.history(limit=1):
        if msg.author == bot.user:
            await msg.delete() # Delete the previous message when the bot starts up

    embed = discord.Embed(
        title="Minecraft Account Verification",
        description=(
            "To gain access to this server, you need to verify that you own a Minecraft account.\n\n"
            "➤ **What do I need to do?**\n"
            "Make sure you've linked your **Discord account** to your Minecraft account **on Hypixel**. To do this:\n"
            "• Join Hypixel (`mc.hypixel.net`)\n"
            "• Right-click the **'My Profile'** head (2nd slot in your hotbar)\n"
            "• Go to **'Social Media'**, and link your Discord there\n\n"
            "➤ **Not sure how?**\n"
            "Check out <#907232971067654155> for a step-by-step guide.\n\n"
            "➤ **How does this system work?**\n"
            "This verification system uses the **official Hypixel API** to check if your Minecraft account is linked to your Discord. You only enter your **Minecraft username** — nothing else.\n\n"
            "We never ask for passwords or tokens. Everything is handled securely through Hypixel."
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Verification System • Pixel Party Community")

    await channel.send(embed=embed, view=VerifyButtonView())
