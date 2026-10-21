let api = null;
let currentLang = "ru";
let currentSettings = {};
let currentInstance = null;
let currentServer = null;
let consoleSince = 0;
let consoleInterval = null;
let debugSince = 0;
let debugInterval = null;
const shownToasts = new Set();

const T = {
    ru: {
        nav_settings:"Настройки", nav_instances:"Инстансы", nav_default:"Главная",
        nav_servers:"Серверы", nav_github:"Github", nav_import:"Импорт Millida",
        nav_prism:"Импорт Prism", nav_about:"О программе",
        welcome_title:"Welcome to Better Millida Launcher",
        changelogs:"Changelogs", thanks:"Special thanks",
        language:"Язык", theme:"Тема", nickname:"Никнейм",
        java_path:"Путь к Java (пусто = авто)", ram_gb:"ОЗУ клиента (ГБ)",
        save:"Сохранить", create:"Создать",
        create_instance:"Создать инстанс", instance_name:"Название",
        create_server:"Создать сервер",
        server_core:"Ядро", server_version:"Версия", server_ram:"RAM (ГБ)",
        server_port:"Порт", start_server:"Запустить", stop_server:"Остановить",
        play:"Играть", set_skin:"Сменить скин",
        back:"Назад", instance_settings:"Настройки инстанса",
        mods:"Моды", danger_zone:"Опасная зона",
        delete_instance:"Удалить", set_active:"Активный",
        download_install:"Скачать", install_local_jar:"Установить .jar",
        search:"Найти", modrinth_search_ph:"Поиск в Modrinth...",
        millida_things:"Enable millida things",
        voice_chat:"Enable voice chat",
        coming_soon:"Скоро будет...",
        import_desc:"Выберите папку Millida Launcher",
        prism_desc:"Выберите папку instances из Prism Launcher.",
        select_folder:"Выбрать",
        attention:"ВНИМАНИЕ", ok:"OK", saved:"Сохранено!",
        no_mods:"— моды не установлены —", no_instances:"— инстансов нет —",
        no_servers:"— серверов нет —",
        confirm_delete:"Удалить?",
        pirate_mode:"Пиратский режим (online-mode=false)",
        players:"Игроки", server_settings:"Настройки", share:"Шеринг",
        online_players:"Онлайн игроки",
        manage_player:"Управление игроком",
        give:"Выдать", op:"OP", deop:"DEOP", kick:"Kick", ban:"Ban",
        wl_add:"+WL", wl_remove:"-WL",
        set_gamemode:"Сменить режим", send:"Отправить",
        share_server:"Поделиться", start_share:"Начать шеринг",
        share_host:"Как хост",
        share_host_desc:"Нажмите — лаунчер откроет HTTP. Передайте IP друзьям.",
        share_join:"Подключиться к другу",
        share_join_desc:"Введите IP хоста.",
        connect:"Подключиться",
        delete_server:"Удалить сервер",
        nick_required:"Укажи никнейм в настройках!",
        game_running:"Игра уже запущена",
        need_install:"Сначала нажми «Скачать» — идут файлы игры",
        launching:"Запуск игры...",
        installing:"Установка...",
        /* --- v4.1 --- */
        things_lite:"Millida Things Lite — только патчи",
        things_patches:"Millida Things — патчи",
        white_ip_emulator:"Enable White IP Emulator (Grey IP Patch)",
        white_ip_hint:"Даёт друзьям твой белый IP, когда ты открываешь мир по сети — без ручного проброса.",
        port_emulator:"Enable Port Emulator",
        port_emu_hint:"Автоматически пробрасывает порт игры через UPnP, когда мир открыт по сети.",
        elyby_skins:"Ely.by Skin System (visual)",
        elyby_hint:"Показывает скин с Ely.by по твоему нику. Также работает в Millida Things.",
        load_elyby_skin:"Загрузить скин Ely.by",
        refresh:"Обновить",
        servers_path:"Серверы",
        default_server_path:"Путь серверов по умолчанию",
        default_server_path_hint:"Пусто = папка server_instances рядом с лаунчером. Меняется и у каждого сервера отдельно.",
        server_path:"Путь сервера",
        net_local:"Локальный IP",
        net_public:"Публичный IP",
        net_status:"Статус",
        net_on:"включено",
        net_off:"выключено",
        net_ports:"Порты игры",
        net_upnp:"UPnP",
        net_upnp_yes:"доступен",
        net_upnp_no:"не найден",
        net_addr:"Адрес для друзей",
        share_addr:"Адрес для друзей",
        path_saved:"Путь сохранён",
        elyby_ok:"Скин Ely.by загружен",
        elyby_fail:"Не удалось загрузить скин Ely.by",
        port_opened:"Порт мира открыт",
        select_folder_title:"Выберите папку",
        open_port:"Открыть порт",
        close_port:"Закрыть порт",
        network_patches:"Сетевые патчи",
        net_patch_on:"Порт проброшен",
        net_patch_off:"Проброс снят",
        /* --- GitHub --- */
        gh_stars:"Звёзды", gh_forks:"Форки", gh_issues:"Issues",
        gh_commits:"Коммиты", gh_releases:"Релизы", gh_commits_title:"Последние коммиты",
        gh_contributors:"Контрибьюторы", gh_files:"Файлы репозитория",
        gh_languages:"Языки", gh_readme:"README",
        gh_open_repo:"Открыть репозиторий", gh_check_update:"Проверить обновления",
        gh_loading:"Загружаю данные с GitHub...", gh_updated:"Данные обновлены",
        gh_error:"Не удалось загрузить данные с GitHub", gh_no_desc:"Описание не указано",
        gh_no_releases:"Релизов пока нет", gh_no_commits:"Коммитов пока нет",
        gh_no_contributors:"Контрибьюторов пока нет", gh_no_files:"Файлов пока нет",
        gh_no_languages:"Информация о языках недоступна", gh_no_readme:"README не найден",
        gh_update_found:"Доступна новая версия", gh_update_none:"Установлена актуальная версия",
        gh_update_title:"Обновление",
        download:"Скачать",
        gh_rate_limited:"GitHub API: превышен лимит запросов (60/час). Показываю кэш. Токен можно положить в data/github_token.txt"
    },
    en: {
        nav_settings:"Settings", nav_instances:"Instances", nav_default:"Home",
        nav_servers:"Servers", nav_github:"Github", nav_import:"Import Millida",
        nav_prism:"Import Prism", nav_about:"About",
        welcome_title:"Welcome to Better Millida Launcher",
        changelogs:"Changelogs", thanks:"Special thanks",
        language:"Language", theme:"Theme", nickname:"Nickname",
        java_path:"Java path (empty = auto)", ram_gb:"Client RAM (GB)",
        save:"Save", create:"Create",
        create_instance:"Create instance", instance_name:"Name",
        create_server:"Create server",
        server_core:"Core", server_version:"Version", server_ram:"RAM (GB)",
        server_port:"Port", start_server:"Start", stop_server:"Stop",
        play:"Play", set_skin:"Change skin",
        back:"Back", instance_settings:"Instance settings",
        mods:"Mods", danger_zone:"Danger zone",
        delete_instance:"Delete", set_active:"Set active",
        download_install:"Download", install_local_jar:"Install .jar",
        search:"Search", modrinth_search_ph:"Search Modrinth...",
        millida_things:"Enable millida things",
        voice_chat:"Enable voice chat",
        coming_soon:"Coming soon...",
        import_desc:"Select Millida Launcher folder",
        prism_desc:"Select the instances folder from Prism Launcher.",
        select_folder:"Select",
        attention:"ATTENTION", ok:"OK", saved:"Saved!",
        no_mods:"— no mods —", no_instances:"— no instances —",
        no_servers:"— no servers —",
        confirm_delete:"Delete?",
        pirate_mode:"Pirate mode (online-mode=false)",
        players:"Players", server_settings:"Settings", share:"Share",
        online_players:"Online players",
        manage_player:"Manage player",
        give:"Give", op:"OP", deop:"DEOP", kick:"Kick", ban:"Ban",
        wl_add:"+WL", wl_remove:"-WL",
        set_gamemode:"Set gamemode", send:"Send",
        share_server:"Share", start_share:"Start sharing",
        share_host:"As host",
        share_host_desc:"Opens HTTP endpoint. Give IP to friends.",
        share_join:"Join a friend",
        share_join_desc:"Enter host IP.",
        connect:"Connect",
        delete_server:"Delete server",
        nick_required:"Set your nickname in settings!",
        game_running:"The game is already running",
        need_install:"Press «Download» first — fetching game files",
        launching:"Launching the game...",
        installing:"Installing...",
        /* --- v4.1 --- */
        things_lite:"Millida Things Lite — patches only",
        things_patches:"Millida Things — patches",
        white_ip_emulator:"Enable White IP Emulator (Grey IP Patch)",
        white_ip_hint:"Gives your friends your public IP when you open a world to LAN — no manual port forwarding.",
        port_emulator:"Enable Port Emulator",
        port_emu_hint:"Automatically forwards the game port via UPnP when a world is opened to LAN.",
        elyby_skins:"Ely.by Skin System (visual)",
        elyby_hint:"Shows your Ely.by skin by nickname. Also works in Millida Things.",
        load_elyby_skin:"Load Ely.by skin",
        refresh:"Refresh",
        servers_path:"Servers",
        default_server_path:"Default servers path",
        default_server_path_hint:"Empty = server_instances next to the launcher. Can also be changed per server.",
        server_path:"Server path",
        net_local:"Local IP",
        net_public:"Public IP",
        net_status:"Status",
        net_on:"enabled",
        net_off:"disabled",
        net_ports:"Game ports",
        net_upnp:"UPnP",
        net_upnp_yes:"available",
        net_upnp_no:"not found",
        net_addr:"Address for friends",
        share_addr:"Address for friends",
        path_saved:"Path saved",
        elyby_ok:"Ely.by skin loaded",
        elyby_fail:"Failed to load Ely.by skin",
        port_opened:"LAN port opened",
        select_folder_title:"Select folder",
        open_port:"Open port",
        close_port:"Close port",
        network_patches:"Network patches",
        net_patch_on:"Port forwarded",
        net_patch_off:"Forwarding removed",
        /* --- GitHub --- */
        gh_stars:"Stars", gh_forks:"Forks", gh_issues:"Issues",
        gh_commits:"Commits", gh_releases:"Releases", gh_commits_title:"Latest commits",
        gh_contributors:"Contributors", gh_files:"Repository files",
        gh_languages:"Languages", gh_readme:"README",
        gh_open_repo:"Open repository", gh_check_update:"Check for updates",
        gh_loading:"Loading data from GitHub...", gh_updated:"Data updated",
        gh_error:"Failed to load data from GitHub", gh_no_desc:"No description",
        gh_no_releases:"No releases yet", gh_no_commits:"No commits yet",
        gh_no_contributors:"No contributors yet", gh_no_files:"No files yet",
        gh_no_languages:"Language info unavailable", gh_no_readme:"README not found",
        gh_update_found:"New version available", gh_update_none:"You have the latest version",
        gh_update_title:"Update",
        download:"Download",
        gh_rate_limited:"GitHub API rate limit reached (60/hour). Showing cache. Put a token in data/github_token.txt"
    }
};

