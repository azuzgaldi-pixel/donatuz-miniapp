// ======================================================
// DONATUZ MINI APP
// AUTO GAME ICON SYSTEM
// ======================================================

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


// ======================================================
// TELEGRAM USER
// ======================================================

const telegramUser = tg.initDataUnsafe?.user || {};

const USER_ID = telegramUser.id || 0;
const USERNAME = telegramUser.username || "";
const FIRST_NAME = telegramUser.first_name || "User";


// ======================================================
// ELEMENTS
// ======================================================

const gamesGrid = document.getElementById("gamesGrid");
const telegramGrid = document.getElementById("telegramGrid");

const searchInput = document.getElementById("searchInput");

const gamesSection = document.getElementById("gamesSection");
const telegramSection = document.getElementById("telegramSection");

const modal = document.getElementById("modal");
const closeModal = document.getElementById("closeModal");

const modalIcon = document.getElementById("modalIcon");
const modalTitle = document.getElementById("modalTitle");
const modalDescription = document.getElementById("modalDescription");

const playerId = document.getElementById("playerId");
const priceList = document.getElementById("priceList");
const orderButton = document.getElementById("orderButton");


// ======================================================
// DATA
// ======================================================

let games = [];
let products = [];

let selectedGame = null;
let selectedProduct = null;
let selectedPrice = null;


// ======================================================
// ICON CACHE
// ======================================================

const iconCache = {};


// ======================================================
// GAME ICON SEARCH NAMES
// ======================================================

const ICON_NAMES = {

    "pubg":
        "PUBG MOBILE",

    "freefire":
        "Free Fire",

    "mlbb":
        "Mobile Legends: Bang Bang",

    "brawlstars":
        "Brawl Stars",

    "roblox":
        "Roblox",

    "coc":
        "Clash of Clans",

    "cr":
        "Clash Royale",

    "standoff2":
        "Standoff 2",

    "codm":
        "Call of Duty Mobile",

    "fcmobile":
        "EA SPORTS FC Mobile",

    "efootball":
        "eFootball",

    "genshin":
        "Genshin Impact",

    "hsr":
        "Honkai: Star Rail",

    "valorant":
        "VALORANT",

    "lol":
        "League of Legends",

    "fortnite":
        "Fortnite",

    "minecraft":
        "Minecraft",

    "arena":
        "Arena Breakout",

    "deltaforce":
        "Delta Force",

    "steam":
        "Steam"

};


// ======================================================
// FALLBACK ICONS
// ======================================================

const FALLBACK_ICONS = {

    "pubg": "🎯",
    "freefire": "🔥",
    "mlbb": "⚔️",
    "brawlstars": "⭐",
    "roblox": "🟥",
    "coc": "🏰",
    "cr": "👑",
    "standoff2": "🔫",
    "codm": "🎖️",
    "fcmobile": "⚽",
    "efootball": "⚽",
    "genshin": "🌟",
    "hsr": "🚂",
    "valorant": "🎯",
    "lol": "⚔️",
    "fortnite": "🛡️",
    "minecraft": "⛏️",
    "arena": "🎯",
    "deltaforce": "🎖️",
    "steam": "🎮"

};


// ======================================================
// PLACEHOLDER
// ======================================================

function makePlaceholder(game) {

    const emoji =
        FALLBACK_ICONS[game.id] || "🎮";

    const svg = `
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="512"
        height="512"
    >

        <defs>

            <linearGradient
                id="bg"
                x1="0%"
                y1="0%"
                x2="100%"
                y2="100%"
            >

                <stop
                    offset="0%"
                    stop-color="#263d85"
                />

                <stop
                    offset="100%"
                    stop-color="#111827"
                />

            </linearGradient>

        </defs>

        <rect
            width="512"
            height="512"
            rx="100"
            fill="url(#bg)"
        />

        <text
            x="256"
            y="320"
            text-anchor="middle"
            font-size="190"
        >
            ${emoji}
        </text>

    </svg>
    `;

    return (
        "data:image/svg+xml;charset=UTF-8," +
        encodeURIComponent(svg)
    );
}


// ======================================================
// GET ICON FROM APP STORE
// ======================================================

