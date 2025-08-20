import os
import discord
from discord.ext import commands
import string
from flask import Flask
from threading import Thread
import json

# --- Flask server to keep bot alive ---
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

t = Thread(target=run)
t.start()

# --- Discord bot setup ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Words to track (case-insensitive)
TRACKED_WORDS = ["nigga", "nigger", "niggers"]

# Dictionary to store counts per user
word_counts = {}

# File to save data
DATA_FILE = "word_counts.json"

# Load data if file exists
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        try:
            word_counts = json.load(f)
            # JSON keys are strings, convert to int
            word_counts = {int(k): v for k, v in word_counts.items()}
        except:
            word_counts = {}

# Save function
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
        user_id = message.author.id
        word_counts[user_id] = word_counts.get(user_id, 0) + count
        save_counts()  # save after each update
        print(f"{message.author} said {count} n-words, total: {word_counts[user_id]}")

    await bot.process_commands(message)

# Command to check your own count
@bot.command()
async def count(ctx):
    total = word_counts.get(ctx.author.id, 0)
    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s N-Word count",
        description=f"**{ctx.author.display_name}** has said the N-Word {total} times!",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# Command to show top 10 leaderboard
@bot.command()
async def top(ctx):
    if not word_counts:
        await ctx.send("No tracked words have been said yet!")
        return

    if getattr(bot, "_processing_top", False):
        return
    bot._processing_top = True

    sorted_users = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    description = ""
    for i, (user_id, count) in enumerate(sorted_users[:10], start=1):
        try:
            user = await bot.fetch_user(user_id)
            description += f"**{i}. {user.display_name}** said {count} N-Words\n"
        except:
            description += f"**{i}. Unknown User** said {count} N-Words\n"

    embed = discord.Embed(
        title="🏆 Top 10 users for N-Words",
        description=description,
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
    bot._processing_top = False

# Run bot
bot.run(os.getenv("TOKEN"))




