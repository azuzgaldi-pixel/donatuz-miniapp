// ===============================
// DonatUZ | Games & Stars
// app.js
// ===============================

const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor("#111827");
    tg.setBackgroundColor("#0b1020");
}

// ===============================
// USER
// ===============================

const TG_USER = tg?.initDataUnsafe?.user || {};

const USER_ID = TG_USER.id || 0;
const USERNAME = TG_USER.username || "";

// ===============================
// GAME LIST
// ===============================

const GAMES = [
    { name: "PUBG Mobile", search: "PUBG MOBILE" },
    { name: "Free Fire", search: "Free Fire" },
    { name: "Mobile Legends", search: "Mobile Legends" },
    { name: "Brawl Stars", search: "Brawl Stars" },
    { name: "Roblox", search: "Roblox" },
    { name: "Clash of Clans", search: "Clash of Clans" },
    { name: "Clash Royale", search: "Clash Royale" },
    { name: "Standoff 2", search: "Standoff 2" },
    { name: "Call of Duty Mobile", search: "Call of Duty Mobile" },
    { name: "FC Mobile", search: "EA SPORTS FC Mobile" },
    { name: "eFootball", search: "eFootball" },
    { name: "Genshin Impact", search: "Genshin Impact" },
    { name: "Honkai: Star Rail", search: "Honkai Star Rail" },
    { name: "Valorant", search: "VALORANT" },
    { name: "League of Legends", search: "League of Legends" },
    { name: "Fortnite", search: "Fortnite" },
    { name: "Minecraft", search: "Minecraft" },
    { name: "Arena Breakout", search: "Arena Breakout" },
    { name: "Delta Force", search: "Delta Force" },
    { name: "Steam", search: "Steam" }
];

// ===============================
// TELEGRAM PRODUCTS
// ===============================

const PRODUCTS = [
    {
        id: "premium",
        name: "Telegram Premium",
        icon: "💎",
        description: "Telegram Premium",
        prices: [
            { title: "1 oy", stars: 500 },
            { title: "3 oy", stars: 1400 },
            { title: "6 oy", stars: 2500 },
            { title: "12 oy", stars: 4500 }
        ]
    },

    {
        id: "stars",
        name: "Telegram Stars",
        icon: "⭐",
        description: "Telegram Stars"
    }
];

// ===============================
// STATE
// ===============================

let selectedGame = null;
let selectedProduct = null;
let selectedPrice = null;

let gameIcons = {};

// ===============================
// DOM
// ===============================

const gamesContainer =
    document.getElementById("games") ||
    document.getElementById("gamesContainer") ||
    document.querySelector(".games");

const productsContainer =
    document.getElementById("products") ||
    document.getElementById("productsContainer") ||
    document.querySelector(".products");

const searchInput =
    document.getElementById("search") ||
    document.getElementById("searchInput");

const modal =
    document.getElementById("modal") ||
    document.getElementById("gameModal") ||
    document.querySelector(".modal");

const modalTitle =
    document.getElementById("modalTitle") ||
    document.querySelector(".modal-title");

const playerId =
    document.getElementById("playerId") ||
    document.getElementById("uid") ||
    document.querySelector('input[name="player_id"]');

const orderButton =
    document.getElementById("orderButton") ||
    document.getElementById("payButton") ||
    document.querySelector(".order-button");

const closeButton =
    document.getElementById("closeModal") ||
    document.querySelector(".close-modal");

// ===============================
// HELPERS
// ===============================

function showAlert(message) {
    if (tg?.showAlert) {
        tg.showAlert(message);
    } else {
        alert(message);
    }
}

function showPopup(message) {
    if (tg?.showPopup) {
        tg.showPopup({
            title: "DonatUZ",
            message: message,
            buttons: [{ type: "ok" }]
        });
    } else {
        alert(message);
    }
}

function haptic(type = "light") {
    try {
        tg?.HapticFeedback?.impactOccurred(type);
    } catch (e) {}
}

// ===============================
// APPLE APP STORE ICON SEARCH
// ===============================

