import os
import string
from datetime import datetime, timezone
from threading import Thread

from flask import Flask
import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

# ---------------- Flask keep-alive (for Render + UptimeRobot) ----------------
app = Flask(__name__)

@app.get("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))  # Render provides PORT
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()

# ---------------- Discord bot setup ----------------
intents = discord.Intents.default()
intents.message_content = True  # make sure it's also enabled in Dev Portal
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Words to track (case-insensitive)
TRACKED_WORDS = ["nigga", "nigger", "niggers"]

# ---------------- MongoDB (persistent storage) ----------------
# Set in Render as env vars: TOKEN, MONGO_URI, (optional) MONGO_DB
mongo_uri = os.environ["MONGO_URI"]
mongo_db_name = os.environ.get("MONGO_DB", "wordcounter")

client = AsyncIOMotorClient(mongo_uri)
db = client[mongo_db_name]
counts = db["counts"]  # documents: { _id: <user_id:int>, count: <int>, updated_at: <datetime> }

async def inc_count(user_id: int, amount: int):
    await counts.update_one(
        {"_id": user_id},
        {"$inc": {"count": amount}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )

async def get_count(user_id: int) -> int:
    doc = await counts.find_one({"_id": user_id}, {"count": 1})
    return int(doc.get("count", 0)) if doc else 0

async def top_users(limit: int = 10):
    cursor = counts.find({}, {"count": 1}).sort("count", -1).limit(limit)
    return [doc async for doc in cursor]

@bot.event
async def on_ready():
    # Optional index helps sort by count quickly
    await counts.create_index("count")
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    content = message.content.lower()
    content = content.translate(str.maketrans('', '', string.punctuation))
    words = content.split()

    found = sum(words.count(w) for w in TRACKED_WORDS)
    if found > 0:
        await inc_count(message.author.id, found)

    await bot.process_commands(message)

@bot.command()
async def count(ctx: commands.Context, member: discord.Member = None):
    member = member or ctx.author
    total = await get_count(member.id)
    embed = discord.Embed(
        title=f"{member.display_name}'s N-Word count",
        description=f"**{member.display_name}** has said the N-Word **{total}** times.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command()
async def top(ctx: commands.Context):
    docs = await top_users(10)
    if not docs:
        return await ctx.send("No tracked words have been said yet!")

    lines = []
    for i, doc in enumerate(docs, start=1):
        uid = doc["_id"]
        cnt = int(doc.get("count", 0))
        # Prefer server nickname if available
        member = ctx.guild.get_member(uid) if ctx.guild else None
        if member:
            name = member.display_name
        else:
            try:
                user = await bot.fetch_user(uid)
                name = getattr(user, "name", f"User {uid}")
            except Exception:
                name = f"Unknown User ({uid})"
        lines.append(f"**{i}. {name}** — {cnt}")

    embed = discord.Embed(
        title="🏆 Top 10 users for N-Words",
        description="\n".join(lines),
        color=discord.Color.yellow()
    )
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(os.environ["TOKEN"])






