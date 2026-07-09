# Changelog

All notable changes to this plugin will be documented in this file.

---

## Version 2.0.9-64bit (Pre-Release)

### Overview for Version 2.0.9-64bit

Maintenance release focused on GTA V Enhanced launch reliability and stale-entry cleanup, while keeping the previously introduced GTA IV fallback and Social Club 401 handling improvements.

### Changed in Version 2.0.9-64bit

- **GTA IV alternate executable fallback:** if **PlayGTAIV.exe** cannot be found anywhere under the detected install path, `launch_game_from_title_id()` now also checks for **LaunchGTAIV.exe**, a known rename from a long-standing community fix for Rockstar Games Launcher issues. The wrapper-launch behavior (-launchTitleInFolder, @commandline.txt) is preserved for the renamed exe as well.
- **Clearer launch failure log message:** the error now states that alternate names and all subfolders were checked, and suggests verifying the game files or reinstalling, to help distinguish a broken/incomplete local install from an actual plugin bug.
- **Social Club played-games auth fix:** `get_played_games()` previously only retried once with a "light" BearerToken refresh, which could succeed while the underlying Social Club session cookies stayed stale, causing the same 401 (scauth) to repeat on every scan and forcing a fallback to the launcher log every time. A second retry stage now performs a full re-authentication if the light refresh is insufficient.
- **Reduced log noise from launcher-log fallback:** reading to the end of a launcher log file without finding all games is expected control flow (it happens for every old/empty rotated log file), not an actual error. This is now logged at debug level instead of error level.

### Fixed in Version 2.0.9-64bit

