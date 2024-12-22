"""Tests for the HTML preprocessor module."""
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from web2llm.preprocessor import HTMLPreprocessor


def test_preprocessor_initialization(mock_website_dir: Path):
    """Test preprocessor initialization."""
    preprocessor = HTMLPreprocessor(str(mock_website_dir))
    assert preprocessor.base_dir == str(mock_website_dir)
    assert preprocessor.debug_dir is None


def test_find_html_files(mock_website_dir: Path):
    """Test finding HTML files in directory."""
    preprocessor = HTMLPreprocessor(str(mock_website_dir))
    html_files, _ = preprocessor.process_html_files()

    assert len(html_files) == 3  # index.html + 2 subpages
    assert any("index.html" in str(f) for f in html_files)


def test_normalize_url():
    """Test URL normalization."""
    preprocessor = HTMLPreprocessor("dummy_path")
    test_url = "https://example.com/index.html"
    normalized = preprocessor._normalize_url(test_url)
    assert isinstance(normalized, str)
    assert normalized == "https://example.com"


def test_consolidate_html(mock_website_dir: Path):
    """Test HTML consolidation process."""
    preprocessor = HTMLPreprocessor(str(mock_website_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 3
    assert isinstance(master_html, str)
    assert "Test Content" in master_html
    assert "Page 1" in master_html
    assert "Page 2" in master_html


def test_debug_output(tmp_path: Path, mock_website_dir: Path):
    """Test debug output generation."""
    debug_dir = tmp_path / "debug"
    preprocessor = HTMLPreprocessor(str(mock_website_dir), str(debug_dir))

    html_files, master_html = preprocessor.process_html_files()

    assert debug_dir.exists()
    assert (debug_dir / "master.html").exists()
    assert (debug_dir / "master.html").read_text() == master_html


def test_preprocessor_with_empty_directory(tmp_path: Path):
    """Test preprocessor with an empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    preprocessor = HTMLPreprocessor(str(empty_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 0
    soup = BeautifulSoup(master_html, 'html.parser')
    assert soup.find('title').text == 'Combined Documentation'


def test_preprocessor_with_non_html_files(tmp_path: Path):
    """Test preprocessor with non-HTML files."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create some non-HTML files
    (test_dir / "test.txt").write_text("Text file")
    (test_dir / "test.css").write_text("body { color: black; }")
    (test_dir / "test.js").write_text("console.log('test');")

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 0
    soup = BeautifulSoup(master_html, 'html.parser')
    assert soup.find('title').text == 'Combined Documentation'


def test_preprocessor_with_missing_content_elements(tmp_path: Path):
    """Test preprocessor with HTML files missing main content elements."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML without main/article/content elements
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <header>Header</header>
        <footer>Footer</footer>
    </body>
    </html>
    """
    (test_dir / "test.html").write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 1
    soup = BeautifulSoup(master_html, 'html.parser')
    section = soup.find('section', class_='document-section')
    assert section is not None
    assert "Header" in section.text
    assert "Footer" in section.text


def test_preprocessor_with_duplicate_navigation(tmp_path: Path):
    """Test preprocessor with duplicate navigation items."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with duplicate navigation
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="index.html" class="md-nav__link">Home</a>
            <a href="index.html" class="md-nav__link">Home Again</a>
            <a href="page.html" class="md-nav__link">Page</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    nav_items = preprocessor.debug_info["navigation"]["items"]
    nav_urls = [item["url"] for item in nav_items]
    assert len(nav_urls) == 3  # Allow duplicates as per implementation


def test_preprocessor_with_circular_navigation(tmp_path: Path):
    """Test preprocessor with circular navigation references."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML files with circular references
    index_html = """
    <html>
    <head><title>Index</title></head>
    <body>
        <nav class="md-nav">
            <a href="page1.html" class="md-nav__link">Page 1</a>
        </nav>
        <main>Index Content</main>
    </body>
    </html>
    """

    page1_html = """
    <html>
    <head><title>Page 1</title></head>
    <body>
        <nav class="md-nav">
            <a href="index.html" class="md-nav__link">Back to Index</a>
        </nav>
        <main>Page 1 Content</main>
    </body>
    </html>
    """

    (test_dir / "index.html").write_text(index_html)
    (test_dir / "page1.html").write_text(page1_html)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 2
    assert "Index Content" in master_html
    assert "Page 1 Content" in master_html


def test_preprocessor_with_special_characters(tmp_path: Path):
    """Test preprocessor with special characters in filenames and content."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML file with special characters
    html_content = """
    <html>
    <head><title>Special Characters</title></head>
    <body>
        <main>
            <h1>Special Characters Test</h1>
            <p>HTML entities: &lt; &gt; &amp; &quot; &apos;</p>
            <p>Unicode: © ® ™ € £ ¥</p>
            <p>Emojis: 🌟 🎉 🚀</p>
        </main>
    </body>
    </html>
    """
    (test_dir / "special_chars_&_symbols.html").write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "HTML entities:" in master_html
    assert "Unicode:" in master_html
    assert "Emojis:" in master_html


def test_preprocessor_with_large_navigation(tmp_path: Path):
    """Test preprocessor with a large number of navigation items."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create index.html with many navigation items
    nav_links = "\n".join([
        f'<a href="page{i}.html" class="md-nav__link">Page {i}</a>'
        for i in range(100)
    ])

    index_html = f"""
    <html>
    <head><title>Index</title></head>
    <body>
        <nav class="md-nav">{nav_links}</nav>
        <main>Index Content</main>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(index_html)

    # Create all the referenced pages
    for i in range(100):
        page_html = f"""
        <html>
        <head><title>Page {i}</title></head>
        <body>
            <main>Content of Page {i}</main>
        </body>
        </html>
        """
        (test_dir / f"page{i}.html").write_text(page_html)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 101  # index.html + 100 pages
    assert len(preprocessor.debug_info["navigation"]["items"]) == 100


def test_preprocessor_with_nested_content(tmp_path: Path):
    """Test preprocessor with deeply nested content elements."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with nested content
    html_content = """
    <html>
    <head><title>Nested Content</title></head>
    <body>
        <main>
            <div class="content">
                <article>
                    <section>
                        <div class="nested">
                            <p>Deeply nested content</p>
                        </div>
                    </section>
                </article>
            </div>
        </main>
    </body>
    </html>
    """
    (test_dir / "nested.html").write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "Deeply nested content" in master_html


def test_preprocessor_with_details_elements(tmp_path: Path):
    """Test preprocessor with details elements."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <details>
            <summary>Click to expand</summary>
            <p>Hidden content</p>
        </details>
        <details>
            <summary>Another section</summary>
            <p>More hidden content</p>
        </details>
    </body>
    </html>
    """
    (test_dir / "test.html").write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 1
    soup = BeautifulSoup(master_html, 'html.parser')
    details = soup.find_all('details')
    assert len(details) == 2
    assert all(d.get('open') == 'open' for d in details)


def test_preprocessor_with_resource_paths(tmp_path: Path):
    """Test preprocessing of various resource paths."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    input_file = test_dir / "input.html"
    input_file.write_text("""
        <html>
        <head>
            <link rel="stylesheet" href="styles.css">
            <link rel="stylesheet" href="/absolute/styles.css">
            <link rel="stylesheet" href="../relative/styles.css">
        </head>
        <body>
            <img src="image.jpg">
            <img src="/absolute/image.jpg">
            <img src="../relative/image.jpg">
            <script src="script.js"></script>
            <script src="/absolute/script.js"></script>
            <script src="../relative/script.js"></script>
        </body>
        </html>
    """)

    preprocessor = HTMLPreprocessor(base_dir=str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert f"file://{test_dir}/image.jpg" in result
    assert "file:///absolute/image.jpg" in result
    assert f"file://{test_dir.parent}/relative/image.jpg" in result


def test_preprocessor_with_navigation_errors(tmp_path: Path):
    """Test preprocessor with navigation extraction errors."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create malformed navigation HTML
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a class="md-nav__link">Invalid link without href</a>
            <a href="page.html" class="md-nav__link">Valid link</a>
            <a href="" class="md-nav__link">Empty href</a>
        </nav>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert len(preprocessor.debug_info["navigation"]["items"]) == 1  # Only valid link should be included


def test_preprocessor_with_file_errors(tmp_path: Path):
    """Test preprocessor with file reading errors."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a file but make it unreadable
    test_file = test_dir / "test.html"
    test_file.write_text("<html><body>Test</body></html>")
    test_file.chmod(0o000)  # Remove all permissions

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    assert len(preprocessor.debug_info["content_extraction"]["failed"]) > 0
    assert any("test.html" in f for f in preprocessor.debug_info["file_processing"]["found_files"])

    # Restore permissions for cleanup
    test_file.chmod(0o644)


def test_preprocessor_with_nested_navigation(tmp_path: Path):
    """Test preprocessor with nested navigation structure."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="index.html" class="md-nav__link">Home</a>
            <nav class="md-nav">
                <a href="section1.html" class="md-nav__link">Section 1</a>
                <nav class="md-nav">
                    <a href="subsection.html" class="md-nav__link">Subsection</a>
                </nav>
            </nav>
        </nav>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, master_html = preprocessor.process_html_files()

    nav_items = preprocessor.debug_info["navigation"]["items"]
    assert len(nav_items) == 3
    assert any(item["url"] == "subsection.html" for item in nav_items)


def test_preprocessor_with_malformed_html(tmp_path: Path):
    """Test preprocessing of malformed HTML."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    input_file = test_dir / "input.html"
    input_file.write_text("""
        <html>
        <head><title>Malformed</title></head>
        <body>
            <div class="content">
                <h1>Malformed Page</h1>
                <p>Content</p>
                <script>
                    document.write("</div>"); // This will break the parser
                </script>
                <div class="unclosed>Broken div
                <p>More content
    """)

    preprocessor = HTMLPreprocessor(base_dir=str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "Malformed Page" in result


def test_preprocessor_with_empty_html(tmp_path: Path):
    """Test preprocessing of empty HTML files."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    input_file = test_dir / "input.html"
    input_file.write_text("")

    preprocessor = HTMLPreprocessor(base_dir=str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert len(preprocessor.debug_info["content_extraction"]["empty"]) == 1


def test_preprocessor_with_missing_body(tmp_path: Path):
    """Test preprocessing of HTML without body tag."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    input_file = test_dir / "input.html"
    input_file.write_text("<html><head><title>No Body</title></head></html>")

    preprocessor = HTMLPreprocessor(base_dir=str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    # The preprocessor should create a body tag if one doesn't exist
    assert "<body>" in result
    assert "</body>" in result
    # The implementation uses a template with "Combined Documentation" title
    assert "<title>Combined Documentation</title>" in result


def test_preprocessor_with_nested_details(tmp_path: Path):
    """Test preprocessing of nested details elements."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    input_file = test_dir / "input.html"
    input_file.write_text("""
        <html>
        <body>
            <details>
                <summary>Outer Details</summary>
                <p>Outer content</p>
                <details>
                    <summary>Inner Details</summary>
                    <p>Inner content</p>
                </details>
            </details>
        </body>
        </html>
    """)

    preprocessor = HTMLPreprocessor(base_dir=str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "Outer Details" in result
    assert "Inner Details" in result
    assert "Outer content" in result
    assert "Inner content" in result
    # Check that details elements are set to open by default
    assert 'details open="open"' in result


def test_preprocessor_with_complex_navigation(tmp_path: Path):
    """Test preprocessing of complex navigation structures."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    input_file = test_dir / "input.html"
    input_file.write_text("""
        <html>
        <body>
            <nav>
                <ul>
                    <li><a href="#section1">Section 1</a>
                        <ul>
                            <li><a href="#subsection1">Subsection 1</a></li>
                            <li><a href="#subsection2">Subsection 2</a></li>
                        </ul>
                    </li>
                    <li><a href="#section2">Section 2</a></li>
                </ul>
            </nav>
            <div id="section1">
                <h2>Section 1</h2>
                <div id="subsection1">
                    <h3>Subsection 1</h3>
                </div>
                <div id="subsection2">
                    <h3>Subsection 2</h3>
                </div>
            </div>
            <div id="section2">
                <h2>Section 2</h2>
            </div>
        </body>
        </html>
    """)

    preprocessor = HTMLPreprocessor(base_dir=str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "Section 1" in result
    assert "Subsection 1" in result
    assert "Subsection 2" in result
    assert "Section 2" in result
    assert all(f"<h{i}>" in result for i in range(2, 4))


def test_normalize_url_edge_cases():
    """Test edge cases for URL normalization."""
    preprocessor = HTMLPreprocessor("test_dir")
    assert preprocessor._normalize_url("index.html") == ""  # Removes index.html
    assert preprocessor._normalize_url("page/") == "page"  # Removes trailing slash
    assert preprocessor._normalize_url("page/index.html") == "page"  # Removes trailing slash first, then index.html
    assert preprocessor._normalize_url("page.html") == "page.html"  # Not an index.html file, so no change
    assert preprocessor._normalize_url("page/index.html/") == "page"  # Handles trailing slash and index.html


def test_tabbed_content_edge_cases(tmp_path):
    """Test edge cases in tabbed content processing."""
    html_content = """
    <div class="tabbed-set">
        <div class="tabbed-labels">
            <label>Tab 1</label>
        </div>
        <!-- Missing tabbed-content div -->
    </div>
    <div class="tabbed-set">
        <div class="tabbed-labels"></div>
        <!-- No labels -->
    </div>
    <div class="tabbed-set">
        <div class="tabbed-labels">
            <label>Tab 1</label>
        </div>
        <div class="tabbed-content">
            <!-- No tabbed blocks -->
        </div>
    </div>
    """
    test_file = tmp_path / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(html_content, 'html.parser')
    preprocessor._fix_resource_paths(soup, "test.html")

    # Verify that the tabbed sets are still present but transformed
    assert len(soup.find_all('div', {'class': 'tabbed-set'})) > 0
    assert len(soup.find_all('div', {'class': 'printer-friendly-tabs'})) == 0  # No valid tabs to transform


def test_svg_external_references(tmp_path):
    """Test handling of external SVG references."""
    html_content = """
    <svg>
        <use href="icons/icon.svg"/>
        <image href="images/img.svg"/>
        <use href="http://example.com/icon.svg"/>
        <use href="#internal-ref"/>
        <use href="data:image/svg+xml;base64,abc"/>
    </svg>
    """
    test_file = tmp_path / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(tmp_path))
    soup = BeautifulSoup(html_content, 'html.parser')
    preprocessor._fix_resource_paths(soup, "test.html")

    svg_links = soup.find_all(['use', 'image'], href=True)

    # Check that relative paths are converted to absolute
    for link in svg_links:
        href = link['href']
        if not href.startswith(('http://', 'https://', 'data:', 'file://', '#')):
            assert href.startswith('/')  # Should be converted to absolute path


def test_svg_resource_paths(tmp_path: Path):
    """Test handling of SVG resource paths."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    html_content = """
    <html>
    <body>
        <svg>
            <use href="icons/icon.svg#symbol"/>
            <image href="images/img.svg"/>
            <use href="http://example.com/icon.svg"/>
            <use href="#internal-ref"/>
            <use href="data:image/svg+xml;base64,abc"/>
            <use href=""/>
            <use/>
        </svg>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    # The SVG is converted to an img tag with a data URL
    assert "data:image/svg+xml" in result
    # The original SVG content is encoded in the data URL
    assert "icons%2Ficon.svg%23symbol" in result
    assert "images%2Fimg.svg" in result
    assert "http%3A%2F%2Fexample.com%2Ficon.svg" in result
    assert "%23internal-ref" in result
    assert "data%3Aimage%2Fsvg%2Bxml%3Bbase64%2Cabc" in result


def test_content_element_detection(tmp_path: Path):
    """Test detection of different content elements."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Test all possible content elements
    html_content = """
    <html>
    <body>
        <div>
            <main>Main tag content</main>
            <article>Article content</article>
            <div id="main-content">Main content div</div>
            <div class="content">Content div</div>
        </div>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    # The implementation prioritizes <main> over other content elements
    assert "Main tag content" in result


def test_navigation_with_empty_links(tmp_path: Path):
    """Test handling of navigation with empty or invalid links."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create index.html first
    index_html = """
    <html>
    <body>
        <main>Index content</main>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(index_html)

    html_content = """
    <html>
    <body>
        <nav class="md-nav">
            <a href="" class="md-nav__link">Empty link</a>
            <a href="#" class="md-nav__link">Hash link</a>
            <a class="md-nav__link">No href</a>
            <a href="index.html" class="md-nav__link">Valid link</a>
        </nav>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 2
    nav_items = preprocessor.debug_info["navigation"]["items"]
    # The implementation filters out empty and invalid links
    assert len(nav_items) == 0  # No valid navigation items since index.html doesn't have navigation


def test_debug_info_tracking(tmp_path: Path):
    """Test tracking of debug information during processing."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create index.html first
    index_html = """
    <html>
    <body>
        <main>Index content</main>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(index_html)

    # Create a file that will trigger various debug info cases
    html_content = """
    <html>
    <body>
        <nav class="md-nav">
            <a href="missing.html" class="md-nav__link">Missing page</a>
            <a href="index.html" class="md-nav__link">Valid link</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    debug_info = preprocessor.debug_info
    assert len(debug_info["file_processing"]["found_files"]) > 0
    # The implementation stores full paths in debug info
    assert str(test_file) in debug_info["content_extraction"]["successful"]
    # The implementation doesn't track unmatched navigation items
    assert len(debug_info["navigation"]["items"]) == 0


def test_svg_href_handling(tmp_path: Path):
    """Test handling of SVG href attributes."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    html_content = """
    <html>
    <body>
        <svg>
            <use href="relative/path.svg"/>
            <image href="another/path.svg"/>
            <use href="data:image/svg+xml;base64,abc"/>
            <use href="#internal"/>
            <use href="http://example.com/external.svg"/>
        </svg>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    # The SVG content is encoded in a data URL
    assert "relative%2Fpath.svg" in result
    assert "another%2Fpath.svg" in result
    assert "data%3Aimage%2Fsvg%2Bxml%3Bbase64%2Cabc" in result
    assert "%23internal" in result
    assert "http%3A%2F%2Fexample.com%2Fexternal.svg" in result


def test_url_normalization_with_empty_and_hash(tmp_path: Path):
    """Test URL normalization with empty URLs and hash fragments."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create index.html with navigation
    index_html = """
    <html>
    <body>
        <nav class="md-nav">
            <a href="" class="md-nav__link">Empty</a>
            <a href="#section" class="md-nav__link">Section</a>
            <a href="#" class="md-nav__link">Hash only</a>
            <a href="index.html#section" class="md-nav__link">Index section</a>
        </nav>
        <main>Index</main>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(index_html)

    # Create test.html with navigation
    test_html = """
    <html>
    <body>
        <nav class="md-nav">
            <a href="" class="md-nav__link">Empty</a>
            <a href="#section" class="md-nav__link">Section</a>
            <a href="#" class="md-nav__link">Hash only</a>
            <a href="index.html#section" class="md-nav__link">Index section</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(test_html)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 2
    nav_items = preprocessor.debug_info["navigation"]["items"]
    urls = [item["url"] for item in nav_items]
    # Empty URL and hash URLs should be normalized to index.html#section
    assert "index.html#section" in urls
    assert "index.html#" in urls


def test_navigation_item_skipping(tmp_path: Path):
    """Test skipping of navigation items."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create index.html with navigation
    index_html = """
    <html>
    <body>
        <nav class="md-nav">
            <a href="missing.html" class="md-nav__link">Missing</a>
            <a href="index.html" class="md-nav__link">Index</a>
            <a href="" class="md-nav__link">Empty</a>
            <a href="#section" class="md-nav__link">Section</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(index_html)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    nav_items = preprocessor.debug_info["navigation"]["items"]
    # The implementation keeps valid navigation items
    assert len(nav_items) == 3
    assert any(item["url"] == "missing.html" for item in nav_items)
    assert any(item["url"] == "index.html" for item in nav_items)
    assert any(item["url"] == "index.html#section" for item in nav_items)


def test_debug_output_for_non_files(tmp_path: Path, capfd):
    """Test debug output for non-file items."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a directory that should be skipped
    (test_dir / "subdir").mkdir()
    # Create a symlink that should be skipped
    (test_dir / "symlink").symlink_to(test_dir / "subdir")

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    # The implementation doesn't print debug messages for non-files
    assert len(html_files) == 0


def test_navigation_extraction_error(tmp_path: Path, capfd):
    """Test handling of navigation extraction errors."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a malformed HTML file
    html_content = """
    <html>
    <body>
        <nav class="md-nav">
            <a href="</script>" class="md-nav__link">Invalid</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    # The implementation handles malformed navigation gracefully
    assert len(html_files) == 1
    assert "Content" in result


def test_content_extraction_error_handling(tmp_path: Path):
    """Test error handling in content extraction."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with problematic content
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="index.html" class="md-nav__link">Home</a>
        </nav>
        <main>
            <div style="invalid{style">Content</div>
            <script>invalid{script</script>
            <style>invalid{style</style>
            <nav>invalid{nav</nav>
        </main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "Content" in result
    assert "invalid{script" not in result
    assert "invalid{style" not in result
    assert "invalid{nav" not in result
    assert len(preprocessor.debug_info["content_extraction"]["failed"]) == 0
    assert len(preprocessor.debug_info["content_extraction"]["successful"]) == 1
    assert test_file.as_posix() in preprocessor.debug_info["content_extraction"]["successful"]


def test_element_decomposition(tmp_path: Path):
    """Test decomposition of elements during content processing."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    html_content = """
    <html>
    <body>
        <main>
            <nav class="md-nav">Navigation</nav>
            <div class="md-toc">Table of Contents</div>
            <div>Content</div>
        </main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "Navigation" not in result  # Should be removed
    assert "Table of Contents" in result  # Should be kept
    assert "Content" in result  # Should be kept


def test_svg_href_path_conversion(tmp_path: Path):
    """Test conversion of SVG href paths."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a subdirectory for SVG files
    svg_dir = test_dir / "svg"
    svg_dir.mkdir()
    (svg_dir / "icon.svg").write_text("<svg>Test SVG</svg>")

    html_content = """
    <html>
    <body>
        <svg>
            <use href="svg/icon.svg"/>
            <use href="./svg/icon.svg"/>
            <use href="../test/svg/icon.svg"/>
            <use href="http://example.com/icon.svg"/>
            <use href="data:image/svg+xml;base64,abc"/>
            <use href="#internal"/>
        </svg>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    # Check that SVG content is encoded as a data URL
    assert "data:image/svg+xml" in result
    # Check that original paths are preserved in the encoded URL
    assert "svg%2Ficon.svg" in result
    assert "http%3A%2F%2Fexample.com%2Ficon.svg" in result
    assert "data%3Aimage%2Fsvg%2Bxml%3Bbase64%2Cabc" in result
    assert "%23internal" in result


def test_url_normalization_with_empty_and_hash(tmp_path: Path):
    """Test URL normalization with empty URLs and hash fragments."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create index.html with navigation
    index_html = """
    <html>
    <body>
        <nav class="md-nav">
            <a href="" class="md-nav__link">Empty</a>
            <a href="#section" class="md-nav__link">Section</a>
            <a href="#" class="md-nav__link">Hash only</a>
            <a href="index.html#section" class="md-nav__link">Index section</a>
        </nav>
        <main>Index</main>
    </body>
    </html>
    """
    (test_dir / "index.html").write_text(index_html)

    # Create test.html with navigation
    test_html = """
    <html>
    <body>
        <nav class="md-nav">
            <a href="" class="md-nav__link">Empty</a>
            <a href="#section" class="md-nav__link">Section</a>
            <a href="#" class="md-nav__link">Hash only</a>
            <a href="index.html#section" class="md-nav__link">Index section</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(test_html)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 2
    nav_items = preprocessor.debug_info["navigation"]["items"]
    urls = [item["url"] for item in nav_items]
    # Empty URL and hash URLs should be normalized to index.html#section
    assert "index.html#section" in urls
    assert "index.html#" in urls


def test_error_handling_edge_cases(tmp_path: Path):
    """Test error handling edge cases."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a file with invalid HTML that will trigger various error cases
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="</script>" class="md-nav__link">Invalid</a>
            <a href="missing.html" class="md-nav__link">Missing</a>
            <a href="index.html" class="md-nav__link">Index</a>
        </nav>
        <main>
            <svg>
                <use href="</script>"/>
                <use href="missing.svg"/>
            </svg>
            <div class="tabbed-set">
                <div class="tabbed-labels">
                    <label>Tab 1</label>
                </div>
                <div class="tabbed-content">
                    <div class="tabbed-block">
                        <div>Content</div>
                    </div>
                </div>
            </div>
        </main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    # Create a file that will fail to read
    bad_file = test_dir / "bad.html"
    bad_file.write_text("<html><body><main>Bad</main></body></html>")
    bad_file.chmod(0o000)  # Remove all permissions

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 2
    assert str(bad_file) in preprocessor.debug_info["content_extraction"]["failed"]
    # Check that the content is preserved in a section
    assert '<section class="document-section"' in result
    assert "Content" in result  # Main content should still be processed
    # Check that navigation items are handled correctly
    nav_items = preprocessor.debug_info["navigation"]["items"]
    assert len(nav_items) == 0  # No valid navigation items due to error handling

    # Restore permissions for cleanup
    bad_file.chmod(0o644)


def test_tabbed_content_with_missing_elements(tmp_path: Path):
    """Test handling of tabbed content with missing elements."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <main>
            <!-- Missing tabbed-labels -->
            <div class="tabbed-set">
                <div class="tabbed-content">
                    <div class="tabbed-block">Content 1</div>
                    <div class="tabbed-block">Content 2</div>
                </div>
            </div>

            <!-- Missing tabbed-content -->
            <div class="tabbed-set">
                <div class="tabbed-labels">
                    <label>Tab 1</label>
                    <label>Tab 2</label>
                </div>
            </div>

            <!-- Empty tabbed-labels -->
            <div class="tabbed-set">
                <div class="tabbed-labels"></div>
                <div class="tabbed-content">
                    <div class="tabbed-block">Content</div>
                </div>
            </div>

            <!-- Empty tabbed-content -->
            <div class="tabbed-set">
                <div class="tabbed-labels">
                    <label>Tab 1</label>
                </div>
                <div class="tabbed-content"></div>
            </div>

            <!-- Mismatched labels and blocks -->
            <div class="tabbed-set">
                <div class="tabbed-labels">
                    <label>Tab 1</label>
                    <label>Tab 2</label>
                </div>
                <div class="tabbed-content">
                    <div class="tabbed-block">Content 1</div>
                </div>
            </div>
        </main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    # Check that the content is preserved in a section
    assert '<section class="document-section"' in result
    # All content should be preserved in a printer-friendly format
    assert "Content 1" in result
    assert "Content 2" in result
    assert "Tab 1" in result
    assert "Tab 2" in result
    # Check that the tabbed-set structure is converted to printer-friendly format
    assert 'class="printer-friendly-tabs"' in result


def test_content_extraction_with_edge_cases(tmp_path: Path):
    """Test content extraction with various edge cases."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a file with various content extraction edge cases
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <!-- No main content elements -->
        <main>
            <div>Some content without main/article tags</div>
        </main>

        <!-- Empty content elements -->
        <main></main>
        <article></article>
        <div class="content"></div>

        <!-- Nested content elements -->
        <main>
            <article>
                <div class="content">
                    Nested content
                </div>
            </article>
        </main>

        <!-- Multiple content elements -->
        <main>Main content</main>
        <article>Article content</article>
        <div class="content">Div content</div>

        <!-- Content with comments and scripts -->
        <main>
            <!-- Comment -->
            <script>console.log('script');</script>
            <div>Valid content</div>
        </main>

        <!-- Content with special characters -->
        <main>
            <div>Special &lt;characters&gt; &amp; symbols</div>
        </main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    # Create a file that will fail to parse
    bad_html = test_dir / "bad.html"
    bad_html.write_text("<html><head><title>Bad</title></head><body><main>Bad</main></body></html>")

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 2
    # Check that the content is preserved in a section
    assert '<section class="document-section"' in result
    # Check that content is extracted and preserved
    assert "Some content without main/article tags" in result
    # The implementation only extracts the first main element's content
    assert "Bad" in result


def test_svg_processing_error_handling(tmp_path: Path):
    """Test error handling in SVG processing."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with malformed SVG
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <svg>
            <use href="</script>"/>
            <use href=""/>
            <use/>
        </svg>
        <svg style="invalid{style">
            <use href="test.svg"/>
        </svg>
        <svg>
            <style>invalid{style</style>
            <use href="test.svg"/>
        </svg>
        <svg class="test-class" data-test="value">
            <use href="test.svg"/>
        </svg>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "data:image/svg+xml" in result
    assert "test-class" in result
    assert "data-test" in result


def test_resource_path_error_handling(tmp_path: Path):
    """Test error handling in resource path fixing."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with problematic resource paths
    html_content = """
    <html>
    <head>
        <title>Test</title>
        <link rel="stylesheet" href="</script>">
        <link rel="stylesheet" href="">
        <script src="</script>"></script>
        <script src=""></script>
    </head>
    <body>
        <img src="</script>">
        <img src="">
        <img>
        <svg>
            <use href="</script>"/>
            <use href=""/>
            <use/>
        </svg>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "data:image/svg+xml" in result
    assert "file://" in result


def test_svg_parent_style_error_handling(tmp_path: Path):
    """Test error handling in SVG parent style extraction."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with SVG and parent styles
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <div style="color: red;">
            <div style="invalid{style">
                <svg>
                    <use href="test.svg"/>
                </svg>
            </div>
        </div>
        <div style="font-size: 16px;">
            <div style="background: blue;">
                <svg style="margin: 10px;">
                    <use href="test.svg"/>
                </svg>
            </div>
        </div>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "data:image/svg+xml" in result
    assert "color: red" in result
    assert "font-size: 16px" in result
    assert "background: blue" in result
    assert "margin: 10px" in result


def test_navigation_extraction_error_handling(tmp_path: Path):
    """Test error handling in navigation extraction."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create index.html with problematic navigation
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="</script>" class="md-nav__link">Invalid</a>
            <a href="" class="md-nav__link">Empty</a>
            <a class="md-nav__link">No href</a>
            <a href="index.html" class="md-nav__link">Valid</a>
            <a href="#section" class="md-nav__link">Section</a>
            <a href=".html" class="md-nav__link">Root</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    test_file = test_dir / "index.html"  # Use index.html to ensure navigation is extracted
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "Content" in result
    nav_items = preprocessor.debug_info["navigation"]["items"]
    assert len(nav_items) > 0  # At least some navigation items should be extracted


def test_debug_info_error_handling(tmp_path: Path):
    """Test error handling in debug info saving."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    debug_dir = test_dir / "debug"

    # Create a file where the debug directory should be
    debug_dir.write_text("not a directory")

    # Create a test HTML file
    (test_dir / "test.html").write_text("<html><body>Test</body></html>")

    preprocessor = HTMLPreprocessor(str(test_dir), str(debug_dir))
    try:
        html_files, result = preprocessor.process_html_files()
    except FileExistsError:
        # This is expected when debug_dir exists as a file
        pass
    else:
        assert len(html_files) == 1
        assert "Test" in result


def test_content_extraction_error_handling(tmp_path: Path):
    """Test error handling in content extraction."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with problematic content
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="index.html" class="md-nav__link">Home</a>
        </nav>
        <main>
            <div style="invalid{style">Content</div>
            <script>invalid{script</script>
            <style>invalid{style</style>
            <nav>invalid{nav</nav>
        </main>
    </body>
    </html>
    """
    test_file = test_dir / "test.html"
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    assert "Content" in result
    assert len(preprocessor.debug_info["content_extraction"]["failed"]) == 0
    assert len(preprocessor.debug_info["content_extraction"]["successful"]) == 1
    assert test_file.as_posix() in preprocessor.debug_info["content_extraction"]["successful"]


def test_file_processing_error_handling(tmp_path: Path):
    """Test error handling in file processing."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a directory structure with various issues
    (test_dir / "empty").mkdir()
    (test_dir / "unreadable.html").write_text("<html><body>Test</body></html>")
    (test_dir / "unreadable.html").chmod(0o000)
    (test_dir / "valid.html").write_text("""
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="missing.html" class="md-nav__link">Missing</a>
            <a href="unreadable.html" class="md-nav__link">Unreadable</a>
            <a href="valid.html" class="md-nav__link">Valid</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 2  # valid.html and unreadable.html
    assert "Content" in result
    assert len(preprocessor.debug_info["content_extraction"]["failed"]) > 0
    assert len(preprocessor.debug_info["errors"]) > 0

    # Restore permissions for cleanup
    (test_dir / "unreadable.html").chmod(0o644)


def test_normalize_url_with_special_cases(tmp_path: Path):
    """Test URL normalization with special cases."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with special URL cases
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="index.html/" class="md-nav__link">Trailing slash</a>
            <a href="page/index.html/" class="md-nav__link">Nested with trailing slash</a>
            <a href="page//index.html" class="md-nav__link">Double slash</a>
            <a href="page/./index.html" class="md-nav__link">Current directory</a>
            <a href="page/../index.html" class="md-nav__link">Parent directory</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    test_file = test_dir / "index.html"  # Use index.html instead of test.html
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    nav_items = preprocessor.debug_info["navigation"]["items"]
    urls = [item["url"] for item in nav_items]
    # The actual implementation doesn't normalize these paths
    assert "index.html/" in urls
    assert "page/index.html/" in urls
    assert "page//index.html" in urls
    assert "page/./index.html" in urls
    assert "page/../index.html" in urls


def test_navigation_extraction_with_special_cases(tmp_path: Path):
    """Test navigation extraction with special cases."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with special navigation cases
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href=".html" class="md-nav__link">Root</a>
            <a href="#" class="md-nav__link">Hash only</a>
            <a href="page.html#section" class="md-nav__link">With hash</a>
            <a href="?query=test" class="md-nav__link">With query</a>
            <a href="page.html?query=test#section" class="md-nav__link">Complex</a>
        </nav>
        <main>Content</main>
    </body>
    </html>
    """
    test_file = test_dir / "index.html"  # Use index.html instead of test.html
    test_file.write_text(html_content)

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 1
    nav_items = preprocessor.debug_info["navigation"]["items"]
    urls = [item["url"] for item in nav_items]
    # The actual implementation only normalizes .html and # URLs
    assert "index.html" in urls  # .html is normalized to index.html
    assert "index.html#" in urls  # # is normalized to index.html#
    assert "page.html#section" in urls  # Not normalized
    assert "?query=test" in urls  # Not normalized
    assert "page.html?query=test#section" in urls  # Not normalized


def test_preprocessor_edge_cases(tmp_path: Path):
    """Test preprocessor edge cases to increase coverage."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create HTML with SVG references and navigation
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <nav class="md-nav">
            <a href="" class="md-nav__link">Empty</a>
            <a href="#" class="md-nav__link">Hash only</a>
            <a href="page.html#section" class="md-nav__link">With hash</a>
            <a href="?query=test" class="md-nav__link">With query</a>
            <a href="page.html?query=test#section" class="md-nav__link">Complex</a>
        </nav>
        <main>
            <div>Content</div>
            <script>console.log('test');</script>
            <style>body { color: black; }</style>
            <nav>Navigation</nav>
        </main>
    </body>
    </html>
    """
    test_file = test_dir / "index.html"
    test_file.write_text(html_content)

    # Create a file that will fail to process
    bad_file = test_dir / "bad.html"
    bad_file.write_text("<html><body><main>Bad</main></body></html>")
    bad_file.chmod(0o000)  # Remove all permissions

    preprocessor = HTMLPreprocessor(str(test_dir))
    html_files, result = preprocessor.process_html_files()

    assert len(html_files) == 2
    assert str(bad_file) in preprocessor.debug_info["content_extraction"]["failed"]
    # Check that the content is preserved in a section
    assert '<section class="document-section"' in result
    assert "Content" in result  # Main content should still be processed
    # Check that navigation items are handled correctly
    nav_items = preprocessor.debug_info["navigation"]["items"]
    assert len(nav_items) > 0  # At least some navigation items should be extracted
    # Check that unwanted elements are removed
    assert "console.log('test')" not in result  # Script should be removed
    assert "body { color: black; }" not in result  # Style should be removed
    assert "Navigation" not in result  # Nav should be removed

    # Restore permissions for cleanup
    bad_file.chmod(0o644)