async function getGameIcon(game) {
    if (gameIcons[game.name]) {
        return gameIcons[game.name];
    }

    try {
        const url =
            "https://itunes.apple.com/search?term=" +
            encodeURIComponent(game.search) +
            "&entity=software&limit=10&country=US";

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("Icon API error");
        }

        const data = await response.json();

        if (data.results && data.results.length > 0) {

            // Avval eng mos natijani topishga harakat qilamiz
            let result = data.results.find(item => {
                const name = (item.trackName || "").toLowerCase();
                const target = game.search.toLowerCase();

                return (
                    name.includes(target) ||
                    target.includes(name)
                );
            });

            if (!result) {
                result = data.results[0];
            }

            const icon =
                result.artworkUrl512 ||
                result.artworkUrl100 ||
                result.artworkUrl60;

            if (icon) {
                gameIcons[game.name] = icon;
                return icon;
            }
        }

    } catch (error) {
        console.log("Icon yuklanmadi:", game.name, error);
    }

    return null;
}

// ===============================
// CREATE GAME CARD
// ===============================

function createGameCard(game) {

    const card = document.createElement("div");

    card.className = "game-card";

    card.innerHTML = `
        <div class="game-icon-wrapper">
            <img
                class="game-icon"
                src=""
                alt="${game.name}"
                loading="lazy"
            >

            <div class="game-placeholder">
                🎮
            </div>
        </div>

        <div class="game-name">
            ${game.name}
        </div>
    `;

    const img = card.querySelector(".game-icon");
    const placeholder = card.querySelector(".game-placeholder");

    getGameIcon(game).then(icon => {

        if (icon) {
            img.src = icon;

            img.onload = () => {
                img.style.display = "block";
                placeholder.style.display = "none";
            };

            img.onerror = () => {
                img.style.display = "none";
                placeholder.style.display = "flex";
            };

        } else {
            img.style.display = "none";
            placeholder.style.display = "flex";
        }

    });

    card.addEventListener("click", () => {
        haptic("light");
        openGameModal(game);
    });

    return card;
}

// ===============================
// RENDER GAMES
// ===============================

function renderGames(list = GAMES) {

    if (!gamesContainer) {
        console.warn("Games container topilmadi");
        return;
    }

    gamesContainer.innerHTML = "";

    if (list.length === 0) {

        gamesContainer.innerHTML = `
            <div class="empty-state">
                <div style="font-size:40px;">🔍</div>
                <div>O‘yin topilmadi</div>
            </div>
        `;

        return;
    }

    list.forEach(game => {
        gamesContainer.appendChild(
            createGameCard(game)
        );
    });
}

// ===============================
// RENDER PRODUCTS
// ===============================

function renderProducts() {

    if (!productsContainer) {
        return;
    }

    productsContainer.innerHTML = "";

    // PREMIUM
    const premium = PRODUCTS.find(
        p => p.id === "premium"
    );

    if (premium) {

        const card = document.createElement("div");

        card.className = "product-card";

        card.innerHTML = `
            <div class="product-icon">
                ${premium.icon}
            </div>

            <div class="product-info">
                <div class="product-name">
                    ${premium.name}
                </div>

                <div class="product-description">
                    Telegram Premium
                </div>
            </div>

            <div class="product-arrow">
                ›
            </div>
        `;

        card.addEventListener("click", () => {
            haptic("light");
            openProductModal(premium);
        });

        productsContainer.appendChild(card);
    }

    // STARS
    const stars = document.createElement("div");

    stars.className = "product-card";

    stars.innerHTML = `
        <div class="product-icon">
            ⭐
        </div>

        <div class="product-info">
            <div class="product-name">
                Telegram Stars
            </div>

            <div class="product-description">
                Telegram Stars haqida
            </div>
        </div>

        <div class="product-arrow">
            ›
        </div>
    `;

    stars.addEventListener("click", () => {
        haptic("light");

        showPopup(
            "Telegram Stars'ni Telegramning o‘zidan sotib olish mumkin. " +
            "DonatUZ Stars yaratib yoki o‘zi chiqarib bera olmaydi."
        );
    });

    productsContainer.appendChild(stars);
}

// ===============================
// OPEN GAME MODAL
// ===============================

function openGameModal(game) {

    selectedGame = game;
    selectedProduct = null;
    selectedPrice = null;

    if (!modal) {
        return;
    }

    if (modalTitle) {
        modalTitle.textContent =
            `${game.name} — Donat`;
    }

    if (playerId) {
        playerId.value = "";
        playerId.placeholder =
            "Player ID / UID kiriting";
    }

    // UID maydonini ko‘rsatish
    if (playerId) {
        playerId.style.display = "block";
    }

    // Narxlar bo‘lsa eski tanlovlarni tozalash
    clearPriceButtons();

    modal.classList.add("active");

    // Agar modal style display bilan ishlasa
    modal.style.display = "flex";

    setTimeout(() => {
        playerId?.focus();
    }, 100);
}

