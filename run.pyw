# -*- coding: utf-8 -*-
import sys, traceback, os, logging
from pathlib import Path

BASE = Path(__file__).parent.resolve()
LOG = BASE / "crash.log"

# глушим шум от pythonnet/WebView2
logging.disable(logging.CRITICAL)
# НЕ форсируем PYTHONNET_RUNTIME=coreclr: без установленного .NET Desktop Runtime
# это роняет System.Windows.Forms, и лаунчер не стартует вообще.
os.environ.setdefault("PYWEBVIEW_GUI", "edgechromium")

try:
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("=== Better Millida Launcher ===\n")
        f.write(f"python: {sys.version}\n")
    import app
    app.main()
except Exception:
    tb = traceback.format_exc()
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n=== CRASH ===\n" + tb)
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, tb[-1500:], "Better Millida — Crash", 0x10)
    except Exception:
        pass
    sys.exit(1)