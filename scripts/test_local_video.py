#!/usr/bin/env python3
"""ローカル動画でテスト（Twitter APIを使用せず）"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.twitter_video_translator.cli import VideoTranslatorCLI
from src.twitter_video_translator.services.transcriber import AudioTranscriber
from src.twitter_video_translator.services.translator import TextTranslator
from src.twitter_video_translator.services.tts import TextToSpeech
from src.twitter_video_translator.services.video_composer import VideoComposer
from src.twitter_video_translator.utils.subtitle import SubtitleGenerator
from src.twitter_video_translator.config import config

def test_local_video(video_path: Path):
    """ローカル動画で処理をテスト"""
    try:
        config.validate_all()
        
        transcriber = AudioTranscriber()
        translator = TextTranslator()
        tts = TextToSpeech()
        composer = VideoComposer()
        subtitle_gen = SubtitleGenerator()
        
        print(f"処理開始: {video_path}")
        
        # 1. 音声抽出
        audio_path = transcriber.extract_audio(video_path)
        
        # 2. 文字起こし（テストデータを使用）
        print("文字起こし（テストデータ）...")
        transcription = {
            "text": "Hello, this is a test video.",
            "language": "English",
            "segments": [
                {
                    "start": 0.0,
                    "end": 3.0,
                    "text": "Hello, this is a test video."
                },
                {
                    "start": 3.0,
                    "end": 6.0,
                    "text": "This video is created for testing purposes."
                },
                {
                    "start": 6.0,
                    "end": 10.0,
                    "text": "Thank you for watching."
                }
            ]
        }
        
        # 3. 翻訳
        translated_segments = translator.translate_segments(
            transcription['segments'], 
            transcription['language']
        )
        
        # 4. 字幕ファイル生成
        subtitle_path = config.temp_dir / "test_subtitles.srt"
        subtitle_gen.generate_srt(translated_segments, subtitle_path)
        
        # 5. 音声生成
        segments_with_audio = tts.generate_speech(translated_segments)
        audio_file = None
        if any('audio_path' in seg for seg in segments_with_audio):
            audio_file = config.temp_dir / "test_translated_audio.mp3"
            composer.merge_audio_segments(segments_with_audio, audio_file)
        
        # 6. 動画合成
        output_path = config.output_dir / f"{video_path.stem}_ja.mp4"
        final_video = composer.compose_video(
            video_path,
            subtitle_path,
            audio_file,
            output_path
        )
        
        print(f"処理完了: {final_video}")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        raise

if __name__ == "__main__":
    test_video_path = Path(__file__).parent / "test_video.mp4"
    if test_video_path.exists():
        test_local_video(test_video_path)
    else:
        print(f"テスト動画が見つかりません: {test_video_path}")