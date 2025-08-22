import os
import discord
from discord.ext import commands
import string
from flask import Flask
from threading import Thread

# --- Keep bot online 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

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
        print(f"{message.author} said {count} tracked words, total: {word_counts[user_id]}")

    await bot.process_commands(message)

# Command to check your own count
@bot.command()
async def count(ctx):
    total = word_counts.get(ctx.author.id, 0)
    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s N-word count",
        description=f"**{ctx.author.display_name}** has said the n-word {total} times!",
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
            user = await bot.fetch_user(user_id)
            description += f"**{i}. {user.display_name}** — {count}\n"
        except:
            description += f"**{i}. Unknown User** — {count}\n"

    embed = discord.Embed(
        title="🏆 Top 10 users for N-Words:",
        description=description,
        color=discord.Color.yellow()
    )
    await ctx.send(embed=embed)

# Run bot
bot.run(os.getenv("TOKEN")
        
