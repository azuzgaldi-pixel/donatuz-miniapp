// =========================================================
// TELEGRAM
// =========================================================

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


// =========================================================
// USER
// =========================================================

const telegramUser = tg.initDataUnsafe?.user || {};

const USER_ID = telegramUser.id || 0;
const USERNAME = telegramUser.username || "";
const FIRST_NAME = telegramUser.first_name || "User";


// Avatar

const avatarElement =
    document.getElementById("userAvatar");

if (telegramUser.photo_url) {

    avatarElement.innerHTML = `
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

} else {

    avatarElement.textContent =
        FIRST_NAME
            .charAt(0)
            .toUpperCase();

}


// =========================================================
// ELEMENTLAR
// =========================================================

const gamesGrid =
    document.getElementById("gamesGrid");

const telegramGrid =
    document.getElementById("telegramGrid");

const searchInput =
    document.getElementById("searchInput");

const gamesSection =
    document.getElementById("gamesSection");

const telegramSection =
    document.getElementById("telegramSection");

const modal =
    document.getElementById("modal");

const closeModal =
    document.getElementById("closeModal");

const modalTitle =
    document.getElementById("modalTitle");

const modalDescription =
    document.getElementById("modalDescription");

const modalIcon =
    document.getElementById("modalIcon");

const playerId =
    document.getElementById("playerId");

const priceList =
    document.getElementById("priceList");

const orderButton =
    document.getElementById("orderButton");

const loading =
    document.getElementById("loading");


// =========================================================
// DATA
// =========================================================

let games = [];
let products = [];

let selectedGame = null;
let selectedProduct = null;
let selectedPrice = null;


// =========================================================
// ICON CACHE
// =========================================================

const iconCache = {};


// =========================================================
// APP STORE'DAN IKONKA QIDIRISH
// =========================================================

async function getGameIcon(searchName) {

    if (iconCache[searchName]) {
        return iconCache[searchName];
    }

    try {

        const url =
            "https://itunes.apple.com/search?term=" +
            encodeURIComponent(searchName) +
            "&entity=software&limit=10&country=US";

        const response =
            await fetch(url);

        const data =
            await response.json();

        if (
            data.results &&
            data.results.length > 0
        ) {

            // Eng mos natijani topishga harakat qilamiz

            const searchLower =
                searchName.toLowerCase();

            let result =
                data.results.find(item =>
                    (
                        item.trackName ||
                        ""
                    )
                    .toLowerCase()
                    .includes(searchLower)
                );

            // Agar aniq topilmasa birinchi natija

            if (!result) {
                result = data.results[0];
            }

            let icon =
                result.artworkUrl512 ||
                result.artworkUrl100 ||
                result.artworkUrl60;

            if (icon) {

                // 100x100 bo'lsa katta versiyasini olish

                icon = icon
                    .replace(
                        "100x100",
                        "512x512"
                    )
                    .replace(
                        "100x100bb",
                        "512x512bb"
                    );

                iconCache[searchName] =
                    icon;

                return icon;
            }
        }

    } catch (error) {

        console.log(
            "Icon loading error:",
            error
        );
    }

    return null;
}


// =========================================================
// O'YINLARNI YUKLASH
// =========================================================

async function loadGames() {

    try {

        const response =
            await fetch("/api/games");

        games =
            await response.json();

        renderGames(games);

    } catch (error) {

        console.error(error);

        gamesGrid.innerHTML = `
            <div style="
                grid-column:1/-1;
                text-align:center;
                color:#8892a6;
                padding:30px;
            ">
                O'yinlarni yuklashda xatolik.
            </div>
        `;
    }
}


// =========================================================
// O'YINLARNI CHIQARISH
// =========================================================

function renderGames(list) {

    gamesGrid.innerHTML = "";

    list.forEach(game => {

        const card =
            document.createElement("div");

        card.className =
            "game-card";

        card.innerHTML = `

            <img
                class="game-icon"
                id="icon-${game.id}"
                src=""
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

        // Avtomatik ikonka

        loadIconForGame(game);
    });
}


// =========================================================
// IKONKANI INTERNETDAN OLISH
// =========================================================

