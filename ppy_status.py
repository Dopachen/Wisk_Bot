import discord
import asyncio
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

load_dotenv()
API_KEY = os.getenv("HYPIXEL_API_KEY")
API_URL = "https://api.hypixel.net/counts"
CHANNEL_ID = 1288528050568302635  
CHECK_INTERVAL = 10

last_queue_status = True
last_rotation_check_date = None
last_rotation_status = True
is_currently_in_rotation = True

est = pytz.timezone("US/Eastern")

def get_pixel_party_players():
    try:
        response = requests.get(API_URL, params={"key": API_KEY})
        data = response.json()
        if data.get("success"):
            return data["games"]["ARCADE"]["modes"].get("PIXEL_PARTY", 0)
    except Exception as e:
        print("error fetching player count:", e)
    return None

def get_next_rotation_timestamp():
    now_est = datetime.now(est)
    next_midnight_est = (now_est + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(next_midnight_est.timestamp())

async def update_rotation_daily():
    global is_currently_in_rotation
    while True:
        now = datetime.now(est)
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = (next_midnight - now).total_seconds()
        await asyncio.sleep(seconds_until_midnight)
        is_currently_in_rotation = not is_currently_in_rotation

async def track_queue_status(bot):
    global last_queue_status, last_rotation_check_date, last_rotation_status

    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    # Start the rotation flipper
    asyncio.create_task(update_rotation_daily())

    while True:
        count = get_pixel_party_players()
        if count is None:
            await asyncio.sleep(CHECK_INTERVAL)
            continue

        is_queueing = count >= 10
        now_unix = int(datetime.now().timestamp())
        rotation_now = is_currently_in_rotation
        rotation_change_ts = get_next_rotation_timestamp()

        should_update = (last_queue_status != is_queueing) or (last_rotation_check_date != datetime.now(est).date())

        if should_update:
            last_queue_status = is_queueing
            last_rotation_check_date = datetime.now(est).date()
            last_rotation_status = rotation_now

            color_dot = "🟢" if is_queueing else "🔴"
            rotation_dot = "🟢" if rotation_now else "🔴"

            embed = discord.Embed(
                title="Queue Status Update",
                color=0x00FF00 if is_queueing else 0xFF0000
            )
            embed.description = (
                f"The game is currently queueing. {color_dot} (<t:{now_unix}:R>)"
                if is_queueing else
                f"The game is **not** currently queueing. {color_dot} (<t:{now_unix}:R>)"
            )
            embed.add_field(name="**Current playercount**", value=f"{count}", inline=False)
            embed.add_field(
                name="**Rotation Status**",
                value=f"In Rotation {rotation_dot} (Changes <t:{rotation_change_ts}:R>)"
                if rotation_now else
                f"Not In Rotation {rotation_dot} (Changes <t:{rotation_change_ts}:R>)",
                inline=False
            )
            embed.set_footer(text=(
                "A notification will be sent immediately when the queue has died."
                if is_queueing else
                "A notification will be sent immediately when the game is queueing again."
            ))

            if is_queueing:
                await channel.send("<@&1288413824910753834>") # Queue ping

            await channel.send(embed=embed)

        await asyncio.sleep(CHECK_INTERVAL)
