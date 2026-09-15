import os
import hmac
import hashlib
import sqlite3
import json
import asyncio
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

import uvicorn


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")

PORT = int(os.getenv("PORT", "8080"))

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN topilmadi!")


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "donatuz.db"


def db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_type TEXT,
            product_name TEXT,
            game TEXT,
            player_id TEXT,
            package TEXT,
            price INTEGER,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_user(user_id, username="", first_name=""):
    conn = db()

    conn.execute("""
        INSERT INTO users (id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name
    """, (user_id, username, first_name))

    conn.commit()
    conn.close()


# =========================================================
# GAMES
# =========================================================

GAMES = [
    {
        "id": "pubg",
        "name": "PUBG Mobile",
        "icon": "🎯",
        "category": "Battle Royale"
    },
    {
        "id": "freefire",
        "name": "Free Fire",
        "icon": "🔥",
        "category": "Battle Royale"
    },
    {
        "id": "mlbb",
        "name": "Mobile Legends",
        "icon": "⚔️",
        "category": "MOBA"
    },
    {
        "id": "brawlstars",
        "name": "Brawl Stars",
        "icon": "⭐",
        "category": "Action"
    },
    {
        "id": "roblox",
        "name": "Roblox",
        "icon": "🟥",
        "category": "Gaming"
    },
    {
        "id": "coc",
        "name": "Clash of Clans",
        "icon": "🏰",
        "category": "Strategy"
    },
    {
        "id": "clashroyale",
        "name": "Clash Royale",
        "icon": "👑",
        "category": "Strategy"
    },
    {
        "id": "standoff2",
        "name": "Standoff 2",
        "icon": "🔫",
        "category": "Shooter"
    },
    {
        "id": "codm",
        "name": "Call of Duty Mobile",
        "icon": "💥",
        "category": "Shooter"
    },
    {
        "id": "fcmobile",
        "name": "FC Mobile",
        "icon": "⚽",
        "category": "Sports"
    },
    {
        "id": "efootball",
        "name": "eFootball",
        "icon": "⚽",
        "category": "Sports"
    },
    {
        "id": "genshin",
        "name": "Genshin Impact",
        "icon": "✨",
        "category": "RPG"
    },
    {
        "id": "hsr",
        "name": "Honkai: Star Rail",
        "icon": "🌌",
        "category": "RPG"
    },
    {
        "id": "valorant",
        "name": "Valorant",
        "icon": "🎮",
        "category": "Shooter"
    },
    {
        "id": "lol",
        "name": "League of Legends",
        "icon": "🛡️",
        "category": "MOBA"
    },
    {
        "id": "fortnite",
        "name": "Fortnite",
        "icon": "🟪",
        "category": "Battle Royale"
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "icon": "⛏️",
        "category": "Adventure"
    },
    {
        "id": "arena",
        "name": "Arena Breakout",
        "icon": "🎖️",
        "category": "Shooter"
    },
    {
        "id": "deltaforce",
        "name": "Delta Force",
        "icon": "🪖",
        "category": "Shooter"
    },
    {
        "id": "steam",
        "name": "Steam",
        "icon": "🎲",
        "category": "Gaming"
    }
]


# =========================================================
# DEMO PACKAGES
# =========================================================

