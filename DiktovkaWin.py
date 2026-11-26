# DiktovkaWin — русский голосовой ввод в любое окно на Windows.
# Транскрибатор для KIMI и мессенджеров: горячая клавиша, шарик-индикатор,
# вставка распознанного текста туда, где стоит курсор.
# Самостоятельный продукт для Windows, родственный DiktovkaMac.
#
# Запуск: python DiktovkaWin.py   |   Скачать модель: python DiktovkaWin.py --download

import os, sys, json, time, threading, queue, traceback, math

BASE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("HF_HOME", os.path.join(BASE, "models"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
import warnings; warnings.filterwarnings("ignore")

LOG = os.path.join(BASE, "DiktovkaWin.log")
CFG_PATH = os.path.join(BASE, "config.json")
IS_WINDOWS = os.name == "nt"

DEFAULT_CFG = {
    "hotkey": "f8",              # любая F-клавиша или комбинация: "ctrl+alt+space", "shift+f9"…
    "language": "ru",
    "model": "large-v3-turbo",   # на слабом ПК можно "small" (гораздо быстрее, чуть хуже качество)
    "device": "auto",            # auto: CUDA при наличии видеокарты NVIDIA, иначе процессор
    "beep": False,               # звук при старте и остановке записи
    "auto_send": False,          # true – после вставки нажать Enter (сразу отправить)
    "prompt": "Привет. Это голосовое сообщение на русском языке, с точками и запятыми.",
}


def log(*a):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
    except Exception:
        pass


def load_cfg():
    cfg = dict(DEFAULT_CFG)
    try:
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, encoding="utf-8") as f:
                cfg.update(json.load(f))
    except Exception:
        log(traceback.format_exc())
    return cfg


# ---------- один экземпляр (Windows: именованный мьютекс) ----------

def single_instance():
    if IS_WINDOWS:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.CreateMutexW(None, False, "DiktovkaWinMutex")
        if not h:
            return False
        return k.GetLastError() != 183  # ERROR_ALREADY_EXISTS
    # не-Windows: по pid-файлу (для тестов разработки)
    pid_path = os.path.join(BASE, "DiktovkaWin.pid")
    try:
        if os.path.exists(pid_path):
            with open(pid_path) as f:
                os.kill(int(f.read().strip()), 0)
            return False
    except (ValueError, ProcessLookupError):
        pass
    except PermissionError:
        return False
    with open(pid_path, "w") as f:
        f.write(str(os.getpid()))
    return True


# ---------- распознавание (faster-whisper) ----------

def load_model(cfg):
    from faster_whisper import WhisperModel
    dev = cfg.get("device", "auto")
    if dev in ("auto", "cuda"):
        try:  # видеокарта NVIDIA – в разы быстрее процессора
            m = WhisperModel(cfg["model"], device="cuda", compute_type="float16")
            warm(m, cfg)
            return m, "видеокарта NVIDIA (CUDA)"
        except Exception as e:
            log("CUDA не завелась, перехожу на процессор:", e)
    threads = max(2, (os.cpu_count() or 8) // 2)
    m = WhisperModel(cfg["model"], device="cpu", compute_type="int8", cpu_threads=threads)
    return m, "процессор"


def warm(model, cfg):
    import numpy as np
    transcribe(model, np.zeros(16000, dtype="float32"), cfg)


def transcribe(model, audio, cfg):
    import numpy as np
    segs, _ = model.transcribe(
        audio.astype(np.float32), language=cfg.get("language", "ru"),
        initial_prompt=cfg.get("prompt"), vad_filter=True,
        condition_on_previous_text=False)
    return " ".join(s.text for s in segs).strip()


# ---------- звук ----------

def beep(cfg, name):
    if not cfg.get("beep"):
        return
    if IS_WINDOWS:
        import winsound
        freq = 880 if name == "start" else 520
        try:
            winsound.Beep(freq, 90)
        except Exception:
            pass


# ---------- вставка текста (Windows: SendInput, без лишних зависимостей) ----------

def post_ctrl_v(also_return=False):
    if IS_WINDOWS:
        import ctypes
        u32 = ctypes.windll.user32
        KEYEVENTF_KEYUP = 0x0002
        VK_CONTROL, VK_V, VK_RETURN = 0x11, 0x56, 0x0D
        def kd(vk): u32.keybd_event(vk, 0, 0, 0)
        def ku(vk): u32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        kd(VK_CONTROL); kd(VK_V); ku(VK_V); ku(VK_CONTROL)
        time.sleep(0.1)
        if also_return:
            kd(VK_RETURN); ku(VK_RETURN)
    else:  # тесты на macOS/Linux: pynput/pyautogui нет – просто лог
        log(f"[test] post_ctrl_v(return={also_return})")


# ---------- горячая клавиша ----------

VK_CODES = {
    "space": 0x20, "enter": 0x0D, "tab": 0x09, "esc": 0x1B, "escape": 0x1B,
    "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23,
    "pgup": 0x21, "pgdown": 0x22, "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "printscreen": 0x2C, "scrolllock": 0x91, "pause": 0x13,
    "numlock": 0x90, "capslock": 0x14,
}
for i in range(1, 25):
    VK_CODES[f"f{i}"] = 0x70 + i - 1
for ch in "abcdefghijklmnopqrstuvwxyz":
    VK_CODES[ch] = ord(ch.upper())
for d in "0123456789":
    VK_CODES[d] = ord(d)
MODS = {"ctrl": 0x0002, "control": 0x0002, "alt": 0x0001, "shift": 0x0004, "win": 0x0008}


def parse_hotkey(s):
    mods, key = 0, None
    for part in s.lower().split("+"):
        part = part.strip()
        if part in MODS:
            mods |= MODS[part]
        elif part in VK_CODES:
            key = VK_CODES[part]
        else:
            raise ValueError(f"Не понял клавишу «{part}» в config.json")
    if key is None:
        raise ValueError(f"Не понял клавишу «{s}» в config.json")
    return mods, key


def run_hotkey_loop(hotkey_str, callback):
    """RegisterHotKey + цикл сообщений — работает без прав администратора."""
    import ctypes
    from ctypes import wintypes
    u32 = ctypes.windll.user32
    mods, vk = parse_hotkey(hotkey_str)
    WM_HOTKEY, MOD_NOREPEAT = 0x0312, 0x4000
    if not u32.RegisterHotKey(None, 1, mods | MOD_NOREPEAT, vk):
        raise RuntimeError(f"RegisterHotKey не удалась – клавиша «{hotkey_str}» занята?")
    log("горячая клавиша: RegisterHotKey", hotkey_str)
    msg = wintypes.MSG()
    while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == WM_HOTKEY:
            try:
                callback()
            except Exception:
                log(traceback.format_exc())
    return 0


# ---------- шарик-индикатор (tkinter, прозрачный оверлей) ----------

PINK = "#FA59A6"
TEAL = "#17B8A6"


class Overlay:
    """Розовый переливающийся шарик внизу по центру экрана.
    Состояния: hidden | shimmer | fade. Не забирает фокус и клики."""

    SIZE = 84

    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.q = queue.Queue()
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="black")
        try:
            self.root.attributes("-transparentcolor", "black")  # Windows
        except Exception:
            pass
        w = h = self.SIZE
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = sh - h - 30                            # внизу по центру
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="black",
                                highlightthickness=0)
        self.canvas.pack()
        self.root.attributes("-alpha", 0.0)
        self.root.withdraw()
        self.state = "hidden"
        self.rotation = 0.0
        self.phase = 0.0
        self.scale = 1.0
        self.ball_items = []
        self.root.after(16, self._tick)

    # вызовы из любого потока
    def shimmer(self, speed=1.0, seconds=None):
        self.q.put(("shimmer", speed, seconds))

    def finish_fade(self, color=TEAL):
        self.q.put(("fade", color))

    def error_fade(self):
        self.q.put(("fade", "#E5484D"))

    def hide(self):
        self.q.put(("hide",))

    def run(self):
        self.root.mainloop()

    # --- внутри потока tkinter ---
    def _draw_ball(self, rgb, scale=1.0):
        c = self.canvas
        c.delete("all")
        S = self.SIZE
        cx, cy = S / 2, S / 2
        R = (S / 2 - 6) * scale
        N = 6
        for i in range(N):
            color = PINK if i % 2 == 0 else "#FFFFFF"
            start = self.rotation + i * 360 / N
            c.create_arc(cx - R, cy - R, cx + R, cy + R,
                         start=start, extent=360 / N,
                         style="pieslice", fill=color, outline="")
        # блик для объёма
        hx, hy, hr = cx - R * 0.35, cy - R * 0.4, R * 0.28
        c.create_oval(hx - hr, hy - hr, hx + hr, hy + hr,
                      fill="#FFFFFF", outline="", stipple="gray50")

    def _tick(self):
        try:
            while True:
                op = self.q.get_nowait()
                kind = op[0]
                if kind == "shimmer":
                    self.state = "shimmer"
                    self._speed = op[1]
                    self.shimmer_until = time.time() + op[2] if op[2] else None
                    self.root.deiconify()
                    self.root.attributes("-alpha", 1.0)
                elif kind == "fade":
                    self.state = "fade"
                    self.fade_color = op[1]
                    self.fade_t = 0.0
                elif kind == "hide":
                    self.state = "hidden"
                    self.root.withdraw()
        except queue.Empty:
            pass

        dt = 0.016
        if self.state == "shimmer":
            self.rotation += dt * getattr(self, "_speed", 1.0) * 200
            self.phase += dt
            self.scale = 1.0 + 0.05 * math.sin(self.phase * 2.1)
            self._draw_ball(PINK, self.scale)
            if self.shimmer_until and time.time() >= self.shimmer_until:
                self.state = "fade"
                self.fade_color = TEAL
                self.fade_t = 0.0
        elif self.state == "fade":
            self.fade_t += dt / 0.45
            t = min(self.fade_t, 1.0)
            self.rotation += dt * 200 * max(0.0, 1.0 - t)
            # смешение цвета: последние секции – финальный цвет
            self._draw_ball(TEAL, 1.0 - 0.4 * t)
            alpha = max(0.0, 1.0 - max(0.0, t * 1.2 - 0.2))
            self.root.attributes("-alpha", alpha)
            if t >= 1.0:
                self.state = "hidden"
                self.root.withdraw()
        self.root.after(16, self._tick)