const CHANGELOGS = {
    ru:"v4.1\n- White IP Emulator (Grey IP Patch) и Port Emulator для миров по сети\n- Скин Стива по умолчанию, если своего скина нет\n- Ely.by Skin System (visual) в Millida Things\n- Millida Things Lite — только патчи\n- Свой путь серверов: по умолчанию и у каждого сервера\n- Больше анимаций и живых эффектов интерфейса\n\nv4.0\n- Рабочий запуск игры: полная установка ассетов, библиотек и нативов\n- Forge/NeoForge ставятся официальным установщиком\n- Умный подбор Java под версию Minecraft (автоскачивание)\n- Paper API v3, лог игры, стабильный шеринг и RCON",
    en:"v4.1\n- White IP Emulator (Grey IP Patch) and Port Emulator for LAN worlds\n- Steve skin as default when you have no custom skin\n- Ely.by Skin System (visual) in Millida Things\n- Millida Things Lite — patches only\n- Custom servers path: global default and per-server\n- More animations and lively UI effects\n\nv4.0\n- Working game launch: full install of assets, libraries and natives\n- Forge/NeoForge installed via official installer\n- Smart Java selection per Minecraft version (auto-download)\n- Paper API v3, game log, stable sharing and RCON"
};

const THANKS = "Neco - dev, design\nYou - for using!\nDeepseek - bug fixes";

const t = k => (T[currentLang] && T[currentLang][k]) || k;

function applyTranslations() {
    document.querySelectorAll("[data-i18n]").forEach(el => el.textContent = t(el.getAttribute("data-i18n")));
    document.querySelectorAll("[data-i18n-ph]").forEach(el => el.placeholder = t(el.getAttribute("data-i18n-ph")));
    document.getElementById("changelog-text").textContent = CHANGELOGS[currentLang] || CHANGELOGS.ru;
    document.getElementById("thanks-text").textContent = THANKS;
}

function switchTab(id) {
    document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
    const el = document.getElementById("tab-" + id);
    if (el) el.classList.add("active");
}

function closeModal() { document.getElementById("ram-modal").style.display = "none"; }
window.closeModal = closeModal;