PACKAGES = {
    "pubg": [
        {"name": "60 UC", "price": 12000},
        {"name": "325 UC", "price": 58000},
        {"name": "660 UC", "price": 110000},
        {"name": "1800 UC", "price": 285000},
    ],

    "freefire": [
        {"name": "100 Diamonds", "price": 16000},
        {"name": "310 Diamonds", "price": 47000},
        {"name": "520 Diamonds", "price": 74000},
        {"name": "1060 Diamonds", "price": 145000},
    ],

    "mlbb": [
        {"name": "86 Diamonds", "price": 18000},
        {"name": "172 Diamonds", "price": 35000},
        {"name": "257 Diamonds", "price": 51000},
        {"name": "706 Diamonds", "price": 130000},
    ],

    "brawlstars": [
        {"name": "30 Gems", "price": 18000},
        {"name": "80 Gems", "price": 43000},
        {"name": "170 Gems", "price": 85000},
    ],

    "roblox": [
        {"name": "400 Robux", "price": 65000},
        {"name": "800 Robux", "price": 120000},
        {"name": "1700 Robux", "price": 245000},
    ],

    "coc": [
        {"name": "Gold Pass", "price": 90000},
        {"name": "500 Gems", "price": 75000},
        {"name": "1200 Gems", "price": 165000},
    ],

    "clashroyale": [
        {"name": "500 Gems", "price": 75000},
        {"name": "1200 Gems", "price": 165000},
        {"name": "2500 Gems", "price": 320000},
    ],

    "standoff2": [
        {"name": "100 Gold", "price": 20000},
        {"name": "500 Gold", "price": 90000},
        {"name": "1000 Gold", "price": 170000},
    ],

    "codm": [
        {"name": "80 CP", "price": 18000},
        {"name": "420 CP", "price": 85000},
        {"name": "880 CP", "price": 165000},
    ],

    "fcmobile": [
        {"name": "100 FC Points", "price": 25000},
        {"name": "520 FC Points", "price": 110000},
        {"name": "1050 FC Points", "price": 205000},
    ],

    "efootball": [
        {"name": "130 Coins", "price": 28000},
        {"name": "550 Coins", "price": 105000},
        {"name": "1280 Coins", "price": 230000},
    ],

    "genshin": [
        {"name": "60 Genesis Crystals", "price": 18000},
        {"name": "300 Genesis Crystals", "price": 75000},
        {"name": "980 Genesis Crystals", "price": 220000},
    ],

    "hsr": [
        {"name": "60 Oneiric Shards", "price": 18000},
        {"name": "300 Oneiric Shards", "price": 75000},
        {"name": "980 Oneiric Shards", "price": 220000},
    ],

    "valorant": [
        {"name": "475 VP", "price": 75000},
        {"name": "1000 VP", "price": 145000},
        {"name": "2050 VP", "price": 285000},
    ],

    "lol": [
        {"name": "575 RP", "price": 90000},
        {"name": "1380 RP", "price": 205000},
        {"name": "2800 RP", "price": 400000},
    ],

    "fortnite": [
        {"name": "800 V-Bucks", "price": 120000},
        {"name": "2800 V-Bucks", "price": 390000},
        {"name": "5000 V-Bucks", "price": 680000},
    ],

    "minecraft": [
        {"name": "Minecoins 320", "price": 65000},
        {"name": "Minecoins 1020", "price": 175000},
        {"name": "Minecoins 1720", "price": 285000},
    ],

    "arena": [
        {"name": "100 Bonds", "price": 25000},
        {"name": "500 Bonds", "price": 110000},
        {"name": "1000 Bonds", "price": 210000},
    ],

    "deltaforce": [
        {"name": "300 Coins", "price": 45000},
        {"name": "680 Coins", "price": 95000},
        {"name": "1380 Coins", "price": 185000},
    ],

    "steam": [
        {"name": "Steam 5 USD", "price": 75000},
        {"name": "Steam 10 USD", "price": 145000},
        {"name": "Steam 20 USD", "price": 285000},
    ],
}


# =========================================================
# TELEGRAM PRODUCTS
# =========================================================

PRODUCTS = [
    {
        "id": "stars",
        "name": "Telegram Stars",
        "icon": "⭐",
        "description": "Telegram Stars",
    },
    {
        "id": "premium",
        "name": "Telegram Premium",
        "icon": "💎",
        "description": "Telegram Premium",
    }
]


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(title="DonatUZ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MINI APP AUTH
# =========================================================

def validate_init_data(init_data: str):
    if not init_data:
        return None

    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))

        received_hash = parsed.pop("hash", None)

        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{key}={parsed[key]}"
            for key in sorted(parsed.keys())
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        user_data = json.loads(parsed.get("user", "{}"))

        return user_data

    except Exception:
        return None


