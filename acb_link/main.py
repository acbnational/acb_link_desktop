"""
ACB Link - Desktop Application
Main entry point for the ACB Link desktop application.

This application provides accessible access to ACB media content including:
- Live audio streams
- Podcasts
- Affiliate organization links
- ACB resources

Requirements:
- Python 3.9+
- wxPython 4.2+
- FastAPI (optional, for web server)
- uvicorn (optional, for web server)

Usage:
    python -m acb_link
    or
    python main.py
"""

import sys

import wx

from acb_link.main_frame import MainFrame


def main():
    """Main entry point for ACB Link."""
    # Create application
    app = wx.App(redirect=False)

    # Set app name for accessibility
    app.SetAppName("ACB Link")
    app.SetVendorName("American Council of the Blind")

    # Create and show main frame
    frame = MainFrame()

    # Set as top window
    app.SetTopWindow(frame)

    # Run event loop
    app.MainLoop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
