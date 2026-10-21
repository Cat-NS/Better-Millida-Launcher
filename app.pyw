# ============================================================
#  Better Millida Launcher v4.0
# ============================================================
import webview, psutil, os, json, shutil, socket, threading, subprocess, re, sys, zipfile
import urllib.request, urllib.parse, time, struct, traceback, hashlib
from pathlib import Path
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog

# В собранном .exe файлы лежат во временной папке PyInstaller (_MEI*),
# которая удаляется при выходе. Поэтому рабочие данные (instances, data,
# settings, серверы) держим РЯДОМ с exe, а ресурсы читаем из _MEIPASS.
FROZEN = getattr(sys, "frozen", False)
if FROZEN:
    RES_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    BASE = Path(sys.executable).parent.resolve()   # куда пишем данные
else:
    RES_DIR = BASE = Path(__file__).parent.resolve()

DATA = BASE / "data"
SERVER = BASE / "server"
SRV_INST = BASE / "server_instances"
INST = BASE / "instances"
SETTINGS_DIR = BASE / "settings"
THINGS_DIR = BASE / "millida_things"
JAVA_DIR = BASE / "java_runtimes"
ASSETS = DATA / "assets"           # общий кэш ассетов для всех инстансов
for d in (DATA, SERVER, SRV_INST, INST, SETTINGS_DIR, THINGS_DIR, JAVA_DIR, ASSETS):
    try:
        d.mkdir(exist_ok=True)
    except Exception:
        pass

# В собранном .exe ресурсы лежат во временной папке — копируем их рядом с exe,
# чтобы Millida Things / bridge.jar / картинки не исчезали при выходе.
if FROZEN:
    try:
        src_things = RES_DIR / "millida_things"
        if src_things.exists():
            for sub in ("bin", "bridge"):
                s = src_things / sub
                d = THINGS_DIR / sub
                if s.is_dir():
                    shutil.copytree(s, d, dirs_exist_ok=True)
        src_icons = RES_DIR / "web" / "icons"
        dst_icons = BASE / "web" / "icons"
        if src_icons.is_dir():
            shutil.copytree(src_icons, dst_icons, dirs_exist_ok=True)
    except Exception:
        pass

# миграция: в одной из версий папка индексов ошибочно называлась "indices"
_old_idx = ASSETS / "indices"
if _old_idx.exists() and not (ASSETS / "indexes").exists():
    try:
        _old_idx.rename(ASSETS / "indexes")
    except OSError:
        pass

SET_FILE = DATA / "settings.json"
DEBUG_LOG = DATA / "debug.log"
GAME_LOG = DATA / "game.log"
MANIFEST_CACHE = DATA / "version_manifest.json"
SRV_INDEX = DATA / "servers_index.json"     # реестр: имя -> папка сервера
DEFAULTS = {
    "language": "ru", "theme": "purple", "nickname": "",
    "java_path": "java", "ram_gb": 4, "active_instance": None,
    "black_ip_patch": False, "millida_things": False, "voice_chat": True,
    # --- сетевые патчи Millida Things ---
    "white_ip_emulator": False,   # Grey IP Patch: публичный IP для друзей без проброса
    "port_emulator": False,       # Port Emulator: авто-проброс порта игры через UPnP
    "elyby_skins": False,         # Ely.by Skin System
    "things_lite": False,         # Millida Things Lite (только патчи)
    # --- сервера ---
    "default_server_path": "",    # пусто = BASE/server_instances
}
DEFAULT_STEVE = BASE / "web" / "icons" / "steve.png"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BetterMillidaLauncher/4.0"}
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
LIBRARIES_MINECRAFT = "https://libraries.minecraft.net/"

