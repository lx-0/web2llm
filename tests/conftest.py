"""Test configuration and fixtures."""
import os
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_html() -> str:
    """Return sample HTML content."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <nav>
            <ul>
                <li><a href="/page1.html">Page 1</a></li>
                <li><a href="/page2.html">Page 2</a></li>
            </ul>
        </nav>
        <div class="content">
            <h1>Test Content</h1>
            <p>This is a test paragraph.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_website_dir(tmp_path: Path, sample_html: str) -> Path:
    """Create a mock website directory structure."""
    site_dir = tmp_path / "test_site"
    site_dir.mkdir()

    # Create main page
    with open(site_dir / "index.html", "w") as f:
        f.write(sample_html)

    # Create subpages
    for i in range(1, 3):
        page_dir = site_dir / f"page{i}"
        page_dir.mkdir(exist_ok=True)
        with open(page_dir / "index.html", "w") as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head><title>Page {i}</title></head>
            <body>
                <h1>Page {i}</h1>
                <p>Content for page {i}</p>
            </body>
            </html>
            """)

    return site_dir