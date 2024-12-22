"""Tests for CLI functionality."""
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from web2llm.__main__ import main, parse_args


@pytest.fixture
def mock_website_dir(tmp_path: Path) -> Path:
    """Create a mock website directory with test files."""
    website_dir = tmp_path / "website"
    website_dir.mkdir()
    (website_dir / "index.html").write_text("<html><body>Test</body></html>")
    return website_dir


def test_cli_basic_conversion(mock_website_dir: Path, tmp_path: Path):
    """Test basic website to PDF conversion via CLI."""
    output_file = tmp_path / "output.pdf"

    with patch('sys.argv', ['web2llm', 'https://example.com', '--output', str(output_file)]):
        args = parse_args()
        main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)
        assert output_file.exists()


def test_cli_with_debug_output(mock_website_dir: Path, tmp_path: Path):
    """Test CLI with debug output enabled."""
    output_file = tmp_path / "output.pdf"

    with patch('sys.argv', [
        'web2llm',
        'https://example.com',
        '--output', str(output_file),
        '--debug'
    ]):
        args = parse_args()
        main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)
        debug_dir = Path.cwd() / "output" / "debug"
        assert debug_dir.exists()
        assert (debug_dir / "master.html").exists()


def test_cli_with_custom_options(mock_website_dir: Path, tmp_path: Path):
    """Test CLI with custom PDF options."""
    output_file = tmp_path / "output.pdf"

    with patch('sys.argv', [
        'web2llm',
        'https://example.com',
        '--output', str(output_file),
        '--debug'
    ]):
        args = parse_args()
        main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)
        assert output_file.exists()


def test_cli_with_invalid_input():
    """Test CLI with invalid URL."""
    with patch('sys.argv', ['web2llm', 'not_a_url', '--output', 'output.pdf']):
        args = parse_args()
        with pytest.raises(SystemExit):
            main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)


def test_cli_with_invalid_output():
    """Test CLI with invalid output path."""
    with patch('sys.argv', ['web2llm', 'https://example.com', '--output', '/invalid/path/output.pdf']):
        args = parse_args()
        with pytest.raises(SystemExit):
            main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)


def test_cli_help():
    """Test CLI help output."""
    with patch('sys.argv', ['web2llm', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            parse_args()
        assert exc_info.value.code == 0


def test_cli_quiet_mode(mock_website_dir: Path, tmp_path: Path):
    """Test CLI in quiet mode."""
    output_file = tmp_path / "output.pdf"

    with patch('sys.argv', [
        'web2llm',
        'https://example.com',
        '--output', str(output_file),
        '--quiet'
    ]):
        args = parse_args()
        main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)
        assert output_file.exists()


def test_cli_with_httrack_options(mock_website_dir: Path, tmp_path: Path):
    """Test CLI with custom HTTrack options."""
    output_file = tmp_path / "output.pdf"

    with patch('sys.argv', [
        'web2llm',
        'https://example.com',
        '--output', str(output_file),
        '--debug'
    ]):
        args = parse_args()
        main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)
        assert output_file.exists()


def test_cli_skip_download(mock_website_dir: Path, tmp_path: Path):
    """Test CLI with skip download option."""
    output_file = tmp_path / "output.pdf"
    downloads_dir = Path.cwd() / "downloads" / "example.com"

    # Remove the downloads directory if it exists
    if downloads_dir.exists():
        import shutil
        shutil.rmtree(downloads_dir)

    with patch('sys.argv', [
        'web2llm',
        'https://example.com',
        '--output', str(output_file),
        '--skip-download'
    ]):
        args = parse_args()
        with pytest.raises(SystemExit):
            main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)


def test_cli_download_only(mock_website_dir: Path, tmp_path: Path):
    """Test CLI with download only option."""
    output_file = tmp_path / "output.pdf"

    with patch('sys.argv', [
        'web2llm',
        'https://example.com',
        '--output', str(output_file),
        '--download-only'
    ]):
        args = parse_args()
        main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)
        assert not output_file.exists()  # PDF should not be created in download-only mode


def test_cli_skip_download_with_missing_web_dir(tmp_path: Path):
    """Test skip_download option when web directory doesn't exist."""
    with patch('sys.argv', [
        'web2llm',
        'https://example.com',
        '--output', 'output.pdf',
        '--skip-download'
    ]), patch('pathlib.Path.cwd', return_value=tmp_path):
        args = parse_args()
        with pytest.raises(SystemExit):
            main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)


def test_cli_main_execution():
    """Test the __main__ block execution."""
    with patch('sys.argv', [
        'web2llm',
        'https://example.com',
        '--output', 'output.pdf'
    ]):
        args = parse_args()
        assert args.url == 'https://example.com'
        assert args.output == 'output.pdf'
        assert not args.debug
        assert not args.quiet
        assert not args.skip_download
        assert not args.download_only


def test_cli_main_module_execution(monkeypatch, capsys):
    """Test execution of the main module when run directly."""
    # Mock sys.argv
    test_args = ['web2llm', 'https://example.com', '--output', 'test.pdf']
    monkeypatch.setattr('sys.argv', test_args)

    # Import and run the main module
    import web2llm.__main__

    # The module should have been executed through the __name__ == '__main__' block
    captured = capsys.readouterr()
    assert captured.err == ''  # No errors should be printed


def test_cli_skip_download_with_nonexistent_web_dir(tmp_path, monkeypatch):
    """Test skip_download with nonexistent web directory."""
    # Set up test environment
    monkeypatch.chdir(tmp_path)

    # Create downloads directory but not the web directory
    downloads_dir = tmp_path / "downloads" / "example_com"
    downloads_dir.mkdir(parents=True)

    # Run main with skip_download
    with pytest.raises(SystemExit) as exc_info:
        main(
            url="https://example.com",
            output="test.pdf",
            skip_download=True
        )
    assert exc_info.value.code == 1  # Check that the exit code is 1


def test_cli_download_only_with_quiet_mode(tmp_path: Path, capfd):
    """Test CLI with download_only and quiet mode."""
    url = "https://example.com"
    output = tmp_path / "output.pdf"

    # Set up the directory structure
    base_dir = Path.cwd()
    downloads_dir = base_dir / "downloads" / "example.com"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    # Mock the WebsiteDownloader to avoid actual downloads
    with patch('web2llm.__main__.WebsiteDownloader') as mock_downloader:
        mock_instance = mock_downloader.return_value
        mock_instance.download.return_value = downloads_dir / "web"

        # Create the web directory
        web_dir = downloads_dir / "web"
        web_dir.mkdir(parents=True, exist_ok=True)

        # Run the CLI with download_only and quiet mode
        with patch('sys.argv', ['web2llm', url, '--output', str(output), '--download-only', '--quiet']):
            args = parse_args()
            main(args.url, args.output, args.debug, args.quiet, args.skip_download, args.download_only)

        # Check that the downloader was called correctly
        mock_downloader.assert_called_once_with(quiet=True)
        mock_instance.download.assert_called_once_with(url, downloads_dir)

        # Check that no output was printed
        captured = capfd.readouterr()
        assert captured.out == ""
        assert captured.err == ""

        # Clean up
        shutil.rmtree(downloads_dir.parent)