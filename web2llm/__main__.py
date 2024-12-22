"""Main module for preparing online documentation for LLM consumption.

This module provides command-line functionality to download websites and convert them
into standardized PDF formats, making post-cutoff documentation accessible to language models.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from .converter import convert_to_pdf
from .downloader import WebsiteDownloader
from .preprocessor import HTMLPreprocessor


def get_website_name(url: str) -> str:
    """Get a safe directory name from the URL."""
    parsed = urlparse(url)
    return parsed.netloc.replace(":", "_").replace("/", "_")


def main(url: str, output: str, debug: bool = False, quiet: bool = False, skip_download: bool = False, download_only: bool = False) -> None:
    """Prepare online documentation for LLM consumption.

    Downloads a website and converts it into a standardized PDF format suitable for
    language model consumption. Handles JavaScript-rendered content, maintains proper
    structure, and generates clean, formatted output.

    Args:
        url: Website URL to process
        output: Output PDF file path
        debug: Whether to save debug information
        quiet: Whether to suppress progress output
        skip_download: Whether to skip downloading and use existing files
        download_only: Whether to only download the website and skip preprocessing/conversion
    """
    # Get website name for directory structure
    website_name = get_website_name(url)

    # Set up directory structure
    base_dir = Path.cwd()
    output_dir = base_dir / "output"
    downloads_dir = base_dir / "downloads" / website_name

    # Create directories
    output_dir.mkdir(parents=True, exist_ok=True)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    # If output path is not absolute, put it in the output directory
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = output_dir / output_path

    try:
        # Download website with progress display unless quiet mode is enabled
        if not skip_download:
            downloader = WebsiteDownloader(quiet=quiet)
            downloaded_dir = downloader.download(url, downloads_dir)
        else:
            web_dir = downloads_dir / "web"
            if not web_dir.exists():
                raise RuntimeError(f"Cannot skip download: {web_dir} does not exist")
            downloaded_dir = web_dir

        if download_only:
            if not quiet:
                print(f"\n✅ Successfully downloaded website to: {downloaded_dir}")
            return

        # Process HTML files
        debug_dir = output_dir / "debug" if debug else None
        if debug_dir:
            debug_dir.mkdir(parents=True, exist_ok=True)

        preprocessor = HTMLPreprocessor(str(downloaded_dir), str(debug_dir) if debug_dir else None)
        html_files, master_html = preprocessor.process_html_files()

        # Convert to PDF
        if not quiet:
            print("\n📄 Converting to PDF...")
        convert_to_pdf(master_html, str(output_path))

        if not quiet:
            print(f"\n✅ Successfully created PDF: {output_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temporary directories if not in debug mode
        if not debug and downloads_dir.exists() and not skip_download and not download_only:
            shutil.rmtree(downloads_dir)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Convert online documentation into LLM-friendly PDF format'
    )
    parser.add_argument('url', help='Website URL to convert')
    parser.add_argument('--output', '-o', required=True, help='Output PDF file path')
    parser.add_argument('--debug', action='store_true', help='Save debug information')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress progress output')
    parser.add_argument('--skip-download', action='store_true', help='Skip downloading and use existing files')
    parser.add_argument('--download-only', action='store_true', help='Only download the website, skip preprocessing and conversion')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)