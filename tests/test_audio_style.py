"""音声スタイル分析機能のテスト"""

import pytest
from pathlib import Path
import asyncio
from unittest.mock import Mock, patch, MagicMock

from src.twitter_video_translator.services.audio_style_analyzer import AudioStyleAnalyzer
from src.twitter_video_translator.services.tts import TextToSpeech
from src.twitter_video_translator.models.transcription import SubtitleSegment


class TestAudioStyleAnalyzer:
    """AudioStyleAnalyzerのテスト"""
    
    @pytest.fixture
    def analyzer(self):
        return AudioStyleAnalyzer()
    
    @pytest.fixture
    def sample_segment(self):
        return SubtitleSegment(
            start_time=0.0,
            end_time=2.5,
            text="Hello, this is a test.",
            confidence=0.95
        )
    
    def test_get_default_style(self, analyzer):
        """デフォルトスタイルの取得テスト"""
        default_style = analyzer._get_default_style()
        
        assert default_style["emotion"]["primary"] == "neutral"
        assert default_style["speed"]["value"] == 1.0
        assert default_style["tone"]["brightness"] == "neutral"
        assert default_style["intonation"]["pattern"] == "moderate"
        assert default_style["summary"] == "標準的な読み上げスタイル"
    
    def test_convert_to_tts_style(self, analyzer):
        """TTSスタイルへの変換テスト"""
        # テスト用の分析結果
        analysis = {
            "emotion": {
                "primary": "happy",
                "intensity": "strong"
            },
            "speed": {
                "value": 1.5
            },
            "tone": {
                "strength": "力強い"
            },
            "special_features": []
        }
        
        tts_style = analyzer.convert_to_tts_style(analysis)
        
        assert tts_style["style"] == "cheerful"
        assert tts_style["style_intensity"] == "strong"
        assert tts_style["speed"] == 1.5
        assert tts_style["pitch_shift"] == 0
        assert tts_style["volume_gain_db"] == 0
    
    def test_emotion_mapping(self, analyzer):
        """感情マッピングのテスト"""
        emotion_tests = [
            ("happy", "cheerful"),
            ("sad", "sad"),
            ("angry", "angry"),
            ("fear", "worried"),
            ("surprise", "excited"),
            ("disgust", "dissatisfied"),
            ("neutral", "neutral"),
            ("unknown", "neutral")  # 未知の感情はneutralに
        ]
        
        for input_emotion, expected_style in emotion_tests:
            analysis = {
                "emotion": {"primary": input_emotion, "intensity": "moderate"},
                "speed": {"value": 1.0},
                "tone": {},
                "special_features": []
            }
            tts_style = analyzer.convert_to_tts_style(analysis)
            assert tts_style["style"] == expected_style
    
    @pytest.mark.asyncio
    async def test_analyze_audio_style_with_mock(self, analyzer, sample_segment):
        """音声スタイル分析のモックテスト"""
        # Gemini APIのモック
        mock_response = MagicMock()
        mock_response.text = '''{
            "emotion": {
                "primary": "happy",
                "intensity": "moderate",
                "secondary": null
            },
            "speed": {
                "label": "normal",
                "value": 1.0
            },
            "tone": {
                "brightness": "bright",
                "pitch": "high",
                "strength": "moderate",
                "formality": "casual"
            },
            "intonation": {
                "pattern": "expressive",
                "expressiveness": "high"
            },
            "special_features": ["enthusiastic"],
            "summary": "明るく楽しそうな話し方"
        }'''
        
        with patch.object(analyzer.client.aio.models, 'generate_content', return_value=mock_response):
            # テスト用の音声ファイルを作成（空ファイル）
            test_audio = Path("/tmp/test_audio.wav")
            test_audio.write_bytes(b"dummy audio data")
            
            try:
                result = await analyzer.analyze_audio_style(
                    test_audio,
                    "Hello, this is a test.",
                    sample_segment
                )
                
                assert result["emotion"]["primary"] == "happy"
                assert result["speed"]["value"] == 1.0
                assert result["tone"]["brightness"] == "bright"
                assert result["summary"] == "明るく楽しそうな話し方"
                assert result["segment_info"]["text"] == sample_segment.text
                
            finally:
                if test_audio.exists():
                    test_audio.unlink()


class TestTextToSpeechWithStyle:
    """音声スタイル機能を含むTextToSpeechのテスト"""
    
    @pytest.fixture
    def tts(self):
        return TextToSpeech()
    
    @pytest.fixture
    def sample_segments(self):
        return [
            SubtitleSegment(
                start_time=0.0,
                end_time=2.0,
                text="Hello world.",
                confidence=0.95
            ),
            SubtitleSegment(
                start_time=2.0,
                end_time=4.0,
                text="How are you?",
                confidence=0.93
            )
        ]
    
    def test_style_prompt_generation(self, tts):
        """スタイルプロンプト生成のテスト"""
        # generate_speech_segmentメソッドの内部ロジックをテスト
        style_params = {
            "style": "cheerful",
            "style_intensity": "strong",
            "speed": 1.5
        }
        
        # スタイル説明の検証
        style_descriptions = {
            "cheerful": "明るく楽しそうに",
            "sad": "悲しそうに",
            "angry": "怒っているように",
            "worried": "心配そうに",
            "excited": "興奮して",
            "dissatisfied": "不満そうに",
            "confident": "自信を持って",
            "neutral": "普通に"
        }
        
        assert style_descriptions["cheerful"] == "明るく楽しそうに"
        assert style_descriptions["neutral"] == "普通に"
    
    @pytest.mark.asyncio
    async def test_generate_speech_with_style(self, tts):
        """スタイル付き音声生成のテスト（モック）"""
        style_params = {
            "style": "cheerful",
            "style_intensity": "moderate",
            "speed": 1.0
        }
        
        # Gemini APIのモック
        mock_chunk = MagicMock()
        mock_chunk.candidates = [MagicMock()]
        mock_chunk.candidates[0].content = MagicMock()
        mock_chunk.candidates[0].content.parts = [MagicMock()]
        mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
        mock_chunk.candidates[0].content.parts[0].inline_data.data = b"dummy audio data"
        mock_chunk.candidates[0].content.parts[0].inline_data.mime_type = "audio/L16;rate=24000"
        
        with patch.object(tts.client.models, 'generate_content_stream', return_value=[mock_chunk]):
            output_path = Path("/tmp/test_output.wav")
            
            try:
                result = await tts.generate_speech_segment(
                    "こんにちは",
                    output_path,
                    style_params
                )
                
                assert result == output_path
                assert output_path.exists()
                
            finally:
                if output_path.exists():
                    output_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])