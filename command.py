import os
import requests
import discord
from datetime import datetime
from discord import app_commands
from dotenv import load_dotenv
import json
from typing import Literal, Optional
import re

load_dotenv()
HYPIXEL_API_KEY = os.getenv("HYPIXEL_API_KEY")
SETTINGS_FILE = "values.json"

def update_ppy_setting(setting_key: str, value):
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        
        if setting_key not in data["servers"]["PPY_COMMUNITY"]:
            return False, f"Invalid setting key: {setting_key}"

        data["servers"]["PPY_COMMUNITY"][setting_key] = value

        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)

        return True, f"Updated `{setting_key}` to `{value}` for the PPY Community server."
    except Exception as e:
        return False, f"Error updating settings: {e}"

def update_arcade_setting(setting_key: str, value):
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        
        if setting_key not in data["servers"]["ARCADE_COMMUNITY"]:
            return False, f"Invalid setting key: {setting_key}"

        data["servers"]["ARCADE_COMMUNITY"][setting_key] = value

        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)

        return True, f"Updated `{setting_key}` to `{value}` for ARCADE server."
    except Exception as e:
        return False, f"Error updating settings: {e}"

async def fetch_uuid(username: str):
    try:
        res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
        if res.status_code == 200:
            return res.json().get("id")
    except Exception as e:
        print("error fetching uuid:", e)
    return None

def get_pixel_party_stats(uuid):
    url = f'https://api.hypixel.net/player?key={HYPIXEL_API_KEY}&uuid={uuid}'
    try:
        res = requests.get(url)
        data = res.json()
        if data.get('player') and data['player'].get('stats') and data['player']['stats'].get('Arcade'):
            return data['player']['stats']['Arcade'].get('pixel_party', {})
        else:
            return {"error": "pixel_party stats not found"}
    except Exception as e:
        return {"error": f"api error: {e}"}

def format_percentage(part, whole):
    return round((part / whole) * 100, 2) if whole else 0

def format_ratio(wins, losses):
    return round(wins / losses, 2) if losses else wins

def format_per_game(value, games):
    return round(value / games, 2) if games else 0