async function loadIconForGame(game) {

    const img =
        document.getElementById(
            `icon-${game.id}`
        );

    if (!img) return;

    // vaqtinchalik loading

    img.src =
        createPlaceholder(game.name);

    const icon =
        await getGameIcon(
            game.icon_search
        );

    if (icon) {

        img.src = icon;

    } else {

        // ikonka topilmasa harf bilan

        img.src =
            createPlaceholder(
                game.name
            );
    }
}


// =========================================================
// PLACEHOLDER
// =========================================================

function createPlaceholder(name) {

    const letter =
        name
            .trim()
            .charAt(0)
            .toUpperCase();

    const svg = `
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="200"
            height="200"
        >
            <rect
                width="200"
                height="200"
                rx="35"
                fill="#26314a"
            />

            <text
                x="100"
                y="125"
                text-anchor="middle"
                font-size="90"
                fill="white"
                font-family="Arial"
                font-weight="bold"
            >
                ${letter}
            </text>
        </svg>
    `;

    return (
        "data:image/svg+xml;charset=UTF-8," +
        encodeURIComponent(svg)
    );
}


// =========================================================
// TELEGRAM MAHSULOTLARI
// =========================================================

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


// =========================================================
// TELEGRAM CARD
// =========================================================

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
            () => openTelegramProduct(product)
        );

        telegramGrid.appendChild(card);
    });
}


// =========================================================
// O'YIN OCHISH
// =========================================================

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

    modalIcon.innerHTML = `
        <img
            src="${createPlaceholder(game.name)}"
            style="
                width:65px;
                height:65px;
                border-radius:18px;
                object-fit:cover;
            "
        >
    `;

    // haqiqiy ikonka

    getGameIcon(
        game.icon_search
    ).then(icon => {

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

    playerId.value = "";

    priceList.innerHTML = `

        <div class="price-item selected">

            <div class="price-left">
                💎 Donat paketlari
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


// =========================================================
// TELEGRAM PRODUCT
// =========================================================

function openTelegramProduct(product) {

    selectedGame = null;

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

    playerId.value = "";

    playerId.style.display =
        "none";

    priceList.innerHTML = "";

    product.prices.forEach(price => {

        const item =
            document.createElement("div");

        item.className =
            "price-item";

        item.innerHTML = `

            <div class="price-left">
                ${price.amount}
                ${product.id === "stars"
                    ? "⭐ Stars"
                    : " oy"}
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
                    .forEach(el =>
                        el.classList.remove(
                            "selected"
                        )
                    );

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


// =========================================================
// MODALNI YOPISH
// =========================================================

closeModal.addEventListener(
    "click",
    () => {

        modal.classList.add(
            "hidden"
        );

        playerId.style.display =
            "block";
    }
);


modal.addEventListener(
    "click",
    event => {

        if (
            event.target === modal
        ) {

            modal.classList.add(
                "hidden"
            );

            playerId.style.display =
                "block";
        }
    }
);


// =========================================================
// BUYURTMA
// =========================================================

orderButton.addEventListener(
    "click",
    async () => {

        // O'yin

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
                "Hozircha bu bo'lim demo rejimida."
            );

            return;
        }


        // Telegram

        if (selectedProduct) {

            if (!selectedPrice) {

                tg.showAlert(
                    "Avval paketni tanlang."
                );

                return;
            }

            // Hozircha demo

            tg.showAlert(
                "To'lov tizimi keyingi bosqichda ulanadi."
            );

            return;
        }

    }
);


// =========================================================
// PUL FORMAT
// =========================================================

function formatMoney(number) {

    return Number(number)
        .toLocaleString("uz-UZ");
}


// =========================================================
// SEARCH
// =========================================================

searchInput.addEventListener(
    "input",
    () => {

        const query =
            searchInput.value
                .toLowerCase()
                .trim();

        const filtered =
            games.filter(game =>
                game.name
                    .toLowerCase()
                    .includes(query)
            );

        renderGames(filtered);
    }
);


// =========================================================
// CATEGORY
// =========================================================

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
                    .forEach(btn =>
                        btn.classList.remove(
                            "active"
                        )
                    );

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
                        "block";

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


// =========================================================
// START
// =========================================================

loadGames();
loadProducts();