function toast(level, title, msg, ttl = 8000) {
    const box = document.getElementById("toasts");
    const el = document.createElement("div");
    el.className = "toast " + level;
    el.innerHTML = `<div class="title">${title}</div><div class="msg">${msg}</div>`;
    // крестик для закрытия уведомления
    const x = document.createElement("button");
    x.className = "toast-close";
    x.textContent = "✕";
    x.title = "×";
    x.onclick = ev => { ev.stopPropagation(); dismissToast(el); };
    el.appendChild(x);
    box.appendChild(el);
    let timer = null;
    if (ttl > 0) timer = setTimeout(() => dismissToast(el), ttl);
    el.addEventListener("mouseenter", () => { if (timer) { clearTimeout(timer); timer = null; } });
    return el;
}
function dismissToast(el) {
    el.style.animation = "toast-out .3s forwards";
    setTimeout(() => el.remove(), 300);
}

/* ---------- вкладка GitHub ---------- */
let ghLoaded = false;
let ghData = null;

function fmtDate(iso) {
    if (!iso) return "";
    try {
        const d = new Date(iso);
        if (isNaN(d)) return iso;
        return d.toLocaleDateString(currentLang === "ru" ? "ru-RU" : "en-US",
            { year: "numeric", month: "short", day: "numeric" });
    } catch (e) { return iso; }
}
function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function loadGithub(force) {
    const st = document.getElementById("gh-status");
    if (!api) return;
    if (ghLoaded && !force) return;
    st.textContent = t("gh_loading");
    st.style.color = "var(--text)";
    let info;
    try {
        info = await api.get_github_info(!!force);
    } catch (e) {
        st.textContent = String(e);
        st.style.color = "#ff5555";
        return;
    }
    ghData = info;
    ghLoaded = true;
    if (!info || !info.ok) {
        st.textContent = (info && info.error) || t("gh_error");
        st.style.color = "#ff5555";
        return;
    }
    st.textContent = info.rate_limited ? t("gh_rate_limited") : t("gh_updated");
    st.style.color = info.rate_limited ? "#fbbf24" : "#4ade80";

    // шапка
    document.getElementById("gh-name").textContent = info.name || info.repo;
    document.getElementById("gh-name").href = info.url || "#";
    document.getElementById("gh-desc").textContent = info.description || t("gh_no_desc");
    document.getElementById("gh-version").textContent = "v" + (info.app_version || "1.0");
    document.getElementById("gh-branch").textContent = "⎇ " + (info.default_branch || "main");
    document.getElementById("gh-license").textContent = info.license || "—";
    document.getElementById("gh-language").textContent = info.language || "—";
    document.getElementById("gh-stars").textContent = info.stars ?? 0;
    document.getElementById("gh-forks").textContent = info.forks ?? 0;
    document.getElementById("gh-issues").textContent = info.open_issues ?? 0;
    document.getElementById("gh-commits").textContent = (info.commits || []).length;

    const av = document.getElementById("gh-avatar");
    if (info.contributors && info.contributors.length) {
        av.src = info.contributors[0].avatar;
        av.style.display = "block";
    }

    // релизы
    const relBox = document.getElementById("gh-releases");
    if (info.releases && info.releases.length) {
        relBox.innerHTML = info.releases.map(r => `
            <div class="gh-item">
                <div class="gh-ico">🏷</div>
                <div class="gh-main">
                    <div class="gh-t">
                        <span class="gh-tag ${r.prerelease ? "gh-prerelease" : ""}">${esc(r.tag)}</span>
                        ${esc(r.name && r.name !== r.tag ? r.name : "")}
                    </div>
                    <div class="gh-s">${r.published_at ? fmtDate(r.published_at) : ""}
                        ${r.assets && r.assets.length ? "• " + r.assets.length + " 📎" : ""}</div>
                </div>
                <a class="action-btn ghost small" href="${esc(r.url)}" target="_blank">↗</a>
            </div>`).join("");
    } else relBox.innerHTML = `<div class="gh-item"><div class="gh-ico">📦</div>
        <div class="gh-main"><div class="gh-t">${t("gh_no_releases")}</div></div></div>`;

    // коммиты
    const cmBox = document.getElementById("gh-commits");
    if (info.commits && info.commits.length) {
        cmBox.innerHTML = info.commits.map(c => `
            <div class="gh-item">
                <div class="gh-ico">📝</div>
                <div class="gh-main">
                    <div class="gh-t">${esc(c.message)}</div>
                    <div class="gh-s">${esc(c.sha)} • ${esc(c.author)} • ${fmtDate(c.date)}</div>
                </div>
                <a class="action-btn ghost small" href="${esc(c.url)}" target="_blank">↗</a>
            </div>`).join("");
    } else cmBox.innerHTML = `<div class="gh-item"><div class="gh-ico">📝</div>
        <div class="gh-main"><div class="gh-t">${t("gh_no_commits")}</div></div></div>`;

    // контрибьюторы
    const ctBox = document.getElementById("gh-contributors");
    if (info.contributors && info.contributors.length) {
        ctBox.innerHTML = info.contributors.map(c => `
            <div class="gh-item">
                <img class="gh-ico" src="${esc(c.avatar)}" style="border-radius:50%">
                <div class="gh-main">
                    <div class="gh-t">${esc(c.login)}</div>
                    <div class="gh-s">${c.contributions} ${t("gh_commits")}</div>
                </div>
                <a class="action-btn ghost small" href="${esc(c.url)}" target="_blank">↗</a>
            </div>`).join("");
    } else ctBox.innerHTML = `<div class="gh-item"><div class="gh-ico">👤</div>
        <div class="gh-main"><div class="gh-t">${t("gh_no_contributors")}</div></div></div>`;

    // файлы
    const fBox = document.getElementById("gh-files");
    if (info.files && info.files.length) {
        fBox.innerHTML = info.files.map(f => `
            <div class="gh-item">
                <div class="gh-ico">${f.type === "dir" ? "📁" : "📄"}</div>
                <div class="gh-main">
                    <div class="gh-t">${esc(f.name)}</div>
                    <div class="gh-s">${f.type} • ${f.size} B</div>
                </div>
                <a class="action-btn ghost small" href="${esc(f.url)}" target="_blank">↗</a>
            </div>`).join("");
    } else fBox.innerHTML = `<div class="gh-item"><div class="gh-ico">📄</div>
        <div class="gh-main"><div class="gh-t">${t("gh_no_files")}</div></div></div>`;

    // языки
    const lBox = document.getElementById("gh-langs");
    if (info.languages && info.languages.length) {
        lBox.innerHTML = info.languages.map(l => `
            <div class="gh-lang">
                <span style="min-width:110px">${esc(l.name)}</span>
                <div class="gh-lang-bar"><div class="gh-lang-fill" style="width:${l.percent}%"></div></div>
                <span style="min-width:52px;text-align:right;opacity:.7">${l.percent}%</span>
            </div>`).join("");
    } else lBox.innerHTML = `<div class="hint">${t("gh_no_languages")}</div>`;

    // README
    document.getElementById("gh-readme").textContent = info.readme || t("gh_no_readme");

    // баннер обновления
    showUpdateBanner(info.update_available);
}

