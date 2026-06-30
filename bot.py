import asyncio
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from dotenv import load_dotenv

# ==========================
# CONFIG
# ==========================

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_ID = int(os.getenv("ROLE_ID"))

TIMEZONE = ZoneInfo("Europe/London")
WORD_FILE = "word.json"

# ==========================
# DISCORD SETUP
# ==========================

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

reset_task = None

# ==========================
# WORD STORAGE
# ==========================

CURRENT_WORD = None


def load_word():
    global CURRENT_WORD

    if os.path.exists(WORD_FILE):
        try:
            with open(WORD_FILE, "r") as f:
                data = json.load(f)
                CURRENT_WORD = data.get("word")
        except Exception:
            CURRENT_WORD = None


def save_word(word):
    global CURRENT_WORD

    CURRENT_WORD = word.lower()

    with open(WORD_FILE, "w") as f:
        json.dump({"word": CURRENT_WORD}, f)


def clear_word():
    global CURRENT_WORD

    CURRENT_WORD = None

    if os.path.exists(WORD_FILE):
        os.remove(WORD_FILE)


# ==========================
# COMMANDS
# ==========================

@tree.command(
    name="setword",
    description="Set today's Wordle word",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(word="Today's Wordle answer")
async def setword(interaction: discord.Interaction, word: str):

    save_word(word)

    await interaction.response.send_message(
        f"✅ Today's word has been set to **{word.lower()}**",
        ephemeral=True
    )


@tree.command(
    name="submit",
    description="Submit today's Wordle word",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(word="The Wordle answer")
async def submit(interaction: discord.Interaction, word: str):

    if CURRENT_WORD is None:
        await interaction.response.send_message(
            "❌ No word has been set yet.",
            ephemeral=True
        )
        return

    if word.lower() != CURRENT_WORD:
        await interaction.response.send_message(
            "❌ That's not today's word.",
            ephemeral=True
        )
        return

    role = interaction.guild.get_role(ROLE_ID)

    if role is None:
        await interaction.response.send_message(
            "❌ Role not found.",
            ephemeral=True
        )
        return

    if role in interaction.user.roles:
        await interaction.response.send_message(
            "You already have today's role!",
            ephemeral=True
        )
        return

    await interaction.user.add_roles(role)

    await interaction.response.send_message(
        "🎉 Correct! Role awarded!",
        ephemeral=True
    )


# ==========================
# DAILY RESET
# ==========================

async def reset_roles_daily():

    await client.wait_until_ready()

    print("Daily reset task started.")

    while not client.is_closed():

        now = datetime.now(TIMEZONE)

        tomorrow = now.date() + timedelta(days=1)

        midnight = datetime.combine(
            tomorrow,
            datetime.min.time(),
            tzinfo=TIMEZONE
        )

        seconds = (midnight - now).total_seconds()

        print(f"Sleeping {int(seconds)} seconds until midnight...")

        await asyncio.sleep(seconds)

        guild = client.get_guild(GUILD_ID)

        if guild is None:
            print("Guild not found.")
            continue

        role = guild.get_role(ROLE_ID)

        if role is None:
            print("Role not found.")
            continue

        removed = 0

        for member in guild.members:
            if role in member.roles:
                try:
                    await member.remove_roles(role)
                    removed += 1
                except Exception as e:
                    print(f"Couldn't remove role from {member}: {e}")

        clear_word()

        print(f"Midnight reset complete. Removed role from {removed} members.")
        print("Today's word has been cleared.")


# ==========================
# EVENTS
# ==========================

@client.event
async def on_ready():

    global reset_task

    load_word()

    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(e)

    if reset_task is None:
        reset_task = asyncio.create_task(reset_roles_daily())

    print("--------------------------")
    print(f"Logged in as {client.user}")
    print(f"Current word: {CURRENT_WORD}")
    print("--------------------------")


# ==========================
# START
# ==========================

client.run(TOKEN)
