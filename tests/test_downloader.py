"""ダウンローダーのテスト"""

import pytest
from pathlib import Path
from src.twitter_video_translator.services.downloader import TwitterDownloader


class TestTwitterDownloader:
    """TwitterDownloaderのテスト"""

    def test_validate_url_valid(self, tmp_path):
        """有効なURLの検証"""
        downloader = TwitterDownloader(tmp_path)

        valid_urls = [
            "https://twitter.com/user/status/123456789",
            "https://x.com/user/status/123456789",
            "http://twitter.com/user/status/123456789",
        ]

        for url in valid_urls:
            assert downloader.validate_url(url) is True

    def test_validate_url_invalid(self, tmp_path):
        """無効なURLの検証"""
        downloader = TwitterDownloader(tmp_path)

        invalid_urls = [
            "https://youtube.com/watch?v=123",
            "https://twitter.com/user",
            "not_a_url",
            "",
        ]

        for url in invalid_urls:
            assert downloader.validate_url(url) is False
