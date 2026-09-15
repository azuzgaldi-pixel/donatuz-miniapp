// =========================================================
// TELEGRAM
// =========================================================

const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();
    tg.expand();
}


// =========================================================
// GLOBAL
// =========================================================

let games = [];
let products = [];

let selectedCategory = "All";
let currentGame = null;

const user = tg?.initDataUnsafe?.user || {
    id: 0,
    first_name: "Demo",
    last_name: "",
    username: "demo_user"
};


// =========================================================
// API
// =========================================================

async function api(url, options = {}) {

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if (tg?.initData) {
        headers["X-Telegram-Init-Data"] = tg.initData;
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (!response.ok) {
        throw new Error(
            await response.text()
        );
    }

    return response.json();
}


// =========================================================
// INIT
// =========================================================

async function init() {

    try {

        games = await api("/api/games");

        products = await api("/api/products");

        renderCategories();

        renderGames();

        renderProfile();

        loadOrders();

    } catch (error) {

        console.error(error);

        showToast(
            "Server bilan bog‘lanishda xatolik"
        );
    }
}


document.addEventListener(
    "DOMContentLoaded",
    init
);


// =========================================================
// NAVIGATION
// =========================================================

function navigate(pageId, button) {

    document
        .querySelectorAll(".page")
        .forEach(page => {
            page.classList.remove("active");
        });

    const page = document.getElementById(pageId);

    if (page) {
        page.classList.add("active");
    }

    document
        .querySelectorAll(".nav-item")
        .forEach(item => {
            item.classList.remove("active");
        });

    if (button) {
        button.classList.add("active");
    }

    if (pageId === "ordersPage") {
        loadOrders();
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// =========================================================
// CATEGORIES
// =========================================================

function renderCategories() {

    const container =
        document.getElementById("categories");

    const categories = [
        "All",
        ...new Set(
            games.map(game => game.category)
        )
    ];

    container.innerHTML = categories
        .map(category => `
            <button
                class="category ${
                    selectedCategory === category
                        ? "active"
                        : ""
                }"
                onclick="selectCategory('${escapeHtml(category)}')"
            >
                ${category === "All" ? "🔥 Barchasi" : category}
            </button>
        `)
        .join("");
}


function selectCategory(category) {

    selectedCategory = category;

    renderCategories();

    renderGames();
}


// =========================================================
// GAMES
// =========================================================

function getFilteredGames() {

    const search =
        document
            .getElementById("searchInput")
            ?.value
            ?.toLowerCase()
            .trim() || "";

    return games.filter(game => {

        const matchesCategory =
            selectedCategory === "All" ||
            game.category === selectedCategory;

        const matchesSearch =
            game.name
                .toLowerCase()
                .includes(search);

        return matchesCategory && matchesSearch;
    });
}


function renderGames() {

    const filtered =
        getFilteredGames();

    const allContainer =
        document.getElementById("gamesGrid");

    allContainer.innerHTML =
        filtered
            .map(gameCard)
            .join("");

    const popular =
        document.getElementById("popularGames");

    const popularGames =
        games.slice(0, 6);

    popular.innerHTML =
        popularGames
            .map(gameCard)
            .join("");
}


function gameCard(game) {

    return `
        <div
            class="game-card"
            onclick="openGame('${game.id}')"
        >

            <div class="game-icon">
                ${game.icon}
            </div>

            <div class="game-name">
                ${escapeHtml(game.name)}
            </div>

            <div class="game-category">
                ${escapeHtml(game.category)}
            </div>

        </div>
    `;
}


function searchGames() {

    renderGames();
}


function showAllGames() {

    selectedCategory = "All";

    document.getElementById(
        "searchInput"
    ).value = "";

    renderCategories();

    renderGames();

    window.scrollTo({
        top: document
            .getElementById("gamesGrid")
            .offsetTop - 90,
        behavior: "smooth"
    });
}


// =========================================================
// GAME DETAILS
// =========================================================

function openGame(gameId) {

    const game =
        games.find(
            item => item.id === gameId
        );

    if (!game) return;

    currentGame = game;

    const body =
        document.getElementById("modalBody");

    body.innerHTML = `

        <div class="modal-title">

            <div class="modal-game-icon">
                ${game.icon}
            </div>

            <h2>
                ${escapeHtml(game.name)}
            </h2>

            <p>
                ${escapeHtml(game.description)}
            </p>

        </div>

        <input
            id="playerId"
            class="player-input"
            placeholder="Player ID / UID"
        >

        <div class="package-list">

            ${game.packages
                .map((pkg, index) => `

                    <button
                        class="package"
                        onclick="createGameOrder(${index})"
                    >

                        <span class="package-name">
                            ${escapeHtml(pkg.name)}
                        </span>

                        <span class="package-price">
                            ${formatMoney(pkg.price)}
                        </span>

                    </button>

                `)
                .join("")}

        </div>

    `;

    openModal();
}


// =========================================================
// CREATE GAME ORDER
// =========================================================

async function createGameOrder(index) {

    if (!currentGame) return;

    const playerId =
        document
            .getElementById("playerId")
            ?.value
            ?.trim();

    if (!playerId) {

        showToast(
            "Avval Player ID / UID kiriting"
        );

        return;
    }

    const pkg =
        currentGame.packages[index];

    try {

        const result = await api(
            "/api/order",
            {
                method: "POST",

                body: JSON.stringify({
                    product_type: "game",
                    product_id: currentGame.id,
                    package_name: pkg.name,
                    amount: pkg.price,
                    player_id: playerId
                })
            }
        );

        if (result.success) {

            closeModal();

            showToast(
                `Buyurtma #${result.order_id} yaratildi`
            );

            navigate(
                "ordersPage",
                document.querySelector(
                    '[data-page="ordersPage"]'
                )
            );
        }

    } catch (error) {

        console.error(error);

        showToast(
            "Buyurtma yaratishda xatolik"
        );
    }
}


// =========================================================
// TELEGRAM PRODUCTS
// =========================================================

function openTelegramProduct(productId) {

    const product =
        products.find(
            item => item.id === productId
        );

    if (!product) return;

    const body =
        document.getElementById("modalBody");

    body.innerHTML = `

        <div class="modal-title">

            <div class="modal-game-icon">
                ${product.icon}
            </div>

            <h2>
                ${escapeHtml(product.name)}
            </h2>

            <p>
                ${escapeHtml(product.description)}
            </p>

        </div>

        <div class="package-list">

            ${product.packages
                .map((pkg, index) => `

                    <button
                        class="package"
                        onclick="telegramPackageInfo('${product.id}', ${index})"
                    >

                        <span class="package-name">
                            ${escapeHtml(pkg.name)}
                        </span>

                        <span class="package-price">
                            ${
                                pkg.price > 0
                                    ? formatMoney(pkg.price)
                                    : "Mavjud"
                            }
                        </span>

                    </button>

                `)
                .join("")}

        </div>

    `;

    openModal();
}


function telegramPackageInfo(
    productId,
    index
) {

    const product =
        products.find(
            item => item.id === productId
        );

    if (!product) return;

    const pkg =
        product.packages[index];

    if (productId === "premium") {

        showToast(
            "Premium uchun rasmiy Telegram to‘lov mexanizmi ulanadi"
        );

        return;
    }

    showToast(
        "Stars uchun rasmiy Telegram Stars to‘lovi ulanadi"
    );
}


// =========================================================
// ORDERS
// =========================================================

async function loadOrders() {

    const container =
        document.getElementById(
            "ordersList"
        );

    if (!container) return;

    try {

        const result =
            await api(
                `/api/orders/${user.id}`
            );

        if (!result.length) {

            container.innerHTML = `
                <div class="empty">
                    📦<br><br>
                    Hali buyurtmalar yo‘q.
                </div>
            `;

            document.getElementById(
                "profileOrderCount"
            ).textContent = "0";

            return;
        }

        document.getElementById(
            "profileOrderCount"
        ).textContent =
            result.length;

        container.innerHTML =
            result
                .map(orderCard)
                .join("");

    } catch (error) {

        console.error(error);

        container.innerHTML = `
            <div class="empty">
                Buyurtmalarni yuklab bo‘lmadi.
            </div>
        `;
    }
}


function orderCard(order) {

    let statusText =
        "⏳ Kutilmoqda";

    let statusClass =
        "pending";

    if (order.status === "completed") {

        statusText =
            "✅ Bajarilgan";

        statusClass =
            "completed";

    } else if (order.status === "paid") {

        statusText =
            "💳 To‘langan";
    }

    return `

        <div class="order-card">

            <div class="order-top">

                <div>

                    <div class="order-name">
                        ${
                            escapeHtml(
                                order.game_name ||
                                order.product_name
                            )
                        }
                    </div>

                    <div class="order-id">
                        #${order.id}
                    </div>

                </div>

            </div>

            <div class="order-package">
                📦 ${escapeHtml(order.package_name)}
            </div>

            <div class="order-bottom">

                <div class="order-price">
                    ${formatMoney(order.amount)}
                </div>

                <div class="status ${statusClass}">
                    ${statusText}
                </div>

            </div>

        </div>

    `;
}


// =========================================================
// PROFILE
// =========================================================

function renderProfile() {

    const fullName =
        [
            user.first_name,
            user.last_name
        ]
        .filter(Boolean)
        .join(" ") ||
        "Foydalanuvchi";

    document.getElementById(
        "profileName"
    ).textContent = fullName;

    document.getElementById(
        "profileUsername"
    ).textContent =
        user.username
            ? `@${user.username}`
            : "Username yo‘q";

    document.getElementById(
        "profileId"
    ).textContent =
        user.id || "—";

    const avatar =
        document.getElementById(
            "profileAvatar"
        );

    if (
        tg?.initDataUnsafe?.user?.photo_url
    ) {

        avatar.innerHTML = `
            <img
                src="${tg.initDataUnsafe.user.photo_url}"
                style="
                    width:100%;
                    height:100%;
                    object-fit:cover;
                    border-radius:22px;
                "
            >
        `;
    }
}


function openProfile() {

    navigate(
        "profilePage",
        document.querySelector(
            '[data-page="profilePage"]'
        )
    );
}


// =========================================================
// MODAL
// =========================================================

function openModal() {

    document
        .getElementById("modal")
        .classList.remove("hidden");
}


function closeModal(event) {

    if (
        event &&
        event.target !== event.currentTarget
    ) {
        return;
    }

    document
        .getElementById("modal")
        .classList.add("hidden");
}


// =========================================================
// SUPPORT / ABOUT
// =========================================================

function showSupport() {

    showModalMessage(
        "💬 Yordam",
        "Muammo bo‘lsa, DonatUZ administratoriga murojaat qiling."
    );
}


function showAbout() {

    showModalMessage(
        "🎮 DonatUZ",
        "DonatUZ — o‘yinlar va Telegram xizmatlarini bir joyga jamlovchi Mini App."
    );
}


function showModalMessage(
    title,
    message
) {

    document.getElementById(
        "modalBody"
    ).innerHTML = `

        <div class="modal-title">

            <div class="modal-game-icon">
                ℹ️
            </div>

            <h2>
                ${escapeHtml(title)}
            </h2>

            <p>
                ${escapeHtml(message)}
            </p>

        </div>

    `;

    openModal();
}


// =========================================================
// TOAST
// =========================================================

function showToast(message) {

    if (tg?.showAlert) {

        tg.showAlert(message);

        return;
    }

    const old =
        document.querySelector(
            ".toast"
        );

    if (old) {
        old.remove();
    }

    const toast =
        document.createElement("div");

    toast.className = "toast";

    toast.textContent = message;

    toast.style.cssText = `
        position:fixed;
        left:50%;
        bottom:95px;
        transform:translateX(-50%);
        z-index:500;
        background:#202737;
        color:white;
        padding:12px 17px;
        border-radius:13px;
        font-size:12px;
        box-shadow:0 10px 35px rgba(0,0,0,.4);
        max-width:85%;
        text-align:center;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 2500);
}


// =========================================================
// FORMAT
// =========================================================

function formatMoney(amount) {

    return (
        Number(amount || 0)
            .toLocaleString("uz-UZ")
            + " UZS"
    );
}


function escapeHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
