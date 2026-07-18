# Rockstar Games Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This repository contains the Rockstar Games integration plugin for the native 64-bit version of GOG Galaxy 2.1+. It is based on the original community integration and has been updated for the current GOG Galaxy client and Python 3.13. The project includes updated game detection, achievement support, local playtime tracking, compatibility fixes, stability improvements, and ongoing maintenance.

---

## ✨ Features

* Imports supported Rockstar-owned games into GOG Galaxy
* Imports unlocked Rockstar achievements
* Detects locally installed Rockstar games
* Installs, launches, and uninstalls games through Rockstar Games Launcher
* Tracks game time locally and preserves it between sessions
* Supports Rockstar Social Club web authentication
* Detects installed Steam and Epic versions of supported Rockstar games
* Includes optional Steam library fallback detection
* Supports GOG Galaxy 2.1+ 64-bit and Python 3.13
* Includes bundled dependencies, compatibility fixes, and stability improvements

---

## 📦 Installation

### Automatic Installation with Plugin Updater (Recommended)

The easiest way to install the Rockstar Games integration is with the [melcom GOG Galaxy Plugin Updater](https://github.com/melcom-creations/galaxy-integrations-64bit/tree/main/tools/melcom-galaxy_plugin_updater). The updater detects existing integrations and can install any supported melcom plugins that are still missing.

1. Download and extract the Plugin Updater.
2. Double-click `update-plugins.bat`.
3. Select your preferred language.
4. Follow the displayed instructions.

### Manual Installation

1. Close GOG Galaxy completely and make sure it is no longer running in the system tray.
2. Download the latest release package from this repository.
3. Extract the ZIP archive directly into:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
```

The release ZIP already contains the required plugin folder. The resulting directory structure must look like this:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
└── rockstar_774732b5-69c4-405c-b6c9-92cd55740cfe\
    ├── manifest.json
    ├── plugin.py
    ├── README.md
    └── ...
```

4. Continue with **First Start and Initial Sync** below.

---

## 🚀 First Start and Initial Sync

For the first synchronization after installing or updating the plugin:

1. Start Rockstar Games Launcher and keep it open.
2. Start GOG Galaxy.
3. Connect the Rockstar Games integration through **Settings -> Integrations** if necessary.
4. Complete the Rockstar Social Club login when prompted.
5. Open the account menu in the top-right corner and select **Sync integrations**.
6. Wait until the synchronization has finished.

---

## 🎮 Library Visibility and Ownership Detection

On Windows, the plugin determines Rockstar-owned games primarily from Rockstar Games Launcher logs and confirmed local installation data. Rockstar titles associated with Steam or Epic Games are shown only when they are installed. This prevents locally detected third-party versions from being treated as permanently owned Rockstar copies.

The original plugin also used an undocumented Social Club web request to retrieve previously played games. This legacy request is disabled by default because the current Rockstar sign-in flow no longer refreshes the required browser session reliably. Disabling it does not affect normal login, local game detection, launching, achievements, or local playtime tracking.

---

## ⚙️ Optional Configuration

The plugin includes `default_config.cfg` with all available settings and their default values. To change a setting, copy this file to the plugin root, rename the copy to `config.cfg`, and edit only that copy. Do not edit or delete `default_config.cfg`.

### Steam Library Fallback

`enable_steam_fallback=True` is enabled by default. It searches configured Steam library folders for supported Rockstar games that were not found through the standard Windows uninstall registry. Set the value to `False` only if you want to disable Steam-based detection completely.

### Legacy Online Game Scraper

`enable_legacy_online_game_scraper=False` should remain disabled during normal use. Setting it to `True` temporarily restores the undocumented Social Club played-games request for advanced diagnostics. If the request fails, the plugin disables it for the remainder of the session to prevent repeated authentication delays.

---

## ⚠️ Known Limitation

The plugin can retrieve Rockstar Social Club friend data, but GOG Galaxy does not currently display Rockstar friends reliably in its interface. This limitation does not affect library synchronization, achievements, game launching, installation detection, or playtime tracking.

---

## 🔄 Resetting the Plugin Database (Troubleshooting)

Reset the local plugin database only if the integration behaves unexpectedly or synchronization problems continue after restarting both applications.

1. Close GOG Galaxy completely.
2. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`.
3. Find every file starting with `rockstar_` and ending in `-storage.db`.
4. Rename each matching file by appending `.old`, for example:

   `rockstar_xxxxxxxxx-storage.db` -> `rockstar_xxxxxxxxx-storage.db.old`

5. Start Rockstar Games Launcher and keep it open.
6. Start GOG Galaxy and reconnect the Rockstar Games integration if necessary.
7. Open the account menu in the top-right corner and select **Sync integrations**.
8. Wait until the synchronization has finished.

---

## ⚠️ Important

Do **not** place backup copies of this plugin inside the `plugins\installed` directory.

GOG Galaxy scans every folder inside this directory during startup. Duplicate plugin folders can lead to GUID conflicts or cause Galaxy to load an outdated version of the plugin.

---

## 🙏 Credits

**Original Community Integration**  
Tylerbrawl  
[Tylerbrawl/Galaxy-Plugin-Rockstar](https://github.com/tylerbrawl/Galaxy-Plugin-Rockstar)

**64-bit Port, Maintenance and Improvements**  
melcom

---

## ❤️ Special Thanks

Big thanks to [MacStew](https://www.gog.com/u/MacStew) for testing and for tracking down the exact Steam App IDs and folder names for L.A. Noire and Red Dead Redemption 2.

---

## 🤝 Support & Feedback

This project is developed and maintained by one person. Response times may vary, especially during periods when health-related limitations reduce available development time.

**GitHub Issues are intentionally disabled.**

If you would like to report a bug or suggest an improvement, please use the contact form on my website:

📩 [Contact form](https://melcom-creations.github.io/melcom-music/contact.html)

Thank you for your patience and support!