function showUpdateBanner(up) {
    const banner = document.getElementById("gh-update-banner");
    if (!banner || !up) return;
    if (up.available) {
        document.getElementById("gh-update-text").textContent =
            `${t("gh_update_found")}: ${up.current} → ${up.latest}`;
        banner.classList.remove("hidden");
    } else {
        banner.classList.add("hidden");
    }
}

async function checkUpdate(silent) {
    if (!api) return;
    try {
        const up = await api.check_for_update();
        if (up && up.available) {
            const banner = document.getElementById("gh-update-banner");
            if (banner) {
                document.getElementById("gh-update-text").textContent =
                    `${t("gh_update_found")}: ${up.current} → ${up.latest}`;
                banner.classList.remove("hidden");
            }
            if (!silent) toast("warn", t("gh_update_title"), `${t("gh_update_found")}: ${up.current} → ${up.latest}`, 12000);
            else toast("warn", t("gh_update_title"), `${t("gh_update_found")}: ${up.current} → ${up.latest}`, 12000);
        } else {
            if (!silent) toast("success", t("gh_update_title"), t("gh_update_none"));
        }
    } catch (e) {
        if (!silent) toast("error", t("gh_update_title"), String(e));
    }
}

/* ---------- прогресс установки/запуска ---------- */
let progressInterval = null;

function showProgress(label) {
    document.getElementById("progress-label").textContent = label;
    document.getElementById("progress-fill").style.width = "0%";
    document.getElementById("progress-detail").textContent = "";
    document.getElementById("progress-box").classList.remove("hidden");
    if (!progressInterval) progressInterval = setInterval(pollProgress, 700);
}
function hideProgress() {
    document.getElementById("progress-box").classList.add("hidden");
    if (progressInterval) { clearInterval(progressInterval); progressInterval = null; }
}
async function pollProgress() {
    if (!api) return;
    try {
        const p = await api.get_progress();
        if (!p || !p.active) { hideProgress(); return; }
        const pct = p.total > 0 ? Math.min(100, Math.round(p.done * 100 / p.total)) : 0;
        document.getElementById("progress-label").textContent = p.label || "...";
        document.getElementById("progress-fill").style.width = pct + "%";
        const det = p.detail || (p.total > 0 ? `${p.done}/${p.total}` : "");
        document.getElementById("progress-detail").textContent = det;
    } catch (e) {}
}

/* ---------- запуск игры с проверками ---------- */
async function playInstance(name, btnId) {
    if (!api) return;
    if (!name) return toast("warn", "!", t("no_instances"));
    const nick = (currentSettings.nickname || "").trim();
    if (!nick) {
        toast("warn", "!", t("nick_required"));
        switchTab("settings");
        return;
    }
    const btn = btnId ? document.getElementById(btnId) : null;
    if (btn) btn.disabled = true;
    showProgress(t("launching") || "Launch");
    try {
        const res = await api.launch_instance(name);
        toast(res.status === "error" ? "error" : "success", "Launch", res.message);
    } finally {
        if (btn) btn.disabled = false;
        setTimeout(hideProgress, 1200);
    }
}