# --------------------------------------------------- GitHub
APP_VERSION = "1.0"                       # версия приложения для гитхаба
GITHUB_OWNER = "Cat-NS"
GITHUB_REPO = "Better-Millida-Launcher"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main"
GH_HEADERS = {
    "User-Agent": "BetterMillidaLauncher",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _gh_headers():
    """Заголовки GitHub API. Если пользователь положил токен в
    data/github_token.txt — используем его (5000 запросов/час вместо 60)."""
    h = dict(GH_HEADERS)
    try:
        tok = DATA / "github_token.txt"
        if tok.exists():
            t = tok.read_text(encoding="utf-8").strip()
            if t:
                h["Authorization"] = f"Bearer {t}"
    except Exception:
        pass
    return h


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


# ---------------------------------------------------------------- http layer
def http_bytes(url, timeout=30, retries=3):
    """GET с повторами. Возвращает тело."""
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(1.0 + i * 1.5)
    raise last


def http_json(url, timeout=30, retries=3):
    return json.loads(http_bytes(url, timeout=timeout, retries=retries))


def http_dl(url, target: Path, progress=None, retries=3):
    """Скачивание в .part с проверкой размера, затем атомарная замена."""
    target.parent.mkdir(parents=True, exist_ok=True)
    part = Path(str(target) + ".part")
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            total = 0
            with urllib.request.urlopen(req, timeout=300) as r, open(part, "wb") as f:
                clen = r.headers.get("Content-Length")
                clen = int(clen) if clen and clen.isdigit() else None
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    total += len(chunk)
                    if progress:
                        progress(len(chunk), clen)
            if clen is not None and total != clen:
                raise IOError(f"Неполная загрузка {total}/{clen}")
            os.replace(part, target)
            return total
        except Exception as e:
            last = e
            try:
                part.unlink()
            except OSError:
                pass
            time.sleep(1.0 + i * 1.5)
    raise last


def sha1_file(path: Path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def maven_path(name: str):
    """com.mojang:patchy:2.2 -> com/mojang/patchy/2.2/patchy-2.2.jar"""
    parts = name.split(":")
    if len(parts) < 3:
        return None
    group, artifact, version = parts[0], parts[1], parts[2]
    classifier = parts[3] if len(parts) > 3 else None
    file_ = f"{artifact}-{version}" + (f"-{classifier}" if classifier else "") + ".jar"
    return f"{group.replace('.', '/')}/{artifact}/{version}/{file_}"


class Debug:
    def __init__(self):
        self.messages = deque(maxlen=400)

    def log(self, level, msg):
        entry = {"t": time.time(), "level": level, "msg": str(msg)}
        self.messages.append(entry)
        try:
            with open(DEBUG_LOG, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}][{level}] {msg}\n")
        except Exception:
            pass

    def error(self, msg, exc=None):
        full = str(msg)
        if exc is not None:
            full += "\n" + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.log("ERROR", full)

    def info(self, msg): self.log("INFO", msg)
    def warn(self, msg): self.log("WARN", msg)


DEBUG = Debug()


class Progress:
    """Лёгкий прогресс для UI (опрос из JS)."""
    def __init__(self):
        self.lock = threading.Lock()
        self.data = {"active": False, "label": "", "done": 0, "total": 0, "detail": ""}

    def start(self, label, total=0):
        with self.lock:
            self.data = {"active": True, "label": label, "done": 0,
                         "total": total, "detail": ""}

    def add(self, n):
        with self.lock:
            self.data["done"] += n

    def set_total(self, total):
        with self.lock:
            self.data["total"] = total

    def detail(self, text):
        with self.lock:
            self.data["detail"] = text

    def finish(self):
        with self.lock:
            self.data["active"] = False
            self.data["detail"] = ""

    def get(self):
        with self.lock:
            return dict(self.data)


class RconClient:
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2

    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.sock = None
        self.rid = 1

    def _send(self, typ, body):
        data = struct.pack("<ii", self.rid, typ) + body.encode("utf-8") + b"\x00\x00"
        packet = struct.pack("<i", len(data)) + data
        self.sock.sendall(packet)
        self.rid += 1

    def _recv(self):
        raw_len = self._recv_all(4)
        if not raw_len or len(raw_len) < 4:
            return None, None
        length = struct.unpack("<i", raw_len)[0]
        data = self._recv_all(length)
        if not data or len(data) < 8:
            return None, None
        rid, typ = struct.unpack("<ii", data[:8])
        body = data[8:-2].decode("utf-8", errors="ignore")
        return typ, body

    def _recv_all(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                return None
            buf += chunk
        return buf

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
        self.sock.settimeout(5)
        self._send(self.SERVERDATA_AUTH, self.password)
        self._recv()
        typ, _ = self._recv()
        return typ == self.SERVERDATA_AUTH_RESPONSE

    def command(self, cmd):
        self._send(self.SERVERDATA_EXECCOMMAND, cmd)
        typ, body = self._recv()
        return body or ""

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


class ServerInstance:
    def __init__(self, name, path: Path):
        self.name = name
        self.path = path
        self.proc = None
        self.console = deque(maxlen=4000)
        self.console_lock = threading.Lock()
        self.running = False
        self.start_time = None
        self.players = {}
        self._reader_thread = None

    def append(self, line):
        with self.console_lock:
            self.console.append({"t": time.time(), "line": line})
        self._parse_line(line)

    def _parse_line(self, line):
        m = re.search(r"(\w+) joined the game", line)
        if m:
            self.players[m.group(1)] = time.time()
        m = re.search(r"(\w+) left the game", line)
        if m and m.group(1) in self.players:
            del self.players[m.group(1)]

    def tail(self, since=0):
        with self.console_lock:
            return [x for x in self.console if x["t"] > since]

    def send(self, cmd):
        if not self.proc or self.proc.poll() is not None:
            return False
        try:
            self.proc.stdin.write((cmd + "\n").encode("utf-8"))
            self.proc.stdin.flush()
            return True
        except Exception as e:
            DEBUG.error(f"server stdin send failed: {e}")
            return False


class LauncherAPI:
    def __init__(self):
        self.window = None
        self.settings = self._load()
        self.server_proc = None
        self.game_proc = None
        self.things_proc = None
        self._forge_matrix = {}
        self._neoforge_matrix = {}
        self.servers = {}
        self._load_existing_servers()
        self.share_server = None
        self.progress = Progress()
        self._java_lock = threading.Lock()
        self._sys_java_cache = {}
        # сетевые патчи: сопоставление порт -> открыт ли через UPnP
        self._mapped_ports = {}
        self._net_watch_stop = threading.Event()
        self._net_watch_thread = None

    def set_window(self, w):
        self.window = w

    def _load(self):
        if SET_FILE.exists():
            try:
                return {**DEFAULTS, **json.loads(SET_FILE.read_text(encoding="utf-8"))}
            except Exception:
                pass
        return DEFAULTS.copy()

    def _save(self):
        SET_FILE.write_text(json.dumps(self.settings, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_settings(self): return self.settings

    def save_settings(self, new):
        self.settings.update(new or {})
        self._save()
        if (self.settings.get("port_emulator") or self.settings.get("white_ip_emulator")) \
                and self.game_proc and self.game_proc.poll() is None:
            self.start_net_patch_watcher()
        elif not (self.settings.get("port_emulator")
                  or self.settings.get("white_ip_emulator")):
            self.stop_net_patch_watcher()
        if self.settings.get("elyby_skins"):
            self._sync_elyby_skin()
        return {"status": "success", "skin_url": self.get_skin_url()}

    def get_progress(self): return self.progress.get()

    def minimize_window(self):
        if self.window: self.window.minimize()
        return True

    def close_window(self):
        if self.window: self.window.destroy()
        return True

    def toggle_fullscreen(self):
        if self.window:
            try:
                self.window.toggle_fullscreen()
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error"}

    def check_ram(self): return round(psutil.virtual_memory().total / (1024 ** 3), 1)

    def get_system_info(self):
        vm = psutil.virtual_memory()
        return {
            "ram_total": round(vm.total / (1024 ** 3), 1),
            "ram_available": round(vm.available / (1024 ** 3), 1),
            "cpu_count": psutil.cpu_count(),
            "os": os.name,
            "local_ip": local_ip(),
            "skin_url": self.get_skin_url(),
            "has_skin": self.has_custom_skin(),
            "nickname": self.settings.get("nickname", ""),
        }

    def get_debug(self, since=0):
        return [m for m in DEBUG.messages if m["t"] > since]

    def clear_debug(self):
        DEBUG.messages.clear()
        return {"status": "success"}

    # ------------------------------------------------ version manifest
    def _manifest(self, force=False):
        """Манифест Mojang с кэшем на диске."""
        if not force and MANIFEST_CACHE.exists():
            try:
                age = time.time() - MANIFEST_CACHE.stat().st_mtime
                if age < 6 * 3600:
                    return json.loads(MANIFEST_CACHE.read_text(encoding="utf-8"))
            except Exception:
                pass
        data = http_json(MANIFEST_URL, timeout=30, retries=3)
        try:
            MANIFEST_CACHE.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass
        return data

    def _version_meta(self, version_id, force=False):
        """Метаданные конкретной версии (с кэшем рядом с инстансами не нужно —
        храним в общем кэше)."""
        cache = DATA / "versions"
        cache.mkdir(exist_ok=True)
        p = cache / f"{version_id}.json"
        if p.exists() and not force:
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        man = self._manifest(force=force)
        v = next((x for x in man["versions"] if x["id"] == version_id), None)
        if not v:
            raise Exception(f"Версия {version_id} не найдена в манифесте")
        vd = http_json(v["url"], timeout=30)
        try:
            p.write_text(json.dumps(vd), encoding="utf-8")
        except Exception:
            pass
        return vd

    # ------------------------------------------------ version lists
    def fetch_versions(self, core="vanilla", version_type="release"):
        core = (core or "").lower()
        try:
            if core == "paper":
                data = http_json("https://fill.papermc.io/v3/projects/paper")
                vs = []
                for group in data.get("versions", {}).values():
                    vs.extend(group)
                return {"status": "success", "versions": vs,
                        "note": "Paper — только релизные версии"}
            if core in ("vanilla", "release"):
                data = self._manifest()
                key = {"release": "release", "snapshot": "snapshot",
                       "old_beta": "old_beta", "old_alpha": "old_alpha"}.get(version_type, "release")
                vs = [v["id"] for v in data["versions"] if v["type"] == key]
                return {"status": "success", "versions": vs}
            if core == "fabric":
                data = http_json("https://meta.fabricmc.net/v2/versions/game")
                vs = [v["version"] for v in data
                      if (v.get("stable") if version_type == "release" else not v.get("stable"))]
                return {"status": "success", "versions": vs}
            if core == "quilt":
                data = http_json("https://meta.quiltmc.org/v3/versions/game")
                vs = [v["version"] for v in data
                      if (v.get("stable") if version_type == "release" else not v.get("stable"))]
                return {"status": "success", "versions": vs}
            if core == "forge":
                data = http_json(
                    "https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json")
                promos = data.get("promos", {})
                mat = {}
                for k, v in promos.items():
                    if k.endswith("-recommended") or k.endswith("-latest"):
                        mc = k.rsplit("-", 1)[0]
                        mat.setdefault(mc, {})[k.rsplit("-", 1)[1]] = v
                self._forge_matrix = mat
                return {"status": "success", "versions": sorted(mat.keys(), reverse=True)}
            if core == "neoforge":
                xml = http_bytes(
                    "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml")
                versions = re.findall(r"<version>([^<]+)</version>", xml.decode())
                mat = {}
                for v in versions:
                    parts = v.split(".")
                    if len(parts) >= 2:
                        mat.setdefault(f"1.{parts[0]}.{parts[1]}", []).append(v)
                self._neoforge_matrix = mat
                return {"status": "success", "versions": sorted(mat.keys(), reverse=True)}
            return {"status": "error", "message": f"Ядро {core} неизвестно"}
        except Exception as e:
            DEBUG.error("fetch_versions", e)
            return {"status": "error", "message": str(e)}

    def resolve_loader_version(self, core, mc):
        core = core.lower()
        try:
            if core == "forge":
                info = self._forge_matrix.get(mc)
                if info:
                    return info.get("recommended") or info.get("latest")
                data = http_json(f"https://files.minecraftforge.net/net/minecraftforge/forge/"
                                 f"{mc}/promotions_slim.json")
                info = data.get("promos", {}).get(f"{mc}-recommended") or \
                       data.get("promos", {}).get(f"{mc}-latest")
                if info:
                    return info
                maven = http_bytes(f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
                                   f"maven-metadata.xml").decode()
                vers = re.findall(rf"<version>{re.escape(mc)}-(\d[^<]+)</version>", maven)
                return vers[-1] if vers else None
            if core == "neoforge":
                if not self._neoforge_matrix:
                    self.fetch_versions("neoforge")
                return (self._neoforge_matrix.get(mc) or [None])[-1]
            if core == "fabric":
                data = http_json("https://meta.fabricmc.net/v2/versions/loader")
                return data[0]["version"] if data else None
            if core == "quilt":
                data = http_json("https://meta.quiltmc.org/v3/versions/loader")
                return data[0]["version"] if data else None
        except Exception as e:
            DEBUG.error("resolve_loader_version", e)
        return None

    # ------------------------------------------------ instances
    def _inst_dir(self, name):
        p = INST / name
        (p / "mods").mkdir(parents=True, exist_ok=True)
        (p / "saves").mkdir(parents=True, exist_ok=True)
        return p

    def _meta_path(self, name): return self._inst_dir(name) / "instance.json"

    def _read_meta(self, name):
        p = self._meta_path(name)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"name": name, "version": "1.20.1", "loader": "vanilla", "loader_version": None}

    def _write_meta(self, name, m):
        self._meta_path(name).write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_instances(self):
        out = []
        for d in sorted(INST.iterdir(), key=lambda x: x.name.lower()):
            if d.is_dir():
                m = self._read_meta(d.name)
                out.append({
                    "name": d.name, "version": m.get("version", "?"),
                    "loader": m.get("loader", "?"),
                    "loader_version": m.get("loader_version"),
                    "mods_count": len(list((d / "mods").glob("*.jar"))),
                    "installed": (d / "version.json").exists() or (d / "loader.json").exists(),
                })
        return out

    def create_instance(self, name, version="1.20.1", loader="vanilla"):
        name = (name or "").strip()
        if not name: return {"status": "error", "message": "Пустое имя"}
        if re.search(r'[<>:"/\\|?*]', name):
            return {"status": "error", "message": "Имя содержит запрещённые символы"}
        if (INST / name).exists(): return {"status": "error", "message": "Уже есть"}
        self._inst_dir(name)
        lv = None if loader == "vanilla" else self.resolve_loader_version(loader, version)
        self._write_meta(name, {"name": name, "version": version, "loader": loader, "loader_version": lv})
        if not self.settings.get("active_instance"):
            self.settings["active_instance"] = name
            self._save()
        return {"status": "success", "message": f"'{name}' создан"}

    def delete_instance(self, name):
        p = INST / name
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            if self.settings.get("active_instance") == name:
                self.settings["active_instance"] = None
                self._save()
            return {"status": "success"}
        return {"status": "error", "message": "Не найдено"}

    def get_instance(self, name):
        if not (INST / name).exists(): return {"status": "error", "message": "Не найдено"}
        m = self._read_meta(name)
        m["mods"] = [f.name for f in (INST / name / "mods").glob("*.jar")]
        m["active"] = self.settings.get("active_instance") == name
        m["installed"] = (INST / name / "version.json").exists() or (INST / name / "loader.json").exists()
        return {"status": "success", "instance": m}

    def update_instance(self, name, version=None, loader=None):
        if not (INST / name).exists(): return {"status": "error", "message": "Не найдено"}
        m = self._read_meta(name)
        changed = False
        if version and version != m.get("version"): m["version"] = version; changed = True
        if loader and loader != m.get("loader"): m["loader"] = loader; changed = True
        if changed:
            m["loader_version"] = None if m["loader"] == "vanilla" \
                else self.resolve_loader_version(m["loader"], m["version"])
            for f in ("version.json", "loader.json"):
                p = INST / name / f
                if p.exists(): p.unlink()
        self._write_meta(name, m)
        return {"status": "success", "loader_version": m.get("loader_version")}

    def set_active_instance(self, name):
        if not (INST / name).exists(): return {"status": "error", "message": "Не найдено"}
        self.settings["active_instance"] = name
        self._save()
        return {"status": "success"}

    # ------------------------------------------------ java
    def _required_java_major(self, mc_version: str) -> int:
        v = (mc_version or "").strip()
        m = re.match(r"^1\.(\d+)", v)
        if m:
            minor = int(m.group(1))
            if minor >= 21: return 21
            if minor in (20,): return 17
            if minor in (18, 19): return 17
            if minor == 17: return 17
            return 8
        m = re.match(r"^(\d+)", v)   # новые версии вида 26.x
        if m:
            return 21
        return 8

    def _java_installed(self, major: int):
        p = JAVA_DIR / f"jdk{major}" / "bin" / ("java.exe" if os.name == "nt" else "java")
        return p if p.exists() else None

    def _system_java_major(self, java_bin="java"):
        """Версия Java в PATH (или по указанному пути). None если не найдена."""
        key = str(java_bin)
        if key in self._sys_java_cache:
            return self._sys_java_cache[key]
        major = None
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            r = subprocess.run([java_bin, "-version"], capture_output=True,
                               text=True, timeout=10, creationflags=creationflags)
            out = (r.stderr or "") + (r.stdout or "")
            m = re.search(r'version "(?P<v>[^"]+)"', out)
            if m:
                v = m.group("v")
                if v.startswith("1."):
                    major = int(v.split(".")[1])
                else:
                    major = int(v.split(".")[0])
        except Exception:
            major = None
        self._sys_java_cache[key] = major
        return major

    def _java_fits(self, major: int, need: int) -> bool:
        """Насколько установленная Java подходит под требуемую для версии MC."""
        if major is None:
            return False
        if need == 8:
            return major == 8          # старый LWJGL2 не любит новые Java
        if need == 17:
            return 17 <= major <= 21   # 1.17–1.20.1: 17 или 21
        return major >= need

    def _pick_java(self, mc_version):
        """Возвращает (путь, major) — ближайшую подходящую Java, или (None, need)."""
        need = self._required_java_major(mc_version)
        candidates = []  # (major, path)

        user_java = (self.settings.get("java_path") or "").strip()
        if user_java and Path(user_java).exists():
            got = self._system_java_major(user_java)
            if self._java_fits(got, need):
                candidates.append((got, user_java))
        got = self._system_java_major("java")
        if self._java_fits(got, need):
            candidates.append((got, "java"))
        for major in (8, 17, 21, 25):
            c = self._java_installed(major)
            if c and self._java_fits(major, need):
                candidates.append((major, str(c)))
        if candidates:
            candidates.sort(key=lambda x: x[0])   # ближайший подходящий major
            return candidates[0][1], candidates[0][0]
        return None, need

    def ensure_java(self, mc_version: str):
        """Гарантирует наличие Java нужной версии. Возвращает dict со статусом."""
        need = self._required_java_major(mc_version)
        path, got = self._pick_java(mc_version)
        if path:
            return {"status": "success", "path": path, "source": "auto", "major": got}
        for source, fn in (("adoptium", self._dl_java_adoptium),
                           ("oracle", self._dl_java_oracle)):
            try:
                result = fn(need)
                if result and result.get("path"):
                    return {"status": "success", "path": result["path"],
                            "source": source, "major": need}
            except Exception as e:
                DEBUG.error(f"java/{source}", e)
        return {"status": "manual", "major": need,
                "message": (f"Не удалось автоматически скачать Java {need}.\n\n"
                            f"Скачайте вручную с:\n"
                            f"• https://adoptium.net/temurin/releases/?version={need}\n"
                            f"• https://www.oracle.com/java/technologies/downloads/\n"
                            f"и укажите путь в настройках.")}

    def _extract_java_zip(self, dst_dir: Path, archive: Path):
        # очищаем возможный мусор от прошлых неудачных распаковок
        for child in list(dst_dir.iterdir()):
            if child.name == archive.name:
                continue
            if child.is_dir() and child.name.lower().startswith(("jdk", "jre", "temurin")):
                shutil.rmtree(child, ignore_errors=True)
        if archive.suffix == ".zip":
            with zipfile.ZipFile(archive, "r") as z:
                bad = z.testzip()
                if bad:
                    raise zipfile.BadZipFile(f"Повреждён архив: {bad}")
                z.extractall(dst_dir)
        else:
            import tarfile
            with tarfile.open(archive) as t:
                t.extractall(dst_dir)
        try:
            archive.unlink()
        except OSError:
            pass
        exe = "java.exe" if os.name == "nt" else "java"
        if (dst_dir / "bin" / exe).exists():
            return
        for child in dst_dir.iterdir():
            if child.is_dir() and child.name.lower().startswith(("jdk", "jre", "temurin")):
                for item in list(child.iterdir()):
                    shutil.move(str(item), str(dst_dir / item.name))
                shutil.rmtree(child, ignore_errors=True)
                break

    def _dl_java_adoptium(self, major: int):
        os_name = "windows" if os.name == "nt" else ("mac" if sys.platform == "darwin" else "linux")
        url = (f"https://api.adoptium.net/v3/binary/latest/{major}/ga/"
               f"{os_name}/x64/jdk/hotspot/normal/eclipse")
        dst = JAVA_DIR / f"jdk{major}"
        dst.mkdir(parents=True, exist_ok=True)
        archive = dst / ("jdk.zip" if os.name == "nt" else "jdk.tar.gz")
        self.progress.detail(f"Скачивание Java {major} (Adoptium)...")
        http_dl(url, archive)
        self.progress.detail(f"Распаковка Java {major}...")
        self._extract_java_zip(dst, archive)
        jb = dst / "bin" / ("java.exe" if os.name == "nt" else "java")
        return {"path": str(jb)} if jb.exists() else None

    def _dl_java_oracle(self, major: int):
        if os.name != "nt" or major < 17:
            return None
        url = f"https://download.oracle.com/java/{major}/latest/jdk-{major}_windows-x64_bin.zip"
        dst = JAVA_DIR / f"jdk{major}"
        dst.mkdir(parents=True, exist_ok=True)
        zip_path = dst / "jdk.zip"
        self.progress.detail(f"Скачивание Java {major} (Oracle)...")
        http_dl(url, zip_path)
        self.progress.detail(f"Распаковка Java {major}...")
        self._extract_java_zip(dst, zip_path)
        jb = dst / "bin" / "java.exe"
        return {"path": str(jb)} if jb.exists() else None

    # ------------------------------------------------ установка файлов игры
    def _natives_key(self, vdata=None):
        if os.name == "nt": return "natives-windows"
        if sys.platform == "darwin": return "natives-macos"
        return "natives-linux"

    def _download_libraries(self, target: Path, vdata, pb: Progress):
        """Скачивает библиотеки (включая maven-стиль) и нативные библиотеки.
        Возвращает список jar для classpath."""
        libs_dir = target / "libraries"
        natives_dir = target / "natives"
        libs_dir.mkdir(exist_ok=True)
        natives_dir.mkdir(exist_ok=True)

        entries = []          # (lib, artifact_path_or_None)
        downloads = []        # (url, path, sha1, size)
        seen = set()

        for lib in vdata.get("libraries", []):
            rules = lib.get("rules")
            if rules and not self._rules_allow(rules):
                continue
            dls = lib.get("downloads", {})
            art = dls.get("artifact")
            if art and art.get("path"):
                rel = art["path"]
                url = art.get("url") or (LIBRARIES_MINECRAFT + rel)
                downloads.append((url, rel, art.get("sha1"), art.get("size")))
                entries.append(rel)
            elif lib.get("name"):
                mp = maven_path(lib["name"])
                if mp:
                    base = lib.get("url") or LIBRARIES_MINECRAFT
                    url = base.rstrip("/") + "/" + mp
                    downloads.append((url, mp, None, None))
                    entries.append(mp)

            # нативные библиотеки (старые версии: classifiers)
            classifiers = dls.get("classifiers") or {}
            nkey = self._natives_key()
            nat = classifiers.get(nkey) or classifiers.get(nkey + "-x64")
            if not nat:
                natives_cfg = lib.get("natives") or {}
                pattern = natives_cfg.get("windows" if os.name == "nt"
                                          else "macos" if sys.platform == "darwin" else "linux")
                if pattern:
                    nat = classifiers.get(pattern.replace("${arch}", "x64"))
            if nat and nat.get("path"):
                downloads.append((nat.get("url") or LIBRARIES_MINECRAFT + nat["path"],
                                  nat["path"], nat.get("sha1"), nat.get("size")))

        # дедупликация и пропуск уже скачанного
        todo = []
        for url, rel, sha, size in downloads:
            if rel in seen:
                continue
            seen.add(rel)
            f = libs_dir / rel
            if f.exists() and (size is None or f.stat().st_size == size):
                continue
            todo.append((url, f, sha, rel))

        pb.set_total(pb.data["total"] + len(todo))

        if todo:
            pb.detail(f"Библиотеки: 0/{len(todo)}")
            counter = {"n": 0}
            lock = threading.Lock()

            def worker(item):
                url, f, sha, rel = item
                try:
                    http_dl(url, f)
                    if sha:
                        got = sha1_file(f)
                        if got != sha:
                            f.unlink(missing_ok=True)
                            raise IOError(f"sha1 не совпал: {rel}")
                except Exception as e:
                    # часть артефактов мертва на CDN Mojang (twitch/jinput-platform) — не фатально
                    DEBUG.warn(f"lib {rel}: {e}")
                finally:
                    with lock:
                        counter["n"] += 1
                        pb.add(1)
                        pb.detail(f"Библиотеки: {counter['n']}/{len(todo)}")

            with ThreadPoolExecutor(max_workers=8) as ex:
                list(ex.map(worker, todo))

        # распаковка нативных библиотек (плоско, т.к. java.library.path без подпапок)
        nkey = self._natives_key()
        for jar in libs_dir.glob(f"**/*{nkey}*.jar"):
            try:
                with zipfile.ZipFile(jar, "r") as z:
                    for n in z.namelist():
                        if n.endswith((".dll", ".so", ".dylib", ".jnilib")) and not n.startswith("META-INF"):
                            data = z.read(n)
                            (natives_dir / Path(n).name).write_bytes(data)
            except Exception as e:
                DEBUG.error(f"natives {jar.name}", e)
        return [str(libs_dir / rel) for rel in entries if (libs_dir / rel).exists()]

    def _ensure_assets(self, target: Path, vdata, pb: Progress):
        """Скачивает индекс ассетов и все объекты (общий кэш)."""
        idx = vdata.get("assetIndex")
        if not idx or not idx.get("id"):
            return
        idx_id = idx["id"]
        idx_dir = ASSETS / "indexes"
        obj_dir = ASSETS / "objects"
        idx_dir.mkdir(parents=True, exist_ok=True)
        obj_dir.mkdir(parents=True, exist_ok=True)
        idx_path = idx_dir / f"{idx_id}.json"
        if not idx_path.exists() or (idx.get("size") and idx_path.stat().st_size != idx["size"]):
            pb.detail("Скачивание индекса ассетов...")
            http_dl(idx["url"], idx_path)
        try:
            data = json.loads(idx_path.read_text(encoding="utf-8"))
        except Exception as e:
            DEBUG.error("asset index", e)
            return
        objects = data.get("objects", {})
        todo = []
        for name, o in objects.items():
            h = o["hash"]
            p = obj_dir / h[:2] / h
            if not p.exists() or p.stat().st_size != o["size"]:
                todo.append((h, o["size"]))
        if not todo:
            return
        pb.set_total(pb.data["total"] + len(todo))
        pb.detail(f"Ассеты: 0/{len(todo)}")
        counter = {"n": 0}
        lock = threading.Lock()
        base = "https://resources.download.minecraft.net/"

        def worker(item):
            h, size = item
            p = obj_dir / h[:2] / h
            try:
                http_dl(f"{base}{h[:2]}/{h}", p)
            except Exception as e:
                DEBUG.error(f"asset {h}", e)
            finally:
                with lock:
                    counter["n"] += 1
                    pb.add(1)
                    if counter["n"] % 25 == 0 or counter["n"] == len(todo):
                        pb.detail(f"Ассеты: {counter['n']}/{len(todo)}")

        with ThreadPoolExecutor(max_workers=12) as ex:
            list(ex.map(worker, todo))

    def _ensure_logging(self, target: Path, vdata):
        log_cfg = (vdata.get("logging") or {}).get("client")
        if not log_cfg or not log_cfg.get("file"):
            return None
        f = log_cfg["file"]
        p = ASSETS / "log_configs" / f.get("id", "client-logs.xml")
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            try:
                http_dl(f["url"], p)
            except Exception as e:
                DEBUG.error("log config", e)
                return None
        return p

    def _install_game_files(self, target: Path, vdata, pb: Progress):
        """Полная установка: client jar + libraries + natives + assets + logging."""
        pb.detail("Подготовка файлов игры...")
        # client jar
        cid = vdata.get("id", "client")
        client_jar = target / f"{cid}.jar"
        dl = (vdata.get("downloads") or {}).get("client")
        if dl and not client_jar.exists():
            pb.set_total(pb.data["total"] + 1)
            pb.detail(f"Скачивание клиента {cid}...")
            http_dl(dl["url"], client_jar)
            pb.add(1)
            if dl.get("sha1"):
                got = sha1_file(client_jar)
                if got != dl["sha1"]:
                    client_jar.unlink(missing_ok=True)
                    raise IOError("sha1 клиента не совпал")
        libs = self._download_libraries(target, vdata, pb)
        self._ensure_assets(target, vdata, pb)
        logp = self._ensure_logging(target, vdata)
        return client_jar, libs, logp

    # ------------------------------------------------ установка инстанса
    def install_instance(self, name):
        if not (INST / name).exists(): return {"status": "error", "message": "Инстанс не найден"}
        m = self._read_meta(name)
        target = INST / name
        self.progress.start(f"Установка {name}")
        try:
            if m["loader"] in ("fabric", "quilt"):
                self._install_profile_loader(target, m)
            elif m["loader"] in ("forge", "neoforge"):
                self._install_forge_style(target, m)
            vdata = self._resolve_vdata(target, m)
            pb = self.progress
            self._install_game_files(target, vdata, pb)
            (target / "version.json").write_text(json.dumps(vdata, indent=2), encoding="utf-8")
            return {"status": "success",
                    "message": f"'{name}' установлен ({m['loader']} {m['version']})"}
        except Exception as e:
            DEBUG.error("install_instance", e)
            return {"status": "error", "message": f"Ошибка: {e}"}
        finally:
            self.progress.finish()

    def _install_profile_loader(self, target: Path, meta):
        """Fabric/Quilt: скачиваем профиль загрузчика."""
        loader = meta["loader"].lower()
        mc = meta["version"]
        lv = meta.get("loader_version") or self.resolve_loader_version(loader, mc)
        url = (f"https://meta.fabricmc.net/v2/versions/loader/{mc}/{lv}/profile/json"
               if loader == "fabric" else
               f"https://meta.quiltmc.org/v3/versions/loader/{mc}/{lv}/profile/json")
        prof = http_json(url)
        (target / "loader.json").write_text(json.dumps(prof, indent=2), encoding="utf-8")
        meta["loader_version"] = lv
        self._write_meta(meta["name"], meta)

    def _install_forge_style(self, target: Path, meta):
        """Forge/NeoForge: запускаем официальный installer --installClient."""
        loader = meta["loader"].lower()
        mc = meta["version"]
        lv = meta.get("loader_version") or self.resolve_loader_version(loader, mc)
        if not lv:
            raise Exception(f"Не удалось определить версию {loader} для {mc}")
        if loader == "forge":
            url = (f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
                   f"{mc}-{lv}/forge-{mc}-{lv}-installer.jar")
        else:
            url = (f"https://maven.neoforged.net/releases/net/neoforged/neoforge/"
                   f"{lv}/neoforge-{lv}-installer.jar")
        self.progress.detail(f"Скачивание установщика {loader} {lv}...")
        installer = target / "loader-installer.jar"
        http_dl(url, installer)

        jr = self.ensure_java(mc)
        if jr["status"] != "success":
            raise Exception(jr.get("message", "Нужна Java для установки загрузчика"))
        self.progress.detail(f"Установка {loader} {lv} (это может занять минуту)...")
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run([jr["path"], "-jar", str(installer), "--installClient", str(target)],
                           cwd=str(target), capture_output=True, text=True,
                           timeout=900, creationflags=creationflags)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        DEBUG.info(f"{loader} installer output:\n{out[-3000:]}")
        try:
            installer.unlink()
        except OSError:
            pass
        # installer создаёт versions/<mc>-<loader>-<lv>/<...>.json
        vdir = target / "versions"
        found = None
        if vdir.exists():
            for j in vdir.glob("*/*.json"):
                found = j
                break
        if not found:
            raise Exception(f"Установщик {loader} не создал профиль. Вывод: {out[-500:]}")
        prof = json.loads(found.read_text(encoding="utf-8"))
        (target / "loader.json").write_text(json.dumps(prof, indent=2), encoding="utf-8")
        meta["loader_version"] = lv
        meta["loader_profile"] = prof.get("id")
        self._write_meta(meta["name"], meta)

    def _resolve_vdata(self, target: Path, meta):
        """Итоговый version json с учётом inheritsFrom (в т.ч. цепочек)."""
        loader_p = target / "loader.json"
        vjson_p = target / "version.json"
        if loader_p.exists():
            vdata = json.loads(loader_p.read_text(encoding="utf-8"))
        elif vjson_p.exists():
            vdata = json.loads(vjson_p.read_text(encoding="utf-8"))
        else:
            vdata = self._version_meta(meta["version"])
        # поднимаемся по цепочке inheritsFrom
        libs = list(vdata.get("libraries", []))
        cur = vdata
        seen_ids = {vdata.get("id")}
        for _ in range(5):
            parent_id = cur.get("inheritsFrom")
            if not parent_id:
                break
            parent = self._version_meta(parent_id)
            libs = parent.get("libraries", []) + libs
            merged = dict(parent)
            merged.update({k: v for k, v in vdata.items() if k != "libraries"})
            merged["libraries"] = libs
            if "arguments" in vdata:
                merged["arguments"] = vdata["arguments"]
            if "minecraftArguments" in vdata:
                merged["minecraftArguments"] = vdata["minecraftArguments"]
            if "mainClass" in vdata:
                merged["mainClass"] = vdata["mainClass"]
            if "logging" in vdata:
                merged["logging"] = vdata["logging"]
            merged["assetIndex"] = parent.get("assetIndex") or vdata.get("assetIndex")
            merged["downloads"] = parent.get("downloads") or vdata.get("downloads")
            merged["id"] = parent.get("id", vdata.get("id"))
            if parent.get("id") in seen_ids:
                break
            seen_ids.add(parent.get("id"))
            cur = merged
            vdata = merged
        return vdata

    # ------------------------------------------------ моды
    def install_mod_local(self, instance):
        if not (INST / instance).exists(): return {"status": "error", "message": "Инстанс не найден"}
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        files = filedialog.askopenfilenames(title="Выберите .jar",
            filetypes=[("Minecraft Mods", "*.jar"), ("Все файлы", "*.*")])
        root.destroy()
        if not files: return {"status": "error", "message": "Отменено"}
        dst = INST / instance / "mods"
        n = 0
        for f in files:
            try: shutil.copy2(f, dst / Path(f).name); n += 1
            except Exception: pass
        return {"status": "success", "message": f"Установлено: {n}"}

    def delete_mod(self, instance, name):
        p = INST / instance / "mods" / name
        if p.exists(): p.unlink(); return {"status": "success"}
        return {"status": "error", "message": "Не найдено"}

    def modrinth_search(self, query, loader=None, mc_version=None, limit=20):
        facets = [["project_type:mod"]]
        if loader: facets.append([f"categories:{loader}"])
        if mc_version: facets.append([f"versions:{mc_version}"])
        params = {"query": query, "limit": limit, "facets": json.dumps(facets)}
        url = "https://api.modrinth.com/v2/search?" + urllib.parse.urlencode(params)
        try:
            data = http_json(url)
            hits = [{"id": h["project_id"], "slug": h["slug"], "title": h["title"],
                     "description": h.get("description", ""),
                     "downloads": h.get("downloads", 0),
                     "icon": h.get("icon_url"), "author": h.get("author")}
                    for h in data.get("hits", [])]
            return {"status": "success", "hits": hits}
        except Exception as e:
            DEBUG.error("modrinth_search", e)
            return {"status": "error", "message": str(e)}

    def modrinth_install(self, instance, project_id, loader=None, mc_version=None):
        if not (INST / instance).exists(): return {"status": "error", "message": "Инстанс не найден"}
        meta = self._read_meta(instance)
        loader = loader or meta.get("loader")
        mc_version = mc_version or meta.get("version")
        if loader in ("vanilla", None):
            return {"status": "error", "message": "Для vanilla нельзя ставить моды"}
        if loader == "paper":
            loader = "bukkit"
        params = []
        if loader: params.append(f'loaders=["{loader}"]')
        if mc_version: params.append(f'game_versions=["{mc_version}"]')
        url = f"https://api.modrinth.com/v2/project/{project_id}/version"
        if params: url += "?" + "&".join(params)
        try:
            versions = http_json(url)
            if not versions: return {"status": "error", "message": "Нет версии"}
            f = versions[0]["files"][0]
            http_dl(f["url"], INST / instance / "mods" / f["filename"])
            return {"status": "success", "message": f"Установлен {f['filename']}"}
        except Exception as e:
            DEBUG.error("modrinth_install", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------ скин
    def pick_folder(self, title="Выберите папку"):
        """Системный диалог выбора папки (для путей серверов)."""
        try:
            root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
            p = filedialog.askdirectory(title=title)
            root.destroy()
            return p or ""
        except Exception as e:
            DEBUG.error("pick_folder", e)
            return ""

    def set_skin(self):
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        f = filedialog.askopenfilename(title="Скин (.png)", filetypes=[("PNG", "*.png")])
        root.destroy()
        if not f: return {"status": "error", "message": "Отменено"}
        shutil.copy2(f, SETTINGS_DIR / "skin.png")
        self.settings["elyby_skins"] = False   # свой скин важнее Ely.by
        self._save()
        return {"status": "success", "message": "Скин установлен",
                "skin_url": f"file:///{(SETTINGS_DIR / 'skin.png').as_posix()}"}

    def _sync_elyby_skin(self):
        """Скачивает скин Ely.by по нику в кэш. Возвращает Path или None."""
        nick = (self.settings.get("nickname") or "").strip()
        if not nick:
            return None
        cache = DATA / f"elyby_skin_{re.sub(r'[^A-Za-z0-9_]', '_', nick)}.png"
        if cache.exists():
            try:
                if cache.stat().st_size > 100 and time.time() - cache.stat().st_mtime < 600:
                    return cache
            except OSError:
                pass
        url = f"https://skinsystem.ely.by/skins/{urllib.parse.quote(nick)}.png"
        try:
            data = http_bytes(url, timeout=8, retries=1)
            if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 100:
                cache.write_bytes(data)
                return cache
        except Exception as e:
            DEBUG.warn(f"Ely.by скин для '{nick}': {e}")
        return cache if cache.exists() else None

    def get_skin_url(self):
        """URL скина для меню: Ely.by / свой скин, а если нет — классический Стив."""
        if self.settings.get("elyby_skins"):
            ep = self._sync_elyby_skin()
            if ep:
                return f"file:///{ep.as_posix()}"
        p = SETTINGS_DIR / "skin.png"
        if p.exists() and p.stat().st_size > 0:
            return f"file:///{p.as_posix()}"
        if DEFAULT_STEVE.exists():
            return f"file:///{DEFAULT_STEVE.as_posix()}"
        return None

    def has_custom_skin(self):
        p = SETTINGS_DIR / "skin.png"
        return p.exists() and p.stat().st_size > 0

    def get_elyby_skin(self):
        """Явная загрузка скина Ely.by (кнопка в настройках скина)."""
        nick = (self.settings.get("nickname") or "").strip()
        if not nick:
            return {"status": "error", "message": "Сначала укажите никнейм в настройках"}
        self.settings["elyby_skins"] = True
        self._save()
        p = self._sync_elyby_skin()
        if p:
            return {"status": "success", "message": f"Скин Ely.by загружен для {nick}",
                    "skin_url": f"file:///{p.as_posix()}"}
        return {"status": "error",
                "message": f"У '{nick}' нет скина на Ely.by (или нет интернета)"}

    # ------------------------------------------------ UPnP
    def enable_black_ip_patch(self, port=25565):
        try: import upnpclient
        except ImportError:
            return {"status": "error", "message": "pip install upnpclient"}
        try: devices = upnpclient.discover(timeout=3)
        except Exception as e:
            DEBUG.error("upnp discover", e); return {"status": "error", "message": str(e)}
        if not devices: return {"status": "error", "message": "UPnP устройств не найдено"}
        my = local_ip(); ok = False; last = None
        for dev in devices:
            for svc in getattr(dev, "services", []):
                st = getattr(svc, "service_type", "") or ""
                if "WANIPConnection" not in st and "WANPPPConnection" not in st: continue
                try:
                    svc.AddPortMapping(NewRemoteHost="", NewExternalPort=port,
                        NewProtocol="TCP", NewInternalPort=port, NewInternalClient=my,
                        NewEnabled="1", NewPortMappingDescription="BML", NewLeaseDuration=0)
                    ok = True
                except Exception as e: last = str(e)
        if ok:
            self.settings["black_ip_patch"] = True; self._save()
            return {"status": "success", "message": f"Порт {port} открыт для {my}"}
        return {"status": "error", "message": last or "Не удалось"}

    def disable_black_ip_patch(self, port=25565):
        try: import upnpclient
        except ImportError: return {"status": "error", "message": "upnpclient нет"}
        try: devices = upnpclient.discover(timeout=3)
        except Exception: devices = []
        for dev in devices:
            for svc in getattr(dev, "services", []):
                st = getattr(svc, "service_type", "") or ""
                if "WANIPConnection" not in st and "WANPPPConnection" not in st: continue
                try: svc.DeletePortMapping(NewRemoteHost="", NewExternalPort=port, NewProtocol="TCP")
                except Exception: pass
        self.settings["black_ip_patch"] = False; self._save()
        return {"status": "success", "message": "Порт закрыт"}

    # ------------------------------------------------ сетевые патчи BML
    _public_ip_cache = {"t": 0, "ip": None}

    def get_public_ip(self, force=False):
        """Публичный (белый) IP — для White IP Emulator / Grey IP Patch."""
        c = self._public_ip_cache
        if not force and c["ip"] and time.time() - c["t"] < 120:
            return c["ip"]
        for url in ("https://api.ipify.org", "https://ifconfig.me/ip",
                    "https://icanhazip.com"):
            try:
                ip = http_bytes(url, timeout=8, retries=1).decode().strip()
                if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip) or ":" in ip:
                    c.update(t=time.time(), ip=ip)
                    return ip
            except Exception:
                continue
        return None

    def _upnp_map(self, port, internal_ip=None, enable=True):
        """Проброс/удаление порта через UPnP. Возвращает (ok, message)."""
        try:
            import upnpclient
        except ImportError:
            return False, "Модуль upnpclient не установлен (pip install upnpclient)"
        try:
            devices = upnpclient.discover(timeout=3)
        except Exception as e:
            DEBUG.error("upnp discover", e)
            return False, str(e)
        if not devices:
            return False, "UPnP-устройства не найдены (роверьте роутер)"
        my = internal_ip or local_ip()
        ok, last = False, None
        for dev in devices:
            for svc in getattr(dev, "services", []):
                st = getattr(svc, "service_type", "") or ""
                if "WANIPConnection" not in st and "WANPPPConnection" not in st:
                    continue
                try:
                    if enable:
                        svc.AddPortMapping(NewRemoteHost="", NewExternalPort=port,
                            NewProtocol="TCP", NewInternalPort=port, NewInternalClient=my,
                            NewEnabled="1", NewPortMappingDescription="BML", NewLeaseDuration=0)
                    else:
                        svc.DeletePortMapping(NewRemoteHost="", NewExternalPort=port,
                                              NewProtocol="TCP")
                    ok = True
                except Exception as e:
                    last = str(e)
        return ok, (f"Порт {port} {'открыт' if enable else 'закрыт'} для {my}" if ok
                    else (last or "Не удалось"))

    def detect_game_ports(self):
        """TCP-порты, которые слушает процесс игры (java). Для Port Emulator."""
        ports = set()
        try:
            pid = (self.game_proc.pid
                   if self.game_proc and self.game_proc.poll() is None else None)
            if pid is None:
                return []
            for c in psutil.net_connections(kind="tcp"):
                if (c.status == psutil.CONN_LISTEN and c.pid == pid
                        and 1024 <= c.laddr.port <= 65535):
                    ports.add(c.laddr.port)
        except Exception as e:
            DEBUG.warn(f"detect_game_ports: {e}")
        return sorted(ports)

    def get_network_patches(self):
        """Статус сетевых патчей для UI."""
        return {
            "local_ip": local_ip(),
            "public_ip": self.get_public_ip(),
            "white_ip_emulator": bool(self.settings.get("white_ip_emulator")),
            "port_emulator": bool(self.settings.get("port_emulator")),
            "elyby_skins": bool(self.settings.get("elyby_skins")),
            "things_lite": bool(self.settings.get("things_lite")),
            "game_ports": self.detect_game_ports(),
            "upnp": self._upnp_available(),
        }

    def _upnp_available(self):
        try:
            import upnpclient  # noqa
            return True
        except ImportError:
            return False

    def enable_port_emulator(self, port=None):
        """Port Emulator: авто-проброс порта игры через UPnP."""
        self.settings["port_emulator"] = True
        self._save()
        ports = [port] if port else self.detect_game_ports()
        if not ports:
            return {"status": "success",
                    "message": "Port Emulator включён. Порт определится, "
                               "когда откроете мир по сети."}
        results = []
        for p in ports:
            ok, msg = self._upnp_map(p, enable=True)
            results.append((p, ok, msg))
        good = [r for r in results if r[1]]
        if good:
            return {"status": "success",
                    "message": "Port Emulator: " + ", ".join(f"порт {p} — ок" for p, _, _ in good)}
        return {"status": "error",
                "message": results[0][2] if results else "Не удалось пробросить порт"}

    def disable_port_emulator(self, port=None):
        self.settings["port_emulator"] = False
        self._save()
        for p in ([port] if port else self.detect_game_ports()):
            self._upnp_map(p, enable=False)
        return {"status": "success", "message": "Port Emulator выключен"}

    def enable_white_ip_emulator(self):
        """White IP Emulator (Grey IP Patch): готовый адрес для друзей."""
        self.settings["white_ip_emulator"] = True
        self._save()
        pub = self.get_public_ip(force=True)
        local = local_ip()
        ports = self.detect_game_ports()
        if ports:
            for p in ports:
                self._upnp_map(p, enable=True)
        addr = f"{pub}:{ports[0]}" if (pub and ports) else (pub or local)
        return {"status": "success",
                "message": (f"White IP Emulator включён. Передай друзьям адрес:\n{addr}"
                            if pub else
                            "White IP Emulator включён, но публичный IP не определён. "
                            "Проверьте интернет."),
                "public_ip": pub, "ports": ports}

    def disable_white_ip_emulator(self):
        self.settings["white_ip_emulator"] = False
        self._save()
        return {"status": "success", "message": "White IP Emulator выключен"}

    def get_share_address(self):
        """Адрес для друзей с учётом White IP Emulator."""
        pub = self.get_public_ip(force=not bool(self._public_ip_cache.get("ip")))
        local = local_ip()
        ports = self.detect_game_ports()
        port = ports[0] if ports else 25565
        return {"public_ip": pub, "local_ip": local, "port": port,
                "address": (f"{pub}:{port}" if (pub and self.settings.get("white_ip_emulator"))
                            else f"{local}:{port}")}

    # --- фоновый Port Emulator: пробрасывает порт, когда мир открыт по сети ---
    def start_net_patch_watcher(self):
        if not (self.settings.get("port_emulator")
                or self.settings.get("white_ip_emulator")):
            return
        if self._net_watch_thread and self._net_watch_thread.is_alive():
            return
        self._net_watch_stop.clear()
        self._net_watch_thread = threading.Thread(target=self._net_patch_loop, daemon=True)
        self._net_watch_thread.start()

    def stop_net_patch_watcher(self):
        self._net_watch_stop.set()
        self._net_watch_thread = None

    def _net_patch_loop(self):
        DEBUG.info("Сетевые патчи: жду открытия мира по сети...")
        while not self._net_watch_stop.wait(3):
            if not self.game_proc or self.game_proc.poll() is not None:
                break
            for p in self.detect_game_ports():
                if p in self._mapped_ports or p < 1024 or 34560 <= p <= 34580:
                    continue
                ok, _ = self._upnp_map(p, enable=True)
                self._mapped_ports[p] = ok
                if ok:
                    pub = self.get_public_ip()
                    addr = f"{pub}:{p}" if pub else f"{local_ip()}:{p}"
                    DEBUG.info(f"Port Emulator: порт {p} открыт — {addr}")
                    try:
                        if self.window:
                            self.window.evaluate_js(
                                "window.onNetPatch && window.onNetPatch("
                                + json.dumps({"port": p, "public_ip": pub, "address": addr})
                                + ")")
                    except Exception:
                        pass
        # игра закрылась — убираем пробросы
        for p in list(self._mapped_ports):
            try:
                self._upnp_map(p, enable=False)
            except Exception:
                pass
        self._mapped_ports.clear()

    # ------------------------------------------------ GitHub
    def _gh(self, path, timeout=15, retries=3):
        """GET к GitHub API с ретраями. Возвращает разобранный JSON."""
        url = path if path.startswith("http") else f"{GITHUB_API}{path}"
        last = None
        for i in range(retries):
            try:
                req = urllib.request.Request(url, headers=_gh_headers())
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read().decode("utf-8", errors="replace"))
            except Exception as e:
                last = e
                time.sleep(1.0 + i * 1.5)
        raise last

    def _gh_text(self, url, timeout=15):
        """GET без лимитов (raw / atom)."""
        req = urllib.request.Request(url, headers={"User-Agent": GH_HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")

    def _gh_atom(self, url):
        """Разбирает Atom-фид (releases.atom / commits.atom) без API."""
        try:
            xml = self._gh_text(url)
        except Exception as e:
            DEBUG.warn(f"atom {url}: {e}")
            return []
        out = []
        for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
            title = re.search(r"<title>(.*?)</title>", entry, re.S)
            updated = re.search(r"<updated>(.*?)</updated>", entry, re.S)
            link = re.search(r'<link[^>]*href="([^"]+)"', entry, re.S)
            author = re.search(r"<name>(.*?)</name>", entry, re.S)
            out.append({
                "title": (title.group(1).strip() if title else ""),
                "updated": (updated.group(1).strip() if updated else ""),
                "url": (link.group(1) if link else ""),
                "author": (author.group(1).strip() if author else ""),
            })
        return out

    def _gh_fallback(self, out):
        """Запасной источник данных, когда API уперся в rate limit."""
        out.setdefault("releases", [])
        out.setdefault("commits", [])
        out.setdefault("contributors", [])
        out.setdefault("files", [])
        out.setdefault("languages", [])
        out.setdefault("readme", "")

        if not out["releases"]:
            for e in self._gh_atom(f"{GITHUB_URL}/releases.atom"):
                tag = e["title"]
                out["releases"].append({
                    "tag": tag, "name": tag, "body": "",
                    "published_at": e["updated"], "prerelease": False,
                    "url": e["url"], "assets": [],
                })
        if not out["commits"]:
            branch = out.get("default_branch") or "main"
            for e in self._gh_atom(f"{GITHUB_URL}/commits/{branch}.atom"):
                out["commits"].append({
                    "sha": e["url"].rstrip("/").split("/")[-1][:7] if e["url"] else "",
                    "message": e["title"],
                    "author": e["author"],
                    "date": e["updated"],
                    "url": e["url"],
                })
        if not out["readme"]:
            try:
                out["readme"] = self._gh_text(f"{GITHUB_RAW}/README.md")[:8000]
            except Exception:
                pass
        if not out["files"]:
            try:
                out["files"] = [{"name": "README.md", "type": "file", "size": 0,
                                 "url": f"{GITHUB_URL}/blob/main/README.md"}]
            except Exception:
                pass

        # основная инфо о репо — со страницы GitHub (без API и лимитов)
        try:
            html = self._gh_text(GITHUB_URL, timeout=20)
            m = re.search(r'"stargazerCount":(\d+)', html)
            if m:
                out.setdefault("stars", int(m.group(1)))
                out["stars"] = int(m.group(1))
            m = re.search(r'"forkCount":(\d+)', html)
            if m:
                out["forks"] = int(m.group(1))
            else:
                out.setdefault("forks", 0)
            out.setdefault("stars", 0)
            out.setdefault("open_issues", 0)
            m = re.search(r'<meta name="description" content="Contribute to [^"]*?'
                          r'development by creating an account on GitHub\."', html)
            if m:
                out["name"] = out.get("name") or f"{GITHUB_OWNER}/{GITHUB_REPO}"
            m = re.search(r'<meta property="og:description" content="([^"]*)"', html)
            if m and m.group(1).strip():
                desc = m.group(1).strip()
                if desc.lower() not in ("contribute to %s/%s development by creating "
                                        "an account on github." %
                                        (GITHUB_OWNER.lower(), GITHUB_REPO.lower()),):
                    out["description"] = desc
            out.setdefault("name", f"{GITHUB_OWNER}/{GITHUB_REPO}")
            out.setdefault("default_branch", "main")
        except Exception as e:
            DEBUG.warn(f"GitHub page fallback: {e}")

        out["ok"] = True
        out["fallback"] = True
        return out

    def get_github_info(self, force=False):
        """Собирает реальную инфу о репозитории через GitHub API.

        GitHub без токена даёт 60 запросов/час, поэтому кэшируем на 30 минут
        и переживаем rate limit, отдавая последние закэшированные данные.
        """
        cache = DATA / "github_cache.json"
        cached = None
        if cache.exists():
            try:
                cached = json.loads(cache.read_text(encoding="utf-8"))
            except Exception:
                cached = None
        if not force and cached and time.time() - cache.stat().st_mtime < 1800:
            return cached
        out = {
            "repo": GITHUB_OWNER + "/" + GITHUB_REPO,
            "url": GITHUB_URL,
            "app_version": APP_VERSION,
            "ok": False, "error": "", "rate_limited": False,
        }
        try:
            repo = self._gh("")
            out["ok"] = True
            out.update({
                "name": repo.get("full_name") or "",
                "description": repo.get("description") or "",
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "watchers": repo.get("subscribers_count", repo.get("watchers_count", 0)),
                "open_issues": repo.get("open_issues_count", 0),
                "language": repo.get("language") or "",
                "license": (repo.get("license") or {}).get("spdx_id") or "",
                "default_branch": repo.get("default_branch") or "main",
                "created_at": repo.get("created_at") or "",
                "updated_at": repo.get("updated_at") or "",
                "pushed_at": repo.get("pushed_at") or "",
                "homepage": repo.get("homepage") or "",
                "topics": repo.get("topics") or [],
                "size": repo.get("size", 0),
                "archived": bool(repo.get("archived")),
            })
        except Exception as e:
            out["error"] = str(e)
            out["rate_limited"] = ("403" in str(e) and "rate limit" in str(e).lower())
            DEBUG.warn(f"GitHub repo: {e}")
            # отдаём прошлые данные, если они есть
            if cached:
                merged = dict(cached)
                merged["stale"] = True
                merged["error"] = out["error"]
                merged["rate_limited"] = out["rate_limited"]
                return merged
            # запасной источник — Atom-фиды (без лимитов)
            try:
                out = self._gh_fallback(out)
            except Exception as e2:
                DEBUG.warn(f"GitHub fallback: {e2}")
            out["update_available"] = self._check_update(out)
            try:
                cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
            return out

        # релизы
        try:
            rels = self._gh("/releases?per_page=10", retries=1)
            out["releases"] = [{
                "tag": r.get("tag_name") or "",
                "name": r.get("name") or r.get("tag_name") or "",
                "body": (r.get("body") or "")[:2000],
                "published_at": r.get("published_at") or "",
                "prerelease": bool(r.get("prerelease")),
                "url": r.get("html_url") or "",
                "assets": [{"name": a.get("name"), "size": a.get("size"),
                            "url": a.get("browser_download_url")}
                           for a in (r.get("assets") or [])],
            } for r in (rels or [])]
        except Exception as e:
            out["releases"] = []
            DEBUG.warn(f"GitHub releases: {e}")

        # теги (если релизов нет)
        if not out.get("releases"):
            try:
                tags = self._gh("/tags?per_page=10")
                out["releases"] = [{
                    "tag": t.get("name") or "", "name": t.get("name") or "",
                    "body": "", "published_at": "", "prerelease": False,
                    "url": f"{GITHUB_URL}/releases/tag/{t.get('name')}",
                    "assets": [],
                } for t in (tags or [])]
            except Exception:
                out["releases"] = []

        # последние коммиты
        try:
            cms = self._gh("/commits?per_page=10", retries=1)
            out["commits"] = [{
                "sha": (c.get("sha") or "")[:7],
                "message": ((c.get("commit") or {}).get("message") or "").split("\n")[0],
                "author": (((c.get("commit") or {}).get("author") or {}).get("name") or ""),
                "date": (((c.get("commit") or {}).get("author") or {}).get("date") or ""),
                "url": c.get("html_url") or "",
            } for c in (cms or [])]
        except Exception as e:
            out["commits"] = []
            DEBUG.warn(f"GitHub commits: {e}")

        # контрибьюторы
        try:
            cs = self._gh("/contributors?per_page=20", retries=1)
            out["contributors"] = [{
                "login": c.get("login") or "",
                "avatar": c.get("avatar_url") or "",
                "contributions": c.get("contributions", 0),
                "url": c.get("html_url") or "",
            } for c in (cs or [])]
        except Exception:
            out["contributors"] = []

        # содержимое корня
        try:
            ct = self._gh("/contents/", retries=1)
            out["files"] = [{
                "name": f.get("name") or "",
                "type": f.get("type") or "",
                "size": f.get("size", 0),
                "url": f.get("html_url") or "",
            } for f in (ct or [])]
        except Exception:
            out["files"] = []

        # языки
        try:
            langs = self._gh("/languages", retries=1)
            total = sum(langs.values()) or 1
            out["languages"] = [{"name": k, "bytes": v,
                                  "percent": round(v * 100.0 / total, 1)}
                                 for k, v in sorted(langs.items(),
                                                    key=lambda x: -x[1])]
        except Exception:
            out["languages"] = []

        # README
        try:
            readme = self._gh("/readme", retries=1)
            out["readme_name"] = readme.get("name") or "README.md"
            out["readme_url"] = readme.get("html_url") or ""
            raw = readme.get("download_url") or ""
            if raw:
                req = urllib.request.Request(raw, headers=_gh_headers())
                with urllib.request.urlopen(req, timeout=15) as r:
                    out["readme"] = r.read().decode("utf-8", errors="replace")[:8000]
        except Exception:
            out["readme"] = ""

        # если часть секций не загрузилась (rate limit) — добираем из Atom
        if not out.get("commits") or not out.get("readme"):
            try:
                self._gh_fallback(out)
            except Exception:
                pass

        # проверка обновления
        out["update_available"] = self._check_update(out)
        try:
            cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
        return out

    @staticmethod
    def _ver_tuple(v):
        nums = re.findall(r"\d+", str(v or ""))
        return tuple(int(x) for x in nums[:4]) or (0,)

    def _check_update(self, gh_info=None):
        """Сравнивает текущую версию с последним релизом на GitHub."""
        try:
            if gh_info is None:
                gh_info = self.get_github_info()
            rels = gh_info.get("releases") or []
            latest = None
            for r in rels:
                v = self._ver_tuple(r.get("tag") or r.get("name"))
                if v and (latest is None or v > self._ver_tuple(latest.get("tag") or latest.get("name"))):
                    latest = r
            if not latest:
                return {"available": False, "current": APP_VERSION,
                        "latest": "", "url": GITHUB_URL}
            latest_ver = self._ver_tuple(latest.get("tag") or latest.get("name"))
            cur_ver = self._ver_tuple(APP_VERSION)
            return {
                "available": latest_ver > cur_ver,
                "current": APP_VERSION,
                "latest": latest.get("tag") or latest.get("name"),
                "url": latest.get("url") or GITHUB_URL,
            }
        except Exception as e:
            DEBUG.warn(f"check update: {e}")
            return {"available": False, "current": APP_VERSION, "latest": "", "url": GITHUB_URL}

    def check_for_update(self):
        """Лёгкая проверка обновления: 1 запрос к /releases/latest."""
        try:
            try:
                rel = self._gh("/releases/latest", retries=2)
                latest = rel.get("tag_name") or rel.get("name") or ""
                url = rel.get("html_url") or GITHUB_URL
            except Exception:
                # нет релизов — пробуем теги
                rel = self._gh("/tags?per_page=1", retries=2)
                latest = (rel[0].get("name") if rel else "") or ""
                url = f"{GITHUB_URL}/releases" if latest else GITHUB_URL
            if not latest:
                return {"available": False, "current": APP_VERSION,
                        "latest": "", "url": GITHUB_URL}
            return {
                "available": self._ver_tuple(latest) > self._ver_tuple(APP_VERSION),
                "current": APP_VERSION, "latest": latest, "url": url,
            }
        except Exception as e:
            DEBUG.warn(f"check_for_update: {e}")
            # fallback на кэш
            try:
                return self._check_update(self.get_github_info())
            except Exception:
                return {"available": False, "current": APP_VERSION,
                        "latest": "", "url": GITHUB_URL}

    def open_github(self):
        """Открывает репозиторий в браузере."""
        try:
            import webbrowser
            webbrowser.open(GITHUB_URL)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------ серверы
    def server_base(self) -> Path:
        """Базовая папка серверов: из настроек или дефолтная."""
        custom = (self.settings.get("default_server_path") or "").strip()
        if custom:
            p = Path(custom)
            try:
                p.mkdir(parents=True, exist_ok=True)
                return p
            except Exception as e:
                DEBUG.warn(f"default_server_path '{custom}' недоступен: {e}")
        return SRV_INST

    def _srv_index_load(self) -> dict:
        if SRV_INDEX.exists():
            try:
                return json.loads(SRV_INDEX.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _srv_index_save(self, idx: dict):
        SRV_INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")

    def _srv_index_set(self, name, path):
        idx = self._srv_index_load()
        idx[name] = str(path)
        self._srv_index_save(idx)

    def _srv_index_del(self, name):
        idx = self._srv_index_load()
        if name in idx:
            del idx[name]
            self._srv_index_save(idx)

    def _iter_server_dirs(self):
        """Все папки серверов: из реестра + базовая + старый дефолт."""
        seen = set()
        for p in list(self._srv_index_load().values()) + \
                 [str(self.server_base()), str(SRV_INST)]:
            try:
                root = Path(p)
            except Exception:
                continue
            if not root.is_dir():
                continue
            candidates = []
            if (root / "server.json").exists():
                candidates.append(root)
            try:
                candidates += [x for x in root.iterdir()
                               if x.is_dir() and (x / "server.json").exists()]
            except OSError:
                pass
            for d in candidates:
                if d not in seen:
                    seen.add(d)
                    yield d

    def _load_existing_servers(self):
        for d in self._iter_server_dirs():
            if (d / "server.json").exists():
                try:
                    m = json.loads((d / "server.json").read_text(encoding="utf-8"))
                    si = ServerInstance(m.get("name", d.name), d)
                    self.servers[si.name] = si
                except Exception:
                    pass

    def _server_dir(self, name, custom=None):
        if custom:
            p = Path(custom) / name if (Path(custom).name != name) else Path(custom)
        else:
            p = self.server_base() / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def create_server(self, name, core="paper", version="1.20.1", ram=4, port=25565,
                      pirate=False, seed="", path=""):
        name = (name or "").strip()
        if not name: return {"status": "error", "message": "Пустое имя"}
        if re.search(r'[<>:"/\\|?*]', name):
            return {"status": "error", "message": "Имя содержит запрещённые символы"}
        if name in self.servers: return {"status": "error", "message": "Уже есть"}
        p = self._server_dir(name, (path or "").strip() or None)
        meta = {"name": name, "core": core, "version": version, "ram": ram,
                "port": port, "pirate": pirate, "seed": seed,
                "motd": f"Better Millida Server - {name}",
                "custom_path": (path or "").strip(),
                "rcon_enabled": False, "rcon_port": 25575, "rcon_password": ""}
        (p / "server.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        self._write_server_properties(p, meta)
        self._srv_index_set(name, p)
        self.servers[name] = ServerInstance(name, p)
        return {"status": "success", "message": f"Сервер '{name}' создан"}

    def _write_server_properties(self, path: Path, meta):
        props = {
            "server-port": meta.get("port", 25565),
            "motd": meta.get("motd", "BML Server"),
            "online-mode": "false" if meta.get("pirate") else "true",
            "level-seed": meta.get("seed", ""),
            "enable-rcon": "true" if meta.get("rcon_enabled") else "false",
            "rcon.port": meta.get("rcon_port", 25575),
            "rcon.password": meta.get("rcon_password", ""),
            "enable-command-block": "true",
            "spawn-protection": "0",
            "max-players": "20",
            "gamemode": "survival",
            "difficulty": "normal",
        }
        with open(path / "server.properties", "w", encoding="utf-8") as f:
            for k, v in props.items():
                f.write(f"{k}={v}\n")

    def list_servers(self):
        out = []
        for name, si in self.servers.items():
            try:
                meta = json.loads((si.path / "server.json").read_text(encoding="utf-8"))
            except Exception:
                meta = {}
            out.append({
                "name": name,
                "core": meta.get("core", "?"),
                "version": meta.get("version", "?"),
                "ram": meta.get("ram", 4),
                "port": meta.get("port", 25565),
                "pirate": meta.get("pirate", False),
                "running": si.running and si.proc and si.proc.poll() is None,
                "players": len(si.players),
                "installed": any(j for j in si.path.glob("*.jar")
                                 if "installer" not in j.name.lower()),
            })
        return out

    def get_server(self, name):
        if name not in self.servers: return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        try:
            meta = json.loads((si.path / "server.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        meta["running"] = si.running and si.proc and si.proc.poll() is None
        meta["players"] = list(si.players.keys())
        meta["path"] = str(si.path)
        meta["base_path"] = str(si.path.parent)
        meta["default_base"] = str(self.server_base())
        return {"status": "success", "server": meta}

    def delete_server(self, name):
        if name not in self.servers: return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        if si.proc and si.proc.poll() is None:
            return {"status": "error", "message": "Остановите сервер сначала"}
        shutil.rmtree(si.path, ignore_errors=True)
        self._srv_index_del(name)
        del self.servers[name]
        return {"status": "success"}

    def update_server(self, name, data=None):
        if name not in self.servers:
            return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        meta_path = si.path / "server.json"
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {"name": name}
        new_path = None
        if data:
            for k, v in data.items():
                if v is not None:
                    meta[k] = v
            new_path = (data.get("custom_path") or "").strip() or None

        # перенос в другую папку, если путь сменился и сервер не запущен
        if new_path is not None and new_path != str(si.path.parent) and new_path != str(si.path):
            if si.proc and si.proc.poll() is None:
                return {"status": "error", "message": "Остановите сервер перед сменой пути"}
            target = Path(new_path)
            if target.name != name:
                target = target / name
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if si.path.exists() and si.path != target:
                    shutil.move(str(si.path), str(target))
                si.path = target
                meta_path = target / "server.json"
                meta["custom_path"] = new_path
                self._srv_index_set(name, target)
            except Exception as e:
                DEBUG.error("server move", e)
                return {"status": "error", "message": f"Не удалось перенести: {e}"}

        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        self._write_server_properties(si.path, meta)
        return {"status": "success"}

    def start_server_card(self, name):
        if name not in self.servers: return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        if si.proc and si.proc.poll() is None:
            return {"status": "error", "message": "Уже запущен"}
        try:
            meta = json.loads((si.path / "server.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}

        version = meta.get("version", "1.20.1")
        jr = self.ensure_java(version)
        if jr["status"] != "success":
            return {"status": "error", "message": jr.get("message", "Нужна Java")}
        java_bin = jr["path"]

        jar_files = [j for j in si.path.glob("*.jar")
                     if "installer" not in j.name.lower()]
        if not jar_files:
            core = meta.get("core", "paper")
            jar = si.path / f"{core}-{version}.jar"
            try:
                self.progress.start(f"Скачивание ядра {core} {version}")
                self._dl_server_core(core, version, jar)
            except Exception as e:
                DEBUG.error("server core dl", e)
                return {"status": "error", "message": f"Не удалось скачать ядро: {e}"}
            finally:
                self.progress.finish()
            jar_files = [jar]

        (si.path / "eula.txt").write_text("eula=true\n", encoding="utf-8")

        ram = max(1, min(int(meta.get("ram", 4)), 16))
        xms = min(2, ram)
        cmd = [java_bin, f"-Xmx{ram}G", f"-Xms{xms}G", "-jar", str(jar_files[0]), "nogui"]
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        try:
            si.proc = subprocess.Popen(
                cmd, cwd=str(si.path), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=flags, bufsize=0)
        except Exception as e:
            DEBUG.error("start_server_card", e)
            return {"status": "error", "message": str(e)}

        si.running = True
        si.start_time = time.time()
        si.append(f"[BML] Server starting: {meta.get('core')} {meta.get('version')}")
        # Network patches: Port Emulator / White IP при старте выделенного сервера
        try:
            port = meta.get("port", 25565)
            if self.settings.get("port_emulator") or self.settings.get("white_ip_emulator"):
                self._upnp_map(port, enable=True)
        except Exception:
            pass

        si._reader_thread = threading.Thread(target=self._read_server_stdout,
                                              args=(si,), daemon=True)
        si._reader_thread.start()
        return {"status": "success", "message": f"Сервер '{name}' запущен"}

    def _read_server_stdout(self, si: ServerInstance):
        try:
            for raw in iter(si.proc.stdout.readline, b""):
                if not raw: break
                line = raw.decode("utf-8", errors="replace").rstrip()
                if line: si.append(line)
        except Exception as e:
            DEBUG.error("server reader", e)
        finally:
            si.running = False
            si.append("[BML] Server stopped")

    def stop_server_card(self, name):
        if name not in self.servers: return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        if not (si.proc and si.proc.poll() is None):
            return {"status": "error", "message": "Не запущен"}
        try:
            si.send("stop")
            try: si.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                si.proc.terminate()
                try: si.proc.wait(timeout=5)
                except subprocess.TimeoutExpired: si.proc.kill()
        except Exception as e:
            DEBUG.error("stop_server_card", e)
        si.running = False
        # Снимаем проброс при остановке сервера (по желанию)
        try:
            meta = json.loads((si.path / "server.json").read_text(encoding="utf-8"))
            port = meta.get("port", 25565)
            if self.settings.get("port_emulator") or self.settings.get("white_ip_emulator"):
                self._upnp_map(port, enable=False)
        except Exception:
            pass
        return {"status": "success", "message": "Сервер остановлен"}

    def send_server_command(self, name, cmd):
        if name not in self.servers: return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        if si.send(cmd):
            si.append(f"[BML/CMD] > {cmd}")
            return {"status": "success"}
        return {"status": "error", "message": "Сервер не запущен"}

    def get_server_console(self, name, since=0):
        if name not in self.servers: return {"lines": [], "players": [], "running": False}
        si = self.servers[name]
        return {"lines": si.tail(since), "players": list(si.players.keys()),
                "running": si.running and si.proc and si.proc.poll() is None}

    def _dl_server_core(self, core, version, target: Path):
        if core == "paper":
            bd = http_json(f"https://fill.papermc.io/v3/projects/paper/versions/"
                           f"{version}/builds/latest")
            dl = (bd.get("downloads") or {}).get("server:default")
            if not dl or not dl.get("url"):
                raise Exception(f"Paper {version}: нет сборки для скачивания")
            self.progress.start(f"Скачивание Paper {version}", 1)
            http_dl(dl["url"], target)
            self.progress.add(1)
            sha = (dl.get("checksums") or {}).get("sha256")
            if sha:
                h = hashlib.sha256()
                with open(target, "rb") as fh:
                    for c in iter(lambda: fh.read(65536), b""):
                        h.update(c)
                if h.hexdigest() != sha:
                    target.unlink(missing_ok=True)
                    raise Exception("Контрольная сумма Paper не совпала")
        elif core == "vanilla":
            vd = self._version_meta(version)
            dl = (vd.get("downloads") or {}).get("server")
            if not dl: raise Exception(f"Версия {version} без server jar")
            self.progress.start(f"Скачивание сервера {version}", 1)
            http_dl(dl["url"], target)
            self.progress.add(1)
        elif core == "fabric":
            lv = http_json("https://meta.fabricmc.net/v2/versions/loader")[0]["version"]
            http_dl(f"https://meta.fabricmc.net/v2/versions/loader/{version}/{lv}/server/jar", target)
        elif core == "quilt":
            lv = http_json("https://meta.quiltmc.org/v3/versions/loader")[0]["version"]
            http_dl(f"https://meta.quiltmc.org/v3/versions/loader/{version}/{lv}/server/jar", target)
        else:
            raise Exception(f"Ядро {core} не поддерживается")

    def rcon_command(self, name, cmd):
        if name not in self.servers: return {"status": "error", "message": "Не найден"}
        try:
            meta = json.loads((self.servers[name].path / "server.json").read_text(encoding="utf-8"))
        except Exception:
            return {"status": "error", "message": "Мета не читается"}
        if not meta.get("rcon_enabled"):
            return {"status": "error", "message": "RCON отключён"}
        try:
            rc = RconClient("127.0.0.1", meta.get("rcon_port", 25575),
                            meta.get("rcon_password", ""))
            if not rc.connect():
                return {"status": "error", "message": "RCON auth failed"}
            resp = rc.command(cmd)
            rc.close()
            return {"status": "success", "response": resp}
        except Exception as e:
            DEBUG.error("rcon", e)
            return {"status": "error", "message": str(e)}

    def give_item(self, server, player, item, count=1):
        return self.send_server_command(server, f"give {player} {item} {count}")
    def op_player(self, server, player):
        return self.send_server_command(server, f"op {player}")
    def deop_player(self, server, player):
        return self.send_server_command(server, f"deop {player}")
    def kick_player(self, server, player, reason="Kicked by admin"):
        return self.send_server_command(server, f"kick {player} {reason}")
    def ban_player(self, server, player):
        return self.send_server_command(server, f"ban {player}")
    def pardon_player(self, server, player):
        return self.send_server_command(server, f"pardon {player}")
    def whitelist_add(self, server, player):
        return self.send_server_command(server, f"whitelist add {player}")
    def whitelist_remove(self, server, player):
        return self.send_server_command(server, f"whitelist remove {player}")
    def tp_player(self, server, player, target):
        return self.send_server_command(server, f"tp {player} {target}")
    def gamemode_player(self, server, player, mode):
        return self.send_server_command(server, f"gamemode {mode} {player}")

    # ------------------------------------------------ шеринг
    def get_server_share_address(self, name):
        """Адрес сервера для друзей (с учётом Port/White IP Emulator)."""
        if name not in self.servers:
            return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        try:
            meta = json.loads((si.path / "server.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        port = meta.get("port", 25565)
        if self.settings.get("port_emulator") or self.settings.get("white_ip_emulator"):
            self._upnp_map(port, enable=True)
        white = bool(self.settings.get("white_ip_emulator"))
        host = (self.get_public_ip() or local_ip()) if white else local_ip()
        return {"status": "success", "host": host, "local_ip": local_ip(),
                "port": port, "white_ip": white,
                "address": f"{host}:{port}"}

    def start_server_network_patch(self, name):
        """Ручное включение Port/White IP для выделенного сервера."""
        if name not in self.servers:
            return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        try:
            meta = json.loads((si.path / "server.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        port = meta.get("port", 25565)
        ok1, m1 = self._upnp_map(port, enable=True)
        pub = self.get_public_ip(force=True) if self.settings.get("white_ip_emulator") else None
        host = pub if pub else local_ip()
        return {"status": "success" if ok1 else "warn",
                "message": f"Порт {port} проброшен через UPnP. Адрес: {host}:{port}",
                "address": f"{host}:{port}", "port": port,
                "white_ip": bool(self.settings.get("white_ip_emulator")),
                "upnp": ok1}

    def stop_server_network_patch(self, name):
        if name not in self.servers:
            return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        try:
            meta = json.loads((si.path / "server.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        port = meta.get("port", 25565)
        ok, m = self._upnp_map(port, enable=False)
        return {"status": "success" if ok else "warn",
                "message": m or f"Проброс порта {port} снят"}

    def start_sharing(self, name):
        if name not in self.servers: return {"status": "error", "message": "Не найден"}
        si = self.servers[name]
        try:
            meta = json.loads((si.path / "server.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        port = meta.get("port", 25565)
        # Port Emulator / White IP Emulator: пробрасываем порт и отдаём белый IP
        if self.settings.get("port_emulator") or self.settings.get("white_ip_emulator"):
            self._upnp_map(port, enable=True)
        host = local_ip()
        if self.settings.get("white_ip_emulator"):
            host = self.get_public_ip() or host
        info = {
            "host": host,
            "local_host": local_ip(),
            "port": port,
            "version": meta.get("version", "?"),
            "core": meta.get("core", "?"),
            "motd": meta.get("motd", ""),
            "nick": self.settings.get("nickname", ""),
            "bml": True,
            "white_ip": bool(self.settings.get("white_ip_emulator")),
            "port_emulator": bool(self.settings.get("port_emulator")),
        }
        if self.share_server:
            try:
                self.share_server.info = info
                return {"status": "success",
                        "message": f"Уже расшарен. IP: {info['host']}:25999"}
            except Exception:
                pass
        import http.server, socketserver

        class ReuseTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/server-info":
                    body = json.dumps(self.server.info).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404); self.end_headers()
            def log_message(self, *a): pass

        try:
            srv = ReuseTCPServer(("0.0.0.0", 25999), Handler)
            srv.info = info
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            self.share_server = srv
            return {"status": "success",
                    "message": f"Сервер расшарен. IP: {info['host']}:25999"}
        except OSError as e:
            DEBUG.error("share", e)
            return {"status": "error",
                    "message": f"Порт 25999 занят ({e}). Закройте программу, "
                               f"использующую его, и попробуйте снова."}
        except Exception as e:
            DEBUG.error("share", e)
            return {"status": "error", "message": str(e)}

    def join_shared_server(self, host):
        try:
            url = f"http://{host}:25999/server-info"
            data = http_json(url, timeout=5, retries=1)
            return {"status": "success", "info": data}
        except Exception as e:
            DEBUG.error("join_shared", e)
            return {"status": "error", "message": f"Не удалось подключиться к {host}: {e}"}

    # ------------------------------------------------ запуск игры
    def launch_instance(self, name):
        if not (INST / name).exists(): return {"status": "error", "message": "Инстанс не найден"}
        meta = self._read_meta(name)
        target = INST / name
        if not ((target / "version.json").exists() or (target / "loader.json").exists()):
            return {"status": "error", "message": "Сначала скачайте инстанс (кнопка «Скачать»)"}
        if self.game_proc and self.game_proc.poll() is None:
            return {"status": "error", "message": "Игра уже запущена"}
        self.progress.start(f"Запуск {name}")
        try:
            vdata = self._resolve_vdata(target, meta)
            # докачиваем недостающее (библиотеки/ассеты) — быстро, если всё есть
            client_jar, libs, logp = self._install_game_files(target, vdata, self.progress)

            nick = (self.settings.get("nickname") or "").strip()
            if not nick:
                nick = "Player"
            uuid = "00000000000000000000000000000000"
            token = "0"
            asset_index = (vdata.get("assetIndex") or {}).get("id", "")
            assets_root = str(ASSETS)

            sep = ";" if os.name == "nt" else ":"
            if libs and not any(Path(c) == client_jar for c in libs):
                libs = libs + [str(client_jar)]
            elif not libs:
                libs = [str(client_jar)]
            cp_str = sep.join(libs)

            args_raw = vdata.get("arguments", {})
            jvm_args, game_args = [], []
            for a in args_raw.get("jvm", []):
                if isinstance(a, str): jvm_args.append(a)
                elif isinstance(a, dict):
                    if "rules" in a and not self._rules_allow(a["rules"]): continue
                    v = a.get("value")
                    if isinstance(v, list): jvm_args.extend(v)
                    elif isinstance(v, str): jvm_args.append(v)
            for a in args_raw.get("game", []):
                if isinstance(a, str): game_args.append(a)
                elif isinstance(a, dict):
                    if "rules" in a and not self._rules_allow(a["rules"]): continue
                    v = a.get("value")
                    if isinstance(v, list): game_args.extend(v)
                    elif isinstance(v, str): game_args.append(v)
            if not game_args and "minecraftArguments" in vdata:
                game_args = vdata["minecraftArguments"].split()
            if not jvm_args:
                jvm_args = ["-Djava.library.path=${natives_directory}", "-cp", "${classpath}"]

            natives_dir = target / "natives"
            libs_dir = target / "libraries"
            game_id = vdata.get("id", meta["version"])

            vars_map = {
                "${auth_player_name}": nick,
                "${version_name}": game_id,
                "${game_directory}": str(target),
                "${assets_root}": assets_root,
                "${assets_index_name}": asset_index,
                "${auth_uuid}": uuid,
                "${auth_access_token}": token,
                "${auth_session}": token,
                "${user_type}": "legacy",
                "${version_type}": vdata.get("type", "release"),
                "${user_properties}": "{}",
                "${clientid}": "0",
                "${auth_xuid}": "0",
                "${launcher_name}": "BetterMillida",
                "${launcher_version}": "4.0",
                "${classpath}": cp_str,
                "${classpath_separator}": sep,
                "${library_directory}": str(libs_dir),
                "${natives_directory}": str(natives_dir),
                "${game_assets}": assets_root,
                "${primary_jar}": str(client_jar),
            }
            if logp:
                vars_map["${path}"] = str(logp)

            def rv(a):
                for k, v in vars_map.items():
                    a = a.replace(k, v)
                return a

            jvm_args = [rv(a) for a in jvm_args]
            game_args = [rv(a) for a in game_args]

            java_bin, _ = self._pick_java(meta["version"])
            if not java_bin:
                jr = self.ensure_java(meta["version"])
                if jr["status"] != "success":
                    return {"status": "error", "message": jr.get("message", "Нужна Java")}
                java_bin = jr["path"]

            ram = max(1, min(int(self.settings.get("ram_gb", 4) or 4), 32))
            cmd = [java_bin, f"-Xmx{ram}G", f"-Xms{min(2, ram)}G"]
            cmd += jvm_args
            if "-cp" not in cmd and "--class-path" not in cmd and "-classpath" not in cmd:
                cmd += ["-cp", cp_str]

            if self.settings.get("millida_things"):
                exe = THINGS_DIR / "bin" / "MillidaThings.exe"
                bridge = THINGS_DIR / "bridge" / "bridge.jar"
                skin = SETTINGS_DIR / "skin.png"
                if not skin.exists() and DEFAULT_STEVE.exists():
                    skin = DEFAULT_STEVE
                lite = bool(self.settings.get("things_lite"))
                ely = bool(self.settings.get("elyby_skins"))
                white_ip = bool(self.settings.get("white_ip_emulator"))
                port_emu = bool(self.settings.get("port_emulator"))
                # в Lite-режиме остаются только патчи — без голоса/скинов/обнаружения
                voice = bool(self.settings.get("voice_chat", True)) and not lite
                if exe.exists():
                    try:
                        self.things_proc = subprocess.Popen([
                            str(exe),
                            "--nick", nick,
                            "--skin", str(skin) if skin.exists() else "",
                            "--voice", str(voice).lower(),
                            "--voice-port", "34567",
                            "--bridge-port", "34568",
                            "--http-port", "34569",
                            "--ely", str(ely).lower(),
                            "--white-ip", str(white_ip).lower(),
                            "--port-emulator", str(port_emu).lower(),
                            "--lite", str(lite).lower(),
                            "--game-dir", str(target),
                        ], creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                    except Exception as e:
                        DEBUG.error("things", e)
                if bridge.exists():
                    cmd.append(
                        f"-javaagent:{bridge}=nick={nick},skin={skin if skin.exists() else ''}"
                        f",voice={str(voice).lower()},ely={str(ely).lower()}"
                        f",whiteip={str(white_ip).lower()},portemu={str(port_emu).lower()}"
                        f",lite={str(lite).lower()}")

            cmd.append(vdata["mainClass"])
            cmd += game_args

            DEBUG.info("launch cmd: " + " ".join(f'"{c}"' if " " in c else c for c in cmd[:25]) + " ...")

            def runner():
                try:
                    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                    with open(GAME_LOG, "w", encoding="utf-8", errors="replace") as lf:
                        lf.write("=== game launch ===\n" + " ".join(cmd) + "\n\n")
                        self.game_proc = subprocess.Popen(
                            cmd, cwd=str(target), stdout=lf, stderr=subprocess.STDOUT,
                            creationflags=flags)
                        self.start_net_patch_watcher()
                        code = self.game_proc.wait()
                    self.stop_net_patch_watcher()
                    if code != 0:
                        DEBUG.error(f"Игра завершилась с кодом {code}. "
                                    f"Смотри data/game.log")
                    else:
                        DEBUG.info("Игра закрыта нормально")
                except Exception as e:
                    self.stop_net_patch_watcher()
                    DEBUG.error("game launch", e)

            threading.Thread(target=runner, daemon=True).start()
            return {"status": "success",
                    "message": f"Запуск {meta['loader']} {meta['version']} (Java, {nick})..."}
        except Exception as e:
            DEBUG.error("launch_instance", e)
            return {"status": "error", "message": str(e)}
        finally:
            self.progress.finish()

    @staticmethod
    def _rules_allow(rules):
        cur_os = "windows" if os.name == "nt" else ("osx" if sys.platform == "darwin" else "linux")
        allowed = False
        for r in rules:
            action = r.get("action")
            os_name = (r.get("os") or {}).get("name")
            if os_name and os_name != cur_os: continue
            arch = (r.get("os") or {}).get("arch")
            if arch and arch != "x86": continue
            allowed = (action == "allow")
        return allowed

    # ------------------------------------------------ импорт
    def import_millida_data(self):
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        path = filedialog.askdirectory(title="Папка Millida Launcher")
        root.destroy()
        if not path: return {"status": "error", "message": "Отменено"}
        src = Path(path); dst = DATA / "millida_import"; dst.mkdir(exist_ok=True)
        n = 0
        for f in src.rglob("*"):
            if f.is_file():
                d = dst / f.relative_to(src); d.parent.mkdir(parents=True, exist_ok=True)
                try: shutil.copy2(f, d); n += 1
                except Exception: pass
        return {"status": "success", "message": f"Импортировано: {n}"}

    def import_prism_data(self):
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        path = filedialog.askdirectory(title="Папка instances из Prism Launcher")
        root.destroy()
        if not path: return {"status": "error", "message": "Отменено"}
        src_root = Path(path)
        imported, errors = [], []
        for inst_dir in src_root.iterdir():
            if not inst_dir.is_dir(): continue
            cfg = inst_dir / "instance.cfg"
            if not cfg.exists(): continue
            try:
                meta = self._parse_prism_cfg(cfg)
                nm = meta.get("name") or inst_dir.name
                safe = re.sub(r'[<>:"/\\|?*]', "_", nm).strip() or inst_dir.name
                dst = INST / safe
                if dst.exists():
                    n = 1
                    while (INST / f"{safe}_{n}").exists(): n += 1
                    safe = f"{safe}_{n}"; dst = INST / safe
                (dst / "mods").mkdir(parents=True, exist_ok=True)
                (dst / "saves").mkdir(parents=True, exist_ok=True)
                mc_ver, loader = self._parse_prism_meta(inst_dir, meta)
                self._write_meta(safe, {"name": safe, "version": mc_ver or "1.20.1",
                                        "loader": loader or "vanilla", "loader_version": None})
                mc_src = inst_dir / ".minecraft"
                copied = 0
                if mc_src.exists():
                    for folder in ("mods", "saves", "config", "resourcepacks",
                                   "shaderpacks", "options.txt", "servers.dat"):
                        s = mc_src / folder
                        if not s.exists(): continue
                        d = dst / folder
                        if s.is_dir():
                            shutil.copytree(s, d, dirs_exist_ok=True)
                            copied += len(list(d.rglob("*")))
                        else:
                            shutil.copy2(s, d); copied += 1
                imported.append({"name": safe, "files": copied})
            except Exception as e:
                errors.append(f"{inst_dir.name}: {e}")
        msg = f"Импортировано: {len(imported)}"
        if errors: msg += f", ошибок: {len(errors)}"
        return {"status": "success", "message": msg, "imported": imported, "errors": errors}

    @staticmethod
    def _parse_prism_cfg(cfg_path: Path) -> dict:
        out = {}
        try:
            for line in cfg_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("["): continue
                if "=" in line:
                    k, v = line.split("=", 1); out[k.strip()] = v.strip()
        except Exception: pass
        return out

    @staticmethod
    def _parse_prism_meta(inst_dir: Path, cfg: dict):
        mc_ver, loader = None, None
        pack = inst_dir / "mmc-pack.json"
        if pack.exists():
            try:
                data = json.loads(pack.read_text(encoding="utf-8"))
                for comp in data.get("components", []):
                    uid = (comp.get("uid") or "").lower()
                    ver = comp.get("version") or ""
                    if uid == "net.minecraft": mc_ver = ver
                    elif "fabric" in uid: loader = "fabric"
                    elif "quilt" in uid: loader = "quilt"
                    elif "forge" in uid and "neoforge" not in uid: loader = "forge"
                    elif "neoforge" in uid: loader = "neoforge"
            except Exception: pass
        return mc_ver, loader


def main():
    api = LauncherAPI()
    try:
        import embedded_web
        html_content = embedded_web.HTML
    except Exception:
        html_content = None
    if html_content:
        w = webview.create_window(
            "Better Millida Launcher", html=html_content,
            js_api=api, width=1180, height=760,
            frameless=True, easy_drag=False, background_color="#2b0b45")
    else:
        w = webview.create_window(
            "Better Millida Launcher", str(BASE / "web" / "index.html"),
            js_api=api, width=1180, height=760,
            frameless=True, easy_drag=False, background_color="#2b0b45")
    api.set_window(w)
    last = None
    for gui in (os.environ.get("PYWEBVIEW_GUI"), "mshtml", None):
        try:
            webview.start(debug=False, gui=gui)
            return
        except Exception as e:
            DEBUG.error(f"webview gui={gui}", e)
            last = e
    if last:
        raise last


if __name__ == "__main__":
    main()