- **GTA V Enhanced one-click launch path:** `gta5_gen9` no longer relies on a Launcher-only timeout flow for Galaxy's Play button. It now uses `PlayGTAV.exe` as the launch wrapper (same pattern as Legacy), so Galaxy can request a direct launch flow instead of just opening the Launcher and waiting for manual user interaction.
- **Enhanced process tracking alignment:** `gta5_gen9` now tracks `GTA5_Enhanced.exe` via `trackEXE`, so running-state detection follows the real game process instead of a short-lived wrapper process.
- **Shared GTA V achievements across Legacy and Enhanced:** `gta5_gen9` now uses the same Social Club achievement ID (`gtav`) as `gta5`, so the already unlocked Rockstar achievements are shown for both variants instead of leaving Enhanced empty.
- **Galaxy cache compatibility note for Enhanced achievements:** in some client states, Galaxy can keep stale local metadata for `rockstar_9001` and still show `N/A` even after successful achievement import. If that happens, remove the Rockstar plugin storage DB from `C:\ProgramData\GOG.com\Galaxy\storage\plugins\` and run a fresh **Sync integrations**.
- **Enhanced install detection stability at startup:** when the Launcher's "Installed titles" table is temporarily unavailable in recent log files, `get_path_to_game_with_source()` now has a Windows GameConfigStore fallback (`HKCU\System\GameConfigStore\Children\*\MatchedExeFullPath`) for `GTA5_Enhanced.exe`, preventing transient "not installed" flips.
- **Stale unknown install-request behavior cleanup:** unknown `game_id` install requests are now logged and ignored, and the obsolete local stale-entry notice flow (`stale_library_entry.html`) has been removed.

### Technical Breakdown for Version 2.0.9-64bit

#### 1. ALT_LAUNCH_EXE fallback in local.py

Added an ALT_LAUNCH_EXE mapping (currently only gta4 to LaunchGTAIV.exe) that is checked, including a recursive subfolder search, after the primary launchEXE search fails. The wrapper-exe detection for command-line arguments now also falls back to checking the original expected exe name, so a rename does not silently drop -launchTitleInFolder/@commandline.txt handling.

#### 2. Two-stage refresh in get_played_games() (http_client.py)

Added a `full_refresh_attempted` parameter to `get_played_games()`. If the retry after `_refresh_credentials_social_club_light()` still fails, the method now calls the full `refresh_credentials()` (base + Social Club re-authentication) once before giving up, then retries `get_played_games()` a final time. This resolves the case where the BearerToken refreshes successfully but the Social Club session cookies used by `getGoogleTagManagerSetupData` remain stale.

#### 3. Log level change in parse_log_file() (plugin.py)

`ROCKSTAR_LOG_FINISHED_ERROR` (log.error) renamed to `ROCKSTAR_LOG_FINISHED` and changed to log.debug, since it is raised as part of normal control flow (`NoGamesInLogException`, caught and handled by the caller) rather than an actual failure.

#### 4. gta5_gen9 wrapper launch normalization (game_cache.py)

The `gta5_gen9` launch entry now uses `PlayGTAV.exe` and adds `trackEXE = GTA5_Enhanced.exe`. This keeps launch behavior consistent with Rockstar's wrapper-driven flow and gives more reliable running-state tracking.

#### 5. Enhanced install fallback via GameConfigStore (local.py)

For `gta5_gen9`, a fallback lookup was added to `get_path_to_game_with_source()` using Windows GameConfigStore `MatchedExeFullPath` entries for `GTA5_Enhanced.exe`, with a short cache window to avoid repeated registry scans.

#### 6. Stale-entry notice removal (plugin.py)

The previous unknown-install explanatory HTML popup path was removed. Unknown install requests are now handled as no-op warnings, and the plugin no longer depends on `stale_library_entry.html`.

#### 7. Galaxy local metadata/cache caveat (client-side)

Achievement import for `rockstar_9001` can succeed while the Galaxy UI still renders `N/A` due to stale local cache state. In that case, resetting the Rockstar plugin storage DB and re-running integration sync refreshes the local metadata layer.

---

## Version 2.0.8-64bit

### Overview for Version 2.0.8-64bit

Maintenance release focused on safer Steam fallback behavior for GTA variants and clearer update metadata structure. The goal is to avoid false-positive installs and keep update information consistent for tooling and long-term maintenance.

### Changed in Version 2.0.8-64bit

- **Steam fallback hardening for GTA variants:** for `gta3`/`gtavc`/`gtasa` and their Definitive Edition counterparts (`gta3unreal`/`gtavcunreal`/`gtasaunreal`), Steam fallback now requires a matching `appmanifest_<AppID>.acf` to be present. For this title family, loose folder-name/wildcard heuristics are skipped to prevent alias/folder collisions from producing duplicate or incorrect detections.
- **Manifest update metadata clarified and standardized:** Added a structured `external_updater` block and aligned manifest field layout with the other plugins. This makes release/update information easier to discover and parse consistently in external tooling and maintenance workflows, and reduces configuration drift between plugin repositories.

### Technical Breakdown for Version 2.0.8-64bit

#### 1. Steam fallback guardrails for GTA variants

Fallback detection for GTA variant IDs now requires explicit Steam appmanifest evidence, which avoids heuristic collisions that can produce incorrect local detection states.

#### 2. Manifest metadata consistency

Updater metadata now follows the shared manifest structure used across plugins, improving release discoverability and reducing repository-to-repository drift.

---

## Version 2.0.7-64bit

### Overview for Version 2.0.7-64bit

Maintenance release focused on Steam fallback accuracy and title mapping completeness for Rockstar games. The changes remove wrong AppID/folder assumptions and add missing mappings so fallback detection behaves predictably.

### Fixed in Version 2.0.7-64bit

- **L.A. Noire Steam App ID Was Wrong:** `STEAM_GAME_IDS["lanoire"]` (`local.py`) was `12400`, which is not L.A. Noire's Steam App ID. Corrected to `110800` (confirmed against the official Steam store page). This is why the Steam-fallback appmanifest lookup for L.A. Noire never found the game.
- **L.A. Noire Fallback Folder Name Had an Extra Space:** the folder-name fallback search for `lanoire` looked for `"L.A. Noire"`, but the actual Steam install folder is named `"L.A.Noire"` (no space). Corrected in both `search_names` and the (currently unused) `known_folder_names` list.

### Added in Version 2.0.7-64bit

- **Red Dead Redemption 2 Steam App ID Mapping:** `rdr2` was present in `game_cache.py` but missing from `STEAM_GAME_IDS` in `local.py`, so Steam-installed RDR2 could never be detected via the fallback path. Added `"rdr2": 1174180` (confirmed against the official Steam store page; install folder name `"Red Dead Redemption 2"` already matches the game's `friendlyName`, so no extra folder-name mapping is needed).
- **GTA: The Trilogy - The Definitive Edition Steam App ID Mappings:** `gta3unreal`, `gtasaunreal`, and `gtavcunreal` were already fully defined in `game_cache.py` (including `launchEXE`) but missing from `STEAM_GAME_IDS` in `local.py`, so none of the three Unreal remakes could be detected via the Steam fallback path. Added `"gta3unreal": 1546970`, `"gtasaunreal": 1547000`, and `"gtavcunreal": 1546990` (all three confirmed against the official Steam store pages).
- **GTA: The Trilogy - The Definitive Edition Fallback Folder Names:** the folder-name fallback search for these three titles had no dedicated entries and would have fallen back to `friendlyName` (e.g. `"Grand Theft Auto: Vice City - The Definitive Edition"`), which does not match the actual Steam install folder names. Added dedicated `search_names` entries for `gta3unreal` (`"GTA III - The Definitive Edition"`), `gtasaunreal` (`"GTA San Andreas - The Definitive Edition"`), and `gtavcunreal` (`"GTA Vice City - The Definitive Edition"`), and kept the (currently unused) `known_folder_names` list in sync.

### Technical Breakdown for Version 2.0.7-64bit

#### 1. AppID mapping corrections and additions

Incorrect and missing Steam AppID mappings were corrected for affected Rockstar titles, so appmanifest-driven fallback detection can resolve installations reliably.

#### 2. Folder-name fallback alignment

Search aliases were aligned with real Steam install folder names to reduce false negatives when metadata-based lookup is not sufficient.

---

## Version 2.0.6-64bit

### Overview for Version 2.0.6-64bit

This release enables Steam fallback out of the box and hardens several stability-critical runtime paths. It improves install detection reliability, prevents stuck background loops, and reduces the risk of event-loop blocking under Windows.

### Fixed in Version 2.0.6-64bit

- `check_for_new_games()` and `check_game_statuses()` (`plugin.py`) only reset their `checking_for_new_games`/ `updating_game_statuses` guard flags at the normal end of the function. An exception partway through left the flag stuck on `True` forever, silently preventing `tick()` from ever starting that background task again until a full plugin restart. Both are now wrapped in `try`/`finally` so the flag always clears.
- `get_json_from_request_strict()` (`http_client.py`) caught any exception and retried by recursively calling itself with no limit, so a persistent network/auth/parse failure could recurse indefinitely. It now gives up and raises after 3 attempts.
- `get_game_size_in_bytes()` and `game_pid_from_tasklist()` (`local.py`) are declared `async` but blocked the event loop with a synchronous `subprocess.Popen(...).communicate()` call. Switched both to `asyncio.create_subprocess_shell()` so they no longer stall the plugin while waiting on `dir`/`tasklist`.

### Changed in Version 2.0.6-64bit

- `enable_steam_fallback` (`consts.py`, `default_config.cfg`) default changed from `False` to `True`. Steam detection for Rockstar classics (`gtasa`, `gtavc`, `gta3`, `gta4`, `lanoire`, `mp3`, `bully`) now works out of the box; users previously had to discover and manually enable this setting themselves to see those titles at all.
- `get_steam_library_folders()` (`local.py`) now actually uses the existing `STEAM_LIBRARY_FOLDERS_CACHE_SECONDS` constant to cache its result for 5 minutes instead of re-reading the registry and `libraryfolders.vdf` on every call. This constant was declared but unused before; it matters more now that Steam fallback is on by default for everyone.

### Documentation for Version 2.0.6-64bit

- `README.md` rewritten: shortened and de-duplicated the installation steps, fixed a section-ordering bug that separated the "Resetting the Plugin Database" steps from their own heading, and documented that `config.cfg` is created automatically on first start so no manual setup is required.

### Technical Breakdown for Version 2.0.6-64bit

#### 1. Runtime reliability hardening

Background guard flags are now always released via `try`/`finally`, request retries are bounded, and subprocess-heavy operations no longer block the async event loop.

#### 2. Steam fallback operational defaults

The default fallback behavior and library-folder caching were aligned so Steam-backed Rockstar detection works immediately while reducing repeated registry and VDF reads.

---

## Version 2.0.5-64bit

### Overview for Version 2.0.5-64bit

Maintenance release aimed at improving launcher-only start flow for GTA classics. The update makes launch feedback in Galaxy more intuitive and keeps UI state aligned while the Rockstar Launcher handoff is in progress.

### Changed in Version 2.0.5-64bit

- `LAUNCHER_ONLY_GRACE_SECONDS` (`local.py`) increased from 15 to 22 seconds, giving slower systems (older HDDs, a Launcher that itself takes a while to boot) more realistic time to pick and start a classic title (`gtasa`, `gtavc`, `gta3`) inside the Rockstar Games Launcher.

### Fixed in Version 2.0.5-64bit

- The Play button for the three Launcher-only classics stayed purple/clickable for the entire grace window after being clicked, since `launch_game()` (`plugin.py`) only called `update_local_game_status()` once `launch_game_from_title_id()` returned, i.e. only after the whole wait was already over. This looked like the click had no effect and could tempt a user into clicking "Play" again mid-wait. `launch_game()` now immediately reports `Running` the moment the Launcher is opened for one of these three titles, greying out the button right away; if nothing is actually started within the grace window, it is reverted back to `Installed` so the button becomes clickable again. A new `self.launching_title_ids` set keeps `check_game_status()` (and therefore the periodic background status check `check_game_statuses()`, driven by `tick()`) in agreement with this immediate update for the duration of the grace window, so the periodic check does not flip the button back to purple while the user is still choosing in the Launcher.

### Technical Breakdown for Version 2.0.5-64bit

#### 1. Launcher handoff UX timing

The launcher grace window was extended to better fit slower systems and reduce premature state rollbacks during manual game selection in the Rockstar Launcher.

#### 2. Local status synchronization

Immediate `Running` signaling plus temporary launch-state tracking keeps foreground actions and periodic status checks in sync until a definitive installed/running outcome is known.

---

## Version 2.0.4-64bit

### Fixed in Version 2.0.4-64bit

- Security fix: several exception-logging calls in `http_client.py` (`get_json_from_request_strict`, `_get_user_json`, `_get_bearer`, `get_played_games`, `_refresh_credentials_social_club_light`, `_refresh_credentials_social_club`, `authenticate`) and `plugin.py` (`authenticate`, `pass_login_credentials`, `get_owned_games_online`) logged `repr(e)` unconditionally, regardless of the `log_sensitive_data` setting. For exceptions raised by failed authenticated aiohttp requests (e.g. `aiohttp.ClientResponseError`, thrown by the Social Club's 401 responses), `repr(e)` includes the full `RequestInfo` of the failing request, including the raw `Cookie` and `Authorization` headers that were sent, i.e. the user's live session cookie and bearer token in plain text. Since this exception was thrown on every plugin start due to the ongoing Social Club 401 issue, every log file generated by the plugin contained a valid, replayable session cookie. Added a new `safe_exception_repr()` helper in `consts.py` that all of these call sites now use instead of raw `repr(e)`; it only reveals the full exception detail when `log_sensitive_data=True` is explicitly set, consistent with how every other sensitive value in this codebase is handled. Unconditional `log.debug(cookies)` in `get_bearer_from_cookie_jar()` (`http_client.py`) was fixed the same way.

---

## Version 2.0.3-64bit

### Added in Version 2.0.3-64bit

- Added Steam fallback detection for Rockstar titles installed via Steam, including Grand Theft Auto III, Grand Theft Auto IV, Grand Theft Auto: Vice City, and Grand Theft Auto: San Andreas, gated behind an opt-in `enable_steam_fallback` configuration setting so default launcher-only behavior is unaffected.
- Added `stale_library_entry.html`, a local notice page explaining that a given GOG Galaxy library entry is an orphaned leftover from an earlier plugin state and pointing the user to the correct, working "Grand Theft Auto V" entry.

### Fixed in Version 2.0.3-64bit

- Fixed Steam fallback path resolution for nested GTA IV installations where the executable lives under `Grand Theft Auto IV\GTAIV`.
- Fixed the `gtasa` launch executable name in `game_cache.py` from `gta_sa.exe` to `gta-sa.exe` so Steam-detected San Andreas installs are recognized correctly.
- `install_game()` in `plugin.py` now opens the stale-entry notice page (via Microsoft Edge `--app` mode, falling back to the default browser) when it receives an install request for a `game_id` that does not map to any known title, instead of silently doing nothing.

### Changed in Version 2.0.3-64bit

- `get_path_to_game()` now resolves Steam-installed Rockstar game directories more robustly by checking nested install folders when the executable is not directly in the top-level game folder.

---

## Version 2.0.2-64bit

### Fixed in Version 2.0.2-64bit

- Fixed `install_game()`, `uninstall_game()`, and `launch_game()` in `plugin.py` crashing with `TypeError: can only concatenate str (not "NoneType") to str` when GOG Galaxy requests an action for a `game_id` that does not map to any entry in `games_cache` (a stale `game_id` cached client-side by GOG Galaxy from an earlier state, not reported by `import_owned_games`). These requests are now logged as a warning and ignored instead of crashing the plugin.
- Fixed `LocalClient.get_local_launcher_path()` in `local.py` appending a stray, unmatched double-quote character to the end of the Rockstar Games Launcher path, which corrupted the path used for install and uninstall requests. Replaced with `os.path.join()`.
- Fixed `install_game_from_title_id()` and `uninstall_game_from_title_id()` in `local.py` passing the launcher command as a single concatenated string to `subprocess.call()` with `shell=False`. Combined with the stray-quote path bug above, this caused a `PermissionError: [WinError 5] Access denied` on every install/uninstall click even though the Rockstar Games Launcher was correctly installed. Arguments are now passed as a list.
- Fixed `LocalClient.get_game_size_in_bytes()` and `LocalClient.game_pid_from_tasklist()` in `local.py` crashing with `UnicodeDecodeError` on non-English Windows installs. Both run `chcp 65001 & ...` to force UTF-8 output, but `chcp`'s own confirmation message is printed in the console's previous codepage before the switch takes effect, so it is not actually UTF-8, and decoding it as such crashed the local size import, which in turn left the Play button greyed out even for correctly installed and owned games. `chcp`'s own output is now suppressed, and decoding uses `errors="replace"` as a defensive fallback.
- Fixed `parse_log_file()` in `plugin.py` opening the Rockstar Games Launcher log with `encoding="utf-8"`, which raised `UnicodeDecodeError` on any non-ASCII line (error report GUIDs, hardware names, and similar), silently discarding lines before they could be checked for the ownership markers used to detect owned games. Switched to `encoding="latin-1"`, which cannot raise a decode error for any byte value.
- Added a fallback to `get_owned_games()` in `plugin.py` for when both the launcher log parser and the online Social Club scrape return nothing: any title confirmed installed via the Windows uninstall registry is now also reported as owned, since a legitimately installed Rockstar title implies ownership.
- Fixed `check_game_statuses()` in `plugin.py` only re-checking titles already present in `local_games_cache`, populated once by `get_local_games()` at plugin start. A game installed afterwards outside of this plugin's own `install_game()` (e.g. directly via the Rockstar Games Launcher) was never picked up until GOG Galaxy was fully restarted. `check_game_statuses()` now sweeps all known titles from `total_games_cache` on every tick, so installs and uninstalls are detected without requiring a restart.

---

## Version 2.0.1-64bit

### Fixed in Version 2.0.1-64bit

- Fixed `LocalClient.get_path_to_game()` in `local.py` reporting a game as installed based solely on a stale Windows uninstall registry key. The directory referenced by `InstallLocation` is now checked for existence on disk before the game is treated as installed.
- Fixed `galaxyutils.config_parser` so it loads `config.cfg` and `default_config.cfg` from the plugin root instead of from `modules/`.

---

## Version 2.0.0-64bit

### Overview for Version 2.0.0-64bit

Initial release of the 64-bit Rockstar plugin for GOG Galaxy 2.1+. Plugin identity and metadata were updated to reflect the new `melcom` ownership and Galaxy 2.1+ compatibility.

### Added in Version 2.0.0-64bit

- Added bundled `modules/` dependencies so the plugin resolves its own libraries independently of the Galaxy client's internal Python environment.

### Changed in Version 2.0.0-64bit

- Updated `manifest.json` metadata for the 64-bit Rockstar plugin release.
- Updated the authentication flow and JavaScript injection behavior to match the working login process of the original plugin.

---

## Notes

- Version numbers 2.0.0 through 2.0.5 represent the complete internal development history of this plugin, consolidated and renumbered prior to its first public release. No version in this range was ever publicly distributed.

## Version 0.5.15 and Earlier

*(Legacy releases by [tylerbrawl](https://github.com/tylerbrawl), see the
[original repository](https://github.com/tylerbrawl/Galaxy-Plugin-Rockstar) for historical changelog
entries.)*
