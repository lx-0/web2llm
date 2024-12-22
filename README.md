# 🌐 web2llm - Website scraper for LLM consumption

> A Python tool that prepares online documentation for LLM consumption by downloading websites and converting them into standardized formats. Ideal for making post-cutoff documentation accessible to language models.
>
> For example, it can transform the latest Pydantic AI documentation into clean, structured PDFs, allowing LLMs to understand features released after their training cutoff.

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## 🎯 Purpose

Prepare online documentation for LLM consumption through:

- 📥 Downloading complete websites with full JavaScript support
- 🔄 Converting content into standardized formats
- 📚 Generating LLM-friendly PDFs with proper structure
- 🤖 Making post-cutoff knowledge accessible

## ✨ Features

- 🌐 Website Processing
  - Full JavaScript support
  - Proper handling of relative paths
  - Automatic resource collection
- 📑 Document Generation
  - Clean PDF output with proper formatting
  - Automatic page breaks
  - Table of contents generation
  - Custom CSS and print styles support
- 🛠️ Configuration Options
  - Configurable margins and layout
  - Environment variable support
  - Progress tracking with color output
  - Debug and quiet modes

## 🔧 Prerequisites

- Python 3.8 or higher
- Conda (Miniconda or Anaconda)
- HTTrack
  - 🍎 MacOS: `brew install httrack`
  - 🐧 Linux: `apt-get install httrack`
  - 🪟 Windows: Download from HTTrack website
- wkhtmltopdf (installed automatically via conda)

## 🚀 Quick Start

### 📦 Installation

1. Install HTTrack for your OS (see Prerequisites)
2. Clone and setup the environment:

```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate web2llm

# Install package
pip install -e .
```

### 📖 Usage

Basic conversion:

```bash
python -m web2llm https://example.com --output docs.pdf
```

### 🎮 Command Options

- `url`: Target website URL (required)
- `--output`, `-o`: Output PDF path (required)
- `--debug`: Keep temporary files and debug info
- `--quiet`, `-q`: Suppress progress output
- `--skip-download`: Use existing files
- `--download-only`: Skip conversion

### 📝 Examples

1. Convert Pydantic AI docs:

```bash
python -m web2llm https://ai.pydantic.dev/ --output pydantic_ai.pdf
```

2. Debug mode:

```bash
python -m web2llm https://example.com --output docs.pdf --debug
```

3. Quiet mode for scripts:

```bash
python -m web2llm https://example.com --output docs.pdf --quiet
```

## ⚙️ Configuration

Set via environment variables or `.env`:

- `DOWNLOAD_DIR`: Temporary files location
- `OUTPUT_DIR`: PDF output location

## 🤝 Testing

Run tests with pytest:

```bash
# Run all tests (via python)
python -m pytest tests/ -v

# Run all tests (directly)
pytest tests/ -v

# Run tests with coverage report
pytest tests/ --cov=web2llm --cov-report=term-missing

# Run specific test file
pytest tests/test_preprocessor.py -v

# Run specific test function
pytest tests/test_preprocessor.py::test_normalize_url -v
```

Tests cover:

- CLI functionality
- Website downloading
- HTML preprocessing
- SVG handling
- Tabbed content processing
- Document merging
- PDF conversion

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