async function getIcon(game) {

    if (iconCache[game.id]) {
        return iconCache[game.id];
    }

    const searchName =
        ICON_NAMES[game.id] ||
        game.name;

    try {

        const url =
            "https://itunes.apple.com/search" +
            "?term=" +
            encodeURIComponent(searchName) +
            "&entity=software" +
            "&limit=10" +
            "&country=US";

        const response =
            await fetch(url, {
                method: "GET"
            });

        if (!response.ok) {
            throw new Error("Icon API error");
        }

        const data =
            await response.json();

        if (
            !data.results ||
            data.results.length === 0
        ) {

            return null;
        }


        // ------------------------------------------------
        // ENG MOS NATIJANI QIDIRISH
        // ------------------------------------------------

        const wanted =
            searchName
                .toLowerCase()
                .replace(/[^a-z0-9]/g, "");


        let result =
            data.results.find(item => {

                const title =
                    (
                        item.trackName ||
                        ""
                    )
                    .toLowerCase()
                    .replace(
                        /[^a-z0-9]/g,
                        ""
                    );

                return (
                    title.includes(wanted) ||
                    wanted.includes(title)
                );

            });


        // topilmasa birinchi natija

        if (!result) {

            result =
                data.results[0];

        }


        let icon =
            result.artworkUrl512 ||
            result.artworkUrl100 ||
            result.artworkUrl60;


        if (!icon) {
            return null;
        }


        // katta rasmga o'tkazish

        icon =
            icon
                .replace(
                    "100x100",
                    "512x512"
                )
                .replace(
                    "100x100bb",
                    "512x512bb"
                )
                .replace(
                    "60x60",
                    "512x512"
                );


        iconCache[game.id] =
            icon;

        return icon;

    } catch (error) {

        console.log(
            "ICON ERROR:",
            game.name,
            error
        );

        return null;
    }

}


// ======================================================
// LOAD ONE GAME ICON
// ======================================================

async function loadGameIcon(game) {

    const image =
        document.getElementById(
            "game-icon-" + game.id
        );

    if (!image) {
        return;
    }


    // Avval chiroyli placeholder

    image.src =
        makePlaceholder(game);


    // Internetdan haqiqiy icon

    const icon =
        await getIcon(game);


    if (icon) {

        image.src =
            icon;

    }

}


// ======================================================
// LOAD GAMES
// ======================================================

async function loadGames() {

    try {

        const response =
            await fetch("/api/games");

        if (!response.ok) {
            throw new Error(
                "Games API error"
            );
        }

        games =
            await response.json();


        renderGames(games);

    } catch (error) {

        console.error(error);

        gamesGrid.innerHTML = `
            <div
                style="
                    grid-column:1/-1;
                    text-align:center;
                    padding:30px;
                    color:#8c96aa;
                "
            >
                O'yinlarni yuklashda xatolik.
            </div>
        `;

    }

}


// ======================================================
// RENDER GAMES
// ======================================================

function renderGames(list) {

    gamesGrid.innerHTML = "";


    if (!list.length) {

        gamesGrid.innerHTML = `
            <div
                style="
                    grid-column:1/-1;
                    text-align:center;
                    padding:30px;
                    color:#8c96aa;
                "
            >
                O'yin topilmadi.
            </div>
        `;

        return;
    }


    list.forEach(game => {

        const card =
            document.createElement("div");

        card.className =
            "game-card";


        card.innerHTML = `

            <img
                class="game-icon"
                id="game-icon-${game.id}"
                src="${makePlaceholder(game)}"
                alt="${game.name}"
            >

            <div>

                <div class="game-name">
                    ${game.name}
                </div>

                <div class="game-small">
                    Donat qilish
                </div>

            </div>

        `;


        gamesGrid.appendChild(card);


        card.addEventListener(
            "click",
            () => openGame(game)
        );


        // MUHIM:
        // Internetdan icon olamiz

        loadGameIcon(game);

    });

}


// ======================================================
// LOAD PRODUCTS
// ======================================================

async function loadProducts() {

    try {

        const response =
            await fetch("/api/products");

        products =
            await response.json();

        renderTelegram(products);

    } catch (error) {

        console.error(error);

    }

}


// ======================================================
// TELEGRAM PRODUCTS
// ======================================================

function renderTelegram(list) {

    telegramGrid.innerHTML = "";


    list.forEach(product => {

        const card =
            document.createElement("div");

        card.className =
            "telegram-card";


        card.innerHTML = `

            <div class="telegram-icon">
                ${product.icon}
            </div>

            <div class="telegram-info">

                <h3>
                    ${product.name}
                </h3>

                <p>
                    ${product.description}
                </p>

            </div>

        `;


        card.addEventListener(
            "click",
            () =>
                openTelegramProduct(product)
        );


        telegramGrid.appendChild(card);

    });

}


// ======================================================
// OPEN GAME
// ======================================================

