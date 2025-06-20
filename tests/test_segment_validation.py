"""セグメント数検証機能のテスト"""

import pytest
from pathlib import Path
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from src.twitter_video_translator.services.tts import TextToSpeech
from src.twitter_video_translator.models.transcription import SubtitleSegment


class TestSegmentValidation:
    """セグメント数検証とリトライ機能のテスト"""
    
    @pytest.fixture
    def tts(self):
        return TextToSpeech()
    
    @pytest.fixture
    def sample_segments(self):
        """テスト用セグメント"""
        return [
            SubtitleSegment(
                start_time=0.0,
                end_time=2.0,
                text="First segment",
                confidence=0.95
            ),
            SubtitleSegment(
                start_time=2.0,
                end_time=4.0,
                text="Second segment",
                confidence=0.93
            ),
            SubtitleSegment(
                start_time=4.0,
                end_time=6.0,
                text="Third segment",
                confidence=0.91
            )
        ]
    
    @pytest.fixture
    def translated_texts(self):
        """翻訳されたテキスト"""
        return ["最初のセグメント", "2番目のセグメント", "3番目のセグメント"]
    
    @pytest.mark.asyncio
    async def test_segment_count_validation_success(self, tts, sample_segments, translated_texts):
        """正常なセグメント数検証のテスト"""
        # 音声生成のモック（全セグメント成功）
        mock_audio_path = Path("/tmp/test_segment.wav")
        
        async def mock_generate_success(text, output_path, style_params=None):
            # ダミーファイルを作成
            output_path.write_bytes(b"dummy audio data")
            return output_path
        
        with patch.object(tts, 'generate_speech_segment', side_effect=mock_generate_success):
            with patch.object(tts.style_analyzer, 'analyze_audio_style', 
                            return_value=tts.style_analyzer._get_default_style()):
                
                # 音声ファイルのモックパスを作成
                test_audio = Path("/tmp/test_audio.wav")
                test_audio.write_bytes(b"dummy audio")
                
                try:
                    result = await tts.generate_speech_for_segments(
                        sample_segments, 
                        translated_texts,
                        test_audio,
                        analyze_style=False  # スタイル分析は無効化
                    )
                    
                    # 検証
                    assert len(result.segments) == 3
                    assert "audio_files" in result.metadata
                    assert len(result.metadata["audio_files"]) == 3
                    
                finally:
                    # クリーンアップ
                    if test_audio.exists():
                        test_audio.unlink()
                    # 生成されたファイルを削除
                    for i in range(3):
                        segment_path = Path(f"/tmp/segment_{i:04d}.wav")
                        if segment_path.exists():
                            segment_path.unlink()
    
    @pytest.mark.asyncio
    async def test_missing_segment_retry(self, tts, sample_segments, translated_texts):
        """不足セグメントの再生成テスト"""
        # 最初の実行で2番目のセグメントだけ失敗
        call_count = 0
        generated_files = []
        
        async def mock_generate_with_failure(text, output_path, style_params=None):
            nonlocal call_count
            call_count += 1
            
            # segment_0001.wavの最初の生成は失敗
            if "0001" in str(output_path) and call_count <= 3:
                raise Exception("一時的なエラー")
            
            # それ以外は成功
            output_path.write_bytes(b"dummy audio data")
            generated_files.append(output_path)
            return output_path
        
        with patch.object(tts, 'generate_speech_segment', side_effect=mock_generate_with_failure):
            with patch('src.twitter_video_translator.config.config.temp_dir', Path("/tmp")):
                
                result = await tts.generate_speech_for_segments(
                    sample_segments,
                    translated_texts,
                    None,  # 音声ファイルなし
                    analyze_style=False
                )
                
                # 最終的に全セグメントが生成されることを確認
                assert len(result.segments) == 3
                assert call_count > 3  # リトライが発生
                
                # クリーンアップ
                for file_path in generated_files:
                    if file_path.exists():
                        file_path.unlink()
    
    @pytest.mark.asyncio
    async def test_persistent_failure_warning(self, tts, sample_segments, translated_texts, capsys):
        """リトライ後も失敗するケースのテスト"""
        
        async def mock_generate_partial(text, output_path, style_params=None):
            # segment_0002.wavは常に失敗
            if "0002" in str(output_path):
                raise Exception("永続的なエラー")
            
            output_path.write_bytes(b"dummy audio data")
            return output_path
        
        with patch.object(tts, 'generate_speech_segment', side_effect=mock_generate_partial):
            with patch('src.twitter_video_translator.config.config.temp_dir', Path("/tmp")):
                
                result = await tts.generate_speech_for_segments(
                    sample_segments,
                    translated_texts,
                    None,
                    analyze_style=False
                )
                
                # 部分的な結果が返されることを確認
                assert len(result.segments) == 2  # 3つ中2つのみ成功
                
                # クリーンアップ
                for i in [0, 1]:  # 0と1は成功
                    segment_path = Path(f"/tmp/segment_{i:04d}.wav")
                    if segment_path.exists():
                        segment_path.unlink()
    
    def test_index_extraction_from_path(self):
        """ファイルパスからインデックス抽出のテスト"""
        test_cases = [
            ("segment_0000.wav", 0),
            ("segment_0001.wav", 1),
            ("segment_0010.wav", 10),
            ("segment_0123.wav", 123),
        ]
        
        for filename, expected_idx in test_cases:
            path = Path(f"/tmp/{filename}")
            idx_str = path.stem.split("_")[-1]
            assert int(idx_str) == expected_idx


if __name__ == "__main__":
    pytest.main([__file__, "-v"])