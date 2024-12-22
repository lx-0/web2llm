"""A Python tool that prepares online documentation for LLM consumption.

This package provides functionality to download websites and convert them into
standardized formats suitable for language models, making post-cutoff documentation
accessible to LLMs through clean, structured PDFs.
"""

__version__ = "0.1.0"

from .converter import PDFConverter
from .downloader import WebsiteDownloader
from .preprocessor import HTMLPreprocessor

__all__ = ["WebsiteDownloader", "HTMLPreprocessor", "PDFConverter"]