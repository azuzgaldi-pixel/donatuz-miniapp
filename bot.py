import os
import sqlite3
import threading
import hashlib
import hmac
import json
from urllib.parse import parse_qsl

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes


# =========================================================
# SETTINGS
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

if not WEBAPP_URL:
    print("WARNING: WEBAPP_URL hali o'rnatilmagan!")


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "donatuz.db"


def db():
    return sqlite3.connect(DB_NAME)


def init_db():

    conn = db()
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


# =========================================================
# GAMES
# =========================================================

GAMES = [
    {
        "id": "pubg",
        "name": "PUBG Mobile",
        "icon": "🎮",
        "packages": [
            {"name": "60 UC", "price": 15000},
            {"name": "325 UC", "price": 70000},
            {"name": "660 UC", "price": 135000},
            {"name": "1800 UC", "price": 350000}
        ]
    },
    {
        "id": "freefire",
        "name": "Free Fire",
        "icon": "🔥",
        "packages": [
            {"name": "100 Diamonds", "price": 15000},
            {"name": "310 Diamonds", "price": 40000},
            {"name": "520 Diamonds", "price": 65000},
            {"name": "1060 Diamonds", "price": 125000}
        ]
    },
    {
        "id": "mlbb",
        "name": "Mobile Legends",
        "icon": "⚔️",
        "packages": [
            {"name": "86 Diamonds", "price": 20000},
            {"name": "172 Diamonds", "price": 38000},
            {"name": "257 Diamonds", "price": 55000},
            {"name": "706 Diamonds", "price": 140000}
        ]
    },
    {
        "id": "brawl",
        "name": "Brawl Stars",
        "icon": "⭐",
        "packages": [
            {"name": "30 Gems", "price": 15000},
            {"name": "80 Gems", "price": 35000},
            {"name": "170 Gems", "price": 70000}
        ]
    },
    {
        "id": "roblox",
        "name": "Roblox",
        "icon": "🧱",
        "packages": [
            {"name": "400 Robux", "price": 60000},
            {"name": "800 Robux", "price": 110000},
            {"name": "1700 Robux", "price": 220000}
        ]
    },
    {
        "id": "coc",
        "name": "Clash of Clans",
        "icon": "🏰",
        "packages": [
            {"name": "500 Gems", "price": 60000},
            {"name": "1200 Gems", "price": 120000},
            {"name": "2500 Gems", "price": 230000}
        ]
    },
    {
        "id": "cr",
        "name": "Clash Royale",
        "icon": "👑",
        "packages": [
            {"name": "500 Gems", "price": 60000},
            {"name": "1200 Gems", "price": 120000},
            {"name": "2500 Gems", "price": 230000}
        ]
    },
    {
        "id": "standoff",
        "name": "Standoff 2",
        "icon": "🔫",
        "packages": [
            {"name": "100 Gold", "price": 20000},
            {"name": "500 Gold", "price": 80000},
            {"name": "1000 Gold", "price": 150000}
        ]
    },
    {
        "id": "codm",
        "name": "Call of Duty Mobile",
        "icon": "🎯",
        "packages": [
            {"name": "80 CP", "price": 20000},
            {"name": "420 CP", "price": 85000},
            {"name": "880 CP", "price": 165000}
        ]
    },
    {
        "id": "fc",
        "name": "EA SPORTS FC Mobile",
        "icon": "⚽",
        "packages": [
            {"name": "100 FC Points", "price": 25000},
            {"name": "520 FC Points", "price": 100000},
            {"name": "1050 FC Points", "price": 190000}
        ]
    },
    {
        "id": "efootball",
        "name": "eFootball",
        "icon": "⚽",
        "packages": [
            {"name": "130 Coins", "price": 25000},
            {"name": "550 Coins", "price": 95000},
            {"name": "1040 Coins", "price": 175000}
        ]
    },
    {
        "id": "genshin",
        "name": "Genshin Impact",
        "icon": "🌟",
        "packages": [
            {"name": "60 Genesis Crystals", "price": 25000},
            {"name": "300 Genesis Crystals", "price": 110000},
            {"name": "980 Genesis Crystals", "price": 300000}
        ]
    },
    {
        "id": "honkai",
        "name": "Honkai: Star Rail",
        "icon": "🚂",
        "packages": [
            {"name": "60 Oneiric Shard", "price": 25000},
            {"name": "300 Oneiric Shard", "price": 110000},
            {"name": "980 Oneiric Shard", "price": 300000}
        ]
    },
    {
        "id": "valorant",
        "name": "Valorant",
        "icon": "🔴",
        "packages": [
            {"name": "475 VP", "price": 70000},
            {"name": "1000 VP", "price": 140000},
            {"name": "2050 VP", "price": 270000}
        ]
    },
    {
        "id": "lol",
        "name": "League of Legends",
        "icon": "🛡️",
        "packages": [
            {"name": "575 RP", "price": 70000},
            {"name": "1380 RP", "price": 150000},
            {"name": "2800 RP", "price": 280000}
        ]
    },
    {
        "id": "fortnite",
        "name": "Fortnite",
        "icon": "🏹",
        "packages": [
            {"name": "1000 V-Bucks", "price": 120000},
            {"name": "2800 V-Bucks", "price": 300000}
        ]
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "icon": "⛏️",
        "packages": [
            {"name": "320 Minecoins", "price": 50000},
            {"name": "1020 Minecoins", "price": 120000}
        ]
    },
    {
        "id": "arena",
        "name": "Arena Breakout",
        "icon": "🎖️",
        "packages": [
            {"name": "60 Bonds", "price": 20000},
            {"name": "330 Bonds", "price": 90000},
            {"name": "680 Bonds", "price": 170000}
        ]
    },
    {
        "id": "delta",
        "name": "Delta Force",
        "icon": "💥",
        "packages": [
            {"name": "300 Coins", "price": 40000},
            {"name": "680 Coins", "price": 85000}
        ]
    },
    {
        "id": "steam",
        "name": "Steam",
        "icon": "🎮",
        "packages": [
            {"name": "$5", "price": 70000},
            {"name": "$10", "price": 135000},
            {"name": "$20", "price": 260000}
        ]
    }
]


