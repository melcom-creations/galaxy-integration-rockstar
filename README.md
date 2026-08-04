# Rockstar Games Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This maintained 64-bit version of the original community integration imports supported Rockstar Games titles into GOG Galaxy 2.1+. It supports the current Galaxy client and Python 3.13.

## ✨ Features

* Imports supported Rockstar games and unlocked achievements
* Detects Rockstar, Steam, and Epic installations on Windows
* Installs, launches, and uninstalls games through the required launcher
* Tracks playtime locally and preserves it between sessions
* Retains successfully confirmed ownership between plugin restarts
* Supports Rockstar Social Club web authentication

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

## 🚀 First Start and Initial Sync

1. Start Steam or Epic Games Launcher if any installed Rockstar titles were purchased there, and keep the required store client open.
2. Start Rockstar Games Launcher and keep it open.
3. Start GOG Galaxy.
4. Connect the Rockstar Games integration through **Settings -> Integrations** if necessary.
5. Complete the Rockstar Social Club login when prompted.
6. Select **Sync integrations** once from the account menu and wait until it finishes. Do not start another manual synchronization while it is running.

## ⚙️ Optional Configuration

When GOG Galaxy starts the integration, the plugin automatically creates `config.cfg` in the plugin root if it does not already exist. Edit this generated file to change settings, and keep `default_config.cfg` unchanged.

* `enable_steam_fallback=True` searches configured Steam libraries when a supported game is missing from the Windows uninstall registry. Disable it only if Steam detection is not wanted.
* `enable_legacy_online_game_scraper=False` should remain disabled during normal use. It enables an undocumented Social Club request for advanced diagnostics and is automatically disabled for the session after a failure.

## 🧰 Troubleshooting

Before resetting anything, restart Rockstar Games Launcher and GOG Galaxy, keep Steam or Epic Games Launcher open when required, and complete one synchronization.

### 🔎 What to Do If Games Are Missing

The plugin detects ownership from Rockstar Games Launcher logs, confirmed installations, and its retained ownership cache. If only installed titles appear, missing games must be confirmed again before the plugin can retain them for later sessions.

1. Temporarily install each missing supported title through Rockstar Games Launcher, Steam, or Epic Games Launcher. Install them one at a time if disk space is limited.
2. Keep Steam or Epic Games Launcher running when applicable and wait until Rockstar Games Launcher recognizes the game.
3. Restart Rockstar Games Launcher and GOG Galaxy, then select **Sync integrations** exactly once.
4. Confirm that the game appears under Rockstar. It can normally be uninstalled again afterward and should remain visible.

This may be necessary after the first connection, after reconnecting, after a storage reset, or if the retained ownership cache does not contain the title. Games that are neither installed nor present in current launcher logs cannot always be reconstructed automatically.

### 🏆 Remove Incorrectly Imported Achievements

Version 2.0.13 and later exclude Rockstar achievement entries that contain only partial progress and are explicitly marked as not achieved. This prevents new progress-only entries from appearing as unlocked achievements in Galaxy.

If an earlier plugin version has already imported incorrect achievements, a normal synchronization may not remove them:

1. Confirm that Version 2.0.13 or later is installed.
2. In **Settings -> Integrations**, fully disconnect the Rockstar integration and remove its imported data.
3. Close GOG Galaxy and Rockstar Games Launcher completely.
4. Start Rockstar Games Launcher, then GOG Galaxy. Reconnect the Rockstar integration and complete one synchronization.
5. Galaxy should rebuild the Rockstar achievement data using only genuinely unlocked achievements.

Disconnecting the integration may also clear retained ownership information. If uninstalled games are missing after reconnecting, follow [What to Do If Games Are Missing](#-what-to-do-if-games-are-missing). Do not delete or edit Galaxy's main database manually.

### 🧪 Create a Fresh Diagnostic Log

1. Close GOG Galaxy completely.
2. Delete the existing files from `%ProgramData%\GOG.com\Galaxy\logs\` so the next session produces fresh logs.
3. Start the required store client, Rockstar Games Launcher, and GOG Galaxy.
4. Reproduce the problem once, then close GOG Galaxy completely.
5. Send `%ProgramData%\GOG.com\Galaxy\logs\plugin-rockstar-774732b5-69c4-405c-b6c9-92cd55740cfe.log` together with the exact steps, expected result, and actual result.

### 🔄 Reset Plugin Storage

> [!WARNING]
> This is a last resort. Resetting plugin storage also clears retained ownership, so uninstalled games may disappear until they are confirmed again.

1. Close GOG Galaxy completely, including its system tray application.
2. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`.
3. Locate the active file that starts with `rockstar_` and ends in `-storage.db`. If more than one file matches and you are unsure which is active, stop and do not rename anything.
4. Append `.old` to the file name, for example: `rockstar_xxxxxxxxx-storage.db.old`.
5. Start Rockstar Games Launcher, then GOG Galaxy. Reconnect the integration if necessary and complete one synchronization.

To undo the reset, close GOG Galaxy, append `.new` to the newly created database, and remove `.old` from the backup. Never restore a database while Galaxy is running. If games are missing afterward, follow [What to Do If Games Are Missing](#-what-to-do-if-games-are-missing).

Continue with [Support & Feedback](#-support--feedback) if the problem remains.

## ⚠️ Known Limitation

GOG Galaxy does not currently display imported Rockstar friends reliably. This does not affect library synchronization, achievements, launching, installation detection, or playtime tracking.

## 🙏 Credits and Special Thanks

**Original Community Integration**  
Tylerbrawl  
[Tylerbrawl/Galaxy-Plugin-Rockstar](https://github.com/tylerbrawl/Galaxy-Plugin-Rockstar)

**64-bit Port, Maintenance and Improvements**  
melcom

Big thanks to [MacStew](https://www.gog.com/u/MacStew) for testing, for tracking down the exact Steam App IDs and folder names for L.A. Noire and Red Dead Redemption 2, and for providing the detailed logs, screenshots, and follow-up verification that made Red Dead Redemption support possible.

## 🤝 Support & Feedback

**GitHub Issues are intentionally disabled.** Health-related limitations prevent me from reliably managing separate issue trackers across all of my plugin repositories.

Before contacting me, follow [Troubleshooting](#-troubleshooting) and prepare a fresh Rockstar Games plugin log with a detailed description.

* **GOG:** Send me a message or add me as a friend through my [GOG profile](https://www.gog.com/u/melcom).
* **Email:** `melcom @ gmx.net`
* **Discord:** `.melcom` - the leading dot is part of the username. You can send me a message or add me as a friend.

Logs can be attached directly or shared using an accessible cloud storage link, such as Dropbox, OneDrive, Google Drive, or a similar service. Response times may vary depending on my health and available development time. Thank you for your understanding.
