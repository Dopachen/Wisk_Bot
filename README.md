# Pixel Party Discord Bot

This bot was made specifically for the Pixel Party and later on Arcade Community. It's not meant to be a generic public bot, more like a farewell gift. I'm no longer maintaining it, as I've quit Pixel Party, but I handed it over to **Rawad**, who now takes care of it going forward.

## What it does
- Lets users verify their Minecraft account and link it with their Discord tag (checks for account age, Hypixel level, etc.)
- Gives Pixel Party stats and assigns roles based on win milestones
- Tracks queue status and rotation for Pixel Party and posts updates (in queue, not in queue)
- Commands for checking pixel party stats, comparing players, etc.

## Files

| File                | What it does                                                                 |
|---------------------|------------------------------------------------------------------------------|
| `main.py`           | Entry point. Runs the bot, loads commands, and sends all auto-messages.     |
| `command.py`        | Slash commands `/stats`, `/compare`, and `/verification_config_*`           |
| `verify_ppy.py`     | Handles verification logic for the **Pixel Party server**                   |
| `verify_arcade.py`  | Handles verification logic for the **Arcade server**                        |
| `essentials_ppy.py` | Stuff like nickname editing and win-role assigning for verified users.       |
| `ppy_status.py`     | Watches Pixel Party’s queue status and rotation, posts updates.              |
| `values.json`       | Config file that stores the server-specific verification requirements.       |

## Final words
I've published the source to show the people who are curious how the bot actually works, not because it’s some reusable framework or public API. This was something I made for our community, and it served its purpose.
