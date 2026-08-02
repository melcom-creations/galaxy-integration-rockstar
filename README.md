# Rockstar Games Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This maintained 64-bit version of the original community integration imports supported Rockstar Games titles into GOG Galaxy 2.1+. It supports the current Galaxy client and Python 3.13.

---

## ✨ Features

* Imports supported Rockstar games and unlocked achievements
* Detects Rockstar, Steam, and Epic installations on Windows
* Installs, launches, and uninstalls games through the required launcher
* Tracks playtime locally and preserves it between sessions
* Retains successfully confirmed ownership between plugin restarts
* Supports Rockstar Social Club web authentication

---

## 📦 Installation

### Automatic Installation with Plugin Updater (Recommended)

Use the [melcom GOG Galaxy Plugin Updater](https://github.com/melcom-creations/galaxy-integrations-64bit/tree/main/tools/melcom-galaxy_plugin_updater), run `update-plugins.bat`, and follow the displayed instructions.

### Manual Installation

1. Close GOG Galaxy completely, including the system tray application.
2. Download the [latest release package](https://github.com/melcom-creations/galaxy-integration-rockstar/releases/latest).
3. Extract the ZIP archive directly into:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
```

The archive already contains the required `rockstar_774732b5-69c4-405c-b6c9-92cd55740cfe` folder. Continue with **First Start and Initial Sync** below.

> [!IMPORTANT]
> Do not place backup copies of this plugin inside the `plugins\installed` directory. GOG Galaxy scans every folder inside this directory during startup, so duplicate plugin folders can cause GUID conflicts or load an outdated version.

---

## 🚀 First Start and Initial Sync

1. Start Steam or Epic Games Launcher if any installed Rockstar titles were purchased there, and keep the required store client open.
2. Start Rockstar Games Launcher and keep it open.
3. Start GOG Galaxy.
4. Connect the Rockstar Games integration through **Settings -> Integrations** if necessary.
5. Complete the Rockstar Social Club login when prompted.
6. Select **Sync integrations** once from the account menu and wait until it finishes. Do not start another manual synchronization while it is running.

---

## 🎮 Library Visibility, Ownership Retention, and Missing Games

On Windows, ownership is determined from Rockstar Games Launcher logs, confirmed local installations, and the plugin's retained ownership cache. Rockstar does not currently provide the integration with a reliable, complete account-library response, so installed Steam and Epic copies provide important confirmation for games purchased through those stores.

Once the plugin has successfully confirmed a supported title, it stores that title in its persistent ownership cache. The game should then remain in the Rockstar library inside GOG Galaxy after it is uninstalled. Deleting, renaming, or resetting the Rockstar plugin storage database starts the plugin with an empty ownership cache. Games that are neither installed nor still present in the available Rockstar Games Launcher logs cannot always be reconstructed automatically.

### ♻️ Recovering Missing Games After a Storage Reset

> [!IMPORTANT]
> If only currently installed titles remain visible after reconnecting the integration, the retained ownership cache was most likely empty or removed. The missing games must be confirmed again before the plugin can retain them for later sessions.

1. Temporarily install each missing supported title through Rockstar Games Launcher, Steam, or Epic Games Launcher. Install them one at a time if disk space is limited.
2. Keep Steam or Epic Games Launcher running when applicable. Start Rockstar Games Launcher and wait until it recognizes the games.
3. Close GOG Galaxy and Rockstar Games Launcher completely, but leave the required store clients running.
4. Start Rockstar Games Launcher again, then start GOG Galaxy. Reconnect the integration if necessary and select **Sync integrations** exactly once.
5. Wait for completion and confirm that the games appear under Rockstar. They can normally be uninstalled again afterward and should remain visible unless plugin storage is reset again.

---

## ⚙️ Optional Configuration

When GOG Galaxy starts the integration, the plugin automatically creates `config.cfg` in the plugin root if it does not already exist. Edit this generated file to change settings, and keep `default_config.cfg` unchanged.

* `enable_steam_fallback=True` searches configured Steam libraries when a supported game is missing from the Windows uninstall registry. Disable it only if Steam detection is not wanted.
* `enable_legacy_online_game_scraper=False` should remain disabled during normal use. It enables an undocumented Social Club request for advanced diagnostics and is automatically disabled for the session after a failure.

---

## ⚠️ Known Limitation

The plugin can retrieve Rockstar Social Club friend data, but GOG Galaxy does not currently display Rockstar friends reliably in its interface. This limitation does not affect library synchronization, achievements, game launching, installation detection, or playtime tracking.

---

## 🛠️ Troubleshooting

Before resetting anything, restart Rockstar Games Launcher and GOG Galaxy, keep Steam or Epic Games Launcher open when required, and complete one synchronization. For missing uninstalled games, use the recovery procedure above first.

### 🔄 Reset Plugin Storage

> [!WARNING]
> Resetting plugin storage also clears retained ownership. Currently uninstalled games may disappear until they are confirmed again. Do not use this as the first response to a missing game.

1. Close GOG Galaxy completely, including its system tray application.
2. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`.
3. Locate the active file that starts with `rockstar_` and ends in `-storage.db`. If more than one file matches and you are unsure which is active, stop and do not rename anything.
4. Append `.old` to the matching file name, for example: `rockstar_xxxxxxxxx-storage.db.old`.
5. Start Rockstar Games Launcher, then GOG Galaxy. Reconnect the integration if necessary and complete one synchronization.

If only installed games remain, follow [Recovering Missing Games After a Storage Reset](#-recovering-missing-games-after-a-storage-reset). To undo the reset, close GOG Galaxy, append `.new` to the newly created active database, and remove `.old` from the backup. Never restore a database while Galaxy is running.

### 🧪 Create a Fresh Diagnostic Log

> [!WARNING]
> A clean diagnostic session also starts without retained ownership. Uninstalled games may temporarily disappear during this test.

1. Close GOG Galaxy completely.
2. Delete the existing files from `%ProgramData%\GOG.com\Galaxy\logs\` so the next session produces fresh logs.
3. In `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`, append `.diagnostic` to the active Rockstar `-storage.db` file. Keep this backup.
4. Start Rockstar Games Launcher and GOG Galaxy, reproduce the problem, and close Galaxy completely.
5. Send only `%ProgramData%\GOG.com\Galaxy\logs\plugin-rockstar-774732b5-69c4-405c-b6c9-92cd55740cfe.log` together with the exact steps, expected result, and actual result.

After the test, close Galaxy and restore the desired `.old` or `.diagnostic` database by removing its added suffix. If no backup can restore the missing ownership data, use the recovery procedure above. Continue with [Support & Feedback](#-support--feedback) for contact options.

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

Before contacting me, follow [Troubleshooting](#-troubleshooting) and prepare a fresh Rockstar Games plugin log with a detailed description.

* **GOG:** Send me a message or add me as a friend through my [GOG profile](https://www.gog.com/u/melcom).
* **Email:** `melcom @ gmx.net`
* **Discord:** `.melcom` - the leading dot is part of the username. You can send me a message or add me as a friend.

Logs can be attached directly or shared using an accessible cloud storage link, such as Dropbox, OneDrive, Google Drive, or a similar service. Response times may vary depending on my health and available development time. Thank you for your understanding.
