import os
import sys

MODULES_PATH = os.path.join(os.path.dirname(__file__), "modules")
if MODULES_PATH not in sys.path:
    sys.path.insert(0, MODULES_PATH)

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform, PresenceState
from galaxy.api.types import NextStep, Authentication, Game, LocalGame, LocalGameState, UserInfo, Achievement, \
    GameTime, UserPresence
from galaxy.api.errors import InvalidCredentials, AuthenticationRequired, NetworkError, UnknownError

from file_read_backwards import FileReadBackwards
from time import time
from typing import List, Any, Optional
import asyncio
import dataclasses
import datetime
import logging as log
import os
import pickle
import re
import sys
import webbrowser

from consts import AUTH_PARAMS, NoGamesInLogException, NoLogFoundException, IS_WINDOWS, LOG_SENSITIVE_DATA, \
    ARE_ACHIEVEMENTS_IMPLEMENTED, CONFIG_OPTIONS, get_unix_epoch_time_from_date, safe_exception_repr
import galaxyutils.config_parser as config_parser
from game_cache import games_cache, get_game_title_id_from_ros_title_id, get_achievement_id_from_ros_title_id, \
    get_game_title_id_from_google_tag_id, get_game_title_id_from_online_title_id, ignore_game_title_ids_list
from http_client import BackendClient
from version import __version__

if IS_WINDOWS:
    import ctypes.wintypes
    from local import LocalClient, check_if_process_exists, LAUNCHER_ONLY_TITLES, LAUNCHER_ONLY_GRACE_SECONDS


@dataclasses.dataclass
class RunningGameInfo(object):
    _pid = None
    _start_time = None

    def set_info(self, pid):
        self._pid = pid
        self._start_time = datetime.datetime.now().timestamp()

    def get_pid(self):
        return self._pid

    def clear_pid(self):
        self._pid = None

    def get_start_time(self):
        return self._start_time

    def update_start_time(self):
        self._start_time = datetime.datetime.now().timestamp()


class RockstarPlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.Rockstar, __version__, reader, writer, token)
        log.debug(f"ROCKSTAR_CONFIG_STATE: Plugin version {__version__} started. Config file in use: "
                  f"{config_parser.CONFIG_PATH}. Loaded value of enable_steam_fallback: "
                  f"{CONFIG_OPTIONS.get('enable_steam_fallback')}; enable_legacy_online_game_scraper: "
                  f"{CONFIG_OPTIONS.get('enable_legacy_online_game_scraper')}.")
        self.games_cache = games_cache
        self._http_client = BackendClient(self.store_credentials)
        self._local_client = None
        self.total_games_cache = self.create_total_games_cache()
        self.friends_cache = []
        self.presence_cache = {}
        self.owned_games_cache = []
        self.last_online_game_check = time() - 300
        # The legacy Social Club played-games scraper uses undocumented browser endpoints. One failure opens this
        # circuit breaker for the rest of the process so a healthy local integration is not forced through repeated
        # credential refresh attempts every five minutes.
        self.legacy_online_game_scraper_available = CONFIG_OPTIONS['enable_legacy_online_game_scraper']
        self.local_games_cache = {}
        self.game_time_cache = {}
        self.running_games_info_list = {}
        # Titles currently in launcher-only grace window.
        # check_game_status() treats them as Running to keep button state stable.
        self.launching_title_ids = set()
        self.game_is_loading = True
        self.checking_for_new_games = False
        self.updating_game_statuses = False
        self.buffer = None
        if IS_WINDOWS:
            self._local_client = LocalClient()
            self.buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, self.buffer)
            self.documents_location = self.buffer.value
            # Used by launcher-log-based install detection.
            self._local_client.documents_location = self.documents_location

    def is_authenticated(self):
        return self._http_client.is_authenticated()

    @staticmethod
    def loads_js(file):
        with open(os.path.abspath(os.path.join(__file__, '..', 'js', file)), 'r') as f:
            return f.read()

    def handshake_complete(self):
        game_time_cache_in_persistent_cache = False
        for key, value in self.persistent_cache.items():
            if key == "game_time_cache":
                self.game_time_cache = pickle.loads(bytes.fromhex(value))
                game_time_cache_in_persistent_cache = True
        if IS_WINDOWS and not game_time_cache_in_persistent_cache:
            # Fallback to local file cache when persistent cache has no game-time snapshot.
            file_location = os.path.join(self.documents_location, "RockstarPlayTimeCache.txt")
            try:
                file = open(file_location, "r")
                for line in file.readlines():
                    if line[:1] != "#":
                        log.debug("ROCKSTAR_LOCAL_GAME_TIME_FROM_FILE: " + str(pickle.loads(bytes.fromhex(line))))
                        self.game_time_cache = pickle.loads(bytes.fromhex(line))
                        break
                if not self.game_time_cache:
                    log.warning("ROCKSTAR_NO_GAME_TIME: The user's played time could not be found in neither the "
                                "persistent cache nor the designated local file. Starting with an empty game-time "
                                "cache.")
            except FileNotFoundError:
                log.warning("ROCKSTAR_NO_GAME_TIME: The user's played time could not be found in neither the persistent"
                            " cache nor the designated local file. Starting with an empty game-time cache.")

    async def authenticate(self, stored_credentials=None):
        try:
            self._http_client.create_session(stored_credentials)
        except KeyError:
            log.error("ROCKSTAR_OLD_LOG_IN: The user has likely previously logged into the plugin with a version less "
                      "than v0.3, and their credentials might be corrupted. Forcing a log-out...")
            raise InvalidCredentials()
        if not stored_credentials:
            # Prepare fingerprint JavaScript mapping for web session injection.
            fingerprint_js = {
                r'https://www.rockstargames.com/': [
                    self.loads_js("fingerprint2.js"),
                    self.loads_js("HashGen.js"),
                    self.loads_js("GenerateFingerprint.js")
                ]
            }
            return NextStep("web_session", AUTH_PARAMS, js=fingerprint_js)
        try:
            log.info("INFO: The credentials were successfully obtained.")
            if LOG_SENSITIVE_DATA:
                cookies = pickle.loads(bytes.fromhex(stored_credentials['cookie_jar']))
                log.debug("ROCKSTAR_COOKIES_FROM_HEX: " + str(cookies))  # sensitive data hidden by default
            # for cookie in cookies:
            #   self._http_client.update_cookies({cookie.name: cookie.value})
            self._http_client.set_current_auth_token(stored_credentials['current_auth_token'])
            self._http_client.set_current_sc_token(stored_credentials['current_sc_token'])
            self._http_client.set_refresh_token_absolute(
                pickle.loads(bytes.fromhex(stored_credentials['refresh_token'])))
            self._http_client.set_fingerprint(stored_credentials['fingerprint'])
            log.info("INFO: The stored credentials were successfully parsed. Beginning authentication...")
            user = await self._http_client.authenticate()
            return Authentication(user_id=user['rockstar_id'], user_name=user['display_name'])
        except (NetworkError, UnknownError):
            raise
        except Exception as e:
            log.warning("ROCKSTAR_AUTH_WARNING: The exception " + safe_exception_repr(e) + " was thrown, presumably "
                        "because of outdated credentials. Attempting to get new credentials...")
            self._http_client.set_auth_lost_callback(True)
            try:
                user = await self._http_client.authenticate()
                return Authentication(user_id=user['rockstar_id'], user_name=user['display_name'])
            except Exception as e:
                log.error("ROCKSTAR_AUTH_FAILURE: Re-authentication failed. " +
                          safe_exception_repr(e))
                log.exception("ROCKSTAR_STACK_TRACE")
                raise InvalidCredentials

    async def pass_login_credentials(self, step, credentials, cookies):
        if LOG_SENSITIVE_DATA:
            log.debug("ROCKSTAR_COOKIE_LIST: " + str(cookies))
        for cookie in cookies:
            if cookie['name'].find("TSc") != -1:
                self._http_client.set_current_auth_token(cookie['value'])
            if cookie['name'] == "BearerToken":
                self._http_client.set_current_sc_token(cookie['value'])
            if cookie['name'] == "RMT":
                if cookie['value'] != "":
                    if LOG_SENSITIVE_DATA:
                        log.debug("ROCKSTAR_REMEMBER_ME: Got RMT: " + cookie['value'])
                    else:
                        # Keep masked output format stable regardless of empty/non-empty token.
                        log.debug("ROCKSTAR_REMEMBER_ME: Got RMT: ***")
                    self._http_client.set_refresh_token(cookie['value'])
                else:
                    if LOG_SENSITIVE_DATA:
                        log.debug("ROCKSTAR_REMEMBER_ME: Got RMT: [Blank!]")
                    else:
                        log.debug("ROCKSTAR_REMEMBER_ME: Got RMT: ***")
                    self._http_client.set_refresh_token('')
            if cookie['name'] == "fingerprint":
                if LOG_SENSITIVE_DATA:
                    log.debug("ROCKSTAR_FINGERPRINT: Got fingerprint: " + cookie['value'].replace("$", ";"))
                else:
                    log.debug("ROCKSTAR_FINGERPRINT: Got fingerprint: ***")
                self._http_client.set_fingerprint(cookie['value'].replace("$", ";"))
                # Store fingerprint with user credentials rather than adding it as a session cookie.
                continue
            if re.search("^rsso", cookie['name']):
                if LOG_SENSITIVE_DATA:
                    log.debug("ROCKSTAR_RSSO: Got " + cookie['name'] + ": " + cookie['value'])
                else:
                    log.debug(f"ROCKSTAR_RSSO: Got rsso-***: {cookie['value'][:5]}***{cookie['value'][-3:]}")
            cookie_object = {
                "name": cookie['name'],
                "value": cookie['value'],
                "domain": cookie['domain'],
                "path": cookie['path']
            }
            self._http_client.update_cookie(cookie_object)
        try:
            user = await self._http_client.authenticate()
        except Exception as e:
            log.error(safe_exception_repr(e))
            raise InvalidCredentials
        return Authentication(user_id=user["rockstar_id"], user_name=user["display_name"])

    async def shutdown(self):
        # Persist playtime snapshot to disk as a fallback when auth/cache state is lost.
        if IS_WINDOWS and self.game_time_cache:
            file_location = os.path.join(self.documents_location, "RockstarPlayTimeCache.txt")
            with open(file_location, "w", encoding="utf-8") as file:
                file.write("# This file contains a cached copy of the user's play time for the Rockstar plugin for "
                           "GOG Galaxy 2.0.\n")
                file.write("# This cache file is managed by the plugin. Manual edits may corrupt play time data.\n")
                file.write(pickle.dumps(self.game_time_cache).hex())
        await self._http_client.close()
        await super().shutdown()

    def create_total_games_cache(self):
        # Build a stable in-memory snapshot used by periodic sweeps and status checks.
        cache = []
        for title_id in list(games_cache):
            cache.append(self.create_game_from_title_id(title_id))
        return cache

    if ARE_ACHIEVEMENTS_IMPLEMENTED:
        async def get_unlocked_achievements(self, game_id, context):
            # Query unlocked achievements from Social Club for the mapped title.

            title_id = get_game_title_id_from_ros_title_id(game_id)
            if title_id is None or title_id not in games_cache:
                log.warning(f"ROCKSTAR_ACHIEVEMENT_UNKNOWN_GAME: Unknown game id '{game_id}', skipping achievements.")
                return []
            if games_cache[title_id]["achievementId"] is None or \
                    (games_cache[title_id]["isPreOrder"]):
                return []
            achievement_id = get_achievement_id_from_ros_title_id(game_id)
            if achievement_id is None:
                return []
            log.debug("ROCKSTAR_ACHIEVEMENT_CHECK: Beginning achievements check for " +
                      title_id + " (Achievement ID: " + achievement_id + ")...")
            url = (f"https://scapi.rockstargames.com/achievements/awardedAchievements?title={achievement_id}"
                   f"&platform=pc&rockstarId={self._http_client.get_rockstar_id()}")
            unlocked_achievements = await self._http_client.get_json_from_request_strict(url)
            achievements_dict = unlocked_achievements["awardedAchievements"]
            achievements_list = []
            for key, value in achievements_dict.items():
                achievement_num = key
                unlock_time = await get_unix_epoch_time_from_date(value["dateAchieved"])
                achievements_list.append(Achievement(unlock_time, achievement_id=achievement_num))
            return achievements_list

    async def get_friends(self) -> List[UserInfo]:
        # Fetch paginated friend data from Social Club.

        url = ("https://scapi.rockstargames.com/friends/getFriendsFiltered?onlineService=sc&nickname=&"
               "pageIndex=0&pageSize=30")
        current_page = None
        for attempt in range(3):
            try:
                candidate = await self._http_client.get_json_from_request_strict(url)
                account_list = candidate.get('rockstarAccountList') if isinstance(candidate, dict) else None
                if isinstance(account_list, dict):
                    current_page = candidate
                    break
                log.debug(f"ROCKSTAR_FRIENDS_STARTUP_RETRY: Social Club returned no friend-list payload "
                          f"(attempt {attempt + 1}/3).")
            except TimeoutError:
                log.warning(f"ROCKSTAR_FRIENDS_TIMEOUT: The request to get the user's friends at page index 0 "
                            f"timed out (attempt {attempt + 1}/3).")
            if attempt < 2:
                await asyncio.sleep(1)
        if current_page is None:
            log.warning("ROCKSTAR_FRIENDS_CACHE_FALLBACK: Social Club did not return a complete startup response. "
                        "Returning the cached friend list.")
            return list(self.friends_cache)
        if LOG_SENSITIVE_DATA:
            log.debug("ROCKSTAR_FRIENDS_REQUEST: " + str(current_page))
        else:
            log.debug("ROCKSTAR_FRIENDS_REQUEST: ***")
        account_list = current_page.get('rockstarAccountList', {}) if isinstance(current_page, dict) else {}
        num_friends = int(account_list.get('totalFriends', 0) or 0)
        num_pages_required = num_friends / 30 if num_friends % 30 != 0 else (num_friends / 30) - 1

        friends_list = account_list.get('rockstarAccounts', [])
        return_list = await self._parse_friends(friends_list)

        if num_pages_required > 0:
            for i in range(1, int(num_pages_required + 1)):
                try:
                    url = ("https://scapi.rockstargames.com/friends/getFriendsFiltered?onlineService=sc&nickname=&"
                           "pageIndex=" + str(i) + "&pageSize=30")
                    for friend in await self._get_friends(url):
                        return_list.append(friend)
                except TimeoutError:
                    log.warning(f"ROCKSTAR_FRIENDS_TIMEOUT: The request to get the user's friends at page index {i} "
                                f"timed out. Returning the merged partial and cached list...")
                    return self._merge_friend_lists(return_list, self.friends_cache)
        return self._merge_friend_lists(return_list, self.friends_cache)

    @staticmethod
    def _merge_friend_lists(*friend_lists):
        merged = []
        seen_ids = set()
        for friend_list in friend_lists:
            for friend in friend_list:
                if friend.user_id not in seen_ids:
                    seen_ids.add(friend.user_id)
                    merged.append(friend)
        return merged

    async def _get_friends(self, url: str) -> List[UserInfo]:
        try:
            current_page = await self._http_client.get_json_from_request_strict(url)
        except TimeoutError:
            raise
        account_list = current_page.get('rockstarAccountList', {}) if isinstance(current_page, dict) else {}
        friends_list = account_list.get('rockstarAccounts', [])
        return await self._parse_friends(friends_list)

    async def _parse_friends(self, friends_list: dict) -> List[UserInfo]:
        return_list = []
        for friend_data in friends_list:
            if not isinstance(friend_data, dict):
                continue
            user_name = friend_data.get('displayName')
            rockstar_id = friend_data.get('rockstarId')
            if not user_name or rockstar_id is None:
                continue
            avatar_uri = f"https://a.rsg.sc/n/{str(user_name).lower()}/l"
            profile_uri = f"https://socialclub.rockstargames.com/member/{user_name}/"
            friend = UserInfo(user_id=str(rockstar_id),
                              user_name=user_name,
                              avatar_url=avatar_uri,
                              profile_url=profile_uri)
            return_list.append(friend)
            for cached_friend in self.friends_cache:
                if cached_friend.user_id == friend.user_id:
                    break
            else:  # An else-statement occurs after a for-statement if the latter finishes WITHOUT breaking.
                self.friends_cache.append(friend)
            if LOG_SENSITIVE_DATA:
                log.debug("ROCKSTAR_FRIEND: Found " + friend.user_name + " (Rockstar ID: " +
                          str(friend.user_id) + ")")
            else:
                log.debug(f"ROCKSTAR_FRIEND: Found {friend.user_name[:1]}*** (Rockstar ID: ***)")
        return return_list

    async def get_owned_games_online(self):
        # Optional compatibility path inherited from the original plugin. This endpoint is undocumented and must not
        # be treated as authoritative authentication or required for the maintained Windows integration.
        owned_title_ids = []
        online_check_success = False
        self.last_online_game_check = time()
        if not self.legacy_online_game_scraper_available:
            return owned_title_ids, online_check_success
        try:
            played_games = await self._http_client.get_played_games()
            for game in played_games:
                owned_title_ids.append(game)
                log.debug("ROCKSTAR_ONLINE_GAME: Found played game " + game + "!")
            online_check_success = True
        except Exception as e:
            self.legacy_online_game_scraper_available = False
            log.warning("ROCKSTAR_LEGACY_SCRAPER_DISABLED: The optional Social Club played-games request failed with "
                        + safe_exception_repr(e) + ". The scraper is disabled for this session; launcher logs and "
                        "local installation data remain active.")
        return owned_title_ids, online_check_success

    async def get_owned_games(self, owned_title_ids=None, online_check_success=False):
        # Build owned games primarily from launcher logs and local install data. Online data is accepted only when the
        # explicitly enabled legacy compatibility scraper completed successfully.
        if owned_title_ids is None:
            owned_title_ids = []
        if not self.is_authenticated():
            raise AuthenticationRequired()

        # The log is in the Documents folder.
        current_log_count = 0
        log_file = None
        log_file_append = ""
        # Read newest launcher log first, then walk rotated files only if needed.
        # Launcher rotates up to 10 logs; inspect all available files if needed.
        while current_log_count < 10:
            # Skip launcher-log probing on non-Windows platforms.
            if not IS_WINDOWS:
                break
            try:
                if current_log_count != 0:
                    log_file_append = ".0" + str(current_log_count)
                log_file = os.path.join(self.documents_location, "Rockstar Games\\Launcher\\launcher" + log_file_append
                                        + ".log")
                if LOG_SENSITIVE_DATA:
                    log.debug("ROCKSTAR_LOG_LOCATION: Checking the file " + log_file + "...")
                else:
                    log.debug("ROCKSTAR_LOG_LOCATION: Checking the file ***...")  # The path to the Launcher log file
                    # likely contains the user's PC profile name (C:\Users\[Name]\Documents...).
                owned_title_ids = await self.parse_log_file(log_file, owned_title_ids, online_check_success)
                break
            except NoGamesInLogException:
                log.debug("ROCKSTAR_LOG_EMPTY: There are no owned games listed in " + str(log_file) + ". Moving to "
                          "the next log file...")
                current_log_count += 1
            except NoLogFoundException:
                log.warning("ROCKSTAR_LAST_LOG_REACHED: There are no more log files that can be found and/or read "
                            "from. Assuming that the online list is correct...")
                break
            except Exception:
                break
        if current_log_count == 10:
            log.debug("ROCKSTAR_LAST_LOG_REACHED: All available launcher logs were checked. Keeping the existing "
                      "owned-games cache and confirmed local installations.")

        # Last-resort ownership fallback: confirmed local installs (registry/log/Steam checks).
        if not owned_title_ids and IS_WINDOWS and self._local_client:
            locally_installed = [title_id for title_id in games_cache
                                  if title_id != "launcher" and self._local_client.get_path_to_game(title_id)]
            if locally_installed:
                owned_title_ids = locally_installed
                log.debug(f"ROCKSTAR_INSTALLED_FALLBACK: Log and online ownership checks both found nothing; "
                          f"falling back to confirmed installed titles (registry or Steam): {locally_installed}")

        for title_id in owned_title_ids:
            # Normalize incoming ids from different Rockstar endpoints into games_cache keys.
            mapped_key = title_id
            if title_id not in games_cache:
                # Try Google Tag id first (e.g. GTAV_PC), then online numeric id.
                try:
                    mapped = get_game_title_id_from_google_tag_id(title_id)
                except Exception:
                    mapped = None
                if not mapped:
                    # Try online numeric id
                    try:
                        mapped = get_game_title_id_from_online_title_id(title_id)
                    except Exception:
                        mapped = None
                if mapped:
                    mapped_key = mapped
                else:
                    log.warning(f"ROCKSTAR_UNKNOWN_TITLE_ID: Could not map owned title id '{title_id}' to known game; skipping")
                    continue

            game = self.create_game_from_title_id(mapped_key)
            if game not in self.owned_games_cache:
                log.debug("ROCKSTAR_ADD_GAME: Adding " + mapped_key + " to owned games cache...")
                self.owned_games_cache.append(game)

        return self.owned_games_cache

    if IS_WINDOWS:
        async def get_local_size(self, game_id: str, context: Any) -> Optional[int]:
            title_id = get_game_title_id_from_ros_title_id(game_id)
            if title_id is None or not self._local_client:
                return None
            return await self._local_client.get_game_size_in_bytes(title_id)

    @staticmethod
    async def parse_log_file(log_file, owned_title_ids, online_check_success):
        owned_title_ids_ = owned_title_ids
        checked_games_count = 0
        # We need to subtract 1 to account for the Launcher.
        total_games_count = len(games_cache) + len(ignore_game_title_ids_list) - 1

        if os.path.exists(log_file):
            # Use latin-1 to avoid decode failures on locale-specific launcher logs.
            with FileReadBackwards(log_file, encoding="latin-1") as frb:
                while checked_games_count < total_games_count:
                    try:
                        line = frb.readline()
                    except UnicodeDecodeError:
                        log.warning("ROCKSTAR_LOG_UNICODE_WARNING: An invalid Unicode character was found in a log line. "
                                    "Continuing to next line...")
                        continue
                    except Exception as e:
                        log.error("ROCKSTAR_LOG_ERROR: Reading from the log file resulted in the exception "
                                  + repr(e) + ". Using the online list... (Please report this issue on the "
                                  "plugin's GitHub page!)")
                        raise
                    if not line:
                        # Expected control flow when a rotated log does not contain all game entries.
                        log.debug("ROCKSTAR_LOG_FINISHED: The entire log file was read, but all of the games "
                                  "could not be accounted for. Proceeding to check the next log file...")
                        raise NoGamesInLogException()
                    # Reconcile launcher ownership with online-derived ownership.
                    if ("launcher" not in line) and ("on branch " in line):  # Found a game!
                        # Each log line for a title branch report describes the title id of the game starting at
                        # character 65. From there, we search for the first occurrence of a colon starting from where
                        # the title_id begins (character 65).
                        end_index = line[65:].index(':') + 65
                        title_id = line[65:end_index].strip()

                        # Ignore title IDs which are present in the ignore_game_title_ids_list.
                        if title_id in ignore_game_title_ids_list:
                            log.debug("ROCKSTAR_IGNORE_GAME: Ignoring owned game " + title_id + "...")
                        else:
                            log.debug("ROCKSTAR_LOG_GAME: The game with title ID " + title_id + " is owned!")
                            if title_id not in owned_title_ids_:
                                if online_check_success is True:
                                    # Case 2: The game is owned, but has not been played.
                                    log.warning("ROCKSTAR_UNPLAYED_GAME: The game with title ID " + title_id +
                                                " is owned, but it has never been played!")
                                owned_title_ids_.append(title_id)
                        checked_games_count += 1

                    elif "no branches!" in line:
                        end_index = line[65:].index(':') + 65
                        title_id = line[65:end_index].strip()

                        # Ignore title IDs which are present in the ignore_game_title_ids_list.
                        if title_id in ignore_game_title_ids_list:
                            log.debug("ROCKSTAR_IGNORE_GAME: Ignoring owned game " + title_id + "...")
                        else:
                            if title_id in owned_title_ids_:
                                # Case 1: The game is not actually owned on the launcher.
                                log.warning("ROCKSTAR_FAKE_GAME: The game with title ID " + title_id + " is not owned on "
                                            "the Rockstar Games Launcher!")
                                owned_title_ids_.remove(title_id)
                        checked_games_count += 1
                    if checked_games_count == total_games_count:
                        break
            return owned_title_ids_
        else:
            raise NoLogFoundException()

    async def get_game_time(self, game_id, context):
        # Track playtime locally based on launch/runtime data.

        title_id = get_game_title_id_from_ros_title_id(game_id)
        if title_id in self.running_games_info_list:
            start_time = self.running_games_info_list[title_id].get_start_time()
            self.running_games_info_list[title_id].update_start_time()
            current_time = datetime.datetime.now().timestamp()
            minutes_passed = (current_time - start_time) / 60
            if not self.running_games_info_list[title_id].get_pid():
                # Game exited; remove stale running marker after accounting time delta.
                del self.running_games_info_list[title_id]
            if self.game_time_cache[title_id]['time_played']:
                total_time_played = self.game_time_cache[title_id]['time_played'] + minutes_passed
                self.game_time_cache[title_id]['time_played'] = total_time_played
                self.game_time_cache[title_id]['last_played'] = current_time
                return GameTime(game_id=game_id, time_played=int(total_time_played), last_played_time=int(current_time))
            else:
                self.game_time_cache[title_id] = {
                    'time_played': minutes_passed,
                    'last_played': current_time
                }
                return GameTime(game_id=game_id, time_played=int(minutes_passed), last_played_time=int(current_time))
        else:
            if title_id not in self.game_time_cache:
                self.game_time_cache[title_id] = {
                    'time_played': None,
                    'last_played': None
                }
            return GameTime(game_id=game_id, time_played=self.game_time_cache[title_id]['time_played'],
                            last_played_time=self.game_time_cache[title_id]['last_played'])

    def game_times_import_complete(self):
        log.debug("ROCKSTAR_GAME_TIME: Pushing the cache of played game times to the persistent cache...")
        self.persistent_cache['game_time_cache'] = pickle.dumps(self.game_time_cache).hex()
        self.push_cache()

    def get_friend_user_name_from_user_id(self, user_id):
        for friend in self.friends_cache:
            if friend.user_id == user_id:
                return friend.user_name
        return None

    async def prepare_user_presence_context(self, user_id_list: List[str]) -> Any:
        if CONFIG_OPTIONS['user_presence_mode'] == 2 or CONFIG_OPTIONS['user_presence_mode'] == 3:
            game = "gtav" if CONFIG_OPTIONS['user_presence_mode'] == 2 else "rdr2"
            try:
                return await self._http_client.get_json_from_request_strict("https://scapi.rockstargames.com/friends/"
                                                                            f"getFriendsWhoPlay?title={game}&platform=pc")
            except Exception as e:
                log.warning(f"ROCKSTAR_PRESENCE_CONTEXT_FAILED: Could not fetch context for mode "
                            f"{CONFIG_OPTIONS['user_presence_mode']}: {safe_exception_repr(e)}")
                return None
        return None

    async def get_user_presence(self, user_id, context):
        # For mode 2/3, stats are queried only when the user owns the target game.

        friend_name = self.get_friend_user_name_from_user_id(user_id)
        if not friend_name:
            return UserPresence(presence_state=PresenceState.Unknown)
        if LOG_SENSITIVE_DATA:
            log.debug(f"ROCKSTAR_PRESENCE_START: Getting user presence for {friend_name} (Rockstar ID: {user_id})...")
        if context and isinstance(context, dict):
            for player in context.get('onlineFriends', []):
                if isinstance(player, dict) and player.get('userId') == user_id:
                    # This user owns the specified game, so we can return this information.
                    break
            else:
                # The user does not own the specified game, so we need to return their last played game.
                return await self._http_client.get_last_played_game(friend_name)
        if CONFIG_OPTIONS['user_presence_mode'] == 0:
            self.presence_cache[user_id] = UserPresence(presence_state=PresenceState.Unknown)
            # 0 - Disable User Presence
        else:
            switch = {
                1: self._http_client.get_last_played_game(friend_name),
                # 1 - Get Last Played Game
                2: self._http_client.get_gta_online_stats(user_id, friend_name),
                # 2 - Get GTA Online Character Stats
                3: self._http_client.get_rdo_stats(user_id, friend_name)
                # 3 - Get Red Dead Online Character Stats
            }
            self.presence_cache[user_id] = await asyncio.create_task(switch[CONFIG_OPTIONS['user_presence_mode']])
        return self.presence_cache[user_id]

    async def open_rockstar_browser(self):
        # This method allows the user to install the Rockstar Games Launcher, if it is not already installed.
        url = "https://www.rockstargames.com/downloads"

        log.info(f"Opening Rockstar website {url}")
        webbrowser.open(url)

    def check_game_status(self, title_id, game_installed=None):
        state = LocalGameState.None_

        if not self._local_client:
            return LocalGame(str(self.games_cache[title_id]["rosTitleId"]), state)

        if game_installed is None:
            game_installed = self._local_client.get_path_to_game(title_id)
        if game_installed:
            state |= LocalGameState.Installed

            if title_id in self.launching_title_ids:
                # Keep UI state consistent during launcher-only grace window.
                state |= LocalGameState.Running
            elif (title_id in self.running_games_info_list and
                    check_if_process_exists(self.running_games_info_list[title_id].get_pid())):
                state |= LocalGameState.Running
            elif title_id in self.running_games_info_list:
                # We will leave the info in the list, because it still contains the game start time for game time
                # tracking. However, we will set the PID to None to indicate that the game has been closed.
                self.running_games_info_list[title_id].clear_pid()

        return LocalGame(str(self.games_cache[title_id]["rosTitleId"]), state)

    if IS_WINDOWS:
        async def get_local_games(self):
            # Return API list and keep a dict cache for fast in-plugin diffing.
            if not self._local_client:
                return []
            local_games = {}
            local_list = []
            for game in self.total_games_cache:
                title_id = get_game_title_id_from_ros_title_id(str(game.game_id))
                if title_id is None or title_id not in self.games_cache:
                    continue
                game_installed = self._local_client.get_path_to_game(title_id)
                if title_id != "launcher" and game_installed:
                    local_game = self.check_game_status(title_id, game_installed)
                    local_games[title_id] = local_game
                    local_list.append(local_game)
                else:
                    continue
            self.local_games_cache = local_games
            log.debug(f"ROCKSTAR_INSTALLED_GAMES: {local_games}")
            return local_list

    async def check_for_new_games(self):
        self.checking_for_new_games = True
        try:
            # Windows ownership is maintained from Rockstar Launcher logs and local installation sources. The old
            # Social Club tracking-page scraper is optional, rate-limited, and protected by a per-session breaker.
            owned_title_ids = None
            online_check_success = False
            if self.legacy_online_game_scraper_available and \
                    (not self.last_online_game_check or time() >= self.last_online_game_check + 300):
                owned_title_ids, online_check_success = await self.get_owned_games_online()
            elif CONFIG_OPTIONS['enable_legacy_online_game_scraper'] and self.legacy_online_game_scraper_available:
                log.debug("ROCKSTAR_LEGACY_SCRAPER_RATE_LIMITED: Waiting for the five-minute compatibility interval.")
            await self.get_owned_games(owned_title_ids, online_check_success)
            await asyncio.sleep(60 if IS_WINDOWS else 300)
        finally:
            # Reset the guard flag even if something above raised, so tick() can start a fresh run instead of
            # this task staying permanently marked as "in progress" until a full plugin restart.
            self.checking_for_new_games = False

    async def check_game_statuses(self):
        self.updating_game_statuses = True
        try:
            # Sweep all known titles so installs done outside plugin actions are detected on next ticks.
            for game in self.total_games_cache:
                title_id = get_game_title_id_from_ros_title_id(str(game.game_id))
                if title_id is None or title_id == "launcher" or title_id not in self.games_cache:
                    continue

                # Keep the sweep resilient: a single malformed title must not block updates for others.
                try:
                    new_local_game = self.check_game_status(title_id)
                except Exception as e:
                    log.warning(f"ROCKSTAR_STATUS_SWEEP_SKIPPED_TITLE: Could not check status for {title_id}: "
                                f"{safe_exception_repr(e)}")
                    continue

                current_local_game = self.local_games_cache.get(title_id)

                if current_local_game is None and new_local_game.local_game_state == LocalGameState.None_:
                    # Never seen before and still not installed - nothing changed, so skip. Avoids reporting a
                    # "None_" state to Galaxy for every never-installed title on every single tick.
                    continue

                if new_local_game != current_local_game:
                    log.debug(f"ROCKSTAR_LOCAL_CHANGE: The status for {title_id} has changed from: "
                              f"{current_local_game} to {new_local_game}.")
                    self.update_local_game_status(new_local_game)
                    self.local_games_cache[title_id] = new_local_game

            await asyncio.sleep(5)
        finally:
            # Always clear update guard, even on failures.
            self.updating_game_statuses = False

    def list_running_game_pids(self):
        info_list = []
        for key, value in self.running_games_info_list.items():
            info_list.append(value.get_pid())
        return str(info_list)

    if IS_WINDOWS:
        async def launch_platform_client(self):
            if not self._local_client or not self._local_client.get_local_launcher_path():
                await self.open_rockstar_browser()
                return

            pid = await self._local_client.launch_game_from_title_id("launcher")
            if not pid:
                log.warning("ROCKSTAR_LAUNCHER_FAILED: The Rockstar Games Launcher could not be launched!")

    if IS_WINDOWS:
        async def shutdown_platform_client(self):
            if not self._local_client or not self._local_client.get_local_launcher_path():
                await self.open_rockstar_browser()
                return

            await self._local_client.kill_launcher()

    if IS_WINDOWS:
        async def launch_game(self, game_id):
            if not self._local_client or not self._local_client.get_local_launcher_path():
                await self.open_rockstar_browser()
                return

            title_id = get_game_title_id_from_ros_title_id(game_id)
            if title_id is None:
                log.warning(f"ROCKSTAR_UNKNOWN_LAUNCH_REQUEST: Received a launch request for game_id "
                            f"'{game_id}', which does not match any known title. Ignoring.")
                return

            is_launcher_only = title_id in LAUNCHER_ONLY_TITLES
            if is_launcher_only:
                # Optimistically mark Running so Play greys out while user is in launcher grace window.
                log.debug(f"ROCKSTAR_LAUNCHER_ONLY_BUTTON_GREYED: Marking {title_id} as running immediately "
                          f"so the Play button greys out while the Launcher grace window "
                          f"({LAUNCHER_ONLY_GRACE_SECONDS}s) is open.")
                self.launching_title_ids.add(title_id)
                local_game = LocalGame(game_id, LocalGameState.Running | LocalGameState.Installed)
                self.update_local_game_status(local_game)
                self.local_games_cache[title_id] = local_game

            try:
                game_pid = await self._local_client.launch_game_from_title_id(title_id)
            finally:
                self.launching_title_ids.discard(title_id)

            if game_pid:
                self.running_games_info_list[title_id] = RunningGameInfo()
                self.running_games_info_list[title_id].set_info(game_pid)
                log.debug(f"ROCKSTAR_PIDS: {self.list_running_game_pids()}")
                local_game = LocalGame(game_id, LocalGameState.Running | LocalGameState.Installed)
                self.update_local_game_status(local_game)
                self.local_games_cache[title_id] = local_game
            else:
                log.error(f'cannot start game: {title_id}')
                if is_launcher_only:
                    # No launch detected in grace window: revert to normal installed state.
                    log.debug(f"ROCKSTAR_LAUNCHER_ONLY_BUTTON_RESTORED: Reverting {title_id} back to the "
                              f"Installed state since nothing was launched within the grace window.")
                    local_game = LocalGame(game_id, LocalGameState.Installed)
                    self.update_local_game_status(local_game)
                    self.local_games_cache[title_id] = local_game

    if IS_WINDOWS:
        async def install_game(self, game_id):
            if not self._local_client or not self._local_client.get_local_launcher_path():
                await self.open_rockstar_browser()
                return

            title_id = get_game_title_id_from_ros_title_id(game_id)
            if title_id is None:
                log.warning(f"ROCKSTAR_UNKNOWN_INSTALL_REQUEST: Received an install request for game_id "
                            f"'{game_id}', which does not match any known title. Ignoring.")
                return
            log.debug("ROCKSTAR_INSTALL_REQUEST: Requesting to install " + title_id + "...")
            # There is no need to check if the game is a pre-order, since the InstallLocation registry key will be
            # unavailable if it is.
            self._local_client.install_game_from_title_id(title_id)

    if IS_WINDOWS:
        async def uninstall_game(self, game_id):
            if not self._local_client or not self._local_client.get_local_launcher_path():
                await self.open_rockstar_browser()
                return

            title_id = get_game_title_id_from_ros_title_id(game_id)
            if title_id is None:
                log.warning(f"ROCKSTAR_UNKNOWN_UNINSTALL_REQUEST: Received an uninstall request for game_id "
                            f"'{game_id}', which does not match any known title. Ignoring.")
                return
            log.debug("ROCKSTAR_UNINSTALL_REQUEST: Requesting to uninstall " + title_id + "...")
            self._local_client.uninstall_game_from_title_id(title_id)

    def create_game_from_title_id(self, title_id):
        return Game(str(self.games_cache[title_id]["rosTitleId"]), self.games_cache[title_id]["friendlyName"], None,
                    self.games_cache[title_id]["licenseInfo"])

    def tick(self):
        if not self.is_authenticated():
            return
        if not self.checking_for_new_games:
            log.debug("Checking for new games...")
            asyncio.create_task(self.check_for_new_games())
        if not self.updating_game_statuses and IS_WINDOWS:
            log.debug("Checking local game statuses...")
            asyncio.create_task(self.check_game_statuses())


def main():
    create_and_run_plugin(RockstarPlugin, sys.argv)


if __name__ == "__main__":
    main()
