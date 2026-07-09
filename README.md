# Rockstar Integration Plugin for GOG Galaxy 2.1+ (64-bit)

Rockstar Games integration for the native 64-bit GOG Galaxy client.
This project is a maintained 64-bit continuation of the original community plugin.

> [!TIP]
> **TLDR**
> The release ZIP already contains the `rockstar_774732b5-69c4-405c-b6c9-92cd55740cfe` folder, so extract it into `%localappdata%\GOG.com\Galaxy\plugins\installed\`.
> Keep Rockstar Games Launcher open, then run **Sync integrations** in GOG Galaxy.
> Status: pre-release; some Rockstar-owned games may still be missing in certain cases.

---

## 🚀 Quick Start (Recommended)

If you just want to install and sync quickly, follow these steps:

1. Close GOG Galaxy completely.
2. Download the latest release ZIP from this repository.
3. Extract it to the folder below. The ZIP already contains `rockstar_774732b5-69c4-405c-b6c9-92cd55740cfe`:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
```

4. Ensure the final folder is exactly:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
└── rockstar_774732b5-69c4-405c-b6c9-92cd55740cfe\
    ├── manifest.json
    ├── plugin.py
    ├── README.md
    └── ...
```

5. Start GOG Galaxy.
6. Start Rockstar Games Launcher and keep it open.
7. In GOG Galaxy, open the account menu (top-right) and click **Sync integrations**.

---

## 📌 Current Status

- This plugin is actively maintained and still in pre-release phase.
- In some cases, Rockstar-owned games may still be missing.
- Steam and Epic Rockstar titles are shown only when installed.

If a Rockstar-owned game is missing, please send logs to:

```text
melcom @ gmx.net
```

Log path:

```text
C:\ProgramData\GOG.com\Galaxy\logs\
```

---

## ✨ Features

- Compatible with GOG Galaxy 2.1+ (64-bit)
- Python 3.13 support
- Updated 64-bit dependencies
- Improved stability and compatibility
- Rockstar Social Club web login support
- Rockstar Games Launcher detection on Windows
- Optional Steam fallback detection via `enable_steam_fallback`
- Playtime cache persistence on shutdown
- Bundled `modules/` dependencies

---

### 🧭 First Start and Initial Sync (Important)

For a clean first run after installing or updating the plugin:

1. Close GOG Galaxy.
2. If this file exists, delete it:

```text
C:\ProgramData\GOG.com\Galaxy\storage\plugins\rockstar_774732b5-69c4-405c-b6c9-92cd55740cfe-47439745864581929-storage.db
```

3. Start GOG Galaxy.
4. Start Rockstar Games Launcher and keep it open.
5. In GOG Galaxy, click **Sync integrations**.
6. Wait until sync finishes.

### 🔄 Resetting the Plugin Database

If the plugin behaves unexpectedly after an update:

1. Open:

```text
C:\ProgramData\GOG.com\Galaxy\storage\plugins\
```

2. Find files starting with `rockstar_` and ending with `-storage.db`.
3. Rename each by appending `.old`.
4. Restart GOG Galaxy and reconnect Rockstar integration if needed.

---

## ⚙️ Optional Configuration

The plugin creates `config.cfg` automatically on first start.

- `enable_steam_fallback=True` (default)
  Automatically searches Steam library folders for Rockstar titles not found via the standard Windows uninstall registry.
  Set this to `False` only if you want to disable Steam-based detection entirely.

---

## ⚠️ Important

Do not place backup copies of this plugin inside `plugins\installed`.

GOG Galaxy scans every folder there during startup. Duplicate plugin folders can cause GUID conflicts or load an outdated plugin copy.

---

## 🙏 Credits

Original community integration:
https://github.com/tylerbrawl/Galaxy-Plugin-Rockstar

64-bit port, maintenance, and improvements:
melcom

---

## ❤️ Special Thanks

Big thanks to [MacStew](https://www.gog.com/u/MacStew) for testing and for tracking down exact Steam App IDs and folder names for L.A. Noire and Red Dead Redemption 2.

---

## 🤝 Support & Feedback

This project is maintained by one person. Response times may vary.

GitHub Issues are intentionally disabled.

Contact form:
https://melcom-creations.github.io/melcom-music/contact.html