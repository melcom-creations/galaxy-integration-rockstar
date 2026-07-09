import datetime
import os
import sys

from time import time

import galaxyutils.config_parser as config_parser
from galaxyutils.config_parser import Option, get_config_options

PLUGIN_ROOT = os.path.dirname(__file__)
config_parser.CONFIG_PATH = os.path.join(PLUGIN_ROOT, 'config.cfg')
config_parser.DEFAULT_CONFIG_PATH = os.path.join(PLUGIN_ROOT, 'default_config.cfg')


class NoLogFoundException(Exception):
    pass


class NoGamesInLogException(Exception):
    pass


ARE_ACHIEVEMENTS_IMPLEMENTED = True

CONFIG_OPTIONS = get_config_options([
    Option(option_name='user_presence_mode', default_value=0, allowed_values=[i for i in range(0, 4)]),
    Option(option_name='log_sensitive_data'),
    Option(option_name='debug_always_refresh'),
    Option(option_name='rockstar_launcher_path_override', str_option=True, default_value=None),
    Option(option_name='enable_steam_fallback', default_value=True)
])

LOG_SENSITIVE_DATA = CONFIG_OPTIONS['log_sensitive_data']


def safe_exception_repr(e):
    """
    Returns a repr() of an exception for logging purposes, but only if log_sensitive_data is enabled.

    Exceptions raised by aiohttp for failed authenticated requests (e.g. aiohttp.ClientResponseError) embed the
    full RequestInfo of the failing request in their repr()/str(), which includes every header that was sent -
    including the raw "Cookie" and "Authorization" headers used to authenticate with Rockstar's Social Club
    (session cookies, bearer tokens, etc). Logging repr(e) unconditionally for such exceptions would leak those
    credentials in plain text into the plugin's log file. This helper keeps the diagnostic value (exception type
    and, where available, HTTP status) while redacting the sensitive parts unless the user has explicitly opted
    into full diagnostic logging via log_sensitive_data=True.
    """
    if LOG_SENSITIVE_DATA:
        return repr(e)
    status = getattr(e, 'status', None)
    if status is not None:
        return f"{type(e).__name__}(status={status}) [details hidden, set log_sensitive_data=True to reveal]"
    return f"{type(e).__name__} [details hidden, set log_sensitive_data=True to reveal]"

MANIFEST_URL = r"https://gamedownloads-rockstargames-com.akamaized.net/public/title_metadata.json"

IS_WINDOWS = (sys.platform == 'win32')

ROCKSTAR_LAUNCHERPATCHER_EXE = "LauncherPatcher.exe"
# Kept explicit because the executable name is very generic.
ROCKSTAR_LAUNCHER_EXE = "Launcher.exe"

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 "
              "Safari/537.36")

WINDOWS_UNINSTALL_KEY = "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\"

AUTH_PARAMS = {
    "window_title": "Login to Rockstar Games Social Club",
    "window_width": 700,
    "window_height": 600,
    "start_uri": "https://signin.rockstargames.com/connect/authorize/rsg?lang=en-US&returnUrl=/",
    "end_uri_regex": r"^https://socialclub\.rockstargames\.com/?(\?.*)?$"
}


async def get_unix_epoch_time_from_date(date):
    """Convert Rockstar timestamp string (YYYY-MM-DD HH:MM:SS) to unix epoch seconds."""
    year = int(date[0:4])
    month = int(date[5:7])
    day = int(date[8:10])
    hour = int(date[11:13])
    minute = int(date[14:16])
    second = int(date[17:19])
    return int(datetime.datetime(year, month, day, hour, minute, second).timestamp())


async def get_time_passed(old_time: int) -> str:
    """Return a coarse human-readable elapsed time label used in presence text."""
    current_time = int(time())
    difference = current_time - old_time
    days_passed = int(difference / (3600 * 24))
    if days_passed == 0:
        return "Today"
    elif days_passed >= 365:
        years_passed = int(days_passed / 365)
        return f"{years_passed} Years Ago" if years_passed != 1 else "1 Year Ago"
    elif days_passed >= 30:
        months_passed = int(days_passed / 30)
        return f"{months_passed} Months Ago" if months_passed != 1 else "1 Month Ago"
    elif days_passed >= 7:
        weeks_passed = int(days_passed / 7)
        return f"{weeks_passed} Weeks Ago" if weeks_passed != 1 else "1 Week Ago"
    return f"{days_passed} Days Ago" if days_passed != 1 else "1 Day Ago"





