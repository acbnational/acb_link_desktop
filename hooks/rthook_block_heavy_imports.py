# PyInstaller runtime hook to prevent openwakeword from being imported
# This runs before the main script and blocks the import

import sys


class BlockedImportFinder:
    """Blocks imports of specified modules."""

    BLOCKED_MODULES = {
        # ML/AI libraries
        "openwakeword",
        "torch",
        "torchaudio",
        "torchvision",
        "transformers",
        "onnxruntime",
        "onnx",
        "sklearn",
        "scikit-learn",
        "scipy",
        "numba",
        "llvmlite",
        "pyarrow",
        "numpy",
        # Dev/IDE tools
        "jedi",
        "IPython",
        "tiktoken",
        # Jupyter ecosystem
        "zmq",
        "ipykernel",
        "ipywidgets",
        "jupyter_client",
        "jupyter_core",
        "traitlets",
        "tornado",
        "rich",
        # uvicorn dev features
        "watchfiles",
        "watchgod",
    }

    def find_module(self, fullname, path=None):
        """Block imports of heavy ML libraries."""
        # Check if this module or any parent is blocked
        base_module = fullname.split(".")[0]
        if base_module in self.BLOCKED_MODULES:
            return self
        return None

    def load_module(self, fullname):
        """Raise ImportError for blocked modules."""
        raise ImportError(
            f"Module '{fullname}' is not included in the bundled application. "
            f"Install it separately with: pip install {fullname.split('.')[0]}"
        )


# Install the import blocker
sys.meta_path.insert(0, BlockedImportFinder())
