import os
import sqlite3
import logging
from contextlib import closing

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    LabeledPrice,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
)

# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://donatuz-miniapp-production.up.railway.app"
)

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

PORT = int(os.getenv("PORT", "8000"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(title="DonatUZ")

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
                currency TEXT DEFAULT 'XTR',
                payload TEXT,
                status TEXT DEFAULT 'pending',
                telegram_payment_charge_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


init_db()

# =========================================================
# GAMES
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
        "icon_search": "League of Legends"
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
# TELEGRAM PRODUCTS
# =========================================================

PRODUCTS = [

    {
        "id": "stars",
        "name": "Telegram Stars",
        "icon": "⭐",
        "description": "Telegram Stars",
        "prices": [
            {"amount": 50, "stars": 50},
            {"amount": 100, "stars": 100},
            {"amount": 250, "stars": 250},
            {"amount": 500, "stars": 500},
            {"amount": 1000, "stars": 1000},
        ]
    },

    {
        "id": "premium",
        "name": "Telegram Premium",
        "icon": "💎",
        "description": "Premium",
        "prices": [
            {"amount": 1, "stars": 500},
            {"amount": 3, "stars": 1400},
            {"amount": 6, "stars": 2500},
            {"amount": 12, "stars": 4500},
        ]
    }

]

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
async def get_games():

    return GAMES


@app.get("/api/products")
async def get_products():

    return PRODUCTS


# =========================================================
# REAL TELEGRAM STARS PAYMENT
# =========================================================

@app.post("/api/pay")
async def pay(request: Request):

    data = await request.json()

    user_id = int(data.get("user_id", 0))

    username = data.get(
        "username",
        ""
    )

    product = data.get(
        "product",
        ""
    )

    player_id = data.get(
        "player_id",
        ""
    )

    stars = int(
        data.get(
            "stars",
            0
        )
    )

    if not user_id:

        return {
            "success": False,
            "message": "Telegram user ID topilmadi"
        }


    if stars <= 0:

        return {
            "success": False,
            "message": "Noto'g'ri Stars miqdori"
        }


    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    with closing(
        sqlite3.connect(DB_NAME)
    ) as conn:

        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO users
            (id, username, first_name)
            VALUES (?, ?, ?)
        """, (
            user_id,
            username,
            ""
        ))


        # -------------------------------------------------
        # ORDER
        # -------------------------------------------------

        cur.execute("""
            INSERT INTO orders
            (
                user_id,
                username,
                product,
                player_id,
                amount,
                currency,
                status
            )
            VALUES (?, ?, ?, ?, ?, 'XTR', 'pending')
        """, (
            user_id,
            username,
            product,
            player_id,
            stars
        ))

        order_id = cur.lastrowid

        payload = (
            f"DONATUZ|ORDER|{order_id}"
        )


        cur.execute("""
            UPDATE orders
            SET payload = ?
            WHERE id = ?
        """, (
            payload,
            order_id
        ))

        conn.commit()


    # -----------------------------------------------------
    # REAL TELEGRAM INVOICE
    # -----------------------------------------------------

    try:

        await telegram_app.bot.send_invoice(

            chat_id=user_id,

            title=f"DonatUZ — {product}",

            description=(
                f"Buyurtma #{order_id}. "
                f"Telegram Stars orqali to'lov."
            ),

            payload=payload,

            provider_token="",

            currency="XTR",

            prices=[
                LabeledPrice(
                    label=product,
                    amount=stars
                )
            ],

        )

        return {
            "success": True,
            "order_id": order_id,
            "message": "Invoice Telegramga yuborildi"
        }


    except Exception as e:

        logger.exception(
            "Invoice error"
        )

        with closing(
            sqlite3.connect(DB_NAME)
        ) as conn:

            conn.execute("""
                UPDATE orders
                SET status = 'invoice_error'
                WHERE id = ?
            """, (
                order_id,
            ))

            conn.commit()


        return {
            "success": False,
            "message": "Invoice yuborilmadi"
        }


# =========================================================
# ORDERS
# =========================================================

@app.get("/api/orders/{user_id}")
async def get_orders(user_id: int):

    with closing(
        sqlite3.connect(DB_NAME)
    ) as conn:

        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                product,
                player_id,
                amount,
                currency,
                status,
                created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
        """, (
            user_id,
        ))

        rows = cur.fetchall()


    result = []


    for row in rows:

        result.append({

            "id": row[0],

            "product": row[1],

            "player_id": row[2],

            "amount": row[3],

            "currency": row[4],

            "status": row[5],

            "created_at": row[6]

        })


    return result


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    with closing(
        sqlite3.connect(DB_NAME)
    ) as conn:

        conn.execute("""
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
                web_app=WebAppInfo(
                    url=WEBAPP_URL
                )
            )
        ]

    ]


    await update.message.reply_text(

        "🎮 DonatUZ'ga xush kelibsiz!\n\n"
        "O'yinlar va Telegram xizmatlarini "
        "qulay tarzda sotib oling.",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )

    )


# =========================================================
# PRE-CHECKOUT
# =========================================================

async def pre_checkout(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query =
        update.pre_checkout_query


    # Payloadni tekshirish

    if not query.invoice_payload.startswith(
        "DONATUZ|ORDER|"
    ):

        await query.answer(
            ok=False,
            error_message=
            "Buyurtma topilmadi."
        )

        return


    await query.answer(
        ok=True
    )


# =========================================================
# SUCCESSFUL PAYMENT
# =========================================================

async def successful_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message =
        update.message

    payment =
        message.successful_payment


    payload =
        payment.invoice_payload


    if not payload.startswith(
        "DONATUZ|ORDER|"
    ):

        return


    try:

        order_id =
            int(
                payload.split("|")[2]
            )

    except:

        return


    charge_id =
        payment.telegram_payment_charge_id


    # -----------------------------------------------------
    # ORDERNI PAID QILAMIZ
    # -----------------------------------------------------

    with closing(
        sqlite3.connect(DB_NAME)
    ) as conn:

        cur = conn.cursor()

        cur.execute("""
            UPDATE orders

            SET
                status = 'paid',
                telegram_payment_charge_id = ?

            WHERE
                id = ?
                AND status = 'pending'
        """, (
            charge_id,
            order_id
        ))


        cur.execute("""
            SELECT
                user_id,
                username,
                product,
                player_id,
                amount
            FROM orders
            WHERE id = ?
        """, (
            order_id,
        ))


        order =
            cur.fetchone()


        conn.commit()


    if not order:

        return


    user_id =
        order[0]

    username =
        order[1]

    product =
        order[2]

    player_id =
        order[3]

    amount =
        order[4]


    # -----------------------------------------------------
    # USERGA TASDIQ
    # -----------------------------------------------------

    await message.reply_text(

        "✅ TO'LOV MUVAFFAQIYATLI!\n\n"

        f"🧾 Buyurtma: #{order_id}\n"
        f"🎮 Xizmat: {product}\n"
        f"⭐ To'lov: {amount} Stars\n\n"

        "💳 To'lov Telegram tomonidan "
        "tasdiqlandi.\n\n"

        "📦 Buyurtmani bajarish jarayoni "
        "boshlanadi."

    )


    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    if ADMIN_ID:

        try:

            await context.bot.send_message(

                chat_id=ADMIN_ID,

                text=(

                    "💰 YANGI TO'LOV!\n\n"

                    f"🧾 Buyurtma: #{order_id}\n"
                    f"👤 User: {user_id}\n"
                    f"@{username}\n"
                    f"🎮 Xizmat: {product}\n"
                    f"🆔 Player ID: {player_id}\n"
                    f"⭐ Stars: {amount}\n"
                    f"💳 Charge ID: {charge_id}\n\n"

                    "📌 Status: PAID"

                )

            )

        except Exception as e:

            logger.error(
                f"Admin message error: {e}"
            )


    # =====================================================
    # MUHIM
    # =====================================================
    #
    # SHU YERDA haqiqiy o'yin top-up API ulanadi.
    #
    # Masalan:
    #
    # await send_game_topup(
    #     game=product,
    #     player_id=player_id,
    #     amount=amount
    # )
    #
    # Hozircha buni uydirmaymiz.
    # To'lov haqiqiy tasdiqlandi,
    # lekin o'yin serveriga top-up yuborish uchun
    # provayder API kerak.
    #
    # =====================================================


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎮 DonatUZ\n\n"

        "/start — Mini App\n"
        "/orders — Buyurtmalar\n"
        "/stats — Statistika"

    )


# =========================================================
# ORDERS COMMAND
# =========================================================

async def orders_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user =
        update.effective_user


    with closing(
        sqlite3.connect(DB_NAME)
    ) as conn:

        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                product,
                amount,
                currency,
                status
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (
            user.id,
        ))

        rows =
            cur.fetchall()


    if not rows:

        await update.message.reply_text(
            "📦 Buyurtmalar yo'q."
        )

        return


    text =
        "📦 Buyurtmalar:\n\n"


    for row in rows:

        text += (

            f"🧾 #{row[0]}\n"
            f"🎮 {row[1]}\n"
            f"💰 {row[2]} {row[3]}\n"
            f"📌 {row[4]}\n\n"

        )


    await update.message.reply_text(
        text
    )


# =========================================================
# STATS
# =========================================================

async def stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    with closing(
        sqlite3.connect(DB_NAME)
    ) as conn:

        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM users"
        )

        users =
            cur.fetchone()[0]


        cur.execute(
            "SELECT COUNT(*) FROM orders"
        )

        orders =
            cur.fetchone()[0]


        cur.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status = 'paid'
        """)

        paid =
            cur.fetchone()[0]


    await update.message.reply_text(

        "📊 DonatUZ\n\n"

        f"👥 Users: {users}\n"
        f"📦 Orders: {orders}\n"
        f"💰 Paid: {paid}"

    )


# =========================================================
# TELEGRAM APPLICATION
# =========================================================

telegram_app =
    Application.builder() \
    .token(BOT_TOKEN) \
    .build()


telegram_app.add_handler(
    CommandHandler(
        "start",
        start
    )
)


telegram_app.add_handler(
    CommandHandler(
        "help",
        help_command
    )
)


telegram_app.add_handler(
    CommandHandler(
        "orders",
        orders_command
    )
)


telegram_app.add_handler(
    CommandHandler(
        "stats",
        stats_command
    )
)


telegram_app.add_handler(
    PreCheckoutQueryHandler(
        pre_checkout
    )
)


telegram_app.add_handler(
    MessageHandler(
        filters.SUCCESSFUL_PAYMENT,
        successful_payment
    )
)


# =========================================================
# STATIC WEB
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
# STARTUP
# =========================================================

@app.on_event("startup")
async def startup():

    await telegram_app.initialize()

    await telegram_app.start()

    if telegram_app.updater:

        await telegram_app.updater.start_polling()

    logger.info(
        "DONATUZ BOT STARTED"
    )


# =========================================================
# SHUTDOWN
# =========================================================

@app.on_event("shutdown")
async def shutdown():

    if telegram_app.updater:

        await telegram_app.updater.stop()

    await telegram_app.stop()

    await telegram_app.shutdown()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )
