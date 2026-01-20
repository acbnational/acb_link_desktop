# PyInstaller hook for speech_recognition
# Strips unnecessary data files to reduce bundle size
#
# The speech_recognition package bundles:
# - PocketSphinx offline models (~28 MB) - not used, we use Google Speech API
# - FLAC binaries for Linux/Mac (~4.5 MB) - not needed on Windows
#
# This hook excludes these files, saving ~32 MB

from PyInstaller.utils.hooks import collect_data_files

# Collect speech_recognition data but filter out unnecessary files
datas = []
for src, dest in collect_data_files("speech_recognition"):
    # Skip PocketSphinx data (offline recognition models we don't use)
    if "pocketsphinx-data" in src:
        continue
    # Skip Linux FLAC binaries
    if "flac-linux" in src:
        continue
    # Skip Mac FLAC binary
    if "flac-mac" in src:
        continue
    # Keep only Windows FLAC and essential files
    datas.append((src, dest))

# Explicitly exclude pocketsphinx since we use Google Speech API
excludedimports = [
    "pocketsphinx",
]
