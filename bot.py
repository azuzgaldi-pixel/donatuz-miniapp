import os
import hmac
import hashlib
import json
import sqlite3
import threading
import urllib.parse
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
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
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
ADMIN_ID = os.getenv("ADMIN_ID", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

PORT = int(os.getenv("PORT", "8000"))

DB_NAME = "donatuz.db"


# =========================================================
# DATABASE
# =========================================================

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
            last_name TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_type TEXT NOT NULL,
            product_name TEXT NOT NULL,
            game_id TEXT,
            game_name TEXT,
            package_name TEXT,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# GAMES
# =========================================================

GAMES = [
    {
        "id": "pubg",
        "name": "PUBG Mobile",
        "category": "Battle Royale",
        "icon": "🔫",
        "description": "PUBG Mobile UC",
        "packages": [
            {"name": "60 UC", "price": 14000},
            {"name": "325 UC", "price": 70000},
            {"name": "660 UC", "price": 140000},
            {"name": "1800 UC", "price": 350000},
        ]
    },
    {
        "id": "freefire",
        "name": "Free Fire",
        "category": "Battle Royale",
        "icon": "🔥",
        "description": "Free Fire Diamonds",
        "packages": [
            {"name": "100 Diamonds", "price": 16000},
            {"name": "310 Diamonds", "price": 45000},
            {"name": "520 Diamonds", "price": 70000},
            {"name": "1060 Diamonds", "price": 140000},
        ]
    },
    {
        "id": "mlbb",
        "name": "Mobile Legends",
        "category": "MOBA",
        "icon": "⚔️",
        "description": "Mobile Legends Diamonds",
        "packages": [
            {"name": "86 Diamonds", "price": 18000},
            {"name": "172 Diamonds", "price": 34000},
            {"name": "257 Diamonds", "price": 50000},
            {"name": "706 Diamonds", "price": 130000},
        ]
    },
    {
        "id": "brawl",
        "name": "Brawl Stars",
        "category": "Action",
        "icon": "⭐",
        "description": "Brawl Stars Gems",
        "packages": [
            {"name": "30 Gems", "price": 18000},
            {"name": "80 Gems", "price": 40000},
            {"name": "170 Gems", "price": 80000},
            {"name": "360 Gems", "price": 160000},
        ]
    },
    {
        "id": "roblox",
        "name": "Roblox",
        "category": "Games",
        "icon": "🟥",
        "description": "Robux",
        "packages": [
            {"name": "400 Robux", "price": 70000},
            {"name": "800 Robux", "price": 135000},
            {"name": "1700 Robux", "price": 270000},
        ]
    },
    {
        "id": "coc",
        "name": "Clash of Clans",
        "category": "Strategy",
        "icon": "🏰",
        "description": "Clash of Clans Gems",
        "packages": [
            {"name": "500 Gems", "price": 70000},
            {"name": "1200 Gems", "price": 140000},
            {"name": "2500 Gems", "price": 270000},
        ]
    },
    {
        "id": "cr",
        "name": "Clash Royale",
        "category": "Strategy",
        "icon": "👑",
        "description": "Clash Royale Gems",
        "packages": [
            {"name": "80 Gems", "price": 18000},
            {"name": "500 Gems", "price": 80000},
            {"name": "1200 Gems", "price": 160000},
        ]
    },
    {
        "id": "standoff",
        "name": "Standoff 2",
        "category": "Shooter",
        "icon": "🎯",
        "description": "Gold",
        "packages": [
            {"name": "100 Gold", "price": 18000},
            {"name": "500 Gold", "price": 75000},
            {"name": "1000 Gold", "price": 140000},
        ]
    },
    {
        "id": "codm",
        "name": "Call of Duty Mobile",
        "category": "Shooter",
        "icon": "💥",
        "description": "COD Points",
        "packages": [
            {"name": "80 CP", "price": 18000},
            {"name": "420 CP", "price": 80000},
            {"name": "880 CP", "price": 160000},
        ]
    },
    {
        "id": "fcmobile",
        "name": "FC Mobile",
        "category": "Sports",
        "icon": "⚽",
        "description": "FC Points",
        "packages": [
            {"name": "105 FC Points", "price": 25000},
            {"name": "550 FC Points", "price": 100000},
            {"name": "1200 FC Points", "price": 200000},
        ]
    },
    {
        "id": "efootball",
        "name": "eFootball",
        "category": "Sports",
        "icon": "⚽",
        "description": "eFootball Coins",
        "packages": [
            {"name": "130 Coins", "price": 25000},
            {"name": "550 Coins", "price": 90000},
            {"name": "1200 Coins", "price": 180000},
        ]
    },
    {
        "id": "genshin",
        "name": "Genshin Impact",
        "category": "RPG",
        "icon": "🌟",
        "description": "Genesis Crystals",
        "packages": [
            {"name": "60 Crystals", "price": 22000},
            {"name": "300 Crystals", "price": 90000},
            {"name": "980 Crystals", "price": 270000},
        ]
    },
    {
        "id": "hsr",
        "name": "Honkai: Star Rail",
        "category": "RPG",
        "icon": "🚂",
        "description": "Oneiric Shards",
        "packages": [
            {"name": "60 Shards", "price": 22000},
            {"name": "300 Shards", "price": 90000},
            {"name": "980 Shards", "price": 270000},
        ]
    },
    {
        "id": "valorant",
        "name": "Valorant",
        "category": "Shooter",
        "icon": "🔻",
        "description": "Valorant Points",
        "packages": [
            {"name": "475 VP", "price": 80000},
            {"name": "1000 VP", "price": 150000},
            {"name": "2050 VP", "price": 300000},
        ]
    },
    {
        "id": "lol",
        "name": "League of Legends",
        "category": "MOBA",
        "icon": "🛡️",
        "description": "Riot Points",
        "packages": [
            {"name": "575 RP", "price": 80000},
            {"name": "1380 RP", "price": 180000},
            {"name": "2800 RP", "price": 350000},
        ]
    },
    {
        "id": "fortnite",
        "name": "Fortnite",
        "category": "Battle Royale",
        "icon": "🪂",
        "description": "V-Bucks",
        "packages": [
            {"name": "800 V-Bucks", "price": 120000},
            {"name": "2800 V-Bucks", "price": 400000},
            {"name": "5000 V-Bucks", "price": 650000},
        ]
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "category": "Games",
        "icon": "⛏️",
        "description": "Minecraft services",
        "packages": [
            {"name": "Minecraft Gift", "price": 300000},
            {"name": "Minecoins", "price": 80000},
        ]
    },
    {
        "id": "arena",
        "name": "Arena Breakout",
        "category": "Shooter",
        "icon": "🪖",
        "description": "In-game currency",
        "packages": [
            {"name": "100 Coins", "price": 20000},
            {"name": "500 Coins", "price": 85000},
            {"name": "1000 Coins", "price": 160000},
        ]
    },
    {
        "id": "delta",
        "name": "Delta Force",
        "category": "Shooter",
        "icon": "🎖️",
        "description": "In-game currency",
        "packages": [
            {"name": "Small Pack", "price": 25000},
            {"name": "Medium Pack", "price": 90000},
            {"name": "Large Pack", "price": 180000},
        ]
    },
    {
        "id": "steam",
        "name": "Steam",
        "category": "Games",
        "icon": "🎮",
        "description": "Steam Wallet",
        "packages": [
            {"name": "$5", "price": 70000},
            {"name": "$10", "price": 135000},
            {"name": "$20", "price": 270000},
        ]
    },
]


PRODUCTS = [
    {
        "id": "stars",
        "name": "Telegram Stars",
        "icon": "⭐",
        "description": "Telegram Stars",
        "packages": [
            {"name": "100 Stars", "price": 25000},
            {"name": "250 Stars", "price": 55000},
            {"name": "500 Stars", "price": 105000},
            {"name": "1000 Stars", "price": 200000},
        ]
    },
    {
        "id": "premium",
        "name": "Telegram Premium",
        "icon": "💎",
        "description": "Telegram Premium",
        "packages": [
            {"name": "3 oy", "price": 0},
            {"name": "6 oy", "price": 0},
            {"name": "12 oy", "price": 0},
        ]
    }
]


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
# TELEGRAM INIT DATA VALIDATION
# =========================================================

def validate_init_data(init_data: str):
    if not init_data:
        return None

    try:
        parsed = urllib.parse.parse_qs(init_data)

        received_hash = parsed.get("hash", [None])[0]

        if not received_hash:
            return None

        data_check_pairs = []

        for key in sorted(parsed.keys()):
            if key == "hash":
                continue

            value = parsed[key][0]
            data_check_pairs.append(f"{key}={value}")

        data_check_string = "\n".join(data_check_pairs)

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

        user_raw = parsed.get("user", [None])[0]

        if not user_raw:
            return None

        return json.loads(user_raw)

    except Exception:
        return None


def get_user_from_request(request: Request):
    init_data = request.headers.get("X-Telegram-Init-Data", "")

    user = validate_init_data(init_data)

    # Local browser test uchun
    if not user:
        user = {
            "id": 0,
            "first_name": "Demo",
            "last_name": "",
            "username": "demo_user"
        }

    return user


# =========================================================
# USER
# =========================================================

def save_user(user):
    if not user:
        return

    conn = db()

    conn.execute("""
        INSERT INTO users
        (id, username, first_name, last_name, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
        username=excluded.username,
        first_name=excluded.first_name,
        last_name=excluded.last_name
    """, (
        user.get("id", 0),
        user.get("username", ""),
        user.get("first_name", ""),
        user.get("last_name", ""),
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


# =========================================================
# API
# =========================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "DonatUZ"
    }


@app.get("/api/games")
async def games():
    return GAMES


@app.get("/api/products")
async def products():
    return PRODUCTS


@app.post("/api/order")
async def create_order(request: Request):
    user = get_user_from_request(request)
    save_user(user)

    data = await request.json()

    product_type = data.get("product_type", "")
    product_id = data.get("product_id", "")
    package_name = data.get("package_name", "")
    amount = int(data.get("amount", 0))

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Noto'g'ri summa"
        )

    if product_type == "game":
        game = next(
            (g for g in GAMES if g["id"] == product_id),
            None
        )

        if not game:
            raise HTTPException(
                status_code=404,
                detail="O'yin topilmadi"
            )

        game_name = game["name"]

    else:
        product = next(
            (p for p in PRODUCTS if p["id"] == product_id),
            None
        )

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Mahsulot topilmadi"
            )

        game_name = ""

    conn = db()

    cursor = conn.execute("""
        INSERT INTO orders
        (
            user_id,
            product_type,
            product_name,
            game_id,
            game_name,
            package_name,
            amount,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.get("id", 0),
        product_type,
        product_id,
        product_id if product_type == "game" else "",
        game_name,
        package_name,
        amount,
        "pending",
        datetime.utcnow().isoformat()
    ))

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "order_id": order_id,
        "status": "pending",
        "message": "Buyurtma qabul qilindi"
    }


@app.get("/api/orders/{user_id}")
async def get_orders(user_id: int):
    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 100
    """, (user_id,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================================================
# TELEGRAM BOT
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    save_user({
        "id": user.id,
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or ""
    })

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 DonatUZ'ni ochish",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ]

    text = (
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "🎮 DonatUZ'ga xush kelibsiz!\n\n"
        "Bu yerda o‘yinlar uchun donat xizmatlari, "
        "Telegram Stars va Premium xizmatlarini ko‘rishingiz mumkin.\n\n"
        "👇 Mini App'ni ochish uchun tugmani bosing:"
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ DonatUZ yordam\n\n"
        "/start — Mini App'ni ochish\n"
        "/orders — Buyurtmalar\n"
        "/help — Yordam"
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (user.id,)).fetchall()

    conn.close()

    if not rows:
        await update.message.reply_text(
            "📦 Sizda hali buyurtmalar yo‘q."
        )
        return

    text = "📦 Oxirgi buyurtmalaringiz:\n\n"

    for row in rows:
        status = row["status"]

        if status == "pending":
            status_text = "⏳ Kutilmoqda"
        elif status == "paid":
            status_text = "💳 To‘langan"
        elif status == "completed":
            status_text = "✅ Bajarilgan"
        else:
            status_text = status

        text += (
            f"🧾 #{row['id']}\n"
            f"🎮 {row['game_name'] or row['product_name']}\n"
            f"📦 {row['package_name']}\n"
            f"💰 {row['amount']:,} UZS\n"
            f"{status_text}\n\n"
        )

    await update.message.reply_text(text)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID:
        await update.message.reply_text("Admin ID sozlanmagan.")
        return

    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("⛔ Ruxsat yo‘q.")
        return

    conn = db()

    users_count = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    orders_count = conn.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    revenue = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status != 'cancelled'"
    ).fetchone()[0]

    conn.close()

    await update.message.reply_text(
        "📊 DonatUZ statistikasi\n\n"
        f"👤 Users: {users_count}\n"
        f"📦 Orders: {orders_count}\n"
        f"💰 Buyurtmalar summasi: {revenue:,} UZS"
    )


def start_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("orders", orders_command)
    )

    application.add_handler(
        CommandHandler("stats", stats_command)
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================================================
# STATIC MINI APP
# =========================================================

app.mount(
    "/",
    StaticFiles(
        directory="web",
        html=True
    ),
    name="web"
)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    bot_thread = threading.Thread(
        target=start_bot,
        daemon=True
    )

    bot_thread.start()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )
