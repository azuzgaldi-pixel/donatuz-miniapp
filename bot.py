import os
import sqlite3
import threading
import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DATABASE
# =========================

DB_NAME = "donatuz.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            game TEXT,
            player_id TEXT,
            package TEXT,
            price INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# GAMES
# =========================

GAMES = [
    {
        "id": "pubg",
        "name": "PUBG Mobile",
        "icon": "🎮",
        "packages": [
            {"name": "60 UC", "price": 15000},
            {"name": "325 UC", "price": 70000},
            {"name": "660 UC", "price": 135000},
            {"name": "1800 UC", "price": 350000},
        ],
    },
    {
        "id": "freefire",
        "name": "Free Fire",
        "icon": "🔥",
        "packages": [
            {"name": "100 Diamonds", "price": 15000},
            {"name": "310 Diamonds", "price": 40000},
            {"name": "520 Diamonds", "price": 65000},
            {"name": "1060 Diamonds", "price": 125000},
        ],
    },
    {
        "id": "mlbb",
        "name": "Mobile Legends",
        "icon": "⚔️",
        "packages": [
            {"name": "86 Diamonds", "price": 20000},
            {"name": "172 Diamonds", "price": 38000},
            {"name": "257 Diamonds", "price": 55000},
            {"name": "706 Diamonds", "price": 140000},
        ],
    },
    {
        "id": "brawl",
        "name": "Brawl Stars",
        "icon": "⭐",
        "packages": [
            {"name": "30 Gems", "price": 15000},
            {"name": "80 Gems", "price": 35000},
            {"name": "170 Gems", "price": 70000},
        ],
    },
    {
        "id": "roblox",
        "name": "Roblox",
        "icon": "🧱",
        "packages": [
            {"name": "400 Robux", "price": 60000},
            {"name": "800 Robux", "price": 110000},
            {"name": "1700 Robux", "price": 220000},
        ],
    },
    {
        "id": "coc",
        "name": "Clash of Clans",
        "icon": "🏰",
        "packages": [
            {"name": "500 Gems", "price": 60000},
            {"name": "1200 Gems", "price": 120000},
            {"name": "2500 Gems", "price": 230000},
        ],
    },
    {
        "id": "cr",
        "name": "Clash Royale",
        "icon": "👑",
        "packages": [
            {"name": "500 Gems", "price": 60000},
            {"name": "1200 Gems", "price": 120000},
            {"name": "2500 Gems", "price": 230000},
        ],
    },
    {
        "id": "standoff",
        "name": "Standoff 2",
        "icon": "🔫",
        "packages": [
            {"name": "100 Gold", "price": 20000},
            {"name": "500 Gold", "price": 80000},
            {"name": "1000 Gold", "price": 150000},
        ],
    },
    {
        "id": "codm",
        "name": "Call of Duty Mobile",
        "icon": "🎯",
        "packages": [
            {"name": "80 CP", "price": 20000},
            {"name": "420 CP", "price": 85000},
            {"name": "880 CP", "price": 165000},
        ],
    },
    {
        "id": "fc",
        "name": "EA SPORTS FC Mobile",
        "icon": "⚽",
        "packages": [
            {"name": "100 FC Points", "price": 25000},
            {"name": "520 FC Points", "price": 100000},
            {"name": "1050 FC Points", "price": 190000},
        ],
    },
    {
        "id": "efootball",
        "name": "eFootball",
        "icon": "⚽",
        "packages": [
            {"name": "130 Coins", "price": 25000},
            {"name": "550 Coins", "price": 95000},
            {"name": "1040 Coins", "price": 175000},
        ],
    },
    {
        "id": "genshin",
        "name": "Genshin Impact",
        "icon": "🌟",
        "packages": [
            {"name": "60 Genesis Crystals", "price": 25000},
            {"name": "300 Genesis Crystals", "price": 110000},
            {"name": "980 Genesis Crystals", "price": 300000},
        ],
    },
    {
        "id": "honkai",
        "name": "Honkai: Star Rail",
        "icon": "🚂",
        "packages": [
            {"name": "60 Oneiric Shard", "price": 25000},
            {"name": "300 Oneiric Shard", "price": 110000},
            {"name": "980 Oneiric Shard", "price": 300000},
        ],
    },
    {
        "id": "valorant",
        "name": "Valorant",
        "icon": "🔴",
        "packages": [
            {"name": "475 VP", "price": 70000},
            {"name": "1000 VP", "price": 140000},
            {"name": "2050 VP", "price": 270000},
        ],
    },
    {
        "id": "lol",
        "name": "League of Legends",
        "icon": "🛡️",
        "packages": [
            {"name": "575 RP", "price": 70000},
            {"name": "1380 RP", "price": 150000},
            {"name": "2800 RP", "price": 280000},
        ],
    },
    {
        "id": "fortnite",
        "name": "Fortnite",
        "icon": "🏹",
        "packages": [
            {"name": "1000 V-Bucks", "price": 120000},
            {"name": "2800 V-Bucks", "price": 300000},
        ],
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "icon": "⛏️",
        "packages": [
            {"name": "Minecoins 320", "price": 50000},
            {"name": "Minecoins 1020", "price": 120000},
        ],
    },
    {
        "id": "arena",
        "name": "Arena Breakout",
        "icon": "🎖️",
        "packages": [
            {"name": "60 Bonds", "price": 20000},
            {"name": "330 Bonds", "price": 90000},
            {"name": "680 Bonds", "price": 170000},
        ],
    },
    {
        "id": "delta",
        "name": "Delta Force",
        "icon": "💥",
        "packages": [
            {"name": "300 Coins", "price": 40000},
            {"name": "680 Coins", "price": 85000},
        ],
    },
    {
        "id": "steam",
        "name": "Steam",
        "icon": "🎮",
        "packages": [
            {"name": "$5", "price": 70000},
            {"name": "$10", "price": 135000},
            {"name": "$20", "price": 260000},
        ],
    },
]


