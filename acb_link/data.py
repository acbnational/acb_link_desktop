"""
ACB Link - Data Constants
Stream and podcast data, affiliate information, and other constants.
"""

from typing import List, Dict


# ACB Media Streams with Live365 station IDs
STREAMS: List[Dict] = [
    {"id": 1, "name": "ACB Media 1", "desc": "Flagship station", "station": "a11911"},
    {"id": 2, "name": "ACB Media 2", "desc": "Flagship station", "station": "a27778"},
    {"id": 3, "name": "ACB Media 3", "desc": "ACB Community calls", "station": "a50498"},
    {"id": 4, "name": "ACB Media 4", "desc": "ACB Community calls", "station": "a95498"},
    {"id": 5, "name": "ACB Media 5", "desc": "Music", "station": "a03498"},
    {"id": 6, "name": "ACB Media 6", "desc": "Music", "station": "a96498"},
    {"id": 7, "name": "Cafe 1", "desc": "Cafe stream", "station": "a79498"},
    {"id": 8, "name": "Cafe 2", "desc": "Cafe stream", "station": "a28498"},
    {"id": 9, "name": "Treasure Trove", "desc": "Classic audio content", "station": "a32498"},
    {"id": 10, "name": "ACBS Main", "desc": "Main ACB stream", "station": "a07498"},
]

# Podcasts organized by category with Pinecast RSS feeds
PODCASTS: Dict[str, List[Dict]] = {
    "ACB Podcasts": [
        {"name": "ACB Reports", "feed": "https://pinecast.com/feed/acb-reports"},
        {"name": "Braille Forum", "feed": "https://pinecast.com/feed/braille-forum"},
        {"name": "ACB Next Generation", "feed": "https://pinecast.com/feed/acb-next-generation"},
        {"name": "ACB Legislative Updates", "feed": "https://pinecast.com/feed/acb-legislative-updates"},
    ],
    "Technology": [
        {"name": "BITS Tech Talk", "feed": "https://pinecast.com/feed/bits-tech-talk"},
        {"name": "Accessibility Matters", "feed": "https://pinecast.com/feed/accessibility-matters"},
        {"name": "Screen Reader Roundup", "feed": "https://pinecast.com/feed/screen-reader-roundup"},
        {"name": "iOS Accessibility", "feed": "https://pinecast.com/feed/ios-accessibility"},
        {"name": "Android Access", "feed": "https://pinecast.com/feed/android-access"},
    ],
    "Entertainment": [
        {"name": "Blind Movie Critics", "feed": "https://pinecast.com/feed/blind-movie-critics"},
        {"name": "Audio Description Review", "feed": "https://pinecast.com/feed/audio-description-review"},
        {"name": "Book Talk", "feed": "https://pinecast.com/feed/book-talk"},
        {"name": "Music Spotlight", "feed": "https://pinecast.com/feed/music-spotlight"},
    ],
    "Lifestyle": [
        {"name": "Cooking Without Looking", "feed": "https://pinecast.com/feed/cooking-without-looking"},
        {"name": "Travel Tales", "feed": "https://pinecast.com/feed/travel-tales"},
        {"name": "Health & Wellness", "feed": "https://pinecast.com/feed/health-wellness"},
        {"name": "Career Corner", "feed": "https://pinecast.com/feed/career-corner"},
    ],
    "Main Menu": [
        {"name": "Main Menu", "feed": "https://pinecast.com/feed/mainmenu"},
        {"name": "Main Menu Archive", "feed": "https://pinecast.com/feed/mainmenu-archive"},
        {"name": "Main Menu Legacy", "feed": "https://pinecast.com/feed/mainmenu-legacy"},
    ],
}

# Affiliate URLs
AFFILIATES = {
    "state": "https://www.acb.org/state-affiliates",
    "special_interest": "https://www.acb.org/special-interest-affiliates",
}

# ACB Resource URLs
RESOURCES = {
    "website": "https://www.acb.org",
    "braille_forum": "https://www.acbmedia.org/forum",
    "blog": "https://www.acbmedia.org/blog",
    "calendar": "https://www.acbmedia.org/calendar",
    "join": "https://acb.org/join-acb",
    "donate": "https://acb.org/donate",
}

# Tab configuration
TAB_NAMES = ["home", "streams", "podcasts", "web_ui", "logs"]
TAB_LABELS = ["Home", "Streams", "Podcasts", "Web UI", "Logs"]

# Playback speed options
SPEED_OPTIONS = ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "1.75x", "2.0x"]
SPEED_VALUES = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

# Equalizer presets
EQ_PRESETS = {
    "flat": {"bass": 0, "mid": 0, "treble": 0},
    "bass_boost": {"bass": 6, "mid": 0, "treble": -2},
    "voice": {"bass": -2, "mid": 4, "treble": 2},
    "treble": {"bass": -2, "mid": 0, "treble": 6},
}

# Recording formats
RECORDING_FORMATS = ["mp3", "wav", "ogg"]
RECORDING_BITRATES = [64, 96, 128, 192, 256, 320]

# Theme options for settings
THEME_OPTIONS = ["system", "light", "dark", "high_contrast_light", "high_contrast_dark", "custom"]