async function pollDebug() {
    if (!api) return;
    try {
        const msgs = await api.get_debug(debugSince);
        for (const m of msgs) {
            debugSince = Math.max(debugSince, m.t);
            if (m.level === "ERROR") {
                const key = m.t.toFixed(3);
                if (shownToasts.has(key)) continue;
                shownToasts.add(key);
                toast("error", "Debugger — Error", m.msg, 12000);
            }
        }
    } catch (e) { console.error(e); }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btn-min").onclick = () => api && api.minimize_window();
    document.getElementById("btn-close").onclick = () => api && api.close_window();
    document.getElementById("btn-full").onclick = () => api && api.toggle_fullscreen();
    document.addEventListener("keydown", e => {
        if (e.key === "F11") { e.preventDefault(); api && api.toggle_fullscreen(); }
    });

    document.querySelectorAll(".sidebar button").forEach(btn => {
        btn.onclick = async () => {
            const tab = btn.dataset.tab;
            if (tab === "servers") await openServersTab();
            else switchTab(tab);
            if (tab === "instances") await refreshInstances();
            if (tab === "github") loadGithub(false);
        };
    });

    // --- вкладка GitHub ---
    document.getElementById("btn-gh-refresh").onclick = () => loadGithub(true);
    document.getElementById("btn-gh-check").onclick = () => checkUpdate(false);
    document.getElementById("btn-gh-open").onclick = () => api && api.open_github();
    document.getElementById("btn-gh-update").onclick = () => {
        const up = ghData && ghData.update_available;
        const url = (up && up.url) || (ghData && ghData.url);
        if (url) window.open(url, "_blank");
    };
    document.getElementById("btn-gh-update-dismiss").onclick = () => {
        document.getElementById("gh-update-banner").classList.add("hidden");
    };

    document.getElementById("btn-save-settings").onclick = async () => {
        if (!api) return;
        const payload = {
            language: document.getElementById("sel-lang").value,
            theme: document.getElementById("sel-theme").value,
            nickname: document.getElementById("inp-nick").value.trim(),
            java_path: document.getElementById("inp-java").value.trim() || "java",
            ram_gb: parseInt(document.getElementById("inp-ram-client").value) || 4,
            millida_things: document.getElementById("chk-things").checked,
            voice_chat: document.getElementById("chk-voice").checked,
            things_lite: document.getElementById("chk-things-lite").checked,
            white_ip_emulator: document.getElementById("chk-white-ip").checked,
            port_emulator: document.getElementById("chk-port-emu").checked,
            elyby_skins: document.getElementById("chk-elyby").checked,
            default_server_path: document.getElementById("inp-server-path").value.trim(),
        };
        const saved = await api.save_settings(payload);
        currentSettings = { ...currentSettings, ...payload };
        currentLang = payload.language;
        document.body.className = "theme-" + payload.theme;
        applyTranslations();
        if (saved && saved.skin_url) applySkin(saved.skin_url);
        refreshNetInfo();
        const st = document.getElementById("settings-status");
        st.textContent = t("saved"); st.style.color = "#4ade80";
        setTimeout(() => st.textContent = "", 2000);
    };

    document.getElementById("btn-play").onclick = () => playInstance(currentSettings.active_instance, "btn-play");
    document.getElementById("btn-set-skin").onclick = async () => {
        if (!api) return;
        const res = await api.set_skin();
        if (res.status === "success") applySkin(res.skin_url);
    };
    document.getElementById("btn-elyby").onclick = async () => {
        if (!api) return;
        const res = await api.get_elyby_skin();
        if (res.status === "success") {
            applySkin(res.skin_url);
            document.getElementById("chk-elyby").checked = true;
            toast("success", "Ely.by", res.message);
        } else {
            toast("warn", "Ely.by", res.message);
        }
        refreshNetInfo();
    };
    document.getElementById("btn-net-refresh").onclick = refreshNetInfo;
    document.getElementById("btn-srv-np-open").onclick = async () => {
        if (!api || !currentServer) return;
        const st = document.getElementById("share-status");
        st.textContent = "..."; st.style.color = "var(--text)";
        const res = await api.start_server_network_patch(currentServer);
        st.textContent = res.message || "";
        st.style.color = res.status === "success" ? "#4ade80" : "#fbbf24";
        if (res.status === "success") toast("success", t("network_patches"), res.message);
        else toast("warn", t("network_patches"), res.message);
    };
    document.getElementById("btn-srv-np-close").onclick = async () => {
        if (!api || !currentServer) return;
        const st = document.getElementById("share-status");
        const res = await api.stop_server_network_patch(currentServer);
        st.textContent = res.message || "";
        st.style.color = "var(--text)";
        toast("success", t("network_patches"), res.message);
    };
    document.getElementById("btn-server-path").onclick = async () => {
        if (!api) return;
        const p = await api.pick_folder(t("select_folder_title"));
        if (p) document.getElementById("inp-server-path").value = p;
    };
    document.getElementById("btn-srv-path").onclick = async () => {
        if (!api) return;
        const p = await api.pick_folder(t("select_folder_title"));
        if (p) document.getElementById("srv-path").value = p;
    };
    document.getElementById("net-info").addEventListener("click", e => {
        const a = e.target.closest(".addr");
        if (!a) return;
        const txt = a.dataset.addr || a.textContent;
        navigator.clipboard && navigator.clipboard.writeText(txt);
        toast("success", "Copy", txt);
    });

    document.getElementById("sel-inst-loader").onchange = loadInstVersions;
    document.getElementById("sel-inst-vtype").onchange = loadInstVersions;
    document.getElementById("btn-create-inst").onclick = async () => {
        if (!api) return;
        const name = document.getElementById("inp-inst-name").value.trim();
        const loader = document.getElementById("sel-inst-loader").value;
        const version = document.getElementById("sel-inst-version").value;
        const res = await api.create_instance(name, version, loader);
        if (res.status === "error") return toast("error","Create",res.message);
        document.getElementById("inp-inst-name").value = "";
        await refreshInstances();
        await refreshActiveLabel();
    };
    document.getElementById("btn-inst-back").onclick = async () => {
        currentInstance = null;
        switchTab("instances"); await refreshInstances();
    };
    document.getElementById("det-loader").onchange = () => loadDetailVersions();
    document.getElementById("det-vtype").onchange = () => loadDetailVersions();
    document.getElementById("btn-det-save").onclick = async () => {
        if (!api || !currentInstance) return;
        await api.update_instance(currentInstance,
            document.getElementById("det-version").value,
            document.getElementById("det-loader").value);
        await api.set_active_instance(currentInstance);
        await refreshActiveLabel();
        await openInstance(currentInstance);
    };
    document.getElementById("btn-det-install").onclick = async () => {
        if (!api || !currentInstance) return;
        const st = document.getElementById("det-status");
        st.textContent = "..."; st.style.color = "var(--text)";
        showProgress(t("installing"));
        let res;
        try {
            res = await api.install_instance(currentInstance);
        } finally {
            setTimeout(hideProgress, 800);
        }
        st.textContent = res.message;
        st.style.color = res.status === "error" ? "#ff5555" : "#4ade80";
        if (res.status === "error") toast("error","Install",res.message);
        await refreshInstances();
    };
    document.getElementById("btn-det-activate").onclick = async () => {
        if (!api || !currentInstance) return;
        await api.set_active_instance(currentInstance);
        await refreshActiveLabel(); await openInstance(currentInstance);
    };
    document.getElementById("btn-det-launch").onclick = () => playInstance(currentInstance, "btn-det-launch");
    document.getElementById("btn-det-install-mod").onclick = async () => {
        if (!api || !currentInstance) return;
        const res = await api.install_mod_local(currentInstance);
        if (res.status === "success") await openInstance(currentInstance);
    };
    document.getElementById("btn-det-delete").onclick = async () => {
        if (!api || !currentInstance) return;
        if (!confirm(t("confirm_delete"))) return;
        await api.delete_instance(currentInstance);
        currentInstance = null;
        await refreshActiveLabel();
        switchTab("instances"); await refreshInstances();
    };
    document.getElementById("btn-mod-search").onclick = searchModrinth;
    document.getElementById("inp-mod-search").addEventListener("keydown", e => {
        if (e.key === "Enter") searchModrinth();
    });

    document.getElementById("sel-srv-core").onchange = loadServerVersions;
    document.getElementById("btn-create-srv").onclick = async () => {
        if (!api) return;
        const name = document.getElementById("inp-srv-name").value.trim();
        const core = document.getElementById("sel-srv-core").value;
        const version = document.getElementById("sel-srv-version").value;
        const ram = parseInt(document.getElementById("inp-srv-ram").value) || 4;
        const port = parseInt(document.getElementById("inp-srv-port").value) || 25565;
        const pirate = document.getElementById("chk-srv-pirate").checked;
        const res = await api.create_server(name, core, version, ram, port, pirate);
        if (res.status === "error") return toast("error","Create",res.message);
        document.getElementById("inp-srv-name").value = "";
        await refreshServers();
    };
    document.getElementById("btn-srv-back").onclick = async () => {
        currentServer = null; stopConsolePolling();
        switchTab("servers"); await refreshServers();
    };
    document.getElementById("btn-srv-start").onclick = async () => {
        if (!api || !currentServer) return;
        const res = await api.start_server_card(currentServer);
        toast(res.status === "error" ? "error" : "success", "Server", res.message);
        startConsolePolling();
    };
    document.getElementById("btn-srv-stop").onclick = async () => {
        if (!api || !currentServer) return;
        const res = await api.stop_server_card(currentServer);
        toast(res.status === "error" ? "error" : "success", "Server", res.message);
    };
    document.getElementById("btn-srv-share").onclick = async () => {
        if (!api || !currentServer) return;
        const res = await api.start_sharing(currentServer);
        toast(res.status === "error" ? "error" : "success", "Share", res.message, 15000);
    };
    document.getElementById("btn-srv-delete").onclick = async () => {
        if (!api || !currentServer) return;
        if (!confirm(t("confirm_delete"))) return;
        await api.delete_server(currentServer);
        currentServer = null; stopConsolePolling();
        switchTab("servers"); await refreshServers();
    };

    document.querySelectorAll(".srv-tab").forEach(b => {
        b.onclick = () => {
            document.querySelectorAll(".srv-tab").forEach(x => x.classList.remove("active"));
            document.querySelectorAll(".srv-tab-content").forEach(x => x.classList.remove("active"));
            b.classList.add("active");
            document.getElementById("srv-tab-" + b.dataset.stab).classList.add("active");
        };
    });

    document.getElementById("btn-send-cmd").onclick = sendConsoleCmd;
    document.getElementById("console-cmd").addEventListener("keydown", e => {
        if (e.key === "Enter") sendConsoleCmd();
    });

    document.getElementById("btn-give").onclick = async () => {
        if (!api || !currentServer) return;
        const p = document.getElementById("inp-manage-nick").value.trim();
        const item = document.getElementById("inp-give-item").value.trim();
        const cnt = parseInt(document.getElementById("inp-give-count").value) || 1;
        if (!p || !item) return toast("warn","!","Укажи ник и предмет");
        const res = await api.give_item(currentServer, p, item, cnt);
        if (res.status === "error") toast("error","Give",res.message);
    };
    document.querySelectorAll("[data-player-cmd]").forEach(b => {
        b.onclick = async () => {
            if (!api || !currentServer) return;
            const p = document.getElementById("inp-manage-nick").value.trim();
            if (!p) return toast("warn","!","Укажи ник");
            const cmd = b.dataset.playerCmd;
            let res;
            if (cmd === "op") res = await api.op_player(currentServer, p);
            else if (cmd === "deop") res = await api.deop_player(currentServer, p);
            else if (cmd === "kick") res = await api.kick_player(currentServer, p);
            else if (cmd === "ban") res = await api.ban_player(currentServer, p);
            else if (cmd === "whitelist_add") res = await api.whitelist_add(currentServer, p);
            else if (cmd === "whitelist_remove") res = await api.whitelist_remove(currentServer, p);
            if (res && res.status === "error") toast("error", cmd, res.message);
            else toast("success", cmd, "OK");
        };
    });
    document.getElementById("btn-set-gm").onclick = async () => {
        if (!api || !currentServer) return;
        const p = document.getElementById("inp-manage-nick").value.trim();
        const mode = document.getElementById("sel-gamemode").value;
        if (!p) return toast("warn","!","Укажи ник");
        const res = await api.gamemode_player(currentServer, p, mode);
        if (res.status === "error") toast("error","Gamemode",res.message);
    };

    document.getElementById("btn-srv-save").onclick = async () => {
        if (!api || !currentServer) return;
        const payload = {
            pirate: document.getElementById("srv-pirate").checked,
            motd: document.getElementById("srv-motd").value,
            seed: document.getElementById("srv-seed").value,
            port: parseInt(document.getElementById("srv-port").value) || 25565,
            ram: parseInt(document.getElementById("srv-ram").value) || 4,
            rcon_enabled: document.getElementById("srv-rcon").checked,
            rcon_port: parseInt(document.getElementById("srv-rcon-port").value) || 25575,
            rcon_password: document.getElementById("srv-rcon-pass").value,
            custom_path: document.getElementById("srv-path").value.trim(),
        };
        const res = await api.update_server(currentServer, payload);
        const st = document.getElementById("srv-settings-status");
        st.textContent = res && res.status === "error" ? res.message : t("saved");
        st.style.color = res && res.status === "error" ? "#ff5555" : "#4ade80";
        setTimeout(() => st.textContent = "", 2600);
        if (!res || res.status !== "error") updateShareAddr();
    };

    document.getElementById("btn-start-share").onclick = async () => {
        if (!api || !currentServer) return;
        const res = await api.start_sharing(currentServer);
        const st = document.getElementById("share-status");
        st.textContent = res.message;
        st.style.color = res.status === "error" ? "#ff5555" : "#4ade80";
    };
    document.getElementById("btn-join-share").onclick = async () => {
        if (!api) return;
        const ip = document.getElementById("inp-share-ip").value.trim();
        if (!ip) return;
        const res = await api.join_shared_server(ip);
        const box = document.getElementById("share-info");
        if (res.status === "error") {
            box.innerHTML = `<p style="color:#ff5555">${res.message}</p>`;
            return;
        }
        const i = res.info;
        box.innerHTML = `
            <div class="panel">
                <h3>${i.motd || "Server"}</h3>
                <p>Host: <b>${i.host}:${i.port}</b></p>
                <p>Version: <b>${i.version}</b> (${i.core})</p>
                <p>Owner: <b>${i.nick}</b> ${i.bml ? "🏷 BML" : ""}</p>
            </div>`;
    };

    document.getElementById("btn-import").onclick = async () => {
        if (!api) return;
        const st = document.getElementById("import-status");
        st.textContent = "...";
        const res = await api.import_millida_data();
        st.textContent = res.message;
        st.style.color = res.status === "error" ? "#ff5555" : "#4ade80";
    };
    document.getElementById("btn-import-prism").onclick = async () => {
        if (!api) return;
        const st = document.getElementById("prism-status");
        const list = document.getElementById("prism-result");
        st.textContent = "..."; list.innerHTML = "";
        const res = await api.import_prism_data();
        st.textContent = res.message;
        st.style.color = res.status === "error" ? "#ff5555" : "#4ade80";
        if (res.status === "success" && res.imported) {
            for (const imp of res.imported) {
                const li = document.createElement("li");
                li.innerHTML = `<span>${imp.name}</span><span style="opacity:.7">${imp.files} files</span>`;
                list.appendChild(li);
            }
            await refreshInstances();
        }
    };
});

