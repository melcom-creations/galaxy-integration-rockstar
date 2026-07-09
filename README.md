# Rockstar Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This repository contains the Rockstar Games integration plugin for the 64-bit version of GOG Galaxy 2.1+.

The original community integration has been updated to work with the current 64-bit Galaxy client and Rockstar Social Club authentication flow. In addition to compatibility improvements, this version includes bundled `modules/` dependencies, authentication fixes, and ongoing plugin maintenance.

---

## ✨ Features

* Compatible with GOG Galaxy 2.1+ (64-bit)
* Python 3.13 support
* Updated 64-bit dependencies
* Improved stability and compatibility
* Rockstar Social Club web login support
* Rockstar Games launcher detection on Windows
* Optional Steam fallback detection for Steam-installed Rockstar titles via `enable_steam_fallback`
* Playtime cache persistence on shutdown
* Bundled `modules/` dependencies
* Ongoing maintenance and bug fixes

---

## 📦 Installation

### Standard Installation (Recommended)

1. Close GOG Galaxy completely.
2. Download the latest release from this repository.
3. Open the following folder:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
```

4. Extract the ZIP archive **directly into this folder**.

The resulting directory structure **must** look like this:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
└── rockstar_774732b5-69c4-405c-b6c9-92cd55740cfe\
    ├── manifest.json
    ├── plugin.py
    ├── README.md
    └── ...
```

  5. Start GOG Galaxy.

---

## 🔄 Resetting the Plugin Database (Recommended)

If the plugin behaves unexpectedly after an update, resetting the local plugin database is recommended.

1. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\` and find the files starting with `rockstar_` and ending in `-storage.db`.
2. Rename each by appending `.old` (e.g. `rockstar_xxxxxxxxx-storage.db` → `rockstar_xxxxxxxxx-storage.db.old`).
3. Start GOG Galaxy again and reconnect the Rockstar integration if necessary.

### First Start and Initial Sync (Important)

For a clean first run after installing or updating the plugin, use this flow:

1. Close GOG Galaxy.
2. If this file exists, delete it:

```text
C:\ProgramData\GOG.com\Galaxy\storage\plugins\rockstar_774732b5-69c4-405c-b6c9-92cd55740cfe-47439745864581929-storage.db
```

3. Start GOG Galaxy.
4. Start the Rockstar Games Launcher and keep it open.
5. In GOG Galaxy, open the account menu (top-right) and click **Sync integrations**.
6. Wait until sync is finished. This can take a little while.

After sync, check the Rockstar platform inside GOG Galaxy.

- Steam and Epic titles are shown only when they are installed.
- The plugin behavior is intentionally aligned with how Rockstar/Epic launcher visibility works for installed external-platform copies.

Note for current development status:

- In some cases, Rockstar-purchased games may still be missing.
- The plugin is still under active development.
- If a Rockstar-owned game is missing, please send your log file to:

```text
melcom @ gmx.net
```

Logs are usually located at:

```text
C:\ProgramData\GOG.com\Galaxy\logs\
```

---

## ⚙️ Optional Configuration

The plugin creates `config.cfg` in its root folder automatically on first start — no setup required. Edit it only if you want to change the option below:

- `enable_steam_fallback=True` (default)
  - Automatically searches Steam library folders for Rockstar titles not found via the standard Windows uninstall registry.
  - Set this to `False` only if you want to disable Steam-based detection entirely.

---

## ⚠️ Important

Do **not** place backup copies of this plugin inside the `plugins\installed` directory.

GOG Galaxy scans every folder inside this directory during startup. Duplicate plugin folders can lead to GUID conflicts or cause Galaxy to load an outdated version of the plugin.

---

## 🙏 Credits

**Original Community Integration**
Tylerbrawl
https://github.com/tylerbrawl/Galaxy-Plugin-Rockstar

**64-bit Port, Maintenance and Improvements**
melcom

---

## ❤️ Special Thanks
I want to take a moment to thank someone who helped make this release better:
* A big thank you to [**MacStew**](https://www.gog.com/u/MacStew) for testing the plugin and tracking down the exact Steam App IDs and folder names for L.A. Noire and Red Dead Redemption 2. Your reports made it possible to fix detection for both games quickly and correctly instead of guessing around it.
Thank you for the help!

---

## 🤝 Support & Feedback

This project is developed and maintained by one person. Response times may vary, especially during periods when health-related limitations reduce available development time.

**GitHub Issues are intentionally disabled.**

If you would like to report a bug or suggest an improvement, please use the contact form on my website:

📩 https://melcom-creations.github.io/melcom-music/contact.html

Thank you for your patience and support!