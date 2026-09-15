const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

let games = [];
let currentGame = null;
let selectedPackage = null;
let currentCategory = "all";


// =========================================================
// TELEGRAM USER
// =========================================================

const telegramUser = tg.initDataUnsafe?.user || null;

function getUserId() {
    return telegramUser?.id || null;
}


// =========================================================
// INITIALIZE
// =========================================================

document.addEventListener("DOMContentLoaded", async () => {

    try {
        await loadGames();
        updateProfile();
        loadOrders();
    } catch (error) {
        console.error(error);
    }

});


// =========================================================
// LOAD GAMES
// =========================================================

async function loadGames() {

    const response = await fetch("/api/games");

    games = await response.json();

    renderGames(games);
}


// =========================================================
// RENDER GAMES
// =========================================================

function renderGames(list) {

    const grid = document.getElementById("gamesGrid");

    grid.innerHTML = "";

    if (!list.length) {

        grid.innerHTML = `
            <div style="
                grid-column:1/-1;
                text-align:center;
                padding:40px;
                color:#8992a5;
            ">
                O'yin topilmadi 😔
            </div>
        `;

        return;
    }

    list.forEach(game => {

        const card = document.createElement("div");

        card.className = "game-card";

        card.onclick = () => openGame(game.id);

        card.innerHTML = `
            <div class="game-icon">
                ${game.icon}
            </div>

            <div class="game-name">
                ${game.name}
            </div>

            <div class="game-category">
                ${game.category}
            </div>

            <div class="game-arrow">
                ›
            </div>
        `;

        grid.appendChild(card);

    });
}


// =========================================================
// SEARCH
// =========================================================

function searchGames() {

    const value =
        document
            .getElementById("gameSearch")
            .value
            .toLowerCase()
            .trim();

    const filtered = games.filter(game => {

        const name =
            game.name.toLowerCase();

        const category =
            game.category.toLowerCase();

        const matchesSearch =
            name.includes(value) ||
            category.includes(value);

        const matchesCategory =
            currentCategory === "all" ||
            game.category === currentCategory;

        return matchesSearch && matchesCategory;

    });

    renderGames(filtered);
}


// =========================================================
// CATEGORY
// =========================================================

function filterCategory(category, button) {

    currentCategory = category;

    document
        .querySelectorAll(".category")
        .forEach(btn => btn.classList.remove("active"));

    button.classList.add("active");

    searchGames();
}


// =========================================================
// OPEN GAME
// =========================================================

function openGame(gameId) {

    currentGame =
        games.find(game => game.id === gameId);

    if (!currentGame) return;

    selectedPackage = null;

    const detail =
        document.getElementById("gameDetail");

    detail.innerHTML = `

        <div class="detail-header">

            <div class="detail-icon">
                ${currentGame.icon}
            </div>

            <div>

                <h1>
                    ${currentGame.name}
                </h1>

                <p>
                    ${currentGame.category}
                </p>

            </div>

        </div>


        <label class="field-label">
            Player ID / UID
        </label>

        <input
            id="playerId"
            class="player-input"
            placeholder="Player ID ni kiriting"
            autocomplete="off"
        >


        <div class="package-title">
            Paketni tanlang
        </div>

        <div
            id="packageGrid"
            class="package-grid"
        ></div>


        <button
            class="buy-button"
            onclick="createOrder()"
        >
            Buyurtma berish
        </button>

    `;


    const packageGrid =
        document.getElementById("packageGrid");


    currentGame.packages.forEach((pkg, index) => {

        const item =
            document.createElement("button");

        item.className = "package";

        item.innerHTML = `
            <div class="package-name">
                ${pkg.name}
            </div>

            <div class="package-price">
                ${formatMoney(pkg.price + 200)} UZS
            </div>
        `;

        item.onclick = () => {

            selectedPackage = pkg;

            document
                .querySelectorAll(".package")
                .forEach(el =>
                    el.classList.remove("selected")
                );

            item.classList.add("selected");

        };

        packageGrid.appendChild(item);

    });


    showPage("game");
}


// =========================================================
// CREATE ORDER
// =========================================================

async function createOrder() {

    if (!telegramUser) {

        showAlert(
            "Mini App Telegram ichida ochilishi kerak."
        );

        return;
    }


    const playerId =
        document
            .getElementById("playerId")
            .value
            .trim();


    if (!playerId) {

        showAlert(
            "Avval Player ID / UID kiriting."
        );

        return;
    }


    if (!selectedPackage) {

        showAlert(
            "Avval paketni tanlang."
        );

        return;
    }


    try {

        tg.MainButton.showProgress();


        const response =
            await fetch("/api/order", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    initData: tg.initData,

                    game: currentGame.id,

                    package:
                        selectedPackage.name,

                    player_id:
                        playerId

                })

            });


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Buyurtma yaratilmadi"
            );

        }


        showAlert(
            `Buyurtma #${data.order_id} yaratildi!\n\n` +
            `Summa: ${formatMoney(data.price)} UZS\n\n` +
            `Hozircha bu demo bosqich. ` +
            `Haqiqiy to'lov keyingi bosqichda ulanadi.`
        );


        loadOrders();

    } catch (error) {

        showAlert(error.message);

    } finally {

        tg.MainButton.hideProgress();

    }
}


// =========================================================
// ORDERS
// =========================================================