# =========================================================
# API MODELS
# =========================================================

class OrderRequest(BaseModel):
    initData: str = ""
    game: str
    package: str
    player_id: str


# =========================================================
# API ROUTES
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "DonatUZ"
    }


@app.get("/api/games")
def get_games():
    result = []

    for game in GAMES:
        item = dict(game)
        item["packages"] = PACKAGES.get(game["id"], [])
        result.append(item)

    return result


@app.get("/api/products")
def get_products():
    return PRODUCTS


@app.post("/api/order")
def create_order(order: OrderRequest):

    user = validate_init_data(order.initData)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Telegram foydalanuvchisi aniqlanmadi"
        )

    user_id = user.get("id")

    if not order.player_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Player ID kiriting"
        )

    game_data = next(
        (g for g in GAMES if g["id"] == order.game),
        None
    )

    if not game_data:
        raise HTTPException(
            status_code=404,
            detail="O'yin topilmadi"
        )

    package_data = next(
        (
            p for p in PACKAGES.get(order.game, [])
            if p["name"] == order.package
        ),
        None
    )

    if not package_data:
        raise HTTPException(
            status_code=404,
            detail="Paket topilmadi"
        )

    price = package_data["price"] + 200

    conn = db()

    cursor = conn.execute("""
        INSERT INTO orders (
            user_id,
            product_type,
            product_name,
            game,
            player_id,
            package,
            price,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        "game",
        game_data["name"],
        game_data["name"],
        order.player_id,
        order.package,
        price,
        "pending"
    ))

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "order_id": order_id,
        "price": price,
        "status": "pending",
        "message": "Buyurtma qabul qilindi"
    }


@app.get("/api/orders/{user_id}")
def get_orders(user_id: int):

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================================================
# STATIC WEB
# =========================================================

app.mount(
    "/",
    StaticFiles(directory="web", html=True),
    name="web"
)


# =========================================================
# TELEGRAM BOT
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user:
        save_user(
            user.id,
            user.username or "",
            user.first_name or ""
        )

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
        "O'yinlarga donat, Telegram Stars va Premium xizmatlari.\n\n"
        "Pastdagi tugma orqali Mini App'ni oching.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📚 DonatUZ yordam\n\n"
        "/start — Mini App'ni ochish\n"
        "/help — Yordam\n"
        "/stats — Statistika\n"
        "/orders — Buyurtmalar"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not ADMIN_ID:
        await update.message.reply_text("Admin ID sozlanmagan.")
        return

    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return

    conn = db()

    users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    orders = conn.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE status='pending'"
    ).fetchone()[0]

    conn.close()

    await update.message.reply_text(
        "📊 DonatUZ statistikasi\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"📦 Buyurtmalar: {orders}\n"
        f"⏳ Kutilayotgan: {pending}"
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = db()

    rows = conn.execute("""
        SELECT id, product_name, package, price, status
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (user_id,)).fetchall()

    conn.close()

    if not rows:
        await update.message.reply_text(
            "📦 Sizda hozircha buyurtmalar yo'q."
        )
        return

    text = "📦 Oxirgi buyurtmalaringiz:\n\n"

    for row in rows:
        text += (
            f"#{row['id']} — {row['product_name']}\n"
            f"🎁 {row['package']}\n"
            f"💰 {row['price']:,} UZS\n"
            f"📌 {row['status']}\n\n"
        )

    await update.message.reply_text(text)


# =========================================================
# BOT RUNNER
# =========================================================

async def run_bot():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("stats", stats_command)
    )

    application.add_handler(
        CommandHandler("orders", orders_command)
    )

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    print("Telegram bot ishga tushdi.")

    while True:
        await asyncio.sleep(3600)


# =========================================================
# SERVER
# =========================================================

def run_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )


if __name__ == "__main__":

    init_db()

    import threading

    server_thread = threading.Thread(
        target=run_server,
        daemon=True
    )

    server_thread.start()

    asyncio.run(run_bot())
