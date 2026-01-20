# PyInstaller hook for openwakeword
# Completely exclude openwakeword and its heavy dependencies
# The app handles ImportError gracefully and falls back to keyboard activation


# This hook tells PyInstaller to NOT include openwakeword
hiddenimports = []

# Exclude all the heavy dependencies that openwakeword pulls in
excludedimports = [
    "openwakeword",
    "openwakeword.model",
    "torch",
    "torchaudio",
    "torchvision",
    "transformers",
    "onnxruntime",
    "onnx",
]
