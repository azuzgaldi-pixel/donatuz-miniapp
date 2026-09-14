const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

let games = [];
let selectedGame = null;
let selectedPackage = null;


// =========================
// LOAD GAMES
// =========================

async function loadGames() {

    try {

        const response = await fetch("/api/games");

        games = await response.json();

        renderGames();

    } catch (error) {

        console.error(error);

        document.getElementById("games").innerHTML =
            "<p>O‘yinlarni yuklashda xatolik.</p>";
    }
}


// =========================
// RENDER GAMES
// =========================

function renderGames() {

    const container = document.getElementById("games");

    container.innerHTML = "";

    games.forEach(game => {

        const div = document.createElement("div");

        div.className = "game";

        div.innerHTML = `
            <div class="game-icon">${game.icon}</div>
            <div class="game-name">${game.name}</div>
        `;

        div.onclick = () => openGame(game.id);

        container.appendChild(div);
    });
}


// =========================
// OPEN GAME
// =========================

function openGame(id) {

    selectedGame = games.find(g => g.id === id);

    if (!selectedGame) return;

    selectedPackage = null;

    document.querySelector(".hero").classList.add("hidden");
    document.querySelector(".service-grid").classList.add("hidden");

    document.querySelector("h2").classList.add("hidden");

    document.getElementById("games").classList.add("hidden");

    document.getElementById("gamePage").classList.remove("hidden");

    document.getElementById("selectedGame").innerHTML = `
        <h1>${selectedGame.icon} ${selectedGame.name}</h1>
    `;

    document.getElementById("playerId").value = "";

    renderPackages();
}


// =========================
// PACKAGES
// =========================

function renderPackages() {

    const container = document.getElementById("packages");

    container.innerHTML = "";

    selectedGame.packages.forEach((pkg, index) => {

        const div = document.createElement("div");

        div.className = "package";

        div.innerHTML = `
            <div class="package-name">${pkg.name}</div>
            <div class="package-price">
                ${formatPrice(pkg.price)} UZS
            </div>
        `;

        div.onclick = () => {

            document.querySelectorAll(".package")
                .forEach(x => x.classList.remove("selected"));

            div.classList.add("selected");

            selectedPackage = pkg;
        };

        container.appendChild(div);
    });
}


// =========================
// CREATE ORDER
// =========================

async function createOrder() {

    const playerId =
        document.getElementById("playerId").value.trim();

    if (!playerId) {

        tg.showAlert("Player ID / UID ni kiriting!");

        return;
    }

    if (!selectedPackage) {

        tg.showAlert("Paketni tanlang!");

        return;
    }

    const userId =
        tg.initDataUnsafe?.user?.id || 0;

    try {

        const response = await fetch("/api/order", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                user_id: userId,

                service: "game",

                game: selectedGame.name,

                player_id: playerId,

                package: selectedPackage.name,

                price: selectedPackage.price

            })

        });

        const result = await response.json();

        if (result.success) {

            tg.showAlert(
                `Buyurtma #${result.order_id} qabul qilindi.`
            );

        }

    } catch (error) {

        tg.showAlert(
            "Xatolik yuz berdi. Qaytadan urinib ko‘ring."
        );

        console.error(error);
    }
}


// =========================
// SERVICES
// =========================

function openService(type) {

    document.querySelector(".hero").classList.add("hidden");
    document.querySelector(".service-grid").classList.add("hidden");
    document.querySelectorAll("h2").forEach(x => x.classList.add("hidden"));
    document.getElementById("games").classList.add("hidden");

    document.getElementById("servicePage").classList.remove("hidden");

    const content =
        document.getElementById("serviceContent");

    if (type === "stars") {

        content.innerHTML = `
            <div class="service-page-box">
                <h1>⭐ Telegram Stars</h1>

                <p>
                    Telegram Stars sotib olish bo‘limi.
                </p>

                <p>
                    To‘lov tizimi keyingi bosqichda
                    ulanadi.
                </p>
            </div>
        `;

    }

    if (type === "premium") {

        content.innerHTML = `
            <div class="service-page-box">
                <h1>💎 Telegram Premium</h1>

                <p>
                    Telegram Premium sotib olish bo‘limi.
                </p>

                <p>
                    To‘lov tizimi keyingi bosqichda
                    ulanadi.
                </p>
            </div>
        `;
    }
}


// =========================
// CLOSE GAME
// =========================

function closeGame() {

    document.getElementById("gamePage").classList.add("hidden");

    document.querySelector(".hero").classList.remove("hidden");
    document.querySelector(".service-grid").classList.remove("hidden");

    document.querySelectorAll("h2")
        .forEach(x => x.classList.remove("hidden"));

    document.getElementById("games").classList.remove("hidden");
}


// =========================
// CLOSE SERVICE
// =========================

function closeService() {

    document.getElementById("servicePage").classList.add("hidden");

    document.querySelector(".hero").classList.remove("hidden");
    document.querySelector(".service-grid").classList.remove("hidden");

    document.querySelectorAll("h2")
        .forEach(x => x.classList.remove("hidden"));

    document.getElementById("games").classList.remove("hidden");
}


// =========================
// PRICE
// =========================

function formatPrice(price) {

    return new Intl.NumberFormat("uz-UZ")
        .format(price);
}


loadGames();