window.addEventListener("pywebviewready", async () => {
    api = window.pywebview.api;
    try { currentSettings = await api.get_settings(); } catch (e) {}
    currentLang = currentSettings.language || "ru";
    document.body.className = "theme-" + (currentSettings.theme || "purple");
    document.getElementById("sel-lang").value = currentLang;
    document.getElementById("sel-theme").value = currentSettings.theme || "purple";
    document.getElementById("inp-nick").value = currentSettings.nickname || "";
    document.getElementById("inp-java").value = currentSettings.java_path || "java";
    document.getElementById("inp-ram-client").value = currentSettings.ram_gb || 4;
    document.getElementById("chk-things").checked = !!currentSettings.millida_things;
    document.getElementById("chk-voice").checked = currentSettings.voice_chat !== false;
    document.getElementById("chk-things-lite").checked = !!currentSettings.things_lite;
    document.getElementById("chk-white-ip").checked = !!currentSettings.white_ip_emulator;
    document.getElementById("chk-port-emu").checked = !!currentSettings.port_emulator;
    document.getElementById("chk-elyby").checked = !!currentSettings.elyby_skins;
    document.getElementById("inp-server-path").value = currentSettings.default_server_path || "";

    applyTranslations();
    initFx();
    refreshNetInfo();
    await refreshActiveLabel();
    await loadInstVersions();
    await loadServerVersions();
    await updateHomeInfo();

    const skin = await api.get_skin_url();
    if (skin) applySkin(skin);

    // фоновая проверка обновлений на GitHub
    setTimeout(() => checkUpdate(true), 2500);

    debugInterval = setInterval(pollDebug, 1500);
});

