from typing import Optional
from winreg import *
import logging as log
import os
import re
import subprocess
import asyncio
import glob
from time import time

# Cache Steam library folder resolution to avoid repeated registry/VDF reads on status ticks.
STEAM_LIBRARY_FOLDERS_CACHE_SECONDS = 300

from galaxy.proc_tools import pids

from consts import WINDOWS_UNINSTALL_KEY, LOG_SENSITIVE_DATA, CONFIG_OPTIONS
from game_cache import games_cache

# Steam App ID mappings for Rockstar games
STEAM_GAME_IDS = {
    "gtasa": 12120,  # Grand Theft Auto: San Andreas
    "gta3": 12100,   # Grand Theft Auto III
    "gtavc": 12110,  # Grand Theft Auto: Vice City
    "gta4": 12210,   # Grand Theft Auto IV
    "lanoire": 110800,  # L.A. Noire
    "mp3": 204100,   # Max Payne 3
    "bully": 12200,  # Bully: Scholarship Edition
    "rdr2": 1174180,  # Red Dead Redemption 2
    # Grand Theft Auto: The Trilogy - The Definitive Edition (Unreal remakes).
    "gta3unreal": 1546970,   # GTA III - The Definitive Edition
    "gtasaunreal": 1547000,  # GTA San Andreas - The Definitive Edition
    "gtavcunreal": 1546990,  # GTA Vice City - The Definitive Edition
}

# These classics are handled as launcher-only for Steam installs.
LAUNCHER_ONLY_TITLES = {"gtasa", "gtavc", "gta3"}
LAUNCHER_ONLY_GRACE_SECONDS = 22

# Require appmanifest evidence for these GTA variants to avoid heuristic false positives.
STRICT_STEAM_MANIFEST_TITLES = {
    "gta3",
    "gtavc",
    "gtasa",
    "gta3unreal",
    "gtavcunreal",
    "gtasaunreal",
}

# Known alternate executable names used by community launch fixes.
ALT_LAUNCH_EXE = {
    "gta4": ["LaunchGTAIV.exe"],
}


def check_if_process_exists(pid):
    if not pid:
        return False
    if int(pid) in pids():
        return True
    return False


