"""新しいプロンプト生成方式のTTS統合メソッド"""

from pathlib import Path
from typing import List, Optional
from rich.console import Console
from ..models.transcription import SubtitleSegment
from ..models.tts import TTSResult
from ..config import config
from .tts import TextToSpeech
from .audio_style_analyzer import AudioStyleAnalyzer
from ..utils.logger import logger
import subprocess

console = Console()


class TextToSpeechWithPrompts(TextToSpeech):
    """プロンプト直接生成方式のTTSサービス"""
    
    async def generate_speech_for_segments(
        self, 
        segments: List[SubtitleSegment], 
        translated_texts: List[str],
        audio_path: Optional[Path] = None,
        target_language: str = "ja"
    ) -> TTSResult:
        """プロンプト生成方式でセグメントごとに音声を生成
        
        Args:
            segments: 字幕セグメントのリスト
            translated_texts: 翻訳されたテキストのリスト
            audio_path: 元の音声ファイルのパス（スタイル分析用）
            target_language: ターゲット言語コード
        """
        console.print(f"[bold blue]{target_language}音声を生成中（プロンプト方式）...[/bold blue]")
        
        # スタイル分析器を初期化
        analyzer = AudioStyleAnalyzer()
        
        audio_files = []
        total_duration = 0.0
        total_size = 0
        segments_data = []
        tasks = []
        full_text_parts = []
        
        # 各セグメントのプロンプト生成と音声生成タスクを作成
        for idx, (segment, translated_text) in enumerate(zip(segments, translated_texts)):
            segment_audio_path = config.temp_dir / f"segment_{idx:04d}.wav"
            full_text_parts.append(translated_text)
            
            # セグメントの音声を抽出（スタイル分析用）
            if audio_path and audio_path.exists():
                try:
                    extracted_audio_path = config.temp_dir / f"segment_extract_{idx:04d}.wav"
                    
                    extract_cmd = [
                        "ffmpeg",
                        "-i", str(audio_path),
                        "-ss", str(segment.start_time),
                        "-t", str(segment.end_time - segment.start_time),
                        "-acodec", "pcm_s16le",
                        "-ar", "16000",
                        "-ac", "1",
                        "-y",
                        str(extracted_audio_path)
                    ]
                    
                    result = subprocess.run(extract_cmd, capture_output=True)
                    if result.returncode == 0 and extracted_audio_path.exists():
                        # プロンプトを生成
                        prompt = await analyzer.generate_tts_prompt(
                            extracted_audio_path,
                            segment.text,  # 元の文字起こしテキスト
                            target_language,
                            translated_text  # ターゲット言語のテキスト
                        )
                        
                        # デバッグ用: プロンプトをログに出力
                        logger.debug(f"Segment {idx} - Original text: {segment.text}")
                        logger.debug(f"Segment {idx} - Translated text: {translated_text}")
                        logger.debug(f"Segment {idx} - Generated TTS prompt:\n{prompt}")
                        
                        # 一時ファイルを削除
                        extracted_audio_path.unlink()
                    else:
                        # 音声抽出失敗時はデフォルトプロンプト
                        prompt = analyzer._get_default_tts_prompt(target_language, translated_text)
                        
                except Exception as e:
                    console.print(f"[yellow]セグメント{idx}の音声抽出失敗: {str(e)}[/yellow]")
                    prompt = analyzer._get_default_tts_prompt(target_language, translated_text)
            else:
                # 元音声がない場合はデフォルトプロンプト
                prompt = analyzer._get_default_tts_prompt(target_language, translated_text)
            
            # 非同期タスクを作成
            task = self.generate_speech_with_prompt(prompt, segment_audio_path)
            tasks.append((idx, segment, segment_audio_path, task, translated_text))
        
        # すべてのタスクを並列実行
        for idx, segment, audio_path, task, text in tasks:
            try:
                result = await task
                if result:
                    audio_files.append(audio_path)
                    if audio_path.exists():
                        total_size += audio_path.stat().st_size
                    
                    segments_data.append({
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "text": text,
                        "audio_path": str(audio_path)
                    })
                    total_duration = max(total_duration, segment.end_time)
            except Exception as e:
                console.print(
                    f"[yellow]セグメント{idx}の音声生成に失敗: {str(e)}[/yellow]"
                )
        
        console.print(
            f"[bold green]音声生成完了（{len(audio_files)}セグメント）[/bold green]"
        )
        
        # 最初の音声ファイルをメインとして返す
        main_audio_file = audio_files[0] if audio_files else config.temp_dir / "empty.wav"
        
        return TTSResult(
            audio_file=main_audio_file,
            duration=total_duration,
            text=" ".join(full_text_parts),
            language=target_language,
            voice=self.voice_name,
            format="wav",
            sample_rate=24000,
            file_size=total_size,
            segments=segments_data,
            metadata={"audio_files": [str(f) for f in audio_files]}
        )
    
    def generate_speech(
        self, 
        segments: List[SubtitleSegment], 
        translated_texts: List[str],
        audio_path: Optional[Path] = None,
        target_language: str = "ja"
    ) -> TTSResult:
        """同期的に音声を生成（メインエントリポイント）"""
        import asyncio
        return asyncio.run(
            self.generate_speech_for_segments(
                segments, translated_texts, audio_path, target_language
            )
        )