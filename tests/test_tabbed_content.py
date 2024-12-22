"""Tests for tabbed content handling in the HTML preprocessor."""
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from web2llm.preprocessor import HTMLPreprocessor


@pytest.fixture
def tabbed_html() -> str:
    """Create a test HTML with tabbed content."""
    return """
    <html>
    <head></head>
    <body>
        <div class="tabbed-set">
            <div class="tabbed-labels">
                <label>Python</label>
                <label>JavaScript</label>
                <label>TypeScript</label>
            </div>
            <div class="tabbed-content">
                <div class="tabbed-block">
                    <pre><code>print("Hello, World!")</code></pre>
                </div>
                <div class="tabbed-block">
                    <pre><code>console.log("Hello, World!");</code></pre>
                </div>
                <div class="tabbed-block">
                    <pre><code>console.log("Hello, World!" as string);</code></pre>
                </div>
            </div>
        </div>

        <div class="tabbed-alternate">
            <div class="tabbed-labels">
                <label>Tab 1</label>
                <label>Tab 2</label>
            </div>
            <div class="tabbed-content">
                <div class="tabbed-block">Content 1</div>
                <div class="tabbed-block">Content 2</div>
            </div>
        </div>
    </body>
    </html>
    """


def test_tabbed_content_conversion(tmp_path: Path, tabbed_html: str):
    """Test conversion of tabbed content to printer-friendly format."""
    # Create a test file
    test_file = tmp_path / "test.html"
    test_file.write_text(tabbed_html)

    # Process the file
    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(tabbed_html, 'html.parser')
    preprocessor._fix_resource_paths(soup, str(test_file))

    # Check that tabbed sets were converted
    printer_tabs = soup.find_all('div', {'class': 'printer-friendly-tabs'})
    assert len(printer_tabs) == 2

    # Check first tabbed set (code examples)
    first_set = printer_tabs[0]
    sections = first_set.find_all('div', {'class': 'tab-section'})
    assert len(sections) == 3

    # Check headers
    headers = [h.get_text(strip=True) for h in first_set.find_all('div', {'class': 'tab-header'})]
    assert headers == ['Python', 'JavaScript', 'TypeScript']

    # Check content
    contents = first_set.find_all('div', {'class': 'tab-content'})
    assert 'print("Hello, World!")' in contents[0].get_text()
    assert 'console.log("Hello, World!");' in contents[1].get_text()

    # Check second tabbed set (alternate style)
    second_set = printer_tabs[1]
    sections = second_set.find_all('div', {'class': 'tab-section'})
    assert len(sections) == 2

    # Check that styles were added
    style_tag = soup.head.find('style')
    assert style_tag is not None
    assert '.printer-friendly-tabs' in style_tag.string


def test_incomplete_tabbed_content(tmp_path: Path):
    """Test handling of incomplete or malformed tabbed content."""
    html = """
    <div class="tabbed-set">
        <div class="tabbed-labels">
            <label>Tab 1</label>
        </div>
        <!-- Missing tabbed-content div -->
    </div>
    <div class="tabbed-set">
        <!-- Missing labels -->
        <div class="tabbed-content">
            <div class="tabbed-block">Content</div>
        </div>
    </div>
    """

    test_file = tmp_path / "test.html"
    test_file.write_text(html)

    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(html, 'html.parser')
    preprocessor._fix_resource_paths(soup, str(test_file))

    # Check that malformed tabbed sets were not converted
    printer_tabs = soup.find_all('div', {'class': 'printer-friendly-tabs'})
    assert len(printer_tabs) == 0

    # Original divs should still be present
    tabbed_sets = soup.find_all('div', {'class': 'tabbed-set'})
    assert len(tabbed_sets) == 2


def test_nested_tabbed_content(tmp_path: Path):
    """Test handling of nested tabbed content."""
    html = """
    <html>
    <head></head>
    <body>
        <div class="tabbed-set">
            <div class="tabbed-labels">
                <label>Outer Tab</label>
            </div>
            <div class="tabbed-content">
                <div class="tabbed-block">
                    <div class="tabbed-set">
                        <div class="tabbed-labels">
                            <label>Inner Tab</label>
                        </div>
                        <div class="tabbed-content">
                            <div class="tabbed-block">Inner Content</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    test_file = tmp_path / "test.html"
    test_file.write_text(html)

    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(html, 'html.parser')
    preprocessor._fix_resource_paths(soup, str(test_file))

    # Check that the outer tab was converted
    printer_tabs = soup.find_all('div', {'class': 'printer-friendly-tabs'})
    assert len(printer_tabs) == 1

    # Check that the inner tab content is present
    outer_tab = printer_tabs[0]
    assert 'Inner Content' in outer_tab.get_text()
    assert 'Inner Tab' in outer_tab.get_text()