# =========================
# PRODUCTS
# =========================

PRODUCTS = [
    {
        "id": "stars",
        "name": "Telegram Stars",
        "icon": "⭐",
        "description": "Telegram Stars sotib olish"
    },
    {
        "id": "premium",
        "name": "Telegram Premium",
        "icon": "💎",
        "description": "Telegram Premium"
    }
]


# =========================
# API
# =========================

@app.get("/api/games")
def get_games():
    return GAMES


@app.get("/api/products")
def get_products():
    return PRODUCTS


@app.post("/api/order")
async def create_order(data: dict):

    user_id = data.get("user_id")
    service = data.get("service")
    game = data.get("game")
    player_id = data.get("player_id")
    package = data.get("package")
    price = data.get("price")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders
        (user_id, service, game, player_id, package, price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        service,
        game,
        player_id,
        package,
        price
    ))

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "order_id": order_id,
        "status": "pending"
    }


@app.get("/api/orders/{user_id}")
def get_orders(user_id: int):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, service, game, player_id, package, price, status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    rows = cursor.fetchall()

    conn.close()

    orders = []

    for row in rows:
        orders.append({
            "id": row[0],
            "service": row[1],
            "game": row[2],
            "player_id": row[3],
            "package": row[4],
            "price": row[5],
            "status": row[6],
            "created_at": row[7]
        })

    return orders


# =========================
# TELEGRAM BOT
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users
        (id, username, first_name)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    conn.commit()
    conn.close()

    keyboard = []

    if WEBAPP_URL:
        keyboard.append([
            InlineKeyboardButton(
                "🚀 Ilovani ochish",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "⚠️ Ilova hali ulanmagan",
                callback_data="not_ready"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Salom, {user.first_name}! 👋\n\n"
        "🎮 DonatUZ'ga xush kelibsiz!\n\n"
        "Bu yerda o‘yinlarga donat qilish,\n"
        "⭐ Telegram Stars va\n"
        "💎 Premium xizmatlarini ko‘rishingiz mumkin.\n\n"
        "Quyidagi tugmani bosib Mini App'ni oching:",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 DonatUZ yordam\n\n"
        "/start — Mini App'ni ochish"
    )


def run_bot():

    telegram_app = Application.builder().token(BOT_TOKEN).build()

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        CommandHandler("help", help_command)
    )

    telegram_app.run_polling()


# =========================
# STATIC WEB
# =========================

if os.path.exists("web"):
    app.mount(
        "/",
        StaticFiles(directory="web", html=True),
        name="web"
    )


# =========================
# START
# =========================

def run_api():
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )


if __name__ == "__main__":

    api_thread = threading.Thread(
        target=run_api,
        daemon=True
    )

    api_thread.start()

    run_bot()
