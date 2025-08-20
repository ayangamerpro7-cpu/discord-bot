# bot.py for PythonAnywhere

import discord
from discord.ext import commands
import os
import string
from flask import Flask
import threading

# --- Web server to keep bot alive (optional for ping) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_web).start()

# --- Discord bot setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Words to track
TRACKED_WORDS = ["nigga", "nigger", "niggers"]

# Dictionary to store counts per user
word_counts = {}

# --- Events ---
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
        print(f"{message.author} said {count} words, total: {word_counts[user_id]}")

    await bot.process_commands(message)

# --- Commands ---
@bot.command()
async def count(ctx, member: discord.Member = None):
    member = member or ctx.author
    total = word_counts.get(member.id, 0)
    embed = discord.Embed(
        title=f"{member.display_name}'s N-Words ",
        description=f"**{member.display_name}** has said the Nigga {total} times!",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command()
async def top(ctx):
    if not word_counts:
        await ctx.send("No words have been tracked yet!")
        return
    sorted_users = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    description = ""
    for i, (user_id, count) in enumerate(sorted_users, start=1):
        try:
            user = await bot.fetch_user(user_id)
            description += f"**{i}. {user.display_name}: {count}**\n"
        except:
            description += f"**{i}. Unknown User: {count}**\n"
    embed = discord.Embed(
        title="Nigga leaderboard - Top 10 Users:",
        description=description,
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# --- Run bot using environment variable ---
bot.run(os.environ["TOKEN"])