# =========================================================
# SERVICES
# =========================================================

PRODUCTS = [
    {
        "id": "stars",
        "name": "Telegram Stars",
        "icon": "⭐",
        "description": "Telegram Stars"
    },
    {
        "id": "premium",
        "name": "Telegram Premium",
        "icon": "💎",
        "description": "Telegram Premium"
    }
]


# =========================================================
# TELEGRAM MINI APP SECURITY
# =========================================================

def validate_init_data(init_data: str):

    if not init_data:
        return None

    try:

        data = dict(parse_qsl(init_data, keep_blank_values=True))

        received_hash = data.pop("hash", None)

        if not received_hash:
            return None

        check_string = "\n".join(
            f"{key}={data[key]}"
            for key in sorted(data)
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        user_data = data.get("user")

        if not user_data:
            return None

        return json.loads(user_data)

    except Exception:
        return None


# =========================================================
# FASTAPI
# =========================================================

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@api.get("/health")
def health():

    return {
        "status": "ok",
        "app": "DonatUZ"
    }


@api.get("/api/games")
def games():

    return GAMES


@api.get("/api/products")
def products():

    return PRODUCTS


@api.post("/api/order")
async def create_order(data: dict):

    init_data = data.get("initData", "")

    user = validate_init_data(init_data)

    if not user:
        raise HTTPException(
            status_code=403,
            detail="Telegram user tasdiqlanmadi"
        )

    user_id = int(user["id"])

    service = data.get("service")
    game = data.get("game")
    player_id = data.get("player_id", "")
    package = data.get("package")
    price = int(data.get("price", 0))

    if service not in ["game", "stars", "premium"]:
        raise HTTPException(
            status_code=400,
            detail="Noto'g'ri xizmat"
        )

    if service == "game":

        if not game:
            raise HTTPException(
                status_code=400,
                detail="O'yin tanlanmagan"
            )

        if not player_id:
            raise HTTPException(
                status_code=400,
                detail="Player ID kerak"
            )

    if not package:
        raise HTTPException(
            status_code=400,
            detail="Paket tanlanmagan"
        )

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders
        (
            user_id,
            service,
            game,
            player_id,
            package,
            price,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        service,
        game,
        player_id,
        package,
        price,
        "pending"
    ))

    order_id = cur.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "order_id": order_id,
        "status": "pending"
    }


