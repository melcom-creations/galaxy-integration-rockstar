from galaxy.api.types import LicenseInfo
from galaxy.api.consts import LicenseType

# The onlineTitleId values are taken from https://www.rockstargames.com/games/get-games.json?sort=&direction=&family=&
# platform=pc.
#
# All other data values can be found from https://gamedownloads-rockstargames-com.akamaized.net/public/
# title_metadata.json.
games_cache = {
    "launcher": {
        "friendlyName": "Rockstar Games Launcher",
        "guid": "Rockstar Games Launcher",
        "rosTitleId": 21,
        "onlineTitleId": None,
        "googleTagId": "Launcher_PC",
        "launchEXE": "Launcher.exe",
        "achievementId": None,
        "licenseInfo": LicenseInfo(LicenseType.Unknown),
        "isPreOrder": False
    },
    "gtasa": {
        "friendlyName": "Grand Theft Auto: San Andreas",
        "guid": "{D417C96A-FCC7-4590-A1BB-FAF73F5BC98E}",
        "rosTitleId": 18,
        "onlineTitleId": 31,
        "googleTagId": "GTASA_PC",
        "launchEXE": "gta-sa.exe",
        "achievementId": None,
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "gta5": {
        "friendlyName": "Grand Theft Auto V",
        # Keep Galaxy display name stable while matching the Launcher log by its current title label.
        "launcherLogTitle": "Grand Theft Auto V Legacy",
        "guid": "{5EFC6C07-6B87-43FC-9524-F9E967241741}",
        "rosTitleId": 11,
        "onlineTitleId": 241,
        "googleTagId": "GTAV_PC",
        "launchEXE": "PlayGTAV.exe",
        # Track the long-lived game process, not the short-lived launcher wrapper.
        "trackEXE": "GTA5.exe",
        "achievementId": "gtav",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "gta5_gen9": {
        # Use Rockstar's internal launcher id. Install/uninstall commands pass this key directly.
        "friendlyName": "Grand Theft Auto V Enhanced",
        "launcherLogTitle": "Grand Theft Auto V Enhanced",
        # Enhanced has no reliable classic uninstall GUID on many systems; local detection uses log and
        # additional fallbacks instead of registry GUID matching.
        "guid": None,
        # Galaxy requires a stable numeric game_id; no public numeric id is exposed for gta5_gen9.
        "rosTitleId": 9001,
        "onlineTitleId": None,
        "googleTagId": None,
        # Use the launcher-aware wrapper to avoid direct-launch ERR_NO_LAUNCHER issues.
        "launchEXE": "PlayGTAV.exe",
        # Track the actual game process rather than the wrapper process.
        "trackEXE": "GTA5_Enhanced.exe",
        # Enhanced and Legacy share the same Social Club achievement set.
        "achievementId": "gtav",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "lanoire": {
        "friendlyName": "L.A. Noire: Complete Edition",
        "guid": "{915726DF-7891-444A-AA03-0DF1D64F561A}",
        "rosTitleId": 9,
        "onlineTitleId": 35,
        "googleTagId": "LAN_PC",
        "launchEXE": "LANoire.exe",
        "achievementId": "lan",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "mp3": {
        "friendlyName": "Max Payne 3",
        "guid": "{1AA94747-3BF6-4237-9E1A-7B3067738FE1}",
        "rosTitleId": 10,
        "onlineTitleId": 40,
        "googleTagId": "MP3_PC",
        "launchEXE": "PlayMaxPayne3.exe",
        "trackEXE": "MaxPayne3.exe",
        "achievementId": "mp3",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    # "lanoirevr": {
    #    "friendlyName": "L.A. Noire: The VR Case Files",
    #    "guid": "L.A. Noire: The VR Case Files",
    #    "rosTitleId": 24,
    #    "onlineTitleId": 35,  # Shares the same online id as L.A. Noire.
    #    "googleTagId": "LANVR_PC",
    #    "launchEXE": "LANoireVR.exe",
    #    "achievementId": "lanvr",
    #    "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
    #    "isPreOrder": False
    # },
    "gta3": {
        "friendlyName": "Grand Theft Auto III",
        "guid": "{92B94569-6683-4617-8C54-EB27A1B51B30}",
        "rosTitleId": 26,
        "onlineTitleId": 24,
        "googleTagId": "GTAIII_PC",
        "launchEXE": "gta3.exe",
        "achievementId": None,
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "gtavc": {
        "friendlyName": "Grand Theft Auto: Vice City",
        "guid": "{4B35F00C-E63D-40DC-9839-DF15A33EAC46}",
        "rosTitleId": 27,
        "onlineTitleId": 33,
        "googleTagId": "GTAVC_PC",
        "launchEXE": "gta-vc.exe",
        "achievementId": None,
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "bully": {
        "friendlyName": "Bully: Scholarship Edition",
        "guid": "{A724605D-B399-4304-B8C7-33B3EF7D4677}",
        "rosTitleId": 23,
        "onlineTitleId": 19,
        "googleTagId": "Bully_PC",
        "launchEXE": "Bully.exe",
        # Rockstar's listed achievements here are for mobile, not PC.
        "achievementId": None,
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "rdr2": {
        "friendlyName": "Red Dead Redemption 2",
        "guid": "Red Dead Redemption 2",
        "rosTitleId": 13,
        "onlineTitleId": 912,
        "googleTagId": "RDR2_PC",
        "launchEXE": "RDR2.exe",
        "achievementId": "rdr2",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "gta4": {
        "friendlyName": "Grand Theft Auto IV",
        "guid": "Grand Theft Auto IV",
        "rosTitleId": 1,
        "onlineTitleId": 25,
        "googleTagId": "GTAIV_PC",
        "launchEXE": "PlayGTAIV.exe",
        "trackEXE": "GTAIV.exe",
        "achievementId": "gtaiv",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "gta3unreal": {
        "friendlyName": "Grand Theft Auto III - The Definitive Edition",
        "guid": "GTA III - Definitive Edition",
        "rosTitleId": 28,
        "googleTagId": "GTA3UNREAL_PC",
        "launchEXE": "Gameface\\Binaries\\Win64\\LibertyCity.exe",
        "trackEXE": "LibertyCity.exe",
        "cmdLineArgs": "-scCommerceProvider=4",
        "achievementId": "gta3unreal",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "gtavcunreal": {
        "friendlyName": "Grand Theft Auto: Vice City - The Definitive Edition",
        "guid": "GTA Vice City - Definitive Edition",
        "rosTitleId": 29,
        "googleTagId": "GTAVCUNREAL_PC",
        "launchEXE": "Gameface\\Binaries\\Win64\\ViceCity.exe",
        "trackEXE": "ViceCity.exe",
        "cmdLineArgs": "-scCommerceProvider=4",
        "achievementId": "gtavcunreal",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    },
    "gtasaunreal": {
        "friendlyName": "Grand Theft Auto: San Andreas - The Definitive Edition",
        "guid": "GTA San Andreas - Definitive Edition",
        "rosTitleId": 30,
        "googleTagId": "GTASAUNREAL_PC",
        "launchEXE": "Gameface\\Binaries\\Win64\\SanAndreas.exe",
        "trackEXE": "SanAndreas.exe",
        "cmdLineArgs": "-scCommerceProvider=4",
        "achievementId": "gtasaunreal",
        "licenseInfo": LicenseInfo(LicenseType.SinglePurchase),
        "isPreOrder": False
    }
}

# Ignore metadata entries with parentApp; they are not launcher-playable titles.
ignore_game_title_ids_list = [
    "rdr2_sp_steam",   # Red Dead Redemption 2 Single Player - Steam
    "rdr2_sp_rgl",     # Red Dead Redemption 2 Single Player - Rockstar Games Launcher
    "rdr2_sp",         # Red Dead Redemption 2 Single Player - General
    "rdr2_rdo",        # Red Dead Online Standalone
    "rdr2_sp_epic",    # Red Dead Redemption 2 Single Player - Epic Games Store
    "gtatrilogy"       # Grand Theft Auto: The Definitive Trilogy
]


def get_game_title_id_from_ros_title_id(ros_title_id):
    # rosTitleId is the launcher's numeric identifier, distinct from onlineTitleId.
    try:
        ros_title_id_int = int(ros_title_id)
    except (TypeError, ValueError):
        # Keep per-tick status loops resilient to malformed values.
        return None
    for game, d in games_cache.items():
        if d["rosTitleId"] == ros_title_id_int:
            return game
    return None


def get_game_title_id_from_online_title_id(online_title_id):
    # onlineTitleId is used by Rockstar web APIs.
    try:
        online_id_int = int(online_title_id)
    except (TypeError, ValueError):
        return None
    for game, d in games_cache.items():
        if d["onlineTitleId"] == online_id_int:
            return game
    return None


def get_game_title_id_from_google_tag_id(google_tag_id):
    # Google Tag ids come from Social Club tag-manager payloads.
    for game, d in games_cache.items():
        if 'googleTagId' in d and d['googleTagId'] == google_tag_id:
            return game
    return None


def get_game_title_id_from_ugc_title_id(ugc_id):
    # UGC ids are normalized against known Google Tag ids.
    for game, d in games_cache.items():
        if 'googleTagId' in d and d['googleTagId'].lower() == ugc_id.lower():
            return game
    return None


def get_achievement_id_from_ros_title_id(ros_title_id):
    # achievementId maps a launcher title to Social Club achievements endpoints.
    try:
        ros_title_id_int = int(ros_title_id)
    except (TypeError, ValueError):
        return None
    for game, d in games_cache.items():
        if d["rosTitleId"] == ros_title_id_int:
            return games_cache[game]["achievementId"]
