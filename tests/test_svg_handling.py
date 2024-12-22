"""Tests for SVG handling in the HTML preprocessor."""
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from web2llm.preprocessor import HTMLPreprocessor


@pytest.fixture
def svg_html() -> str:
    """Create a test HTML with various SVG elements."""
    return """
    <html>
    <head></head>
    <body>
        <div style="color: blue;">
            <svg width="100" height="100" style="margin: 10px;">
                <circle cx="50" cy="50" r="40" stroke="black" fill="red"/>
            </svg>
            <svg class="icon" aria-label="Test Icon">
                <rect width="20" height="20"/>
            </svg>
            <svg data-custom="test">
                <!-- Comment to be removed -->
                <path d="M10 10"/>
            </svg>
        </div>
    </body>
    </html>
    """


def test_svg_to_img_conversion(tmp_path: Path, svg_html: str):
    """Test conversion of SVG elements to img tags."""
    # Create a test file
    test_file = tmp_path / "test.html"
    test_file.write_text(svg_html)

    # Process the file
    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(svg_html, 'html.parser')
    preprocessor._fix_resource_paths(soup, str(test_file))

    # Check that SVGs were converted to images
    images = soup.find_all('img')
    assert len(images) == 3

    # Check first image (with explicit dimensions)
    assert images[0]['width'] == "100"
    assert images[0]['height'] == "100"
    assert "margin: 10px" in images[0]['style']
    assert images[0]['src'].startswith('data:image/svg+xml')

    # Check second image (with aria-label)
    assert images[1]['alt'] == "Test Icon"
    assert images[1]['class'] == ["icon"]

    # Check third image (with data attribute)
    assert images[2]['data-custom'] == "test"
    assert 'Comment to be removed' not in str(images[2])


def test_svg_style_inheritance(tmp_path: Path):
    """Test that SVG inherits styles from parent elements."""
    html = """
    <div style="color: blue; font-size: 16px;">
        <span style="margin: 10px;">
            <svg width="50" height="50">
                <circle cx="25" cy="25" r="20"/>
            </svg>
        </span>
    </div>
    """

    test_file = tmp_path / "test.html"
    test_file.write_text(html)

    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(html, 'html.parser')
    preprocessor._fix_resource_paths(soup, str(test_file))

    img = soup.find('img')
    assert "color: blue" in img['style']
    assert "font-size: 16px" in img['style']
    assert "margin: 10px" in img['style']


def test_svg_attributes_handling(tmp_path: Path):
    """Test handling of various SVG attributes."""
    html = """
    <svg viewbox="0 0 100 100">
        <circle cx="50" cy="50" r="40"/>
    </svg>
    <svg>
        <rect width="20" height="20"/>
    </svg>
    """

    test_file = tmp_path / "test.html"
    test_file.write_text(html)

    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(html, 'html.parser')
    preprocessor._fix_resource_paths(soup, str(test_file))

    images = soup.find_all('img')

    # First image should have the viewBox from viewbox
    assert "0%200%20100%20100" in images[0]['src']

    # Second image should have default viewBox
    assert "0%200%2024%2024" in images[1]['src']


def test_external_svg_references(tmp_path: Path):
    """Test handling of external SVG references."""
    html = """
    <html>
    <head></head>
    <body>
        <img src="image.svg"/>
        <img src="icons/icon.svg"/>
    </body>
    </html>
    """

    test_file = tmp_path / "test.html"
    test_file.write_text(html)

    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(html, 'html.parser')
    preprocessor._fix_resource_paths(soup, str(test_file))

    # Check that relative paths were converted to absolute
    images = soup.find_all('img')
    assert all(img['src'].startswith('file://') for img in images)