async function loadInstVersions() {
    if (!api) return;
    const core = document.getElementById("sel-inst-loader").value;
    const vtype = document.getElementById("sel-inst-vtype").value;
    const sel = document.getElementById("sel-inst-version");
    sel.innerHTML = "<option>...</option>";
    const res = await api.fetch_versions(core, vtype);
    sel.innerHTML = "";
    (res.versions || ["1.20.1"]).forEach(v => {
        const o = document.createElement("option"); o.value = v; o.textContent = v;
        sel.appendChild(o);
    });
}
async function loadServerVersions() {
    if (!api) return;
    const core = document.getElementById("sel-srv-core").value;
    const sel = document.getElementById("sel-srv-version");
    sel.innerHTML = "<option>...</option>";
    const res = await api.fetch_versions(core, "release");
    sel.innerHTML = "";
    (res.versions || ["1.20.1"]).forEach(v => {
        const o = document.createElement("option"); o.value = v; o.textContent = v;
        sel.appendChild(o);
    });
}
async function loadDetailVersions() {
    if (!api) return;
    const core = document.getElementById("det-loader").value;
    const vtype = document.getElementById("det-vtype").value;
    const sel = document.getElementById("det-version");
    sel.innerHTML = "<option>...</option>";
    const res = await api.fetch_versions(core, vtype);
    sel.innerHTML = "";
    (res.versions || ["1.20.1"]).forEach(v => {
        const o = document.createElement("option"); o.value = v; o.textContent = v;
        sel.appendChild(o);
    });
}

async function refreshInstances() {
    if (!api) return;
    const arr = await api.list_instances();
    const grid = document.getElementById("inst-list");
    grid.innerHTML = "";
    if (!arr.length) { grid.innerHTML = `<div style="opacity:.6">${t("no_instances")}</div>`; return; }
    for (const it of arr) {
        const card = document.createElement("div");
        card.className = "instance-card" + (it.name === currentSettings.active_instance ? " active" : "");
        card.innerHTML = `
            <div class="name">${it.name}</div>
            <div class="meta">${it.loader} • ${it.version}</div>
            <div class="meta">mods: ${it.mods_count}</div>
            <div class="meta">${it.installed ? "✓" : "⚠"}</div>`;
        card.onclick = () => openInstance(it.name);
        grid.appendChild(card);
    }
}
async function openInstance(name) {
    if (!api) return;
    const res = await api.get_instance(name);
    if (res.status === "error") return toast("error","Instance",res.message);
    currentInstance = name;
    const inst = res.instance;
    document.getElementById("det-name").textContent = name;
    document.getElementById("det-loader").value = inst.loader || "vanilla";
    await loadDetailVersions();
    document.getElementById("det-version").value = inst.version;
    renderMods(inst.mods || []);
    switchTab("instance-detail");
}
function renderMods(mods) {
    const ul = document.getElementById("det-mods");
    ul.innerHTML = "";
    if (!mods.length) { ul.innerHTML = `<li style="justify-content:center;opacity:.6">${t("no_mods")}</li>`; return; }
    mods.forEach(m => {
        const li = document.createElement("li");
        li.innerHTML = `<span>${m}</span>`;
        const b = document.createElement("button");
        b.textContent = "✕";
        b.onclick = async () => { await api.delete_mod(currentInstance, m); await openInstance(currentInstance); };
        li.appendChild(b); ul.appendChild(li);
    });
}
async function refreshActiveLabel() {
    if (!api) return;
    currentSettings = await api.get_settings();
    document.getElementById("active-inst-label").textContent = currentSettings.active_instance || "—";
}

async function searchModrinth() {
    if (!api || !currentInstance) return;
    const q = document.getElementById("inp-mod-search").value.trim();
    if (!q) return;
    const box = document.getElementById("modrinth-results");
    box.innerHTML = "<div style='opacity:.6'>searching...</div>";
    const res = await api.modrinth_search(q);
    box.innerHTML = "";
    if (res.status === "error") { box.innerHTML = `<div style='color:#ff5555'>${res.message}</div>`; return; }
    if (!res.hits.length) { box.innerHTML = "<div style='opacity:.6'>— empty —</div>"; return; }
    for (const h of res.hits) {
        const card = document.createElement("div");
        card.className = "mod-card";
        const icon = h.icon ? `<img src="${h.icon}">` : "";
        card.innerHTML = `${icon}<div class="info"><div class="title">${h.title}</div><div class="desc">${h.description || ""}</div><button class="dl-btn" data-id="${h.id}">↓ install</button></div>`;
        card.querySelector(".dl-btn").onclick = async (e) => {
            e.stopPropagation();
            const btn = e.target;
            btn.textContent = "...";
            const r = await api.modrinth_install(currentInstance, h.id);
            btn.textContent = r.status === "success" ? "✓" : "✕";
            if (r.status === "success") await openInstance(currentInstance);
            else toast("error","Modrinth",r.message);
        };
        box.appendChild(card);
    }
}

async function openServersTab() {
    switchTab("servers");
    if (!api) return;
    const ram = await api.check_ram();
    if (ram < 20) {
        const msg = currentLang === "ru"
            ? `У вас ${ram} ГБ ОЗУ. Для dedicated сервера рекомендуется 20+ ГБ.`
            : `You have ${ram} GB RAM. Server recommends 20+ GB.`;
        document.getElementById("ram-warning-text").textContent = msg;
        document.getElementById("ram-modal").style.display = "flex";
    }
    await refreshServers();
}

async function refreshServers() {
    if (!api) return;
    const arr = await api.list_servers();
    const grid = document.getElementById("srv-list");
    grid.innerHTML = "";
    if (!arr.length) { grid.innerHTML = `<div style="opacity:.6">${t("no_servers")}</div>`; return; }
    for (const s of arr) {
        const card = document.createElement("div");
        card.className = "server-card";
        card.innerHTML = `
            <div class="name"><span class="status ${s.running ? 'on' : ''}"></span>${s.name}</div>
            <div class="meta">${s.core} • ${s.version}</div>
            <div class="meta">port: ${s.port} • ram: ${s.ram}G</div>
            <div class="meta">players: ${s.players} ${s.pirate ? "• pirate" : ""}</div>`;
        card.onclick = () => openServer(s.name);
        grid.appendChild(card);
    }
}

async function openServer(name) {
    if (!api) return;
    const res = await api.get_server(name);
    if (res.status === "error") return toast("error","Server",res.message);
    currentServer = name;
    const s = res.server;
    document.getElementById("srv-name").textContent = name;
    document.getElementById("srv-pirate").checked = !!s.pirate;
    document.getElementById("srv-motd").value = s.motd || "";
    document.getElementById("srv-seed").value = s.seed || "";
    document.getElementById("srv-port").value = s.port || 25565;
    document.getElementById("srv-ram").value = s.ram || 4;
    document.getElementById("srv-rcon").checked = !!s.rcon_enabled;
    document.getElementById("srv-rcon-port").value = s.rcon_port || 25575;
    document.getElementById("srv-rcon-pass").value = s.rcon_password || "";
    document.getElementById("srv-path").value = s.custom_path || s.base_path || "";
    document.getElementById("srv-path-hint").textContent =
        `${t("default_server_path")}: ${s.default_base || "server_instances"}`;
    updateShareAddr();
    const st = document.getElementById("srv-status");
    st.textContent = s.running ? "● running" : "○ stopped";
    st.style.color = s.running ? "#4ade80" : "var(--text)";

    consoleSince = 0;
    document.getElementById("console-out").innerHTML = "";
    startConsolePolling();
    switchTab("server-detail");
}