class LocalClient:
    def __init__(self):
        self.root_reg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        self.user_reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        self.installer_location = None
        self._steam_library_folders_cache = None
        self._steam_library_folders_cache_time = None
        self._gameconfigstore_gta5_gen9_cache_path = None
        self._gameconfigstore_gta5_gen9_cache_time = None
        # Set by plugin.py after resolving the user's Documents path.
        self.documents_location = None
        self.get_local_launcher_path()

    def get_local_launcher_path(self):
        try:
            if CONFIG_OPTIONS['rockstar_launcher_path_override']:
                self.installer_location = CONFIG_OPTIONS['rockstar_launcher_path_override']
                if LOG_SENSITIVE_DATA:
                    log.debug("ROCKSTAR_INSTALLER_PATH: " + self.installer_location)
                else:
                    log.debug("ROCKSTAR_INSTALLER_PATH: ***")
            else:
                # The uninstall key for the launcher is called Rockstar Games Launcher.
                key = OpenKey(self.root_reg, WINDOWS_UNINSTALL_KEY + "Rockstar Games Launcher")
                dir, type = QueryValueEx(key, "InstallLocation")
                self.installer_location = os.path.join(dir, "Launcher.exe")
                if LOG_SENSITIVE_DATA:
                    log.debug("ROCKSTAR_INSTALLER_PATH: " + self.installer_location)
                else:
                    log.debug("ROCKSTAR_INSTALLER_PATH: ***")
        except WindowsError:
            self.installer_location = None
        return self.installer_location

    async def kill_launcher(self):
        # The Launcher exits without displaying an error message if LauncherPatcher.exe is killed before Launcher.exe.
        subprocess.Popen("taskkill /im SocialClubHelper.exe")

    def get_path_to_game_registry_only(self, title_id):
        if not games_cache[title_id].get('guid'):
            # Titles with guid=None are not expected to exist in uninstall registry.
            return None
        try:
            key = OpenKey(self.root_reg, WINDOWS_UNINSTALL_KEY + games_cache[title_id]['guid'])
            dir, type = QueryValueEx(key, "InstallLocation")
            log.debug(f"ROCKSTAR_REGISTRY_FOUND: Game {title_id} found in registry at: {dir if LOG_SENSITIVE_DATA else '***'}")
            # Validate registry install path exists to avoid stale-key false positives.
            if not dir or not os.path.isdir(dir):
                if LOG_SENSITIVE_DATA:
                    log.debug("ROCKSTAR_STALE_REGISTRY_KEY: Found an uninstall key for " + title_id +
                              " but the InstallLocation " + str(dir) + " no longer exists on disk. Treating as "
                              "not installed.")
                else:
                    log.debug("ROCKSTAR_STALE_REGISTRY_KEY: Found an uninstall key for " + title_id +
                              " but the InstallLocation no longer exists on disk. Treating as not installed.")
                return None
            log.debug(f"ROCKSTAR_GAME_INSTALLED: Game {title_id} is installed at: {dir if LOG_SENSITIVE_DATA else '***'}")
            return dir
        except WindowsError:
            return None

    def get_path_to_game_with_source(self, title_id):
        """Return install source and path for launch decisions.

        Resolution order: registry -> launcher log -> GameConfigStore -> Steam fallback.
        """
        registry_path = self.get_path_to_game_registry_only(title_id)
        if registry_path:
            return 'registry', registry_path

        log_path = self.get_path_to_game_launcher_log_fallback(title_id)
        if log_path:
            return 'launcher_log', log_path

        gameconfigstore_path = self.get_path_to_game_gameconfigstore_fallback(title_id)
        if gameconfigstore_path:
            return 'gameconfigstore', gameconfigstore_path

        if not CONFIG_OPTIONS.get('enable_steam_fallback', False):
            log.debug("ROCKSTAR_GAME_NOT_INSTALLED: The game with ID " + title_id + " is not installed.")
            return None, None

        log.debug("ROCKSTAR_GAME_NOT_INSTALLED: Game " + title_id + " not found in registry or launcher log; "
                  "trying Steam fallback.")
        steam_path = self.get_path_to_game_steam_fallback(title_id)
        if steam_path:
            return 'steam', steam_path
        return None, None

    def get_installed_titles_from_launcher_log(self):
        """Read installed titles from Rockstar Launcher logs.

        Parses the [titlestorage] "Installed titles" table and returns
        {launcher title: install path}.
        """
        documents_location = getattr(self, 'documents_location', None)
        if not documents_location:
            return {}

        installed = {}
        current_log_count = 0
        while current_log_count < 10:
            log_file_append = "" if current_log_count == 0 else ".0" + str(current_log_count)
            log_file = os.path.join(documents_location,
                                     "Rockstar Games\\Launcher\\launcher" + log_file_append + ".log")
            current_log_count += 1
            if not os.path.isfile(log_file):
                continue
            try:
                with open(log_file, encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except Exception:
                continue

            in_table = False
            for line in lines:
                if "[titlestorage]" not in line:
                    continue
                if "Installed titles:" in line:
                    in_table = True
                    continue
                if not in_table:
                    continue
                content = line.split("[titlestorage]", 1)[1].strip()
                if not content or content.startswith("Title "):
                    # The header row ("Title   Progress   Version   Location") - not a data row.
                    continue
                # Split fixed-width-like columns by 2+ spaces.
                columns = re.split(r"\s{2,}", content)
                if len(columns) >= 4:
                    installed[columns[0].strip()] = columns[3].strip()
                else:
                    # Unexpected row format usually means the table section ended.
                    in_table = False

            if installed:
                # First readable table from newest log is sufficient.
                break
        return installed

    def get_path_to_game_launcher_log_fallback(self, title_id):
        """Resolve install path from launcher logs for titles without registry GUIDs."""
        if games_cache[title_id].get('guid'):
            # Titles with GUID should be resolved through registry-first logic.
            return None

        installed_titles = self.get_installed_titles_from_launcher_log()
        if not installed_titles:
            return None

        target_name = games_cache[title_id].get('launcherLogTitle', games_cache[title_id]['friendlyName'])
        location = installed_titles.get(target_name)
        if not location or not os.path.isdir(location):
            return None

        exe_name = games_cache[title_id]['launchEXE']
        if os.path.isfile(os.path.join(location, exe_name)):
            log.debug(f"ROCKSTAR_LAUNCHER_LOG_INSTALL_FOUND: Found {title_id} via the Launcher's own log at: "
                      f"{location if LOG_SENSITIVE_DATA else '***'}")
            return location

        resolved = self.resolve_nested_game_install_dir(location, title_id)
        if resolved:
            log.debug(f"ROCKSTAR_LAUNCHER_LOG_INSTALL_FOUND: Found {title_id} via the Launcher's own log "
                      f"(nested) at: {resolved if LOG_SENSITIVE_DATA else '***'}")
            return resolved

        log.debug(f"ROCKSTAR_LAUNCHER_LOG_EXE_MISSING: Launcher log lists {title_id} as installed at "
                  f"{location if LOG_SENSITIVE_DATA else '***'}, but {exe_name} was not found there.")
        return None

    def get_path_to_game(self, title_id):
        _, path = self.get_path_to_game_with_source(title_id)
        return path

    def get_steam_library_folders(self):
        if (self._steam_library_folders_cache is not None and self._steam_library_folders_cache_time is not None
                and time() < self._steam_library_folders_cache_time + STEAM_LIBRARY_FOLDERS_CACHE_SECONDS):
            return self._steam_library_folders_cache

        try:
            key = OpenKey(ConnectRegistry(None, HKEY_CURRENT_USER), r"Software\Valve\Steam")
            steam_path, _ = QueryValueEx(key, "SteamPath")
        except WindowsError:
            self._steam_library_folders_cache = []
            self._steam_library_folders_cache_time = time()
            return []

        library_folders = []
        steamapps = os.path.join(steam_path, "steamapps")
        if os.path.isdir(steamapps):
            library_folders.append(steamapps)

        library_folders_config = os.path.join(steamapps, "libraryfolders.vdf")
        if os.path.isfile(library_folders_config):
            try:
                with open(library_folders_config, encoding="utf-8", errors="replace") as f:
                    library_text = f.read()
                for match in re.finditer(r'"path"\s*"([^"]+)"', library_text):
                    # Unescape VDF backslashes before building filesystem paths.
                    library_path = match.group(1).replace('\\\\', '\\')
                    if library_path:
                        steamapps_path = os.path.join(library_path, "steamapps")
                        if os.path.isdir(steamapps_path) and steamapps_path not in library_folders:
                            library_folders.append(steamapps_path)
            except Exception:
                log.debug("ROCKSTAR_STEAM_LIBFOLDERS_PARSE_FAILED: Could not parse Steam libraryfolders.vdf")

        self._steam_library_folders_cache = library_folders
        self._steam_library_folders_cache_time = time()
        return library_folders

    def get_steam_app_install_dir(self, library_folder, steam_app_id):
        manifest_path = os.path.join(library_folder, f"appmanifest_{steam_app_id}.acf")
        if not os.path.isfile(manifest_path):
            return None

        try:
            with open(manifest_path, encoding="utf-8", errors="replace") as f:
                manifest_text = f.read()
            match = re.search(r'"installdir"\s*"([^"]+)"', manifest_text)
            if match:
                install_dir = os.path.join(library_folder, "common", match.group(1))
                if os.path.isdir(install_dir):
                    return install_dir
        except Exception:
            pass
        return None

    def resolve_nested_game_install_dir(self, install_dir, title_id):
        """Resolve install directories where the game executable is stored one level deeper."""
        exe_name = games_cache[title_id]['launchEXE']
        candidate_dirs = [install_dir]
        if os.path.isdir(install_dir):
            try:
                for entry in os.listdir(install_dir):
                    child_path = os.path.join(install_dir, entry)
                    if os.path.isdir(child_path):
                        candidate_dirs.append(child_path)
            except Exception:
                pass

        for candidate_dir in candidate_dirs:
            exe_path = os.path.join(candidate_dir, exe_name)
            if os.path.isfile(exe_path):
                return candidate_dir
        return None

    def get_path_to_game_steam_fallback(self, title_id):
        """Fallback method to find Steam-installed Rockstar games when not found in Windows Registry."""
        if title_id not in STEAM_GAME_IDS:
            log.debug(f"ROCKSTAR_STEAM_NO_MAPPING: Game {title_id} has no Steam App ID mapping.")
            return None

        steam_app_id = STEAM_GAME_IDS[title_id]
        steam_game_name = games_cache[title_id]['friendlyName']

        steam_library_folders = self.get_steam_library_folders()
        if not steam_library_folders:
            # Fallback to common paths when Steam is not installed or library parsing failed.
            steam_library_folders = [
                os.path.expandvars(r'C:\Program Files\Steam\steamapps'),
                os.path.expandvars(r'C:\Program Files (x86)\Steam\steamapps'),
                os.path.expandvars(r'D:\Steam\steamapps'),
                os.path.expandvars(r'E:\Steam\steamapps'),
                os.path.expandvars(r'F:\Steam\steamapps'),
            ]

        for library_folder in steam_library_folders:
            if not os.path.isdir(library_folder):
                continue

            # First try the Steam app manifest to resolve the install directory precisely.
            install_dir = self.get_steam_app_install_dir(library_folder, steam_app_id)
            if install_dir:
                resolved_dir = self.resolve_nested_game_install_dir(install_dir, title_id)
                if resolved_dir:
                    if LOG_SENSITIVE_DATA:
                        log.debug(f"ROCKSTAR_STEAM_FOUND: Game {title_id} found in Steam at: {resolved_dir}")
                    else:
                        log.debug(f"ROCKSTAR_STEAM_FOUND: Game {title_id} found in Steam")
                    return resolved_dir

            if title_id in STRICT_STEAM_MANIFEST_TITLES:
                # For these titles we only trust manifest-backed detection.
                continue

            # Try folder name matches inside the steamapps/common directory.
            common_path = os.path.join(library_folder, "common")
            if os.path.isdir(common_path):
                search_names = [steam_game_name]
                if title_id == "gtasa":
                    search_names.extend(["Grand Theft Auto San Andreas", "GTA San Andreas"])
                elif title_id == "gta3":
                    search_names.extend(["Grand Theft Auto III", "GTA III"])
                elif title_id == "gtavc":
                    search_names.extend(["Grand Theft Auto Vice City", "GTA Vice City"])
                elif title_id == "lanoire":
                    search_names.extend(["L.A.Noire"])
                elif title_id == "bully":
                    search_names.extend(["Bully Scholarship Edition", "Bully"])
                elif title_id == "gta3unreal":
                    search_names.extend(["GTA III - The Definitive Edition"])
                elif title_id == "gtasaunreal":
                    search_names.extend(["GTA San Andreas - The Definitive Edition"])
                elif title_id == "gtavcunreal":
                    search_names.extend(["GTA Vice City - The Definitive Edition"])

                for candidate in search_names:
                    game_dir = os.path.join(common_path, candidate)
                    if os.path.isdir(game_dir):
                        resolved_dir = self.resolve_nested_game_install_dir(game_dir, title_id)
                        if resolved_dir:
                            if LOG_SENSITIVE_DATA:
                                log.debug(f"ROCKSTAR_STEAM_FOUND: Game {title_id} found in Steam at: {resolved_dir}")
                            else:
                                log.debug(f"ROCKSTAR_STEAM_FOUND: Game {title_id} found in Steam")
                            return resolved_dir

                # As a final fallback, scan matching folders using wildcard names.
                wildcard_patterns = [
                    f"*{steam_game_name.replace(':', '').replace(' ', '*')}*",
                ]
                for pattern in wildcard_patterns:
                    for path in glob.glob(os.path.join(common_path, pattern)):
                        if os.path.isdir(path):
                            exe_path = os.path.join(path, games_cache[title_id]['launchEXE'])
                            if os.path.isfile(exe_path):
                                if LOG_SENSITIVE_DATA:
                                    log.debug(f"ROCKSTAR_STEAM_FOUND: Game {title_id} found in Steam at: {path}")
                                else:
                                    log.debug(f"ROCKSTAR_STEAM_FOUND: Game {title_id} found in Steam")
                                return path

        if LOG_SENSITIVE_DATA:
            log.debug(f"ROCKSTAR_STEAM_NOT_FOUND: Game {title_id} (Steam App {steam_app_id}) not found in Steam paths")
        else:
            log.debug(f"ROCKSTAR_STEAM_NOT_FOUND: Game {title_id} not found in Steam paths")
        return None

    def get_path_to_game_gameconfigstore_fallback(self, title_id):
        # Windows fallback for gta5_gen9 when launcher log does not list it yet.
        if title_id != "gta5_gen9":
            return None

        if (self._gameconfigstore_gta5_gen9_cache_path and self._gameconfigstore_gta5_gen9_cache_time
                and time() < self._gameconfigstore_gta5_gen9_cache_time + 300):
            cached = self._gameconfigstore_gta5_gen9_cache_path
            if os.path.isfile(os.path.join(cached, "GTA5_Enhanced.exe")):
                return cached

        try:
            children = OpenKey(self.user_reg, r"System\GameConfigStore\Children")
        except WindowsError:
            return None

        index = 0
        while True:
            try:
                subkey_name = EnumKey(children, index)
                index += 1
            except OSError:
                break

            try:
                subkey = OpenKey(children, subkey_name)
                matched_exe, _ = QueryValueEx(subkey, "MatchedExeFullPath")
            except WindowsError:
                continue

            if not matched_exe:
                continue

            if os.path.basename(str(matched_exe)).lower() != "gta5_enhanced.exe":
                continue

            install_dir = os.path.dirname(str(matched_exe))
            if os.path.isfile(os.path.join(install_dir, "PlayGTAV.exe")):
                self._gameconfigstore_gta5_gen9_cache_path = install_dir
                self._gameconfigstore_gta5_gen9_cache_time = time()
                log.debug(f"ROCKSTAR_GAMECONFIGSTORE_INSTALL_FOUND: Found gta5_gen9 via GameConfigStore at: "
                          f"{install_dir if LOG_SENSITIVE_DATA else '***'}")
                return install_dir

        return None

    async def get_game_size_in_bytes(self, title_id) -> Optional[int]:
        path = self.get_path_to_game(title_id)
        if not path:
            log.warning(f"ROCKSTAR_GAME_SIZE_FAILURE: The game {title_id} is not installed or could not be found.")
            return None
        # Normalize before quoting to avoid cmd path parsing edge cases.
        path = os.path.normpath(path)
        # Quote path unless already quoted.
        if path[:1] != '"':
            path = f'"{path}"'
        find_game_size = await asyncio.create_subprocess_shell(
            # Suppress chcp banner to keep output decoding stable across locales.
            f'chcp 65001 >nul & dir {path} /a /s /-c', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        output, err = await find_game_size.communicate()

        # Parse summary line; tolerate undecodable bytes instead of failing hard.
        line_list = output.decode(errors="replace").splitlines()
        if len(line_list) < 2:
            # Capture raw output for diagnosis when dir returns no parseable summary.
            log.warning(
                f"ROCKSTAR_GAME_SIZE_DIR_EMPTY_OUTPUT: The 'dir' command for {title_id} returned no usable "
                f"output. Return code: {find_game_size.returncode}. "
                f"Path used: {path if LOG_SENSITIVE_DATA else '***'}. "
                f"Stdout: {output.decode(errors='replace').strip()!r}. "
                f"Stderr: {err.decode(errors='replace').strip()!r}."
            )
            return None
        game_size_line = line_list[len(line_list) - 2]
        size = None
        if "bytes" in game_size_line:
            size = int([str(s) for s in game_size_line.split() if s.isdigit()][1])
        if size:
            log.debug(f"ROCKSTAR_GAME_SIZE: The size of {title_id} is {size} bytes.")
        else:
            log.warning(f"ROCKSTAR_GAME_SIZE_FAILURE: The size of {title_id} could not be determined!")
        return size

    async def game_pid_from_tasklist(self, title_id) -> str:
        pid = None
        tracked_key = "trackEXE" if "trackEXE" in games_cache[title_id] else "launchEXE"
        tracked_exe = os.path.basename(games_cache[title_id][tracked_key])
        # Force UTF-8 tasklist output for predictable parsing.
        find_actual_pid = await asyncio.create_subprocess_shell(
            f'chcp 65001 >nul & tasklist /FI "IMAGENAME eq {tracked_exe}" /FI "STATUS eq running" '
            f'/FO LIST', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        output, err = await find_actual_pid.communicate()

        for line in output.decode(errors="replace").splitlines():
            if "PID" in line:
                pid = [str(s) for s in line.split() if s.isdigit()][0]
                break
        return pid

    async def launch_game_from_title_id(self, title_id):
        source, path = self.get_path_to_game_with_source(title_id)
        if not path:
            log.error(f"ROCKSTAR_LAUNCH_FAILURE: The game {title_id} could not be launched.")
            return
        path = path.replace('"', '').replace(',0', '')

        if source == 'steam' and title_id in STEAM_GAME_IDS and title_id in LAUNCHER_ONLY_TITLES:
            # Open launcher and wait briefly for user-started launch for launcher-only Steam classics.
            launcher_path = self.get_local_launcher_path()
            if not launcher_path:
                log.error(f"ROCKSTAR_LAUNCH_FAILURE: Could not find the Rockstar Games Launcher to open for "
                          f"{title_id}.")
                return None
            log.debug(f"ROCKSTAR_LAUNCH_VIA_LAUNCHER_ONLY: Opening the Rockstar Games Launcher for {title_id} "
                      f"and waiting up to {LAUNCHER_ONLY_GRACE_SECONDS}s for the user to start it there.")
            subprocess.Popen([launcher_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)

            # Use fixed grace window so Play does not remain blocked indefinitely.
            for _ in range(LAUNCHER_ONLY_GRACE_SECONDS):
                await asyncio.sleep(1)
                pid = await self.game_pid_from_tasklist(title_id)
                if pid:
                    log.debug(f"ROCKSTAR_LAUNCH_LAUNCHER_ONLY_SUCCESS: {title_id} was started from within the "
                              f"Launcher.")
                    return pid
            log.debug(f"ROCKSTAR_LAUNCH_LAUNCHER_ONLY_TIMEOUT: {title_id} was not started from within the "
                      f"Launcher within {LAUNCHER_ONLY_GRACE_SECONDS}s. Giving up cleanly.")
            return None
        elif source == 'steam' and title_id in STEAM_GAME_IDS:
            # Steam-sourced titles must start through steam:// to preserve ownership/DRM handoff.
            steam_app_id = STEAM_GAME_IDS[title_id]
            log.debug(f"ROCKSTAR_LAUNCH_VIA_STEAM: Launching {title_id} through Steam (App ID {steam_app_id}).")
            try:
                os.startfile(f"steam://rungameid/{steam_app_id}")
            except OSError as e:
                log.error(f"ROCKSTAR_STEAM_LAUNCH_FAILURE: Could not launch {title_id} via Steam ({e}).")
                return None
        else:
            expected_exe = games_cache[title_id]['launchEXE']
            game_path = os.path.join(path, expected_exe)
            if not os.path.isfile(game_path):
                # Search nested folders when install root is one level above executable.
                for root, _, files in os.walk(path):
                    if expected_exe.lower() in (f.lower() for f in files):
                        game_path = os.path.join(root, expected_exe)
                        break

            if not os.path.isfile(game_path) and title_id in ALT_LAUNCH_EXE:
                # Try known alternate executable names before failing.
                for alt_exe in ALT_LAUNCH_EXE[title_id]:
                    alt_path = os.path.join(path, alt_exe)
                    if os.path.isfile(alt_path):
                        game_path = alt_path
                        log.debug(f"ROCKSTAR_LAUNCH_ALT_EXE: {expected_exe} not found for {title_id}, using "
                                  f"known alternate {alt_exe} instead.")
                        break
                    for root, _, files in os.walk(path):
                        if alt_exe.lower() in (f.lower() for f in files):
                            game_path = os.path.join(root, alt_exe)
                            log.debug(f"ROCKSTAR_LAUNCH_ALT_EXE: {expected_exe} not found for {title_id}, "
                                      f"using known alternate {alt_exe} instead.")
                            break
                    if os.path.isfile(game_path):
                        break

            if not os.path.isfile(game_path):
                log.error(f"ROCKSTAR_LAUNCH_FAILURE: Could not find launch executable {expected_exe} for "
                          f"{title_id} in {path} (also checked known alternate names and all subfolders). "
                          f"The file may be missing, renamed, or the install path may be stale. Please verify "
                          f"the game files or reinstall.")
                return

            log.debug(f"ROCKSTAR_LAUNCH_REQUEST: Requesting to launch {game_path}...")

            cmd = [game_path]
            # The expected_exe's own name is normally used to detect the "Play*.exe" wrapper pattern. If a
            # known alternate name was used instead (see ALT_LAUNCH_EXE), it is a rename of that same wrapper
            # exe under a different name, so the wrapper behavior still applies and is preserved even
            # because the renamed file no longer starts with "play".
            is_wrapper_exe = (os.path.basename(game_path).lower().startswith("play")
                               or os.path.basename(expected_exe).lower().startswith("play"))
            if is_wrapper_exe:
                cmd.extend(["-launchTitleInFolder", path])
                if "cmdLineArgs" in games_cache[title_id]:
                    cmd.extend(games_cache[title_id]["cmdLineArgs"].split())
                commandline_file = os.path.join(path, "@commandline.txt")
                if os.path.isfile(commandline_file):
                    cmd.append("@commandline.txt")
                    log.debug(f"ROCKSTAR_LAUNCH_COMMANDLINE: Using @commandline.txt for {title_id}")
                else:
                    log.debug(f"ROCKSTAR_LAUNCH_COMMANDLINE: No @commandline.txt found for {title_id}, starting wrapper without it")
            else:
                if "cmdLineArgs" in games_cache[title_id]:
                    cmd.extend(games_cache[title_id]["cmdLineArgs"].split())
                log.debug(f"ROCKSTAR_LAUNCH_DIRECT: Starting non-wrapper executable for {title_id}")

            log.debug(f"ROCKSTAR_LAUNCH_CMD: {' '.join(cmd)}")
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             shell=False, cwd=path)

        launcher_pid = None
        retries = 120
        while not launcher_pid:
            await asyncio.sleep(1)
            launcher_pid = await self.game_pid_from_tasklist("launcher")
            retries -= 1
            if retries == 0:
                log.debug("ROCKSTAR_LAUNCHER_PID_FAILURE: The Rockstar Games Launcher took too long to launch!")
                return None
        log.debug(f"ROCKSTAR_LAUNCHER_PID: {launcher_pid}")

        # After launcher boot, poll for game process; extend while launcher remains active.
        retries = 30
        while True:
            await asyncio.sleep(1)
            pid = await self.game_pid_from_tasklist(title_id)
            if pid:
                return pid
            retries -= 1
            if retries == 0:
                # Keep waiting while launcher is still active (updates/first-start can be slow).
                if await self.game_pid_from_tasklist("launcher"):
                    log.debug(f"ROCKSTAR_LAUNCH_WAITING: The game {title_id} has not launched yet, but the Rockstar "
                              f"Games Launcher is still running. Restarting the loop...")
                    retries += 30
                else:
                    return None

    def install_game_from_title_id(self, title_id):
        if not self.installer_location:
            return
        subprocess.call([self.installer_location, "-enableFullMode", f"-install={title_id}"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)

    def uninstall_game_from_title_id(self, title_id):
        if not self.installer_location:
            return
        subprocess.call([self.installer_location, "-enableFullMode", f"-uninstall={title_id}"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)