async function loadOrders() {

    const userId = getUserId();

    if (!userId) return;

    try {

        const response =
            await fetch(
                `/api/orders/${userId}`
            );

        const orders =
            await response.json();

        renderOrders(orders);

        document
            .getElementById("profileOrders")
            .textContent = orders.length;

    } catch (error) {

        console.error(error);

    }
}


function renderOrders(orders) {

    const container =
        document.getElementById("ordersList");


    if (!orders.length) {

        container.innerHTML = `
            <div class="empty-orders">

                <div>📦</div>

                <p>
                    Hozircha buyurtmalar yo'q.
                </p>

            </div>
        `;

        return;
    }


    container.innerHTML = "";


    orders.forEach(order => {

        const card =
            document.createElement("div");

        card.className = "order-card";


        let statusText =
            "⏳ Kutilmoqda";


        if (order.status === "completed") {
            statusText = "✅ Bajarildi";
        }

        if (order.status === "processing") {
            statusText = "🔄 Jarayonda";
        }

        if (order.status === "cancelled") {
            statusText = "❌ Bekor qilindi";
        }


        card.innerHTML = `

            <div class="order-top">

                <span class="order-id">
                    #${order.id}
                </span>

                <span class="order-status">
                    ${statusText}
                </span>

            </div>


            <div class="order-name">
                ${order.product_name}
            </div>

            <div class="order-package">
                ${order.package}
            </div>

            <div class="order-price">
                ${formatMoney(order.price)} UZS
            </div>

        `;


        container.appendChild(card);

    });
}


// =========================================================
// PROFILE
// =========================================================

function updateProfile() {

    if (!telegramUser) return;


    const firstName =
        telegramUser.first_name || "Foydalanuvchi";

    const lastName =
        telegramUser.last_name || "";

    document
        .getElementById("profileName")
        .textContent =
            `${firstName} ${lastName}`.trim();


    document
        .getElementById("profileUsername")
        .textContent =
            telegramUser.username
                ? `@${telegramUser.username}`
                : "Username yo'q";


    document
        .getElementById("profileId")
        .textContent =
            telegramUser.id;


    const avatar =
        document.getElementById("profileAvatar");


    if (telegramUser.photo_url) {

        avatar.innerHTML = `
            <img
                src="${telegramUser.photo_url}"
                style="
                    width:100%;
                    height:100%;
                    border-radius:50%;
                    object-fit:cover;
                "
            >
        `;

    }

}


// =========================================================
// PAGE NAVIGATION
// =========================================================

function showPage(page) {

    document
        .querySelectorAll(".page")
        .forEach(p =>
            p.classList.remove("active")
        );


    const pageElement =
        document.getElementById(
            `${page}Page`
        );


    if (pageElement) {
        pageElement.classList.add("active");
    }


    document
        .querySelectorAll(".nav-item")
        .forEach(item =>
            item.classList.remove("active")
        );


    if (page === "home") {

        document
            .getElementById("navHome")
            .classList.add("active");

    }

    if (page === "telegram") {

        document
            .getElementById("navTelegram")
            .classList.add("active");

    }

    if (page === "orders") {

        document
            .getElementById("navOrders")
            .classList.add("active");

        loadOrders();

    }

    if (page === "profile") {

        document
            .getElementById("navProfile")
            .classList.add("active");

        loadOrders();

    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// =========================================================
// TELEGRAM STARS
// =========================================================

function openStars() {

    showModal(`
        <div style="text-align:center;padding:20px 0">

            <div style="font-size:55px">
                ⭐
            </div>

            <h2 style="margin-top:10px">
                Telegram Stars
            </h2>

            <p style="
                color:#8c95a8;
                font-size:13px;
                line-height:1.5;
                margin-top:10px;
            ">
                Telegram Stars raqamli xizmatlar
                uchun ishlatiladigan virtual birlik.
            </p>

            <button
                class="buy-button"
                onclick="closeModal()"
            >
                Tushunarli
            </button>

        </div>
    `);
}


// =========================================================
// PREMIUM
// =========================================================

function openPremium() {

    showModal(`
        <div style="text-align:center;padding:20px 0">

            <div style="font-size:55px">
                💎
            </div>

            <h2 style="margin-top:10px">
                Telegram Premium
            </h2>

            <p style="
                color:#8c95a8;
                font-size:13px;
                line-height:1.5;
                margin-top:10px;
            ">
                Premium uchun haqiqiy sotib olish
                tizimi keyingi bosqichda ulanadi.
            </p>

            <button
                class="buy-button"
                onclick="closeModal()"
            >
                Tushunarli
            </button>

        </div>
    `);
}


// =========================================================
// MODAL
// =========================================================

function showModal(html) {

    document
        .getElementById("modalContent")
        .innerHTML = html;

    document
        .getElementById("gameModal")
        .classList.remove("hidden");
}


function closeModal() {

    document
        .getElementById("gameModal")
        .classList.add("hidden");
}


// =========================================================
// ALERT
// =========================================================

function showAlert(message) {

    if (tg.showAlert) {

        tg.showAlert(message);

    } else {

        alert(message);

    }
}


// =========================================================
// HELP
// =========================================================

function showHelp() {

    showAlert(
        "DonatUZ yordam xizmati tez orada ishga tushadi."
    );
}


// =========================================================
// MONEY
// =========================================================

function formatMoney(number) {

    return Number(number)
        .toLocaleString("uz-UZ");

}