# =========================================================
# BOT
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    conn = db()
    cur = conn.cursor()

    cur.execute("""
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
                web_app=WebAppInfo(
                    url=WEBAPP_URL
                )
            )
        ])

    text = (
        f"Salom, {user.first_name}! 👋\n\n"
        "🎮 DonatUZ'ga xush kelibsiz!\n\n"
        "O'yinlarga donat qiling,\n"
        "⭐ Telegram Stars va\n"
        "💎 Premium xizmatlarini ko'ring.\n\n"
        "Quyidagi tugma orqali Mini App'ni oching:"
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        return

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    orders = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM orders WHERE status='pending'"
    )
    pending = cur.fetchone()[0]

    conn.close()

    await update.message.reply_text(
        "📊 DonatUZ statistika\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"🛒 Buyurtmalar: {orders}\n"
        f"⏳ Kutilayotgan: {pending}"
    )


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            user_id,
            service,
            game,
            player_id,
            package,
            price,
            status
        FROM orders
        ORDER BY id DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    conn.close()

    if not rows:

        await update.message.reply_text(
            "Buyurtmalar hali yo'q."
        )

        return

    text = "🛒 Oxirgi buyurtmalar:\n\n"

    for row in rows:

        text += (
            f"#{row[0]}\n"
            f"👤 {row[1]}\n"
            f"🎮 {row[3] or row[2]}\n"
            f"🆔 {row[4] or '-'}\n"
            f"📦 {row[5]}\n"
            f"💰 {row[6]:,} UZS\n"
            f"📌 {row[7]}\n\n"
        )

    await update.message.reply_text(text)


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🎮 DonatUZ\n\n"
        "/start — Mini App\n"
        "/help — Yordam"
    )


# =========================================================
# ADMIN ORDER NOTIFICATION
# =========================================================

async def notify_admin(
    context,
    order_id,
    user_id,
    game,
    package,
    price,
    player_id
):

    if not ADMIN_ID:
        return

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 Yangi buyurtma!\n\n"
                f"🧾 Buyurtma: #{order_id}\n"
                f"👤 User ID: {user_id}\n"
                f"🎮 O'yin: {game}\n"
                f"🆔 Player ID: {player_id}\n"
                f"📦 Paket: {package}\n"
                f"💰 Narx: {price:,} UZS\n"
                f"📌 Status: pending"
            )
        )

    except Exception as e:

        print("Admin notification error:", e)


# =========================================================
# RUN
# =========================================================

def run_api():

    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        api,
        host="0.0.0.0",
        port=port
    )


def run_bot():

    telegram_app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        CommandHandler("help", help_command)
    )

    telegram_app.add_handler(
        CommandHandler("stats", stats)
    )

    telegram_app.add_handler(
        CommandHandler("orders", orders)
    )

    telegram_app.run_polling()


if os.path.exists("web"):

    api.mount(
        "/",
        StaticFiles(
            directory="web",
            html=True
        ),
        name="web"
    )


if __name__ == "__main__":

    api_thread = threading.Thread(
        target=run_api,
        daemon=True
    )

    api_thread.start()

    run_bot()
