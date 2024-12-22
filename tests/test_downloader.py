"""Tests for the website downloader module."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from web2llm.downloader import WebsiteDownloader


def test_downloader_initialization():
    """Test downloader initialization."""
    downloader = WebsiteDownloader(quiet=True)
    assert downloader.quiet is True


@pytest.mark.integration
def test_download_website(tmp_path: Path):
    """Test downloading a website."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"
    web_dir = output_dir / "web"
    web_dir.mkdir(parents=True)

    downloader = WebsiteDownloader(quiet=True)

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["", None]
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        result = downloader.download(url, output_dir)

        assert result == web_dir
        mock_run.assert_called_once()


def test_download_failure(tmp_path: Path):
    """Test handling of download failures."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"

    downloader = WebsiteDownloader(quiet=True)

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["", None]
        mock_process.poll.return_value = 1
        mock_run.return_value = mock_process
        with pytest.raises(RuntimeError):
            downloader.download(url, output_dir)


def test_find_html_files(tmp_path: Path):
    """Test finding HTML files in website directory."""
    website_dir = tmp_path / "web"
    website_dir.mkdir(parents=True)

    # Create some test HTML files
    (website_dir / "index.html").touch()
    (website_dir / "page1.html").touch()

    downloader = WebsiteDownloader()
    html_files = downloader.find_html_files(website_dir)

    assert len(html_files) == 2
    assert any("index.html" in str(f) for f in html_files)


def test_downloader_initialization_with_options():
    """Test downloader initialization with custom options."""
    downloader = WebsiteDownloader(quiet=True)
    assert downloader.quiet is True


def test_download_with_custom_depth(tmp_path: Path):
    """Test downloading with custom depth setting."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"
    web_dir = output_dir / "web"
    web_dir.mkdir(parents=True)

    downloader = WebsiteDownloader(quiet=True)

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["", None]
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        result = downloader.download(url, output_dir)

        assert result == web_dir
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert '-r2' in cmd  # Default depth


def test_download_with_custom_extensions(tmp_path: Path):
    """Test downloading with custom file extensions."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"
    web_dir = output_dir / "web"
    web_dir.mkdir(parents=True)

    downloader = WebsiteDownloader(quiet=True)

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["", None]
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        result = downloader.download(url, output_dir)

        assert result == web_dir
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert '-r2' in cmd  # Default depth


def test_download_with_custom_user_agent(tmp_path: Path):
    """Test downloading with custom user agent."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"
    web_dir = output_dir / "web"
    web_dir.mkdir(parents=True)

    downloader = WebsiteDownloader(quiet=True)

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["", None]
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        result = downloader.download(url, output_dir)

        assert result == web_dir
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert 'Mozilla/5.0' in cmd  # Default user agent


def test_download_with_invalid_url():
    """Test downloading with invalid URL."""
    url = "not_a_url"
    output_dir = Path("output")

    downloader = WebsiteDownloader()

    with pytest.raises(RuntimeError, match="Could not find downloaded website directory"):
        downloader.download(url, output_dir)


def test_download_with_connection_error(tmp_path: Path):
    """Test handling of connection errors during download."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"

    downloader = WebsiteDownloader()

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["Connection refused", None]
        mock_process.poll.return_value = 1
        mock_process.returncode = 1
        mock_run.return_value = mock_process
        with pytest.raises(RuntimeError, match="HTTrack failed with return code"):
            downloader.download(url, output_dir)


def test_download_with_permission_error(tmp_path: Path):
    """Test handling of permission errors."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"

    downloader = WebsiteDownloader()

    with patch('subprocess.Popen') as mock_run:
        mock_run.side_effect = PermissionError("Permission denied")
        with pytest.raises(PermissionError):
            downloader.download(url, output_dir)


def test_find_html_files_with_empty_dir(tmp_path: Path):
    """Test finding HTML files in an empty directory."""
    website_dir = tmp_path / "web"
    website_dir.mkdir(parents=True)

    downloader = WebsiteDownloader()
    html_files = downloader.find_html_files(website_dir)

    assert len(html_files) == 0


def test_find_html_files_with_subdirectories(tmp_path: Path):
    """Test finding HTML files in subdirectories."""
    website_dir = tmp_path / "web"
    website_dir.mkdir(parents=True)
    subdir = website_dir / "subdir"
    subdir.mkdir()

    # Create test files
    (website_dir / "index.html").touch()
    (subdir / "page.html").touch()
    (website_dir / "not_html.txt").touch()

    downloader = WebsiteDownloader()
    html_files = downloader.find_html_files(website_dir)

    assert len(html_files) == 2
    assert any("index.html" in str(f) for f in html_files)
    assert any("page.html" in str(f) for f in html_files)


def test_download_with_process_error(tmp_path: Path):
    """Test handling of process errors during download."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"

    downloader = WebsiteDownloader()

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["Error: Process failed", None]
        mock_process.poll.return_value = 1
        mock_process.returncode = 1
        mock_run.return_value = mock_process
        with pytest.raises(RuntimeError, match="HTTrack failed with return code"):
            downloader.download(url, output_dir)


def test_download_with_output_error(tmp_path: Path):
    """Test handling of output directory errors."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"
    output_dir.touch()  # Create a file instead of a directory

    downloader = WebsiteDownloader()

    with pytest.raises(FileExistsError):
        downloader.download(url, output_dir)


def test_download_with_empty_url():
    """Test downloading with empty URL."""
    url = ""
    output_dir = Path("output")

    downloader = WebsiteDownloader()

    with pytest.raises(RuntimeError, match="Could not find downloaded website directory"):
        downloader.download(url, output_dir)


def test_download_with_process_timeout(tmp_path: Path):
    """Test handling of process timeout."""
    url = "https://example.com"
    output_dir = tmp_path / "downloaded"

    downloader = WebsiteDownloader()

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = TimeoutError("Process timed out")
        mock_process.poll.return_value = None
        mock_run.return_value = mock_process
        with pytest.raises(TimeoutError, match="Process timed out"):
            downloader.download(url, output_dir)


def test_download_with_unicode_url(tmp_path: Path):
    """Test downloading with URL containing Unicode characters."""
    url = "https://example.com/über/straße"
    output_dir = tmp_path / "downloaded"
    web_dir = output_dir / "web"
    web_dir.mkdir(parents=True)

    downloader = WebsiteDownloader(quiet=True)

    with patch('subprocess.Popen') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["", None]
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        result = downloader.download(url, output_dir)

        assert result == web_dir
        mock_run.assert_called_once()


def test_downloader_quiet_mode_print_progress(capsys):
    """Test print progress in quiet mode."""
    downloader = WebsiteDownloader(quiet=True)

    # Test different types of messages in quiet mode
    test_messages = [
        "Warning: test warning",
        "Error: test error",
        "Info: test info",
        "File: test.html saved",
        "Loading: test.html",
        "Failed: test failed",
        "Normal message"
    ]

    for message in test_messages:
        downloader._print_progress(message)

    # Check that nothing was printed
    captured = capsys.readouterr()
    assert captured.out == ""  # No output in quiet mode