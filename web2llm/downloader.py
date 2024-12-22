"""Module for downloading websites using httrack."""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse


class WebsiteDownloader:
    """Downloads a website using HTTrack with real-time progress display."""

    def __init__(self, quiet: bool = False):
        """Initialize the downloader.

        Args:
            quiet: If True, suppress progress output
        """
        self.quiet = quiet

    def _print_progress(self, line: str) -> None:
        """Print progress information.

        Args:
            line: Line of output from HTTrack
        """
        if self.quiet:
            return

        # Filter and format HTTrack output for better readability
        line = line.strip()
        if line:
            if line.startswith(("Warning:", "Error:", "Info:")):
                # Status messages
                print(f"\033[1m{line}\033[0m")  # Bold
            elif "saved" in line.lower() or "file:" in line.lower():
                # File progress
                print(f"\033[92m{line}\033[0m")  # Green
            elif "loading" in line.lower():
                # Loading status
                print(f"\033[94m{line}\033[0m")  # Blue
            elif any(word in line.lower() for word in ["error", "warning", "failed"]):
                # Errors and warnings
                print(f"\033[91m{line}\033[0m")  # Red
            else:
                print(line)

        # Ensure output is displayed immediately
        sys.stdout.flush()

    def download(self, url: str, output_dir: Path) -> Path:
        """Download a website using HTTrack with real-time progress display.

        Args:
            url: URL to download
            output_dir: Directory to save downloaded files

        Returns:
            Path to the downloaded website directory

        Raises:
            RuntimeError: If HTTrack fails or downloaded directory not found
        """
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build HTTrack command with correct syntax
        cmd = [
            "httrack",
            url,
            "-O", str(output_dir),
            "-r2",
            "-c8",
            "-F", "Mozilla/5.0",
            "-s0",
            "-N1",
            "-%v",
            "-v"
        ]

        if not self.quiet:
            print(f"\n📥 Starting download of {url}")
            print("=" * 80)

        # Run HTTrack with real-time output processing
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Process output in real-time
        try:
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                self._print_progress(line)

            # Check if HTTrack completed successfully
            if process.returncode != 0:
                raise RuntimeError(f"HTTrack failed with return code {process.returncode}")

            # Find the downloaded website directory
            web_dir = output_dir / "web"
            if web_dir.exists():
                if not self.quiet:
                    print(f"\n✅ Download completed successfully: {web_dir}")
                return web_dir

            raise RuntimeError(f"Could not find downloaded website directory: {web_dir}")

        finally:
            # Ensure process is terminated
            if process.poll() is None:
                process.terminate()
                process.wait()

    def find_html_files(self, website_dir: Path) -> List[Path]:
        """Find all HTML files in the website directory.

        Args:
            website_dir: Directory to search in

        Returns:
            List of HTML file paths
        """
        html_files = list(website_dir.rglob("*.html"))

        if not self.quiet:
            print(f"\n📄 Found {len(html_files)} HTML files")

        return html_files