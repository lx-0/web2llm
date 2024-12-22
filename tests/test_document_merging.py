"""Tests for document merging functionality in the HTML preprocessor."""
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from web2llm.preprocessor import HTMLPreprocessor


@pytest.fixture
def complex_website(tmp_path: Path) -> Path:
    """Create a complex website structure with multiple HTML files."""
    web_dir = tmp_path / "website"
    web_dir.mkdir(parents=True)

    # Create index.html with navigation
    index_html = """
    <html>
    <head><title>Main Page</title></head>
    <body>
        <nav class="md-nav">
            <a href="index.html" class="md-nav__link">Home</a>
            <a href="section1/page1.html" class="md-nav__link">Page 1</a>
            <a href="section1/page2.html" class="md-nav__link">Page 2</a>
            <a href="section2/page3.html" class="md-nav__link">Page 3</a>
        </nav>
        <main>
            <h1>Welcome</h1>
            <p>Main content</p>
        </main>
    </body>
    </html>
    """
    (web_dir / "index.html").write_text(index_html)

    # Create section1 with two pages
    section1 = web_dir / "section1"
    section1.mkdir()

    page1_html = """
    <html>
    <head><title>Page 1</title></head>
    <body>
        <main>
            <h1>Page 1</h1>
            <p>Content of page 1</p>
            <div class="tabbed-set">
                <div class="tabbed-labels">
                    <label>Tab A</label>
                    <label>Tab B</label>
                </div>
                <div class="tabbed-content">
                    <div class="tabbed-block">Content A</div>
                    <div class="tabbed-block">Content B</div>
                </div>
            </div>
        </main>
    </body>
    </html>
    """
    (section1 / "page1.html").write_text(page1_html)

    page2_html = """
    <html>
    <head><title>Page 2</title></head>
    <body>
        <main>
            <h1>Page 2</h1>
            <p>Content of page 2</p>
            <svg width="100" height="100">
                <circle cx="50" cy="50" r="40"/>
            </svg>
        </main>
    </body>
    </html>
    """
    (section1 / "page2.html").write_text(page2_html)

    # Create section2 with one page
    section2 = web_dir / "section2"
    section2.mkdir()

    page3_html = """
    <html>
    <head><title>Page 3</title></head>
    <body>
        <main>
            <h1>Page 3</h1>
            <p>Content of page 3</p>
            <img src="../images/test.png"/>
        </main>
    </body>
    </html>
    """
    (section2 / "page3.html").write_text(page3_html)

    return web_dir


def test_navigation_extraction(complex_website: Path):
    """Test extraction and processing of navigation items."""
    preprocessor = HTMLPreprocessor(str(complex_website))
    html_files, _ = preprocessor.process_html_files()

    # Check that all files were found
    assert len(html_files) == 4

    # Check navigation items in debug info
    nav_items = preprocessor.debug_info["navigation"]["items"]
    assert len(nav_items) == 4

    # Check navigation order
    nav_urls = [item["url"] for item in nav_items]
    assert "index.html" in nav_urls
    assert "section1/page1.html" in nav_urls
    assert "section2/page3.html" in nav_urls


def test_content_consolidation(complex_website: Path):
    """Test consolidation of content from multiple files."""
    preprocessor = HTMLPreprocessor(str(complex_website))
    html_files, master_html = preprocessor.process_html_files()

    # Parse the consolidated content
    soup = BeautifulSoup(master_html, 'html.parser')

    # Check that all sections are present
    sections = soup.find_all('section', {'class': 'document-section'})
    assert len(sections) == 4

    # Check section order and content
    texts = [section.get_text() for section in sections]
    assert any('Welcome' in text for text in texts)
    assert any('Content of page 1' in text for text in texts)
    assert any('Content of page 2' in text for text in texts)
    assert any('Content of page 3' in text for text in texts)

    # Check that tabbed content was processed
    printer_tabs = soup.find_all('div', {'class': 'printer-friendly-tabs'})
    assert len(printer_tabs) > 0

    # Check that SVGs were converted to images
    images = soup.find_all('img')
    assert any(img['src'].startswith('data:image/svg+xml') for img in images)

    # Check that relative image paths were converted to absolute
    assert all(img['src'].startswith(('data:', 'file://', 'http://', 'https://'))
              for img in images)


def test_error_handling(complex_website: Path):
    """Test handling of errors during file processing."""
    # Create an invalid HTML file
    invalid_html = """
    This is not HTML at all.
    Just some random text
    without any HTML structure.
    """
    (complex_website / "invalid.html").write_text(invalid_html)

    preprocessor = HTMLPreprocessor(str(complex_website))
    html_files, master_html = preprocessor.process_html_files()

    # Check that the file was found but not processed
    assert any("invalid.html" in f for f in preprocessor.debug_info["file_processing"]["found_files"])
    assert not any("invalid.html" in f for f in preprocessor.debug_info["content_extraction"]["successful"])

    # Check that valid content was still processed
    soup = BeautifulSoup(master_html, 'html.parser')
    assert 'Welcome' in soup.get_text()  # Index page content should be present


def test_large_file_merging(complex_website: Path):
    """Test merging of many files with large content."""
    # Create multiple large files
    for i in range(10):
        large_html = f"""
        <html>
        <head><title>Large Page {i}</title></head>
        <body>
            <main>
                <h1>Large Page {i}</h1>
                {'<p>Content paragraph</p>' * 100}
                <div class="tabbed-set">
                    <div class="tabbed-labels">
                        <label>Tab 1</label>
                        <label>Tab 2</label>
                    </div>
                    <div class="tabbed-content">
                        <div class="tabbed-block">{'<p>Tab content</p>' * 50}</div>
                        <div class="tabbed-block">{'<p>More content</p>' * 50}</div>
                    </div>
                </div>
            </main>
        </body>
        </html>
        """
        (complex_website / f"large{i}.html").write_text(large_html)

    preprocessor = HTMLPreprocessor(str(complex_website))
    html_files, master_html = preprocessor.process_html_files()

    # Check that all files were processed
    assert len(html_files) >= 14  # Original 4 + 10 new files

    # Check that the master HTML contains content from all files
    soup = BeautifulSoup(master_html, 'html.parser')
    sections = soup.find_all('section', {'class': 'document-section'})
    assert len(sections) >= 14

    # Check memory usage stats if available
    if "memory_usage" in preprocessor.debug_info:
        assert isinstance(preprocessor.debug_info["memory_usage"], dict)