// ===============================
// OPEN PRODUCT MODAL
// ===============================

function openProductModal(product) {

    selectedProduct = product;
    selectedGame = null;
    selectedPrice = null;

    if (!modal) {
        return;
    }

    if (modalTitle) {
        modalTitle.textContent =
            product.name;
    }

    if (playerId) {
        playerId.style.display = "none";
    }

    clearPriceButtons();

    // Premium narxlarini chiqarish
    if (
        product.id === "premium" &&
        product.prices
    ) {

        const priceContainer =
            document.createElement("div");

        priceContainer.id =
            "dynamicPrices";

        priceContainer.className =
            "price-list";

        product.prices.forEach((price, index) => {

            const button =
                document.createElement("button");

            button.className =
                "price-button";

            button.innerHTML = `
                <span>
                    ${price.title}
                </span>

                <span>
                    ⭐ ${price.stars}
                </span>
            `;

            button.addEventListener("click", () => {

                document
                    .querySelectorAll(".price-button")
                    .forEach(btn =>
                        btn.classList.remove("selected")
                    );

                button.classList.add("selected");

                selectedPrice = price;

                haptic("light");
            });

            priceContainer.appendChild(button);
        });

        const modalBody =
            modal.querySelector(".modal-body") ||
            modal.querySelector(".modal-content") ||
            modal;

        modalBody.appendChild(priceContainer);
    }

    modal.classList.add("active");
    modal.style.display = "flex";
}

// ===============================
// CLEAR PRICE BUTTONS
// ===============================

function clearPriceButtons() {

    const old =
        document.getElementById("dynamicPrices");

    if (old) {
        old.remove();
    }

    selectedPrice = null;
}

// ===============================
// CLOSE MODAL
// ===============================

function closeModal() {

    if (!modal) {
        return;
    }

    modal.classList.remove("active");
    modal.style.display = "none";

    selectedGame = null;
    selectedProduct = null;
    selectedPrice = null;

    clearPriceButtons();

    if (playerId) {
        playerId.value = "";
    }

    haptic("light");
}

if (closeButton) {
    closeButton.addEventListener(
        "click",
        closeModal
    );
}

// Modal tashqarisiga bosilganda yopish
if (modal) {

    modal.addEventListener("click", e => {

        if (e.target === modal) {
            closeModal();
        }

    });
}

// ===============================
// PAYMENT
// ===============================

async function createPayment() {

    if (!USER_ID) {

        showAlert(
            "Telegram foydalanuvchisi aniqlanmadi. " +
            "Mini App'ni Telegram ichidan oching."
        );

        return;
    }

    let productName = "";
    let stars = 0;
    let uid = "";

    // ===========================
    // GAME
    // ===========================

    if (selectedGame) {

        uid =
            playerId?.value?.trim() || "";

        if (!uid) {

            showAlert(
                "Avval Player ID / UID kiriting."
            );

            playerId?.focus();

            return;
        }

        productName =
            selectedGame.name;

        /*
         * Hozircha test Stars miqdori.
         *
         * MUHIM:
         * Bu joy haqiqiy game package
         * bilan keyin almashtiriladi.
         */
        stars = 100;
    }

    // ===========================
    // PREMIUM
    // ===========================

    else if (selectedProduct) {

        if (
            selectedProduct.id === "premium"
        ) {

            if (!selectedPrice) {

                showAlert(
                    "Premium muddatini tanlang."
                );

                return;
            }

            productName =
                `${selectedProduct.name} — ${selectedPrice.title}`;

            stars =
                Number(selectedPrice.stars);

        }

        else {

            showAlert(
                "Telegram Stars'ni Telegramning o‘zidan sotib oling."
            );

            return;
        }
    }

    else {

        showAlert(
            "Mahsulot yoki o‘yin tanlanmagan."
        );

        return;
    }

    if (!stars || stars <= 0) {

        showAlert(
            "To‘lov summasi noto‘g‘ri."
        );

        return;
    }

    // Tugmani vaqtincha bloklash
    if (orderButton) {
        orderButton.disabled = true;
        orderButton.dataset.oldText =
            orderButton.textContent;

        orderButton.textContent =
            "Invoice yuborilmoqda...";
    }

    try {

        const response =
            await fetch("/api/pay", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    user_id: USER_ID,

                    username: USERNAME,

                    product: productName,

                    player_id: uid,

                    stars: stars

                })

            });

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Server xatosi"
            );
        }

        haptic("medium");

        /*
         * Backend Telegramga invoice yuboradi.
         *
         * Telegram invoice chat oynasida
         * ko‘rinadi va foydalanuvchi
         * Stars bilan to‘laydi.
         */

        showPopup(
            "Invoice Telegramga yuborildi. " +
            "Telegramdagi to‘lov oynasini ochib, " +
            "to‘lovni tasdiqlang."
        );

        closeModal();

    } catch (error) {

        console.error(
            "PAYMENT ERROR:",
            error
        );

        showAlert(
            "To‘lovni boshlashda xatolik:\n" +
            error.message
        );

    } finally {

        if (orderButton) {

            orderButton.disabled =
                false;

            orderButton.textContent =
                orderButton.dataset.oldText ||
                "Buyurtma berish";
        }
    }
}