# ---------- основная логика ----------

class App:
    def __init__(self, cfg, ov):
        self.cfg = cfg
        self.ov = ov
        self.model = None
        self.chunks = []
        self.recording = False
        self.stream = None
        self.busy = False
        self.done_at = 0.0
        self.ui = queue.Queue()   # действия в потоке оверлея/трея

    def toggle(self):
        now = time.time()
        if self.busy:
            return
        if now - self.done_at < 1.0:
            return  # защита от двойного срабатывания
        if self.recording:
            threading.Thread(target=self.finish, daemon=True).start()
        else:
            if self.model is None:
                self.ov.error_fade()
                return
            threading.Thread(target=self.record, daemon=True).start()

    def record(self):
        try:
            import numpy as np
            import sounddevice as sd
            self.chunks = []
            q = queue.Queue()

            def cb(indata, frames, t, status):
                q.put(indata[:, 0].copy())

            self.stream = sd.InputStream(samplerate=16000, channels=1,
                                         dtype="float32", blocksize=1024, callback=cb)
            self.stream.start()
            self.recording = True
            log("запись началась")
            beep(self.cfg, "start")
            self.ov.shimmer(speed=1.4)
            while self.recording:
                try:
                    self.chunks.append(q.get(timeout=0.2))
                except queue.Empty:
                    pass
            log("цикл записи завершён")
        except Exception:
            log(traceback.format_exc())
            self.ov.error_fade()
            self.recording = False

    def finish(self):
        import numpy as np
        try:
            self.recording = False
            self.stream.stop(); self.stream.close()
            beep(self.cfg, "stop")
            audio = np.concatenate(self.chunks) if self.chunks else np.zeros(0, dtype="float32")
            log(f"запись остановлена, {len(audio)/16000:.1f} с")
            if len(audio) < 16000 * 0.3:
                self.ov.error_fade()
                return
            self.ov.finish_fade()  # гаснем сразу: распознавание идёт молча
            t0 = time.time()
            text = transcribe(self.model, audio, self.cfg)
            log(f"{len(audio)/16000:.1f} с речи → {time.time()-t0:.1f} с: {text}")
            if not text:
                self.ov.error_fade()
                return
            self.paste(text)
        except Exception:
            log(traceback.format_exc())
            self.ov.error_fade()
        finally:
            self.busy = False
            self.done_at = time.time()

    def paste(self, text):
        import pyperclip
        try:
            old = pyperclip.paste()
        except Exception:
            old = None
        pyperclip.copy(text)
        time.sleep(0.1)
        post_ctrl_v(bool(self.cfg.get("auto_send")))
        time.sleep(0.4)
        if old is not None:
            try:
                pyperclip.copy(old)
            except Exception:
                pass

    def load(self):
        try:
            self.ov.shimmer(speed=0.8)
            t0 = time.time()
            self.model, where = load_model(self.cfg)
            log(f"модель {self.cfg['model']} загружена на {where} за {time.time()-t0:.1f} с")
            self.ov.finish_fade()
        except Exception:
            log(traceback.format_exc())
            self.ov.error_fade()


