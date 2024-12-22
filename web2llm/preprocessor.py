"""Module for preprocessing and consolidating HTML files."""

import base64
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote, urljoin, urlparse

from bs4 import BeautifulSoup, Comment, Tag


@dataclass
class NavigationItem:
    url: str
    text: str


class HTMLPreprocessor:
    """Preprocesses HTML files for PDF conversion."""

    def __init__(self, base_dir: str, debug_dir: Optional[str] = None):
        """Initialize the preprocessor."""
        self.base_dir = base_dir
        self.debug_dir = debug_dir
        self.debug_info = {
            "file_processing": {
                "found_files": [],
                "failed_files": []
            },
            "content_extraction": {
                "successful": [],
                "failed": [],
                "empty": []
            },
            "url_mapping": {
                "successful": [],
                "failed": []
            },
            "navigation": {
                "items": [],
                "matched": [],
                "unmatched": []
            },
            "content_extraction_details": [],
            "errors": [],
            "summary": {}
        }
        self.seen_urls = set()
        self.url_to_file_map = {}  # Map navigation URLs to actual file paths
        self.processed_files = set()

    def _normalize_url(self, url: str) -> str:
        """Normalize a URL by removing trailing slashes and index.html."""
        url = url.rstrip('/')
        if url.endswith('index.html'):
            url = url[:-10].rstrip('/')
        return url

    def _fix_resource_paths(self, soup: BeautifulSoup, file_path: str) -> None:
        """Fix paths to local resources."""
        base_dir = os.path.dirname(os.path.abspath(file_path))
        base_url = f"file://{base_dir}/"

        # Expand all details elements
        for details in soup.find_all('details'):
            details['open'] = 'open'  # Add open attribute to show content by default

        # Handle tabbed code blocks
        for tabbed_set in soup.find_all('div', {'class': ['tabbed-set', 'tabbed-alternate']}):
            # Create a new div to hold the transformed content
            new_div = soup.new_tag('div', attrs={'class': 'printer-friendly-tabs'})

            # Find all tab labels
            labels_div = tabbed_set.find('div', {'class': 'tabbed-labels'})
            if not labels_div:
                continue

            labels = labels_div.find_all('label')
            if not labels:
                continue

            # Find the tabbed content container
            tabbed_content = tabbed_set.find('div', {'class': 'tabbed-content'})
            if not tabbed_content:
                continue

            # Find all tab blocks
            tab_blocks = tabbed_content.find_all('div', {'class': 'tabbed-block'})
            if not tab_blocks:
                continue

            # Process each tab
            for label, content in zip(labels, tab_blocks):
                # Create a header for the tab
                tab_header = soup.new_tag('div', attrs={'class': 'tab-header'})
                tab_header.string = label.get_text(strip=True)

                # Create a wrapper for this tab's content
                tab_wrapper = soup.new_tag('div', attrs={'class': 'tab-section'})
                tab_wrapper.append(tab_header)

                # Create a new content div
                content_div = soup.new_tag('div', attrs={'class': 'tab-content'})

                # Extract and preserve the content
                content_html = str(content)
                content_div.append(BeautifulSoup(content_html, 'html.parser'))

                tab_wrapper.append(content_div)
                new_div.append(tab_wrapper)

            # Replace the original tabbed set with our printer-friendly version
            tabbed_set.replace_with(new_div)

            # Add styles for printer-friendly tabs to the head section
            style = soup.new_tag('style')
            style.string = '''
                .printer-friendly-tabs {
                    margin: 2em 0;
                    padding: 1.5em;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    background: #fff;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .printer-friendly-tabs .tab-section {
                    margin-bottom: 2em;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 2em;
                }
                .printer-friendly-tabs .tab-section:last-child {
                    border-bottom: none;
                    margin-bottom: 0;
                    padding-bottom: 0;
                }
                .printer-friendly-tabs .tab-header {
                    font-weight: bold;
                    margin-bottom: 1em;
                    padding: 0.75em 1em;
                    background: #f5f5f5;
                    border-radius: 4px;
                    border-left: 4px solid #2196f3;
                    color: #333;
                }
                .printer-friendly-tabs .tab-content {
                    margin: 0 1em;
                    padding: 1em;
                    background: #fafafa;
                    border-radius: 4px;
                }
                .printer-friendly-tabs pre {
                    margin: 1em 0;
                    padding: 1.5em;
                    background: #f8f8f8;
                    border-radius: 4px;
                    border: 1px solid #eee;
                    overflow-x: auto;
                }
                .printer-friendly-tabs code {
                    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
                    font-size: 0.9em;
                }
                .printer-friendly-tabs .highlight {
                    margin: 0;
                    padding: 0;
                }
            '''
            if not soup.head.find('style', string=lambda x: x and '.printer-friendly-tabs' in x):
                soup.head.append(style)

        # Fix image sources
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and not src.startswith(('http://', 'https://', 'data:', 'file://')):
                img['src'] = urljoin(base_url, src)

        # Handle inline SVGs
        for svg in soup.find_all('svg'):
            # Add required SVG attributes if missing
            if not svg.get('xmlns'):
                svg['xmlns'] = 'http://www.w3.org/2000/svg'
            if not svg.get('width'):
                svg['width'] = '24'
            if not svg.get('height'):
                svg['height'] = '24'
            if not svg.get('viewBox'):
                if svg.get('viewbox'):
                    svg['viewBox'] = svg.get('viewbox')
                else:
                    svg['viewBox'] = '0 0 24 24'

            # Ensure proper rendering in wkhtmltopdf
            current_style = svg.get('style', '')
            svg['style'] = f"display: inline-block; vertical-align: middle; {current_style}"

            # Remove comments from the SVG
            for comment in svg.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            # Extract CSS variables from parent elements
            parent_styles = []
            parent = svg.parent
            while parent and parent.name:
                if parent.get('style'):
                    parent_styles.append(parent.get('style'))
                parent = parent.parent

            # Add parent styles to SVG
            if parent_styles:
                svg['style'] = f"{' '.join(parent_styles)} {svg.get('style', '')}"

            # Clean up SVG string
            svg_str = str(svg)
            svg_str = re.sub(r'<!--.*?-->', '', svg_str, flags=re.DOTALL)  # Remove any remaining comments
            svg_str = re.sub(r'\s+', ' ', svg_str)  # Normalize whitespace
            svg_str = svg_str.strip()  # Remove leading/trailing whitespace

            # URL encode the entire SVG string at once
            svg_str = quote(svg_str, safe='')

            data_uri = f"data:image/svg+xml;charset=utf-8,{svg_str}"

            # Create new img tag with proper attributes
            new_img = soup.new_tag('img')
            new_img['src'] = data_uri
            new_img['width'] = svg.get('width', '24')
            new_img['height'] = svg.get('height', '24')
            new_img['style'] = svg.get('style', 'display: inline-block; vertical-align: middle;')
            new_img['alt'] = svg.get('aria-label', '') or 'SVG icon'  # Add alt text for accessibility

            # Copy over any CSS classes
            if svg.get('class'):
                new_img['class'] = svg.get('class')

            # Copy over any data attributes
            for attr in svg.attrs:
                if attr.startswith('data-'):
                    new_img[attr] = svg[attr]

            svg.replace_with(new_img)

        # Fix external SVG references
        for svg_link in soup.find_all(['use', 'image'], href=True):
            href = svg_link.get('href')
            if href and not href.startswith(('http://', 'https://', 'data:', 'file://', '#')):
                svg_link['href'] = urljoin(base_url, href)

        # Fix CSS links
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href and not href.startswith(('http://', 'https://', 'data:', 'file://')):
                link['href'] = urljoin(base_url, href)

        # Fix script sources
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not src.startswith(('http://', 'https://', 'data:', 'file://')):
                script['src'] = urljoin(base_url, src)

    def _read_file(self, file_path: str) -> str:
        """Read the contents of a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _extract_navigation(self, html_file: str) -> list[NavigationItem]:
        """Extract navigation items from the HTML."""
        def _normalize_url(url: str) -> str:
            if url == '.html':
                return 'index.html'
            if url.startswith('#'):
                return f"index.html{url}"
            return url

        soup = BeautifulSoup(self._read_file(html_file), 'html.parser')
        nav_items = []
        seen_items = set()

        for nav in soup.find_all('nav', {'class': 'md-nav'}):
            for link in nav.find_all('a', {'class': 'md-nav__link'}):
                url = link.get('href', '')
                text = link.get_text(strip=True)

                if not url or not text:
                    continue

                url = _normalize_url(url)
                item_key = f"{url}|{text}"

                if item_key not in seen_items:
                    seen_items.add(item_key)
                    nav_items.append(NavigationItem(url=url, text=text))

        return nav_items

    def _deduplicate_navigation(self) -> None:
        """Deduplicate navigation items while preserving order."""
        seen = set()
        unique_items = []
        for item in self.debug_info["navigation"]["items"]:
            url = item['url']
            if url.startswith('#'):
                url = f"index.html{url}"
            key = f"{url}|{item['text']}"
            if key not in seen:
                seen.add(key)
                item['url'] = url  # Update the URL to include index.html for fragments
                unique_items.append(item)
        self.debug_info["navigation"]["items"] = unique_items

    def _map_url_to_file(self, url: str, html_files: List[str]) -> Optional[str]:
        """Map a navigation URL to an actual file path."""
        if url in self.url_to_file_map:
            return self.url_to_file_map[url]

        # Handle special cases
        if url == "index.html" or url == ".html":
            for file_path in html_files:
                basename = os.path.basename(file_path)
                if basename in ['.html', 'index.html']:
                    self.url_to_file_map[url] = file_path
                    return file_path

        # Try direct match
        for file_path in html_files:
            if file_path.endswith(url):
                self.url_to_file_map[url] = file_path
                return file_path

        return None

    def process_html_files(self) -> Tuple[List[str], str]:
        """Process HTML files and return a list of file paths and master HTML content."""
        html_files = []
        master_content = []
        processed_files = set()

        try:
            print(f"Searching for HTML files in: {self.base_dir}")
            for root, _, files in os.walk(self.base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    print(f"Found file: {file_path}")

                    if os.path.isfile(file_path):
                        if file.endswith('.html') or file == '.html':  # Explicitly handle .html file
                            print(f"Adding HTML file: {file_path}")
                            html_files.append(file_path)
                            self.debug_info["file_processing"]["found_files"].append(file_path)
                        else:
                            print(f"Skipping non-HTML file: {file_path}")
                    else:
                        print(f"Skipping non-file: {file_path}")

            # Find the main/index file to extract navigation
            main_file = None
            for file_path in html_files:
                basename = os.path.basename(file_path)
                if basename in ['index.html', '.html']:
                    main_file = file_path
                    break

            # Extract navigation first
            if main_file:
                try:
                    nav_items = self._extract_navigation(main_file)
                    for item in nav_items:
                        self.debug_info["navigation"]["items"].append({
                            "url": item.url,
                            "text": item.text
                        })
                except Exception as e:
                    print(f"Error extracting navigation from {main_file}: {str(e)}")

            # Process navigation items in order
            for nav_item in self.debug_info["navigation"]["items"]:
                file_path = self._map_url_to_file(nav_item['url'], html_files)
                if file_path and file_path not in processed_files:
                    try:
                        print(f"Processing navigation item file: {file_path}")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            soup = BeautifulSoup(content, 'html.parser')

                            # Fix resource paths
                            self._fix_resource_paths(soup, file_path)

                            # Extract main content
                            main_content = None
                            elements_found = {
                                "main": False,
                                "article": False,
                                "main_div": False,
                                "content_div": False,
                                "body": False
                            }

                            # Try different content selectors in order of preference
                            if soup.find('main'):
                                main_content = soup.find('main')
                                elements_found["main"] = True
                            elif soup.find('article'):
                                main_content = soup.find('article')
                                elements_found["article"] = True
                            elif soup.find('div', {'id': 'main-content'}):
                                main_content = soup.find('div', {'id': 'main-content'})
                                elements_found["main_div"] = True
                            elif soup.find('div', {'class': 'content'}):
                                main_content = soup.find('div', {'class': 'content'})
                                elements_found["content_div"] = True
                            else:
                                main_content = soup.find('body')
                                elements_found["body"] = True

                            if main_content:
                                # Only remove unwanted elements if we found a main content area
                                if elements_found["main"] or elements_found["article"] or elements_found["main_div"] or elements_found["content_div"]:
                                    for element in main_content.find_all(['script', 'style', 'nav']):
                                        element.decompose()
                                else:
                                    # If we're using the body, preserve header and footer but remove other unwanted elements
                                    for element in main_content.find_all(['script', 'style', 'nav']):
                                        element.decompose()

                                # Add a section wrapper with file info
                                section = soup.new_tag('section')
                                section['class'] = 'document-section'
                                section['data-source'] = os.path.basename(file_path)
                                section['data-nav-text'] = nav_item['text']
                                main_content.wrap(section)

                                content_str = str(section)
                                master_content.append(content_str)

                                self.debug_info["content_extraction_details"].append({
                                    "file": file_path,
                                    "nav_text": nav_item['text'],
                                    "elements_found": elements_found,
                                    "status": "success",
                                    "content_length": len(content_str)
                                })
                                self.debug_info["content_extraction"]["successful"].append(file_path)
                                processed_files.add(file_path)
                            else:
                                self.debug_info["content_extraction"]["empty"].append(file_path)

                    except Exception as e:
                        self.debug_info["content_extraction"]["failed"].append(file_path)
                        self.debug_info["errors"].append({
                            "type": "content_extraction",
                            "file": file_path,
                            "error": str(e)
                        })
                        print(f"Error processing file {file_path}: {str(e)}")

            # Process remaining files that weren't in navigation
            for file_path in html_files:
                if file_path not in processed_files:
                    try:
                        print(f"Processing remaining file: {file_path}")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            soup = BeautifulSoup(content, 'html.parser')

                            # Fix resource paths
                            self._fix_resource_paths(soup, file_path)

                            # Extract main content
                            main_content = None
                            elements_found = {
                                "main": False,
                                "article": False,
                                "main_div": False,
                                "content_div": False,
                                "body": False
                            }

                            # Try different content selectors in order of preference
                            if soup.find('main'):
                                main_content = soup.find('main')
                                elements_found["main"] = True
                            elif soup.find('article'):
                                main_content = soup.find('article')
                                elements_found["article"] = True
                            elif soup.find('div', {'id': 'main-content'}):
                                main_content = soup.find('div', {'id': 'main-content'})
                                elements_found["main_div"] = True
                            elif soup.find('div', {'class': 'content'}):
                                main_content = soup.find('div', {'class': 'content'})
                                elements_found["content_div"] = True
                            else:
                                main_content = soup.find('body')
                                elements_found["body"] = True

                            if main_content:
                                # Only remove unwanted elements if we found a main content area
                                if elements_found["main"] or elements_found["article"] or elements_found["main_div"] or elements_found["content_div"]:
                                    for element in main_content.find_all(['script', 'style', 'nav']):
                                        element.decompose()
                                else:
                                    # If we're using the body, preserve header and footer but remove other unwanted elements
                                    for element in main_content.find_all(['script', 'style', 'nav']):
                                        element.decompose()

                                # Add a section wrapper with file info
                                section = soup.new_tag('section')
                                section['class'] = 'document-section'
                                section['data-source'] = os.path.basename(file_path)
                                main_content.wrap(section)

                                content_str = str(section)
                                master_content.append(content_str)

                                self.debug_info["content_extraction_details"].append({
                                    "file": file_path,
                                    "elements_found": elements_found,
                                    "status": "success",
                                    "content_length": len(content_str)
                                })
                                self.debug_info["content_extraction"]["successful"].append(file_path)
                            else:
                                self.debug_info["content_extraction"]["empty"].append(file_path)

                    except Exception as e:
                        self.debug_info["content_extraction"]["failed"].append(file_path)
                        self.debug_info["errors"].append({
                            "type": "content_extraction",
                            "file": file_path,
                            "error": str(e)
                        })
                        print(f"Error processing file {file_path}: {str(e)}")

        except Exception as e:
            self.debug_info["errors"].append({
                "type": "file_processing",
                "error": str(e)
            })
            print(f"Error processing HTML files: {str(e)}")

        # Create master HTML file with base path and styles
        master_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Combined Documentation</title>
            <base href="file://{os.path.abspath(self.base_dir)}/">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                .document-section {{ margin-bottom: 30px; padding: 20px; border-bottom: 1px solid #eee; }}
                .document-section::before {{
                    content: attr(data-nav-text), ' (', attr(data-source), ')';
                    display: block;
                    font-size: 0.8em;
                    color: #666;
                    margin-bottom: 10px;
                }}
                img {{ max-width: 100%; height: auto; }}
                pre {{ background: #f5f5f5; padding: 15px; overflow-x: auto; }}
                code {{ background: #f5f5f5; padding: 2px 5px; }}
            </style>
        </head>
        <body>
            {''.join(master_content)}
        </body>
        </html>
        """

        # Deduplicate navigation items
        self._deduplicate_navigation()

        # Update summary statistics
        self.debug_info["summary"] = {
            "total_files": len(html_files),
            "processed_files": len(self.debug_info["content_extraction"]["successful"]),
            "navigation_items": len(self.debug_info["navigation"]["items"]),
            "matched_items": len(self.debug_info["navigation"]["matched"]),
            "unmatched_items": len(self.debug_info["navigation"]["unmatched"]),
            "coverage": f"{(len(self.debug_info['content_extraction']['successful']) / len(html_files) * 100):.1f}%" if html_files else "0.0%"
        }

        # Save debug information if debug directory is provided
        if self.debug_dir:
            os.makedirs(self.debug_dir, exist_ok=True)
            debug_file = os.path.join(self.debug_dir, 'preprocessor_debug.json')
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(self.debug_info, f, indent=2)

            master_file = os.path.join(self.debug_dir, 'master.html')
            with open(master_file, 'w', encoding='utf-8') as f:
                f.write(master_html)

        return html_files, master_html