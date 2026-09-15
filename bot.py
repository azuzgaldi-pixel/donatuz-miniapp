import os
import sqlite3
import logging
from contextlib import closing

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================================================
# SOZLAMALAR
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://donatuz-miniapp-production.up.railway.app"
)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

PORT = int(os.getenv("PORT", "8000"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(title="DonatUZ Mini App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# DATABASE
# =========================================================

DB_NAME = "donatuz.db"


def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                product TEXT,
                player_id TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


init_db()

# =========================================================
# O'YINLAR
# icon_search -> internetdan avtomatik ikonka qidirish nomi
# =========================================================

GAMES = [
    {
        "id": "pubg",
        "name": "PUBG Mobile",
        "icon_search": "PUBG MOBILE"
    },
    {
        "id": "freefire",
        "name": "Free Fire",
        "icon_search": "Garena Free Fire"
    },
    {
        "id": "mlbb",
        "name": "Mobile Legends",
        "icon_search": "Mobile Legends Bang Bang"
    },
    {
        "id": "brawlstars",
        "name": "Brawl Stars",
        "icon_search": "Brawl Stars"
    },
    {
        "id": "roblox",
        "name": "Roblox",
        "icon_search": "Roblox"
    },
    {
        "id": "coc",
        "name": "Clash of Clans",
        "icon_search": "Clash of Clans"
    },
    {
        "id": "cr",
        "name": "Clash Royale",
        "icon_search": "Clash Royale"
    },
    {
        "id": "standoff2",
        "name": "Standoff 2",
        "icon_search": "Standoff 2"
    },
    {
        "id": "codm",
        "name": "Call of Duty Mobile",
        "icon_search": "Call of Duty Mobile"
    },
    {
        "id": "fcmobile",
        "name": "FC Mobile",
        "icon_search": "EA SPORTS FC Mobile"
    },
    {
        "id": "efootball",
        "name": "eFootball",
        "icon_search": "eFootball"
    },
    {
        "id": "genshin",
        "name": "Genshin Impact",
        "icon_search": "Genshin Impact"
    },
    {
        "id": "hsr",
        "name": "Honkai Star Rail",
        "icon_search": "Honkai Star Rail"
    },
    {
        "id": "valorant",
        "name": "Valorant",
        "icon_search": "VALORANT"
    },
    {
        "id": "lol",
        "name": "League of Legends",
        "icon_search": "League of Legends Wild Rift"
    },
    {
        "id": "fortnite",
        "name": "Fortnite",
        "icon_search": "Fortnite"
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "icon_search": "Minecraft"
    },
    {
        "id": "arena",
        "name": "Arena Breakout",
        "icon_search": "Arena Breakout"
    },
    {
        "id": "deltaforce",
        "name": "Delta Force",
        "icon_search": "Delta Force"
    },
    {
        "id": "steam",
        "name": "Steam",
        "icon_search": "Steam"
    }
]

# =========================================================
# MAHSULOTLAR
# Hozircha demo narxlar
# =========================================================

PRODUCTS = [
    {
        "id": "stars",
        "name": "Telegram Stars",
        "icon": "⭐",
        "description": "Telegram Stars",
        "prices": [
            {"amount": 50, "price": 12000},
            {"amount": 100, "price": 23000},
            {"amount": 250, "price": 55000},
            {"amount": 500, "price": 105000},
            {"amount": 1000, "price": 200000}
        ]
    },
    {
        "id": "premium",
        "name": "Telegram Premium",
        "icon": "💎",
        "description": "Telegram Premium",
        "prices": [
            {"amount": 1, "price": 65000},
            {"amount": 3, "price": 175000},
            {"amount": 6, "price": 320000},
            {"amount": 12, "price": 590000}
        ]
    }
]

# =========================================================
# API
# =========================================================

@app.get("/")
async def home():
    return {
        "status": "online",
        "app": "DonatUZ Mini App"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


@app.get("/api/games")
async def get_games():
    return GAMES


@app.get("/api/products")
async def get_products():
    return PRODUCTS


@app.post("/api/order")
async def create_order(request: Request):

    data = await request.json()

    user_id = data.get("user_id")
    username = data.get("username", "")
    product = data.get("product", "")
    player_id = data.get("player_id", "")
    amount = data.get("amount", 0)

    if not user_id:
        return {
            "success": False,
            "message": "User ID topilmadi"
        }

    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT OR IGNORE INTO users
            (id, username, first_name)
            VALUES (?, ?, ?)
        """, (
            user_id,
            username,
            ""
        ))

        cur.execute("""
            INSERT INTO orders
            (user_id, username, product, player_id, amount)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            username,
            product,
            player_id,
            amount
        ))

        order_id = cur.lastrowid

        conn.commit()

    return {
        "success": True,
        "order_id": order_id,
        "message": "Buyurtma qabul qilindi"
    }


@app.get("/api/orders/{user_id}")
async def get_orders(user_id: int):

    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, product, player_id, amount, status, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))

        rows = cur.fetchall()

    orders = []

    for row in rows:
        orders.append({
            "id": row[0],
            "product": row[1],
            "player_id": row[2],
            "amount": row[3],
            "status": row[4],
            "created_at": row[5]
        })

    return orders


# =========================================================
# TELEGRAM BOT
# =========================================================

telegram_app = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO users
            (id, username, first_name)
            VALUES (?, ?, ?)
        """, (
            user.id,
            user.username or "",
            user.first_name or ""
        ))

        conn.commit()

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 DonatUZ'ni ochish",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ]

    await update.message.reply_text(
        "🎮 DonatUZ'ga xush kelibsiz!\n\n"
        "O'yinlar, Telegram Stars va Premium xizmatlarini "
        "qulay tarzda ko'rishingiz mumkin.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎮 DonatUZ yordam\n\n"
        "/start — Mini Appni ochish\n"
        "/orders — Buyurtmalar\n"
        "/stats — Statistika"
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, product, amount, status
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (user.id,))

        rows = cur.fetchall()

    if not rows:
        await update.message.reply_text(
            "📦 Hozircha buyurtmalaringiz yo'q."
        )
        return

    text = "📦 Oxirgi buyurtmalaringiz:\n\n"

    for row in rows:
        text += (
            f"🧾 #{row[0]}\n"
            f"🎮 {row[1]}\n"
            f"💰 {row[2]:,} so'm\n"
            f"📌 {row[3]}\n\n"
        )

    await update.message.reply_text(text)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        users_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM orders")
        orders_count = cur.fetchone()[0]

    await update.message.reply_text(
        "📊 DonatUZ statistikasi\n\n"
        f"👥 Foydalanuvchilar: {users_count}\n"
        f"📦 Buyurtmalar: {orders_count}"
    )


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("orders", orders_command))
telegram_app.add_handler(CommandHandler("stats", stats_command))

# =========================================================
# STATIC FILES
# =========================================================

app.mount(
    "/",
    StaticFiles(directory="web", html=True),
    name="web"
)

# =========================================================
# TELEGRAM BOTNI ISHGA TUSHIRISH
# =========================================================

@app.on_event("startup")
async def startup():

    await telegram_app.initialize()
    await telegram_app.start()

    if telegram_app.updater:
        await telegram_app.updater.start_polling()

    logger.info("Telegram bot ishga tushdi")


@app.on_event("shutdown")
async def shutdown():

    if telegram_app.updater:
        await telegram_app.updater.stop()

    await telegram_app.stop()
    await telegram_app.shutdown()

    logger.info("Telegram bot to'xtadi")


# =========================================================
# SERVER
# =========================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )
