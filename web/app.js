const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

let games = [];
let selectedGame = null;
let selectedPackage = null;


// =====================================================
// LOAD
// =====================================================

async function loadGames() {

    try {

        const response = await fetch("/api/games");

        if (!response.ok) {
            throw new Error("API error");
        }

        games = await response.json();

        renderGames();

    } catch (error) {

        console.error(error);

        document.getElementById("games").innerHTML = `
            <div class="loading">
                ❌ O‘yinlarni yuklab bo‘lmadi
            </div>
        `;
    }
}


// =====================================================
// GAMES
// =====================================================

function renderGames() {

    const container =
        document.getElementById("games");

    container.innerHTML = "";

    games.forEach(game => {

        const element =
            document.createElement("div");

        element.className = "game";

        element.innerHTML = `
            <div class="game-icon">
                ${game.icon}
            </div>

            <div class="game-name">
                ${game.name}
            </div>
        `;

        element.onclick = () =>
            openGame(game.id);

        container.appendChild(element);
    });
}


// =====================================================
// OPEN GAME
// =====================================================

function openGame(id) {

    selectedGame =
        games.find(game => game.id === id);

    if (!selectedGame) return;

    selectedPackage = null;

    document.getElementById("home")
        .classList.add("hidden");

    document.getElementById("gamePage")
        .classList.remove("hidden");

    document.getElementById("servicePage")
        .classList.add("hidden");

    document.getElementById("gameTitle").innerHTML = `
        <h1>
            ${selectedGame.icon}
            ${selectedGame.name}
        </h1>
    `;

    document.getElementById("playerId").value = "";

    renderPackages();
}


// =====================================================
// PACKAGES
// =====================================================

function renderPackages() {

    const container =
        document.getElementById("packages");

    container.innerHTML = "";

    selectedGame.packages.forEach(pkg => {

        const element =
            document.createElement("div");

        element.className = "package";

        element.innerHTML = `
            <div class="package-name">
                ${pkg.name}
            </div>

            <div class="package-price">
                ${formatPrice(pkg.price)} UZS
            </div>
        `;

        element.onclick = () => {

            document
                .querySelectorAll(".package")
                .forEach(item =>
                    item.classList.remove("selected")
                );

            element.classList.add("selected");

            selectedPackage = pkg;
        };

        container.appendChild(element);
    });
}


// =====================================================
// CREATE ORDER
// =====================================================

async function createOrder() {

    const playerId =
        document.getElementById("playerId")
            .value
            .trim();

    if (!playerId) {

        tg.showAlert(
            "Player ID / UID ni kiriting!"
        );

        return;
    }

    if (!selectedPackage) {

        tg.showAlert(
            "Avval paketni tanlang!"
        );

        return;
    }

    if (!tg.initData) {

        tg.showAlert(
            "Mini App Telegram ichidan ochilishi kerak."
        );

        return;
    }

    try {

        const response =
            await fetch("/api/order", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    initData: tg.initData,

                    service: "game",

                    game: selectedGame.name,

                    player_id: playerId,

                    package: selectedPackage.name,

                    price: selectedPackage.price

                })
            });

        const result =
            await response.json();

        if (!response.ok) {

            throw new Error(
                result.detail || "Xatolik"
            );
        }

        tg.showAlert(
            `✅ Buyurtma #${result.order_id} qabul qilindi!`
        );

        goHome();

    } catch (error) {

        console.error(error);

        tg.showAlert(
            "❌ Buyurtma yuborilmadi: " +
            error.message
        );
    }
}


// =====================================================
// SERVICES
// =====================================================

function openService(type) {

    document.getElementById("home")
        .classList.add("hidden");

    document.getElementById("gamePage")
        .classList.add("hidden");

    document.getElementById("servicePage")
        .classList.remove("hidden");

    const content =
        document.getElementById("serviceContent");

    if (type === "stars") {

        content.innerHTML = `
            <div class="service-box">

                <div class="big">⭐</div>

                <h1>
                    Telegram Stars
                </h1>

                <p>
                    Telegram Stars sotib olish
                    xizmati.
                </p>

                <p>
                    To‘lov va avtomatik yetkazib
                    berish moduli keyingi bosqichda
                    rasmiy tizim orqali ulanadi.
                </p>

            </div>
        `;
    }

    if (type === "premium") {

        content.innerHTML = `
            <div class="service-box">

                <div class="big">💎</div>

                <h1>
                    Telegram Premium
                </h1>

                <p>
                    Telegram Premium sotib olish
                    xizmati.
                </p>

                <p>
                    To‘lov va yetkazib berish moduli
                    keyingi bosqichda rasmiy tizim
                    orqali ulanadi.
                </p>

            </div>
        `;
    }
}


// =====================================================
// HOME
// =====================================================

function goHome() {

    document.getElementById("gamePage")
        .classList.add("hidden");

    document.getElementById("servicePage")
        .classList.add("hidden");

    document.getElementById("home")
        .classList.remove("hidden");
}


// =====================================================
// PRICE
// =====================================================

function formatPrice(price) {

    return new Intl.NumberFormat(
        "uz-UZ"
    ).format(price);
}


// =====================================================
// START
// =====================================================

loadGames();