function openGame(game) {

    selectedGame =
        game;

    selectedProduct =
        null;

    selectedPrice =
        null;


    modalTitle.textContent =
        game.name;


    modalDescription.textContent =
        "Player ID / UID raqamingizni kiriting";


    playerId.style.display =
        "block";


    modalIcon.innerHTML = `

        <img
            src="${makePlaceholder(game)}"
            style="
                width:65px;
                height:65px;
                border-radius:18px;
                object-fit:cover;
            "
        >

    `;


    // haqiqiy iconni modalga ham yuklaymiz

    getIcon(game).then(icon => {

        if (icon) {

            modalIcon.innerHTML = `

                <img
                    src="${icon}"
                    style="
                        width:65px;
                        height:65px;
                        border-radius:18px;
                        object-fit:cover;
                    "
                >

            `;

        }

    });


    playerId.value =
        "";


    priceList.innerHTML = `

        <div
            class="price-item selected"
        >

            <div class="price-left">
                💎 Donat paketi
            </div>

            <div class="price-right">
                Tez orada
            </div>

        </div>

    `;


    orderButton.textContent =
        "Buyurtma berish";


    modal.classList.remove(
        "hidden"
    );

}


// ======================================================
// OPEN TELEGRAM PRODUCT
// ======================================================

function openTelegramProduct(product) {

    selectedGame =
        null;

    selectedProduct =
        product;

    selectedPrice =
        null;


    modalTitle.textContent =
        product.name;


    modalDescription.textContent =
        product.description;


    modalIcon.innerHTML =
        product.icon;


    playerId.style.display =
        "none";


    priceList.innerHTML =
        "";


    product.prices.forEach(price => {

        const item =
            document.createElement("div");

        item.className =
            "price-item";


        const text =
            product.id === "stars"
                ? `${price.amount} ⭐ Stars`
                : `${price.amount} oy`;


        item.innerHTML = `

            <div class="price-left">
                ${text}
            </div>

            <div class="price-right">
                ${formatMoney(price.price)}
                so'm
            </div>

        `;


        item.addEventListener(
            "click",
            () => {

                document
                    .querySelectorAll(
                        ".price-item"
                    )
                    .forEach(el => {

                        el.classList.remove(
                            "selected"
                        );

                    });


                item.classList.add(
                    "selected"
                );


                selectedPrice =
                    price;

            }
        );


        priceList.appendChild(item);

    });


    orderButton.textContent =
        "Davom etish";


    modal.classList.remove(
        "hidden"
    );

}


// ======================================================
// CLOSE MODAL
// ======================================================

closeModal.addEventListener(
    "click",
    closeModalWindow
);


modal.addEventListener(
    "click",
    event => {

        if (
            event.target === modal
        ) {

            closeModalWindow();

        }

    }
);


function closeModalWindow() {

    modal.classList.add(
        "hidden"
    );

    playerId.style.display =
        "block";

}


// ======================================================
// ORDER
// ======================================================

orderButton.addEventListener(
    "click",
    async () => {


        // GAME

        if (selectedGame) {

            const uid =
                playerId.value.trim();


            if (!uid) {

                tg.showAlert(
                    "Player ID / UID ni kiriting."
                );

                return;

            }


            tg.showAlert(
                "Bu bo'lim hozircha demo rejimida."
            );


            return;

        }


        // TELEGRAM

        if (selectedProduct) {

            if (!selectedPrice) {

                tg.showAlert(
                    "Avval paketni tanlang."
                );

                return;

            }


            tg.showAlert(
                "To'lov tizimi keyingi bosqichda ulanadi."
            );

        }

    }
);


// ======================================================
// MONEY
// ======================================================

function formatMoney(number) {

    return Number(number)
        .toLocaleString("uz-UZ");

}


// ======================================================
// SEARCH
// ======================================================

searchInput.addEventListener(
    "input",
    () => {

        const query =
            searchInput.value
                .toLowerCase()
                .trim();


        const filtered =
            games.filter(game => {

                return game.name
                    .toLowerCase()
                    .includes(query);

            });


        renderGames(filtered);

    }
);


// ======================================================
// CATEGORY
// ======================================================

document
    .querySelectorAll(".category")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                document
                    .querySelectorAll(
                        ".category"
                    )
                    .forEach(btn => {

                        btn.classList.remove(
                            "active"
                        );

                    });


                button.classList.add(
                    "active"
                );


                const category =
                    button.dataset.category;


                if (
                    category === "games"
                ) {

                    gamesSection.style.display =
                        "block";

                    telegramSection.style.display =
                        "none";

                    searchInput.style.display =
                        "flex";

                } else {

                    gamesSection.style.display =
                        "none";

                    telegramSection.style.display =
                        "block";

                    searchInput.style.display =
                        "none";

                }

            }
        );

    });


// ======================================================
// START
// ======================================================

loadGames();
loadProducts();


// ======================================================
// DEBUG
// ======================================================

console.log(
    "DonatUZ Mini App started"
);

console.log(
    "Telegram User:",
    telegramUser
);
