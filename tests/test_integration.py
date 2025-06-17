"""統合テスト"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.twitter_video_translator.cli import TwitterVideoTranslatorCLI
from src.twitter_video_translator.config import Config


class TestIntegration:
    """統合テスト"""

    @patch("src.twitter_video_translator.services.downloader.yt_dlp.YoutubeDL")
    @patch("src.twitter_video_translator.services.transcriber.Groq")
    @patch("src.twitter_video_translator.services.translator.genai.GenerativeModel")
    @patch("src.twitter_video_translator.services.tts.genai.Client")
    @patch("src.twitter_video_translator.services.video_composer.subprocess.run")
    @patch("src.twitter_video_translator.services.video_composer.ffmpeg")
    @patch("src.twitter_video_translator.services.transcriber.ffmpeg")
    def test_full_pipeline(
        self,
        mock_transcriber_ffmpeg,
        mock_composer_ffmpeg,
        mock_subprocess,
        mock_genai_client,
        mock_genai,
        mock_groq,
        mock_yt_dlp,
        tmp_path,
    ):
        """全パイプラインのテスト"""

        # テスト用の設定
        test_config = Config(
            groq_api_key="test_key",
            gemini_api_key="test_key",
            output_dir=tmp_path / "output",
            temp_dir=tmp_path / "temp",
        )

        # モックの設定
        # yt-dlp
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = {
            "formats": [{"ext": "mp4"}],
            "ext": "mp4",
            "_filename": str(tmp_path / "temp" / "original_video.mp4")
        }
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance

        # 動画ファイルを作成
        video_file = tmp_path / "temp" / "original_video.mp4"
        video_file.parent.mkdir(exist_ok=True)
        video_file.write_text("dummy video")

        # Groq
        mock_groq_instance = MagicMock()
        mock_transcription = MagicMock()
        mock_transcription.text = "Hello world"
        mock_transcription.language = "en"
        mock_transcription.segments = [
            {"start": 0.0, "end": 2.0, "text": "Hello world"}
        ]
        mock_groq_instance.audio.transcriptions.create.return_value = mock_transcription
        mock_groq.return_value = mock_groq_instance

        # Gemini
        mock_genai_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "[0] こんにちは世界"
        mock_genai_instance.generate_content.return_value = mock_response
        mock_genai.return_value = mock_genai_instance

        # Gemini Client
        mock_genai_client_instance = MagicMock()
        mock_genai_client.return_value = mock_genai_client_instance

        # ffmpeg
        mock_transcriber_ffmpeg.input.return_value = MagicMock()
        mock_transcriber_ffmpeg.output.return_value = MagicMock()
        mock_transcriber_ffmpeg.run = MagicMock()

        mock_composer_ffmpeg.input.return_value = MagicMock()
        mock_composer_ffmpeg.output.return_value = MagicMock()
        mock_composer_ffmpeg.run = MagicMock()

        # subprocess
        mock_subprocess.return_value = None

        # 音声ファイルを作成
        audio_file = tmp_path / "temp" / "audio.wav"
        audio_file.write_text("dummy audio")

        # CLIを実行
        with (
            patch("src.twitter_video_translator.cli.config", test_config),
            patch(
                "src.twitter_video_translator.services.transcriber.config", test_config
            ),
            patch(
                "src.twitter_video_translator.services.translator.config", test_config
            ),
            patch("src.twitter_video_translator.services.tts.config", test_config),
            patch(
                "src.twitter_video_translator.services.video_composer.config",
                test_config,
            ),
        ):

            cli = TwitterVideoTranslatorCLI()

            # 字幕のみモードでテスト（TTSをスキップ）
            result = cli.run(
                "https://twitter.com/user/status/123456789",
                output_path=None,
                use_tts=False,
            )

            # 結果の確認
            assert result is not None
            assert mock_ydl_instance.extract_info.called
            assert mock_groq_instance.audio.transcriptions.create.called
            assert mock_genai_instance.generate_content.called