@app_commands.command(name="stats", description="Check the Pixel Party stastitics of a player.")
@app_commands.guilds(discord.Object(id=900845277311815701)) 
@app_commands.describe(username="Minecraft username")
async def stats(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    uuid = await fetch_uuid(username)
    if not uuid:
        await interaction.followup.send(f"Couldn't find UUID for `{username}`.")
        return

    stats = get_pixel_party_stats(uuid)
    if "error" in stats:
        await interaction.followup.send(f"Error: {stats['error']}")
        return

    games = stats.get("games_played", 0)
    wins = stats.get("wins", 0)
    losses = games - wins
    rounds = stats.get("rounds_completed", 0)
    powerups = stats.get("power_ups_collected", 0)

    games_hyper = stats.get("games_played_hyper", 0)
    wins_hyper = stats.get("wins_hyper", 0)
    losses_hyper = games_hyper - wins_hyper
    rounds_hyper = stats.get("rounds_completed_hyper", 0)
    powerups_hyper = stats.get("power_ups_collected_hyper", 0)

    games_normal = games - games_hyper
    wins_normal = wins - wins_hyper
    losses_normal = losses - losses_hyper
    rounds_normal = rounds - rounds_hyper
    powerups_normal = powerups - powerups_hyper

    def wl(w, l): return f"{w / l:.3f}" if l else f"{w:.3f}"
    def wr(w, g): return f"{(w / g) * 100:.3f}%" if g else "0.000%"
    def rpg(r, g): return f"{r / g:.2f}" if g else "0.00"
    def ppg(p, g): return f"{p / g:.2f}" if g else "0.00"
    def sep(n): return f"{n:,}".replace(",", ".")

    embed = discord.Embed(
        title=f"Pixel Party Stats for {username}",
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url=f"https://minotar.net/helm/{uuid}/100")

    embed.add_field(
        name="**__Overall Stats__**",
        value=(
            f"**Total Games**: {sep(games)}\n"
            f"**Wins**: {sep(wins)}\n"
            f"**Losses**: {sep(losses)}\n"
            f"**W/L Ratio**: {wl(wins, losses)}\n"
            f"**Winrate**: {wr(wins, games)}\n\n"
            f"**Total Rounds**: {sep(rounds)}\n"
            f"**RPG**: {rpg(rounds, games)}\n"
            f"**Powerups**: {sep(powerups)}\n"
            f"**PPG**: {ppg(powerups, games)}"
        ),
        inline=True
    )

    embed.add_field(
        name="**__Hyper Stats__**",
        value=(
            f"**Total Games**: {sep(games_hyper)}\n"
            f"**Wins**: {sep(wins_hyper)}\n"
            f"**Losses**: {sep(losses_hyper)}\n"
            f"**W/L Ratio**: {wl(wins_hyper, losses_hyper)}\n"
            f"**Winrate**: {wr(wins_hyper, games_hyper)}\n\n"
            f"**Total Rounds**: {sep(rounds_hyper)}\n"
            f"**RPG**: {rpg(rounds_hyper, games_hyper)}\n"
            f"**Powerups**: {sep(powerups_hyper)}\n"
            f"**PPG**: {ppg(powerups_hyper, games_hyper)}"
        ),
        inline=True
    )

    embed.add_field(
        name="**__Normal Stats__**",
        value=(
            f"**Total Games**: {sep(games_normal)}\n"
            f"**Wins**: {sep(wins_normal)}\n"
            f"**Losses**: {sep(losses_normal)}\n"
            f"**W/L Ratio**: {wl(wins_normal, losses_normal)}\n"
            f"**Winrate**: {wr(wins_normal, games_normal)}\n\n"
            f"**Total Rounds**: {sep(rounds_normal)}\n"
            f"**RPG**: {rpg(rounds_normal, games_normal)}\n"
            f"**Powerups**: {sep(powerups_normal)}\n"
            f"**PPG**: {ppg(powerups_normal, games_normal)}"
        ),
        inline=True
    )

    embed.set_footer(text="Made by Dopa and Rawad")

    await interaction.followup.send(embed=embed)

@app_commands.command(name="compare", description="Compare two players' Pixel Party stats side-by-side.")
@app_commands.guilds(discord.Object(id=900845277311815701)) 
@app_commands.describe(player1="Minecraft username of the first player", player2="Minecraft username of the second player")
async def compare(interaction: discord.Interaction, player1: str, player2: str):
    await interaction.response.defer()

    def error_embed(title: str, msg: str):
        return discord.Embed(title=title, description=msg, color=discord.Color.purple())

    try:
        res1 = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player1}")
        res2 = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player2}")

        if res1.status_code != 200 or res2.status_code != 200:
            embed = error_embed(
                "Invalid Username",
                "Couldn't find one or both Minecraft usernames. Please double-check the spelling."
            )
            await interaction.followup.send(embed=embed)
            return

        uuid1 = res1.json().get("id")
        uuid2 = res2.json().get("id")
        name1 = res1.json().get("name")
        name2 = res2.json().get("name")

        stats1 = get_pixel_party_stats(uuid1)
        stats2 = get_pixel_party_stats(uuid2)

        if "error" in stats1 or "error" in stats2:
            embed = error_embed(
                "Failed to Fetch Stats",
                "One of the usernames is currently on cooldown due to Hypixel API limits. Please wait a few minutes before trying again." # Most likely rate limit, could be anything though
            )
            await interaction.followup.send(embed=embed)
            return

        def extract(stats, mode="all"):
            if mode == "hyper":
                prefix = "_hyper"
            elif mode == "normal":
                prefix = ""
            else:
                prefix = None

            g = stats.get("games_played", 0)
            w = stats.get("wins", 0)
            r = stats.get("rounds_completed", 0)
            p = stats.get("power_ups_collected", 0)

            if prefix is not None:
                g = stats.get(f"games_played{prefix}", 0)
                w = stats.get(f"wins{prefix}", 0)
                r = stats.get(f"rounds_completed{prefix}", 0)
                p = stats.get(f"power_ups_collected{prefix}", 0)

            l = g - w
            wl = w / l if l else w
            wr = (w / g * 100) if g else 0
            rpg = (r / g) if g else 0
            ppg = (p / g) if g else 0
            return g, w, l, wl, wr, r, rpg, p, ppg

        def sep(n, d=0): return f"{n:,.{d}f}".replace(",", ".")

        def with_diff(v1, v2, d=0, suffix=""):
            diff = v1 - v2
            if abs(diff) < 1e-6:
                return f"(=)" if not suffix else f"(= {suffix})"
            return f"(+{sep(diff, d)}{suffix})" if diff > 0 else f"(-{sep(abs(diff), d)}{suffix})"

        def block(title, s1, s2):
            labels = [
                ("Games", 0),
                ("Wins", 0),
                ("Losses", 0),
                ("W/L", 2),
                ("Winrate", 2),
                ("Rounds", 0),
                ("RPG", 2),
                ("Powerups", 0),
                ("PPG", 2)
            ]
            out1 = []
            out2 = []
            for i, (label, d) in enumerate(labels):
                val1 = s1[i]
                val2 = s2[i]
                is_pct = label == "Winrate"
                suffix = "%" if is_pct else ""
                if is_pct:
                    out1.append(f"**{label}**: {sep(val1, d)}% {with_diff(val1, val2, d, '%')}")
                    out2.append(f"**{label}**: {sep(val2, d)}% {with_diff(val2, val1, d, '%')}")
                else:
                    out1.append(f"**{label}**: {sep(val1, d)} {with_diff(val1, val2, d)}")
                    out2.append(f"**{label}**: {sep(val2, d)} {with_diff(val2, val1, d)}")
            return "\n".join(out1), "\n".join(out2)

        s1_overall = extract(stats1, "all")
        s2_overall = extract(stats2, "all")
        s1_hyper = extract(stats1, "hyper")
        s2_hyper = extract(stats2, "hyper")

        # Normal = overall - hyper (we only get overall and hyper from the API so we need to calculate normal manually)
        def fix_normal(overall, hyper):
            g = overall[0] - hyper[0]
            w = overall[1] - hyper[1]
            l = g - w
            wl = w / l if l else w
            wr = (w / g * 100) if g else 0
            r = overall[5] - hyper[5]
            rpg = r / g if g else 0
            p = overall[7] - hyper[7]
            ppg = p / g if g else 0
            return (g, w, l, wl, wr, r, rpg, p, ppg)

        s1_normal = fix_normal(s1_overall, s1_hyper)
        s2_normal = fix_normal(s2_overall, s2_hyper)

        embed = discord.Embed(
            title=f"Comparison: {name1} vs {name2}",
            color=discord.Color.purple()
        )

        o1, o2 = block("Overall", s1_overall, s2_overall)
        h1, h2 = block("Hyper", s1_hyper, s2_hyper)
        n1, n2 = block("Normal", s1_normal, s2_normal)

        embed.add_field(name=f"**{name1} - Overall**", value=o1, inline=True)
        embed.add_field(name=f"**{name2} - Overall**", value=o2, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        embed.add_field(name=f"**{name1} — Hyper**", value=h1, inline=True)
        embed.add_field(name=f"**{name2} — Hyper**", value=h2, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        embed.add_field(name=f"**{name1} — Normal**", value=n1, inline=True)
        embed.add_field(name=f"**{name2} — Normal**", value=n2, inline=True)

        embed.set_footer(text="Made by Dopa & Rawad")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        embed = error_embed(
            "Unknown Error",
            f"An unexpected error occurred.\n```{str(e)}```"
        )
        await interaction.followup.send(embed=embed)

@app_commands.command(name="verification_config_arcade", description="Set or view verification settings for ARCADE server")
@app_commands.guilds(discord.Object(id=730247359732383774)) 
@app_commands.describe(setting="The setting you want to change or 'show_current_settings'", value="The new value to apply (not needed if viewing)")
async def arcade_set_verification(interaction: discord.Interaction, setting: Literal["least_discord_account_age", "least_hypixel_account_age", "least_hypixel_level", "show_current_settings"], value: Optional[str] = None):
    required_role_id = 807861638996557875 # Mod Role Arcade

    if not any(role.id == required_role_id for role in interaction.user.roles):
        await interaction.response.send_message("you don't have permission to execute this command.", ephemeral=True)
        return
    
    if setting == "show_current_settings":
        try:
            with open("values.json", "r") as f:
                data = json.load(f)
            arcade_settings = data["servers"]["ARCADE_COMMUNITY"]
            pretty = "\n".join(f"**{k}**: {v}" for k, v in arcade_settings.items())
            await interaction.response.send_message(f"**Current ARCADE Verification Settings:**\n{pretty}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to load settings: {e}", ephemeral=True)
        return

    if value is None:
        await interaction.response.send_message("You need to provide a value for that setting.", ephemeral=True)
        return

    if setting == "least_hypixel_level":
        try:
            value = int(value)
        except ValueError:
            await interaction.response.send_message("Value must be a number for hypixel level.", ephemeral=True)
            return
    else:
        if not re.fullmatch(r"\d+(d|w|m|y)", value):
            await interaction.response.send_message(
                "Invalid time format. Use formats like `30d`, `2w`, `1m`, or `1y`.", ephemeral=True
            )
            return

    success, message = update_arcade_setting(setting, value)
    await interaction.response.send_message(message, ephemeral=True)

@app_commands.command(name="verification_config_ppy", description="Set or view verification settings for the PPY Community server")
@app_commands.guilds(discord.Object(id=900845277311815701)) 
@app_commands.describe(setting="The setting you want to change or 'show_current_settings'", value="The new value to apply (not needed if viewing)")
async def ppy_set_verification(interaction: discord.Interaction, setting: Literal["least_discord_account_age", "least_hypixel_account_age", "least_hypixel_level", "show_current_settings"], value: Optional[str] = None):
    required_role_id = 1175761444957073508 # Staff Role PPY

    if not any(role.id == required_role_id for role in interaction.user.roles):
        await interaction.response.send_message("you don't have permission to execute this command.", ephemeral=True)
        return
    if setting == "show_current_settings":
        try:
            with open("values.json", "r") as f:
                data = json.load(f)
            ppy_settings = data["servers"]["PPY_COMMUNITY"]
            pretty = "\n".join(f"**{k}**: {v}" for k, v in ppy_settings.items())
            await interaction.response.send_message(f"**Current PPY Community Verification Settings:**\n{pretty}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to load settings: {e}", ephemeral=True)
        return

    if value is None:
        await interaction.response.send_message("You need to provide a value for that setting.", ephemeral=True)
        return

    if setting == "least_hypixel_level":
        try:
            value = int(value)
        except ValueError:
            await interaction.response.send_message("Value must be a number for hypixel level.", ephemeral=True)
            return
    else:
        if not re.fullmatch(r"\d+(d|w|m|y)", value):
            await interaction.response.send_message(
                "Invalid time format. Use formats like `30d`, `2w`, `1m`, or `1y`.", ephemeral=True
            )
            return

    success, message = update_ppy_setting(setting, value)
    await interaction.response.send_message(message, ephemeral=True)

async def setup(bot):
    guild_one = discord.Object(id=730247359732383774) # Arcade 
    guild_two = discord.Object(id=900845277311815701) # PPY 
    bot.tree.add_command(arcade_set_verification, guild=guild_one)
    bot.tree.add_command(ppy_set_verification, guild=guild_two)
    bot.tree.add_command(stats, guild=guild_two)
    bot.tree.add_command(compare, guild=guild_two)
    await bot.tree.sync(guild=guild_one)
    await bot.tree.sync(guild=guild_two)

