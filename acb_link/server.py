"""
ACB Link - Local Web Server
FastAPI server for rendering accessible HTML content.
"""

import os
import subprocess
import threading
import webbrowser
from typing import Optional

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from .data import AFFILIATES, PODCASTS, RESOURCES, STREAMS


class LocalWebServer:
    """Local web server for rendering accessible HTML content."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.server_thread: Optional[threading.Thread] = None
        self.server: Optional["uvicorn.Server"] = None
        self._running = False

        if HAS_FASTAPI:
            self.app = self._create_app()
        else:
            self.app = None

    def _create_app(self) -> "FastAPI":
        """Create the FastAPI application."""
        app = FastAPI(title="ACB Link Server")

        @app.get("/", response_class=HTMLResponse)
        async def home():
            return self._build_home_page()

        @app.get("/streams", response_class=HTMLResponse)
        async def streams():
            return self._build_streams_page()

        @app.get("/podcasts", response_class=HTMLResponse)
        async def podcasts():
            return self._build_podcasts_page()

        @app.get("/affiliates", response_class=HTMLResponse)
        async def affiliates():
            return self._build_affiliates_page()

        @app.get("/resources", response_class=HTMLResponse)
        async def resources():
            return self._build_resources_page()

        @app.get("/stream/{station_id}")
        async def get_stream(station_id: str):
            """Return stream URL for embedding."""
            return {"url": f"https://live365.com/station/{station_id}"}

        return app

    def start(self):
        """Start the web server in a background thread."""
        if not HAS_FASTAPI:
            raise RuntimeError("FastAPI not installed. Run: pip install fastapi uvicorn")

        if self._running:
            return

        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="error")
        self.server = uvicorn.Server(config)

        self.server_thread = threading.Thread(
            target=self.server.run, daemon=True, name="ACBLinkWebServer"
        )
        self.server_thread.start()
        self._running = True

    def stop(self):
        """Stop the web server."""
        if self.server and self._running:
            self.server.should_exit = True
            self._running = False

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def base_url(self) -> str:
        """Get the base URL of the server."""
        return f"http://{self.host}:{self.port}"

    def open_in_browser(self, path: str = "/", browser: str = "edge"):
        """Open a path in the specified browser."""
        url = f"{self.base_url}{path}"

        if browser == "chrome":
            browser_path = self._find_chrome()
            if browser_path:
                subprocess.Popen([browser_path, "--app=" + url])
            else:
                webbrowser.open(url)
        elif browser == "edge":
            browser_path = self._find_edge()
            if browser_path:
                subprocess.Popen([browser_path, "--app=" + url])
            else:
                webbrowser.open(url)
        else:
            webbrowser.open(url)

    def _find_edge(self) -> Optional[str]:
        """Find Microsoft Edge executable."""
        paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def _find_chrome(self) -> Optional[str]:
        """Find Google Chrome executable."""
        paths = [
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    # HTML Builder Methods

    def _get_base_styles(self) -> str:
        """Get base CSS styles for all pages."""
        return """
        <style>
            :root {
                --bg-color: #ffffff;
                --text-color: #1a1a1a;
                --link-color: #0066cc;
                --heading-color: #003366;
                --border-color: #cccccc;
                --focus-color: #0066cc;
                --card-bg: #f5f5f5;
            }

            @media (prefers-color-scheme: dark) {
                :root {
                    --bg-color: #1a1a1a;
                    --text-color: #ffffff;
                    --link-color: #66b3ff;
                    --heading-color: #99ccff;
                    --border-color: #444444;
                    --card-bg: #2a2a2a;
                }
            }

            * {
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 16px;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: var(--bg-color);
                color: var(--text-color);
            }

            h1, h2, h3 {
                color: var(--heading-color);
            }

            h1 {
                font-size: 2em;
                margin-bottom: 0.5em;
            }

            h2 {
                font-size: 1.5em;
                margin-top: 1.5em;
            }

            a {
                color: var(--link-color);
                text-decoration: underline;
            }

            a:hover, a:focus {
                text-decoration: none;
            }

            a:focus {
                outline: 3px solid var(--focus-color);
                outline-offset: 2px;
            }

            nav {
                background: var(--card-bg);
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
            }

            nav ul {
                list-style: none;
                margin: 0;
                padding: 0;
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
            }

            nav a {
                font-weight: bold;
            }

            .card {
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }

            .card h3 {
                margin-top: 0;
            }

            .skip-link {
                position: absolute;
                top: -40px;
                left: 0;
                background: var(--focus-color);
                color: white;
                padding: 8px 16px;
                z-index: 100;
                text-decoration: none;
            }

            .skip-link:focus {
                top: 0;
            }

            .stream-list, .podcast-list, .affiliate-list {
                list-style: none;
                padding: 0;
            }

            .stream-list li, .podcast-list li, .affiliate-list li {
                padding: 10px;
                border-bottom: 1px solid var(--border-color);
            }

            .stream-list li:last-child, .podcast-list li:last-child {
                border-bottom: none;
            }

            button, .btn {
                background: var(--link-color);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
            }

            button:hover, .btn:hover {
                opacity: 0.9;
            }

            button:focus, .btn:focus {
                outline: 3px solid var(--focus-color);
                outline-offset: 2px;
            }

            @media (max-width: 600px) {
                nav ul {
                    flex-direction: column;
                    gap: 10px;
                }
            }
        </style>
        """

    def _get_nav_html(self) -> str:
        """Get navigation HTML."""
        return """
        <a href="#main" class="skip-link">Skip to main content</a>
        <nav role="navigation" aria-label="Main navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/streams">Streams</a></li>
                <li><a href="/podcasts">Podcasts</a></li>
                <li><a href="/affiliates">Affiliates</a></li>
                <li><a href="/resources">Resources</a></li>
            </ul>
        </nav>
        """

    def _build_home_page(self) -> str:
        """Build the home page HTML."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ACB Link - Home</title>
            {self._get_base_styles()}
        </head>
        <body>
            {self._get_nav_html()}
            <main id="main" role="main">
                <h1>Welcome to ACB Link</h1>
                <p>Your gateway to American Council of the Blind media content.</p>

                <section aria-labelledby="streams-heading">
                    <h2 id="streams-heading">Quick Access - Streams</h2>
                    <div class="card">
                        <ul class="stream-list">
                            {''.join(f'<li><a href="/streams#{name.lower().replace(" ", "-")}">{name}</a></li>' for name in list(STREAMS.keys())[:5])}
                        </ul>
                        <p><a href="/streams">View all streams →</a></p>
                    </div>
                </section>

                <section aria-labelledby="podcasts-heading">
                    <h2 id="podcasts-heading">Featured Podcasts</h2>
                    <div class="card">
                        <ul class="podcast-list">
                            {''.join(f'<li><a href="/podcasts#{cat.lower().replace(" ", "-")}">{cat}</a></li>' for cat in PODCASTS.keys())}
                        </ul>
                        <p><a href="/podcasts">Browse all podcasts →</a></p>
                    </div>
                </section>
            </main>

            <footer role="contentinfo">
                <p>© American Council of the Blind. All rights reserved.</p>
            </footer>
        </body>
        </html>
        """

    def _build_streams_page(self) -> str:
        """Build the streams page HTML."""
        streams_html = ""
        for name, station_id in STREAMS.items():
            anchor = name.lower().replace(" ", "-")
            streams_html += f"""
            <div class="card" id="{anchor}">
                <h3>{name}</h3>
                <p>Station ID: {station_id}</p>
                <a href="https://live365.com/station/{station_id}" target="_blank"
                   aria-label="Listen to {name} on Live365">Listen on Live365</a>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ACB Link - Streams</title>
            {self._get_base_styles()}
        </head>
        <body>
            {self._get_nav_html()}
            <main id="main" role="main">
                <h1>ACB Media Streams</h1>
                <p>Listen to live audio streams from ACB Media.</p>
                {streams_html}
            </main>
        </body>
        </html>
        """

    def _build_podcasts_page(self) -> str:
        """Build the podcasts page HTML."""
        podcasts_html = ""
        for category, pods in PODCASTS.items():
            anchor = category.lower().replace(" ", "-")
            podcasts_html += f"""
            <section aria-labelledby="{anchor}-heading">
                <h2 id="{anchor}-heading">{category}</h2>
            """
            for name, feed_url in pods.items():
                podcasts_html += f"""
                <div class="card">
                    <h3>{name}</h3>
                    <a href="{feed_url}" target="_blank">RSS Feed</a>
                </div>
                """
            podcasts_html += "</section>"

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ACB Link - Podcasts</title>
            {self._get_base_styles()}
        </head>
        <body>
            {self._get_nav_html()}
            <main id="main" role="main">
                <h1>Podcasts</h1>
                <p>Browse podcasts from ACB and partners.</p>
                {podcasts_html}
            </main>
        </body>
        </html>
        """

    def _build_affiliates_page(self) -> str:
        """Build the affiliates page HTML."""
        affiliates_html = ""
        for name, url in AFFILIATES.items():
            affiliates_html += f"""
            <div class="card">
                <h3>{name}</h3>
                <a href="{url}" target="_blank" aria-label="Visit {name} website">{url}</a>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ACB Link - Affiliates</title>
            {self._get_base_styles()}
        </head>
        <body>
            {self._get_nav_html()}
            <main id="main" role="main">
                <h1>ACB Affiliates</h1>
                <p>Connect with ACB affiliate organizations.</p>
                {affiliates_html}
            </main>
        </body>
        </html>
        """

    def _build_resources_page(self) -> str:
        """Build the resources page HTML."""
        resources_html = ""
        for name, url in RESOURCES.items():
            resources_html += f"""
            <div class="card">
                <h3>{name}</h3>
                <a href="{url}" target="_blank">{url}</a>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ACB Link - Resources</title>
            {self._get_base_styles()}
        </head>
        <body>
            {self._get_nav_html()}
            <main id="main" role="main">
                <h1>ACB Resources</h1>
                <p>Helpful resources from the American Council of the Blind.</p>
                {resources_html}
            </main>
        </body>
        </html>
        """
