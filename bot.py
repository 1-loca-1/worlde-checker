import discord
import os
import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_ID = int(os.getenv("ROLE_ID"))

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# stores today's word in memory
TODAY_WORD = None


# -------------------------
# ADMIN: set today's word
# -------------------------
@tree.command(
    name="setword",
    description="Set today's Wordle word",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(word="The word for today")
async def setword(interaction: discord.Interaction, word: str):

    global TODAY_WORD
    TODAY_WORD = word.lower()

    await interaction.response.send_message(
        f"✅ Today's word has been set to: **{TODAY_WORD}**",
        ephemeral=True
    )

# -------------------------
# USER: submit answer
# -------------------------
@tree.command(
    name="submit",
    description="Submit today's word",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(word="Your guess")
async def submit(interaction: discord.Interaction, word: str):

    global TODAY_WORD

    if TODAY_WORD is None:
        return await interaction.response.send_message(
            "❌ No word has been set yet.",
            ephemeral=True
        )

    if word.lower() != TODAY_WORD:
        return await interaction.response.send_message(
            "❌ Wrong answer.",
            ephemeral=True
        )

    role = interaction.guild.get_role(ROLE_ID)

    if role in interaction.user.roles:
        return await interaction.response.send_message(
            "You already have the role.",
            ephemeral=True
        )

    await interaction.user.add_roles(role)

    await interaction.response.send_message(
        "🎉 Correct! You got the Wordle role.",
        ephemeral=True
    )

async def reset_roles_daily():
    await client.wait_until_ready()

    guild = client.get_guild(GUILD_ID)
    role = guild.get_role(ROLE_ID)

    while True:
        now = datetime.now(ZoneInfo("Europe/London"))

        # calculate next midnight
        next_midnight = datetime.combine(
            now.date(),
            time(0, 0),
            tzinfo=ZoneInfo("Europe/London")
        )

        if now >= next_midnight:
            next_midnight = datetime.combine(
                now.date().replace(day=now.day + 1),
                time(0, 0),
                tzinfo=ZoneInfo("Europe/London")
            )

        sleep_seconds = (next_midnight - now).total_seconds()

        await asyncio.sleep(sleep_seconds)

        # 🔥 RESET ROLE
        for member in guild.members:
            if role in member.roles:
                try:
                    await member.remove_roles(role)
                except:
                    pass

        print("Daily reset complete")


# -------------------------
# SYNC COMMANDS
# -------------------------
@client.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        print("Commands synced")
    except Exception as e:
        print(f"Sync error: {e}")

    print(f"Logged in as {client.user}")


client.run(TOKEN)
