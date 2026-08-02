# Rockstar Games Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This plugin imports supported Rockstar Games titles into GOG Galaxy 2.1+ 64-bit. Based on the original community integration, it has been updated for the current GOG Galaxy client and Python 3.13, with achievements, improved game detection, and local playtime tracking.

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

---

## 📦 Installation

### Automatic Installation with Plugin Updater (Recommended)

Use the [melcom GOG Galaxy Plugin Updater](https://github.com/melcom-creations/galaxy-integrations-64bit/tree/main/tools/melcom-galaxy_plugin_updater) to install or update the integration automatically.

1. Download and extract the Plugin Updater.
2. Double-click `update-plugins.bat`.
3. Select your preferred language.
4. Follow the displayed instructions.

### Manual Installation

1. Close GOG Galaxy completely, including the system tray application.
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

**Next step:** Continue with **First Start and Initial Sync** below.

> [!IMPORTANT]
> Do not place backup copies of this plugin inside the `plugins\installed` directory. GOG Galaxy scans every folder inside this directory during startup, so duplicate plugin folders can cause GUID conflicts or load an outdated version.

---

## 🚀 First Start and Initial Sync

For the first synchronization after installing or updating the plugin:

1. Start Steam or Epic Games Launcher if any installed Rockstar titles were purchased there, and keep the required store client open.
2. Start Rockstar Games Launcher and keep it open.
3. Start GOG Galaxy.
4. Connect the Rockstar Games integration through **Settings -> Integrations** if necessary.
5. Complete the Rockstar Social Club login when prompted.
6. Open the account menu in the top-right corner and select **Sync integrations** once.
7. Wait until the synchronization has finished. Do not start another manual synchronization while the first one is still running.

---

## 🎮 Library Visibility, Ownership Retention, and Missing Games

On Windows, the plugin determines Rockstar-owned games primarily from Rockstar Games Launcher logs and confirmed local installation data. The current Rockstar services do not provide the plugin with a reliable, complete list of every game owned by the account. Steam and Epic installations therefore provide important confirmation for titles purchased through those stores.

Once the plugin has successfully confirmed a supported title, it stores that title in its persistent ownership cache. The game should then remain in the Rockstar library inside GOG Galaxy after it is uninstalled. Deleting, renaming, or resetting the Rockstar plugin storage database starts the plugin with an empty ownership cache. Games that are neither installed nor still present in the available Rockstar Games Launcher logs cannot always be reconstructed automatically.

The original plugin also used an undocumented Social Club web request to retrieve previously played games. This legacy request is disabled by default because the current Rockstar sign-in flow no longer refreshes the required browser session reliably. Disabling it does not affect normal login, local game detection, launching, achievements, or local playtime tracking.

### ♻️ Recovering Missing Games After a Storage Reset

> [!IMPORTANT]
> If only currently installed titles remain visible after reconnecting the integration, the retained ownership cache was most likely empty or removed. The missing games must be confirmed again before the plugin can retain them for later sessions.

1. Temporarily install each missing supported Rockstar title through the store where it was purchased: Rockstar Games Launcher, Steam, or Epic Games Launcher. The games can be handled one at a time if disk space is limited.
2. Keep Steam or Epic Games Launcher running when applicable. Start Rockstar Games Launcher and wait until it recognizes the installed games.
3. Close GOG Galaxy and Rockstar Games Launcher completely. Leave Steam or Epic Games Launcher running when they are required for the installed copies.
4. Start Rockstar Games Launcher again and keep it open, then start GOG Galaxy.
5. Reconnect the Rockstar integration if necessary. Select **Sync integrations** exactly once and wait until the synchronization has fully completed.
6. Confirm that the recovered titles appear under the Rockstar integration. After they have been successfully confirmed and stored, they can normally be uninstalled again and should remain in the library unless the plugin storage is reset another time.

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

Reset the local plugin database only if synchronization problems continue after restarting both applications and completing one normal synchronization.

> [!WARNING]
> Resetting this database also resets the plugin's retained ownership cache. Previously confirmed but currently uninstalled games may disappear until they are confirmed again. Keep the renamed `.old` database as a backup and do not use this procedure as the first response to a missing game.

1. Close GOG Galaxy completely.
2. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`.
3. Find every file starting with `rockstar_` and ending in `-storage.db`.
4. Rename each matching file by appending `.old`, for example:

   `rockstar_xxxxxxxxx-storage.db` -> `rockstar_xxxxxxxxx-storage.db.old`

5. Start Rockstar Games Launcher and keep it open.
6. Start GOG Galaxy, reconnect the integration if necessary, select **Sync integrations** from the account menu, and wait for synchronization to finish.

If only installed games remain afterward, follow [Recovering Missing Games After a Storage Reset](#-recovering-missing-games-after-a-storage-reset). To undo the database reset instead, close GOG Galaxy completely, rename the newly created active Rockstar storage database by appending `.new`, and remove `.old` from the matching backup file name. Never replace or restore a plugin database while GOG Galaxy is running.

---

## 🛠️ What to Do If the Plugin Has Problems

If the database reset above does not resolve the problem, create a clean session with fresh diagnostic files before contacting me. The reset procedure preserves the previous database as a `.old` file; the steps below remove the active database so the issue can be reproduced from a clean state.

> [!WARNING]
> A clean diagnostic database also starts without the retained ownership cache. The temporary disappearance of currently uninstalled games is therefore expected during this test. Restore the matching `.old` database afterward or follow the recovery procedure above.

1. Close GOG Galaxy completely, including the system tray application.
2. Open the following directory and delete the existing log files:

   ```text
   %ProgramData%\GOG.com\Galaxy\logs
   ```

3. Open the plugin storage directory:

   ```text
   C:\ProgramData\GOG.com\Galaxy\storage\plugins
   ```

   Delete only the active Rockstar Games database file starting with `rockstar_` and ending in `-storage.db`. Do not delete database files belonging to other integrations. If you are unsure which file is correct, do not delete anything from this directory.
4. Start Rockstar Games Launcher and keep it open. Start GOG Galaxy, reproduce the problem, and then close GOG Galaxy completely so the new log is fully written.
5. Return to the logs directory and locate the newly created Rockstar Games plugin log:

   ```text
   plugin-rockstar-774732b5-69c4-405c-b6c9-92cd55740cfe.log
   ```

Send only this log file, not the entire logs folder. Include the exact steps taken, the expected and actual result, and whether the problem can be reproduced. After collecting the fresh log, the matching `.old` Rockstar storage database can be restored as described in the previous section.

Without a fresh plugin log and a detailed description, I cannot reliably determine what is causing the problem. Once everything is ready, continue with [Support & Feedback](#-support--feedback) for contact options.

---

## 🙏 Credits

**Original Community Integration**  
Tylerbrawl  
[Tylerbrawl/Galaxy-Plugin-Rockstar](https://github.com/tylerbrawl/Galaxy-Plugin-Rockstar)

**64-bit Port, Maintenance and Improvements**  
melcom

---

## ❤️ Special Thanks

Big thanks to [MacStew](https://www.gog.com/u/MacStew) for testing, for tracking down the exact Steam App IDs and folder names for L.A. Noire and Red Dead Redemption 2, and for providing the detailed logs, screenshots, and follow-up verification that made Red Dead Redemption support possible.

---

## 🤝 Support & Feedback

**GitHub Issues are intentionally disabled.** Health-related limitations prevent me from reliably managing separate issue trackers across all of my plugin repositories.

Before contacting me, follow **What to Do If the Plugin Has Problems** and prepare a fresh Rockstar Games plugin log with a detailed description.

* **GOG:** Send me a message or add me as a friend through my [GOG profile](https://www.gog.com/u/melcom).
* **Email:** `melcom @ gmx.net`
* **Discord:** `.melcom` - the leading dot is part of the username. You can send me a message or add me as a friend.

Logs can be attached directly or shared using an accessible cloud storage link, such as Dropbox, OneDrive, Google Drive, or a similar service. Response times may vary depending on my health and available development time. Thank you for your understanding.