// ===============================
// ORDER BUTTON
// ===============================

if (orderButton) {

    orderButton.addEventListener(
        "click",
        createPayment
    );
}

// ===============================
// SEARCH
// ===============================

if (searchInput) {

    searchInput.addEventListener(
        "input",
        () => {

            const query =
                searchInput.value
                    .trim()
                    .toLowerCase();

            if (!query) {

                renderGames(GAMES);

                return;
            }

            const filtered =
                GAMES.filter(game =>
                    game.name
                        .toLowerCase()
                        .includes(query)
                );

            renderGames(filtered);

        }
    );
}

// ===============================
// NAVIGATION
// ===============================

document.addEventListener(
    "click",
    event => {

        const button =
            event.target.closest(
                "[data-page]"
            );

        if (!button) {
            return;
        }

        const page =
            button.dataset.page;

        document
            .querySelectorAll(
                "[data-page]"
            )
            .forEach(el =>
                el.classList.remove(
                    "active"
                )
            );

        button.classList.add("active");

        document
            .querySelectorAll(
                ".page"
            )
            .forEach(el => {

                el.classList.remove(
                    "active"
                );

                if (
                    el.id === page ||
                    el.dataset.page === page
                ) {
                    el.classList.add(
                        "active"
                    );
                }

            });

        haptic("light");
    }
);

// ===============================
// BACK BUTTON
// ===============================

if (tg?.BackButton) {

    tg.BackButton.onClick(() => {

        if (
            modal?.classList.contains(
                "active"
            )
        ) {
            closeModal();
        } else {
            tg.close();
        }

    });
}

// ===============================
// LOAD ORDERS
// ===============================

async function loadOrders() {

    if (!USER_ID) {
        return;
    }

    try {

        const response =
            await fetch(
                `/api/orders/${USER_ID}`
            );

        if (!response.ok) {
            return;
        }

        const orders =
            await response.json();

        const ordersContainer =
            document.getElementById(
                "orders"
            );

        if (!ordersContainer) {
            return;
        }

        ordersContainer.innerHTML = "";

        if (
            !orders ||
            orders.length === 0
        ) {

            ordersContainer.innerHTML = `
                <div class="empty-state">
                    Hozircha buyurtmalar yo‘q.
                </div>
            `;

            return;
        }

        orders.forEach(order => {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "order-item";

            let statusText =
                "Kutilmoqda";

            if (
                order.status === "paid"
            ) {
                statusText =
                    "To‘langan";
            }

            if (
                order.status === "failed"
            ) {
                statusText =
                    "Bekor qilingan";
            }

            item.innerHTML = `
                <div>
                    <strong>
                        ${escapeHtml(
                            order.product || ""
                        )}
                    </strong>

                    <div>
                        ${escapeHtml(
                            order.created_at || ""
                        )}
                    </div>
                </div>

                <div>
                    ⭐ ${order.amount || 0}
                    <br>
                    <span>
                        ${statusText}
                    </span>
                </div>
            `;

            ordersContainer.appendChild(
                item
            );
        });

    } catch (error) {

        console.log(
            "Orders error:",
            error
        );

    }
}

// ===============================
// HTML ESCAPE
// ===============================

function escapeHtml(text) {

    return String(text)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}

// ===============================
// INITIALIZE
// ===============================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        renderGames();
        renderProducts();
        loadOrders();

        console.log(
            "DonatUZ Mini App ishga tushdi"
        );

        console.log(
            "Telegram User ID:",
            USER_ID
        );

    }
);

// Agar DOMContentLoaded allaqachon o‘tgan bo‘lsa
if (
    document.readyState ===
    "interactive" ||
    document.readyState === "complete"
) {

    renderGames();
    renderProducts();

}
