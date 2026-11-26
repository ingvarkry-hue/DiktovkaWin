# DiktovkaWin

**Транскрибатор для KIMI и мессенджеров** — русский голосовой ввод в **любое** окно на Windows.
Локально, быстро, без облака.
**Russian voice typing into any Windows app. Local, fast, offline.**

[English below](#english)

---

## Русский

Говорите в KIMI — и в любом другом приложении: Telegram, WhatsApp, браузер, Word, почта.
Нажали клавишу — говорите — нажали ещё раз — готовый текст в поле ввода.
Речь распознаёт нейросеть **Whisper** (faster-whisper) прямо на вашем компьютере:
запись никуда не отправляется. Пока идёт распознавание, внизу экрана по центру
крутится розовый шарик — видно, что речь преобразуется. Закончил — шарик гаснет,
текст на месте.

![DiktovkaWin в работе](docs/demo.gif)

### Установка — одна команда

Нажмите **Win+R**, вставьте и нажмите Enter:

```
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/ingvarkry-hue/DiktovkaWin/main/install.ps1 | iex"
```

Установщик сам поставит Python (если его нет), библиотеки и модель распознавания
(около 1,6 ГБ), создаст ярлык на рабочем столе и в автозапуске. Займёт 5–15 минут,
зависит от интернета. Вся установка живёт в папке `C:\DiktovkaWin` — систему не трогает.

**Первый запуск:** Windows спросит про доступ к микрофону — разрешите.

### Как пользоваться

1. Поставьте курсор в поле ввода.
2. Нажмите **F8** — внизу экрана появится розовый шарик.
3. Говорите.
4. Нажмите **F8** ещё раз — шарик погаснет, текст окажется в поле ввода.

### Настройки — `C:\DiktovkaWin\config.json`

Открыть: правый клик по значку микрофона в трее → «Настройки».

| Параметр | Что делает |
| --- | --- |
| `hotkey` | клавиша записи: `"f8"`, `"f9"`, `"ctrl+alt+space"`… |
| `model` | `"large-v3-turbo"` (лучше) или `"small"` (быстрее, чуть хуже качество) |
| `device` | `"auto"` — видеокарта NVIDIA (CUDA) или процессор |
| `language` | язык речи, `"ru"` по умолчанию |
| `beep` | `true` — звук при старте и остановке записи |
| `auto_send` | `true` — после вставки сразу нажимать Enter |
| `prompt` | подсказка для Whisper (стиль пунктуации) |

После правки: выход через значок в трее и запуск ярлыка «DiktovkaWin» снова.

### Скорость

- С видеокартой NVIDIA — 1–2 секунды на минуту речи.
- Без видеокарты — на процессоре, 5–20 секунд на минуту речи. Если медленно —
  в `config.json` поставьте `"model": "small"`.

### Если что-то не так

- **Ничего не происходит по клавише** — проверьте значок микрофона возле часов;
  нет значка — запустите ярлык «DiktovkaWin».
- **«Не вижу микрофон»** — Параметры Windows → Конфиденциальность → Микрофон →
  разрешить доступ приложениям.
- **Остальное** — файл `C:\DiktovkaWin\DiktovkaWin.log`.

### Удаление

Win+R →

```
powershell -ExecutionPolicy Bypass -File C:\DiktovkaWin\uninstall.ps1
```

---

## English

A **voice transcriber for KIMI and messengers**: speak in KIMI — or in any other app,
Telegram, WhatsApp, browser, Word, mail. Press the hotkey — speak — press again —
finished text lands in the input field. Speech is recognized by the **Whisper**
neural network (faster-whisper) right on your computer: the recording never leaves
the machine. While recognizing, a pink sphere spins at the bottom-center of the screen.

### Install — one command

Press **Win+R**, paste and hit Enter:

```
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/ingvarkry-hue/DiktovkaWin/main/install.ps1 | iex"
```

The installer sets up Python (if missing), libraries and the speech model (~1.6 GB),
adds a desktop shortcut and an autostart entry. Everything lives in `C:\DiktovkaWin` —
the system stays untouched. **On first launch, allow microphone access.**

### Usage

1. Put the cursor into an input field.
2. Press **F8** — a pink sphere appears at the bottom of the screen.
3. Speak.
4. Press **F8** again — the sphere fades out and the text appears in the field.

### Configuration — `C:\DiktovkaWin\config.json`

Right-click the tray icon → «Настройки». Options: `hotkey` (default `"f8"`),
`model` (`"large-v3-turbo"` or `"small"`), `device` (`"auto"` = NVIDIA CUDA or CPU),
`language`, `beep`, `auto_send`, `prompt`. Restart the app after editing.

### Uninstall

Win+R →

```
powershell -ExecutionPolicy Bypass -File C:\DiktovkaWin\uninstall.ps1
```

---

## Лицензия / License

MIT, см. [LICENSE](LICENSE).

Распознавание речи — [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
(модели OpenAI Whisper) / Speech recognition by
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper models).