# ---------- трей (pystray) ----------

def run_tray(app, cfg):
    from PIL import Image
    import pystray

    icon_path = os.path.join(BASE, "icon.png")
    image = Image.open(icon_path) if os.path.exists(icon_path) else Image.new("RGBA", (64, 64), PINK)

    def on_record(_, __):
        app.toggle()

    def on_cfg(_, __):
        if IS_WINDOWS:
            os.startfile(CFG_PATH)  # noqa
        else:
            import subprocess
            subprocess.Popen(["open", CFG_PATH])

    def on_dir(_, __):
        if IS_WINDOWS:
            os.startfile(BASE)  # noqa
        else:
            import subprocess
            subprocess.Popen(["open", BASE])

    def on_quit(_, __):
        app.recording = False
        try:
            os._exit(0)
        except Exception:
            pass

    menu = pystray.Menu(
        pystray.MenuItem("Записать / остановить", on_record),
        pystray.MenuItem("Настройки (config.json)", on_cfg),
        pystray.MenuItem("Папка DiktovkaWin", on_dir),
        pystray.MenuItem("Выход", on_quit),
    )
    tray = pystray.Icon("DiktovkaWin", image, "DiktovkaWin", menu)
    log("запущена, клавиша", cfg["hotkey"])
    tray.run()


def main():
    cfg = load_cfg()

    if "--download" in sys.argv:  # скачать модель и проверить, что она работает
        m, where = load_model(cfg)
        warm(m, cfg)
        print(f"OK: модель {cfg['model']} работает, считает на {where}")
        return

    if not single_instance():
        print("DiktovkaWin уже запущена – значок микрофона в трее.")
        return

    ov = Overlay()
    app = App(cfg, ov)
    threading.Thread(target=app.load, daemon=True).start()

    if IS_WINDOWS:
        threading.Thread(target=run_hotkey_loop, args=(cfg["hotkey"], app.toggle),
                         daemon=True).start()
    else:
        log("[test] hotkey loop пропущен (не Windows)")
    threading.Thread(target=run_tray, args=(app, cfg), daemon=True).start()
    ov.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log(traceback.format_exc())
        raise
