"""字幕生成のテスト"""

import pytest
from pathlib import Path
from src.twitter_video_translator.utils.subtitle import SubtitleGenerator


class TestSubtitleGenerator:
    """SubtitleGeneratorのテスト"""

    def test_seconds_to_srt_time(self):
        """秒数からSRT時間形式への変換"""
        assert SubtitleGenerator.seconds_to_srt_time(0) == "00:00:00,000"
        assert SubtitleGenerator.seconds_to_srt_time(1.5) == "00:00:01,500"
        assert SubtitleGenerator.seconds_to_srt_time(61.25) == "00:01:01,250"
        assert SubtitleGenerator.seconds_to_srt_time(3661.0) == "01:01:01,000"

    def test_generate_srt(self, tmp_path):
        """SRTファイル生成"""
        segments = [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Hello world",
                "translated_text": "こんにちは世界",
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "This is a test",
                "translated_text": "これはテストです",
            },
        ]

        output_path = tmp_path / "test.srt"
        SubtitleGenerator.generate_srt(segments, output_path, use_translation=True)

        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8")
        assert "こんにちは世界" in content
        assert "これはテストです" in content
        assert "00:00:00,000 --> 00:00:02,500" in content
