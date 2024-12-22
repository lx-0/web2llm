"""Module for converting HTML content to PDF using wkhtmltopdf."""

import os
import re
from pathlib import Path


class PDFConverter:
    """Class for converting HTML content to PDF using wkhtmltopdf."""

    def __init__(self):
        """Initialize the PDF converter with default options."""
        self.default_options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'javascript-delay': 2000,
            'no-stop-slow-scripts': None,
            'enable-javascript': None,
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
            'quiet': None,
            'print-media-type': None,
            'orientation': 'Portrait',
            'title': 'Documentation',
            'enable-external-links': None,
            'enable-internal-links': None,
            'outline': None,
            'outline-depth': 3,
            'grayscale': None,
            'log-level': 'info',
            'disable-smart-shrinking': None,
            'image-quality': 100,
            'zoom': 1.0,
            'print-media-type': None,
            'javascript-delay': 1000
        }


def convert_to_pdf(html_content: str, output_path: str, use_advanced_options: bool = True) -> None:
    """Convert HTML content to PDF.

    Args:
        html_content: HTML content to convert
        output_path: Path where to save the PDF file
        use_advanced_options: Whether to use advanced PDF options (default: True)
    """
    import pdfkit  # Import here to avoid loading if not needed

    # Ensure output directory exists
    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)

    converter = PDFConverter()
    options = converter.default_options

    try:
        # Create temporary file for processing
        temp_dir = Path(output_dir) / ".temp"
        temp_dir.mkdir(exist_ok=True)
        temp_html = temp_dir / "temp.html"
        temp_html.write_text(html_content, encoding="utf-8")

        try:
            # Use explicit wkhtmltopdf path and configuration
            config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
            pdfkit.from_file(
                str(temp_html),
                output_path,
                options=options,
                configuration=config,
                verbose=True
            )
        finally:
            temp_html.unlink(missing_ok=True)
            temp_dir.rmdir()

    except Exception as e:
        raise RuntimeError(f"PDF conversion failed: {str(e)}")


def _fix_relative_paths(html_content: str, base_dir: str) -> str:
    """Fix relative paths in HTML content."""
    # Convert base_dir to file:// URL format
    base_url = f"file://{os.path.abspath(base_dir)}"

    # Add SVG MIME type support
    def fix_path(match):
        attr, path = match.groups()
        if path.startswith(('http://', 'https://', 'file://', 'data:', '#')):
            return f'{attr}="{path}"'

        # Add proper MIME type for SVGs
        if path.endswith('.svg'):
            abs_path = os.path.abspath(os.path.join(base_dir, path))
            return f'{attr}="file://{abs_path}#svgView(preserveAspectRatio(none))"'

        return f'{attr}="file://{os.path.abspath(os.path.join(base_dir, path))}"'

    # Fix paths in src and href attributes
    html_content = re.sub(r'(src|href)="([^"]+)"', fix_path, html_content)

    # Add SVG-specific meta tag
    if '<head>' in html_content and '<meta http-equiv="Content-Type"' not in html_content:
        svg_meta = '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
        html_content = html_content.replace('<head>', f'<head>{svg_meta}')

    # Add base tag to head if not present
    if '<base' not in html_content and '<head>' in html_content:
        base_tag = f'<base href="{base_url}/">'
        html_content = html_content.replace('<head>', f'<head>{base_tag}')

    return html_content