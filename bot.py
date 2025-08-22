import os
import discord
from discord.ext import commands
import string
import json

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Words to track (case-insensitive)
TRACKED_WORDS = ["nigga", "nigger", "niggers"]

# File to save counts
DATA_FILE = "word_counts.json"

# Load counts from file if it exists
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        word_counts = json.load(f)
else:
    word_counts = {}

# Save counts to file
def save_counts():
    with open(DATA_FILE, "w") as f:
        json.dump(word_counts, f)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    content = content.translate(str.maketrans('', '', string.punctuation))

    count = sum(content.split().count(word) for word in TRACKED_WORDS)

    if count > 0:
        user_id = str(message.author.id)
        word_counts[user_id] = word_counts.get(user_id, 0) + count
        print(f"{message.author} said {count} tracked words, total: {word_counts[user_id]}")
        save_counts()

    await bot.process_commands(message)

# Command to check your own count
@bot.command()
async def count(ctx):
    total = word_counts.get(str(ctx.author.id), 0)
    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s N-word count",
        description=f"**{ctx.author.display_name}** has said the N-word {total} times!",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# Command to show top 10 leaderboard
@bot.command()
async def top(ctx):
    if not word_counts:
        await ctx.send("No tracked words have been said yet!")
        return

    sorted_users = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    description = ""
    for i, (user_id, count) in enumerate(sorted_users[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            description += f"**{i}. {user.display_name}** — {count}\n"
        except:
            description += f"**{i}. Unknown User** — {count}\n"

    embed = discord.Embed(
        title="🏆 Top 10 users for N-Word count:",
        description=description,
        color=discord.Color.yellow()
    )
    await ctx.send(embed=embed)

# Run the bot
bot.run(os.getenv("TOKEN"))