function startConsolePolling() {
    stopConsolePolling();
    consoleInterval = setInterval(pollConsole, 800);
    pollConsole();
}
function stopConsolePolling() {
    if (consoleInterval) clearInterval(consoleInterval);
    consoleInterval = null;
}

async function pollConsole() {
    if (!api || !currentServer) return;
    const res = await api.get_server_console(currentServer, consoleSince);
    if (!res) return;
    const out = document.getElementById("console-out");
    for (const l of (res.lines || [])) {
        consoleSince = Math.max(consoleSince, l.t);
        const div = document.createElement("div");
        div.className = "line " + classifyLine(l.line);
        div.textContent = l.line;
        out.appendChild(div);
    }
    if (res.lines && res.lines.length) out.scrollTop = out.scrollHeight;

    const ul = document.getElementById("players-online");
    ul.innerHTML = "";
    if (!res.players || !res.players.length) {
        ul.innerHTML = `<li style="justify-content:center;opacity:.6">— пусто —</li>`;
    } else {
        for (const p of res.players) {
            const li = document.createElement("li");
            li.innerHTML = `<span>${p}</span><button data-p="${p}">→</button>`;
            li.querySelector("button").onclick = () => {
                document.getElementById("inp-manage-nick").value = p;
            };
            ul.appendChild(li);
        }
    }

    const st = document.getElementById("srv-status");
    st.textContent = res.running ? "● running" : "○ stopped";
    st.style.color = res.running ? "#4ade80" : "var(--text)";
}

function classifyLine(line) {
    if (line.includes("[BML/CMD]")) return "cmd";
    if (line.includes("joined the game")) return "join";
    if (line.includes("left the game")) return "leave";
    if (line.includes("ERROR") || line.includes("Exception")) return "error";
    if (line.includes("WARN")) return "warn";
    if (line.includes("INFO")) return "info";
    return "";
}

async function sendConsoleCmd() {
    if (!api || !currentServer) return;
    const inp = document.getElementById("console-cmd");
    const cmd = inp.value.trim();
    if (!cmd) return;
    inp.value = "";
    await api.send_server_command(currentServer, cmd);
}

function applySkin(url) {
    // если своего скина нет — всегда классический Стив
    if (!url) url = "icons/steve.png";
    const busted = url + (url.includes("?") ? "&" : "?") + "t=" + Date.now();
    ["char-skin", "char-skin-home"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.src = busted;
    });
}

/* ---------- v4.1: сетевые патчи ---------- */
async function refreshNetInfo() {
    if (!api) return;
    const box = document.getElementById("net-info");
    if (!box) return;
    try {
        const n = await api.get_network_patches();
        const onoff = v => v ? `<span class="ok">${t("net_on")}</span>`
                             : `<span class="off">${t("net_off")}</span>`;
        const ports = (n.game_ports || []).join(", ") || "—";
        const ip = n.public_ip || "—";
        const addr = (n.public_ip && n.game_ports && n.game_ports.length)
            ? `${n.public_ip}:${n.game_ports[0]}` : "";
        box.innerHTML =
            `<div>${t("net_local")}: <b>${n.local_ip || "—"}</b></div>` +
            `<div>${t("net_public")}: <b>${ip}</b></div>` +
            `<div>${t("net_ports")}: <b>${ports}</b></div>` +
            `<div>${t("net_upnp")}: ${n.upnp ? `<span class="ok">${t("net_upnp_yes")}</span>`
                                            : `<span class="off">${t("net_upnp_no")}</span>`}</div>` +
            `<div>${t("white_ip_emulator")}: ${onoff(n.white_ip_emulator)} &nbsp;·&nbsp; ` +
            `${t("port_emulator")}: ${onoff(n.port_emulator)}</div>` +
            (addr ? `<span class="addr" data-addr="${addr}">${t("net_addr")}: ${addr}</span>` : "");
    } catch (e) {
        box.innerHTML = `<span class="off">${e}</span>`;
    }
}

async function updateShareAddr() {
    if (!api || !currentServer) return;
    const box = document.getElementById("srv-share-addr");
    if (!box) return;
    try {
        const r = await api.get_server_share_address(currentServer);
        if (!r || r.status !== "success") { box.innerHTML = ""; return; }
        box.innerHTML =
            `<h3>${t("share_addr")}</h3>` +
            `<span class="addr" data-addr="${r.address}">${r.address}</span>` +
            `<p class="hint">${r.white_ip ? "White IP Emulator ✓" : r.local_ip}</p>`;
    } catch (e) {}
}

window.onNetPatch = data => {
    const addr = (data && data.address) || "";
    toast("success", "Port Emulator", `${t("port_opened")}: ${addr}`);
    refreshNetInfo();
    if (currentServer) updateShareAddr();
};

/* ---------- v4.1: фон и микро-анимации ---------- */
function initFx() {
    // мягкие частицы
    const cv = document.getElementById("fx-particles");
    if (cv && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        const ctx = cv.getContext("2d");
        const resize = () => { cv.width = innerWidth; cv.height = innerHeight; };
        resize(); addEventListener("resize", resize);
        const spawn = () => ({
            x: Math.random() * cv.width, y: Math.random() * cv.height,
            r: Math.random() * 1.8 + .4, vy: -(Math.random() * .35 + .08),
            vx: (Math.random() - .5) * .22, a: Math.random() * .45 + .12
        });
        const pts = Array.from({ length: 55 }, spawn);
        const frame = () => {
            const accent = getComputedStyle(document.body)
                .getPropertyValue("--accent").trim() || "#c084fc";
            ctx.clearRect(0, 0, cv.width, cv.height);
            ctx.fillStyle = accent;
            for (const p of pts) {
                p.x += p.vx; p.y += p.vy;
                if (p.y < -12 || p.x < -12 || p.x > cv.width + 12) {
                    Object.assign(p, spawn()); p.y = cv.height + 12;
                }
                ctx.globalAlpha = p.a;
                ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
            }
            ctx.globalAlpha = 1;
            requestAnimationFrame(frame);
        };
        frame();
    }

    // волна от клика
    document.addEventListener("click", e => {
        const r = document.createElement("span");
        r.className = "click-ripple";
        r.style.left = e.clientX + "px";
        r.style.top = e.clientY + "px";
        document.body.appendChild(r);
        setTimeout(() => r.remove(), 600);
    });
}

async function updateHomeInfo() {
    if (!api) return;
    const info = await api.get_system_info();
    document.getElementById("home-info").innerHTML =
        `RAM: <b>${info.ram_total} GB</b> (free ${info.ram_available} GB)<br>` +
        `CPU: <b>${info.cpu_count}</b> cores<br>` +
        `OS: <b>${info.os}</b><br>` +
        `Local IP: <b>${info.local_ip}</b>`;
}