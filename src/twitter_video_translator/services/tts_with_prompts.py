"""新しいプロンプト生成方式のTTS統合メソッド"""

from pathlib import Path
from typing import List, Optional, Tuple
from rich.console import Console
from ..models.transcription import SubtitleSegment
from ..models.tts import TTSResult
from ..config import config
from .tts import TextToSpeech
from .audio_style_analyzer import AudioStyleAnalyzer
from ..utils.logger import logger
import subprocess
import json
import asyncio

console = Console()


class TextToSpeechWithPrompts(TextToSpeech):
    """プロンプト直接生成方式のTTSサービス"""
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """音声ファイルの長さを取得
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            音声の長さ（秒）
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data["format"]["duration"])
            else:
                logger.error(f"ffprobe error: {result.stderr}")
                return 0.0
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 0.0
    
    def adjust_prompt_for_speed(self, prompt: str, speed_factor: float, target_language: str = "ja") -> str:
        """プロンプトに速度調整を追加
        
        Args:
            prompt: 元のプロンプト
            speed_factor: 速度係数（1.0=通常、1.2=20%速く、0.8=20%遅く）
            target_language: ターゲット言語
            
        Returns:
            速度調整済みプロンプト
        """
        if abs(speed_factor - 1.0) < 0.05:  # 5%未満の差は無視
            return prompt
        
        # 言語別の速度指示
        if target_language == "ja":
            if speed_factor > 1.5:
                speed_instruction = "とても速く話してください。"
            elif speed_factor > 1.2:
                speed_instruction = "速めに話してください。"
            elif speed_factor > 1.0:
                speed_instruction = "少し速めに話してください。"
            elif speed_factor < 0.7:
                speed_instruction = "とてもゆっくり話してください。"
            elif speed_factor < 0.9:
                speed_instruction = "ゆっくり話してください。"
            else:
                speed_instruction = "少しゆっくり話してください。"
        else:
            # 英語やその他の言語
            if speed_factor > 1.5:
                speed_instruction = "Speak very quickly. "
            elif speed_factor > 1.2:
                speed_instruction = "Speak quickly. "
            elif speed_factor > 1.0:
                speed_instruction = "Speak somewhat quickly. "
            elif speed_factor < 0.7:
                speed_instruction = "Speak very slowly. "
            elif speed_factor < 0.9:
                speed_instruction = "Speak slowly. "
            else:
                speed_instruction = "Speak somewhat slowly. "
        
        # プロンプトの冒頭に速度指示を挿入
        return speed_instruction + prompt
    
    async def generate_speech_with_timing(
        self,
        prompt: str,
        output_path: Path,
        segment: SubtitleSegment,
        target_language: str = "ja",
        max_attempts: int = 3
    ) -> Tuple[Optional[Path], float]:
        """タイミングを考慮した音声生成
        
        Args:
            prompt: TTSプロンプト
            output_path: 出力パス
            segment: 字幕セグメント（タイミング情報含む）
            max_attempts: 最大試行回数
            
        Returns:
            (音声ファイルパス, 実際の音声長)のタプル
        """
        segment_duration = segment.end_time - segment.start_time
        speed_factor = 1.0
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # 速度調整したプロンプトで音声生成
            adjusted_prompt = self.adjust_prompt_for_speed(prompt, speed_factor, target_language)
            
            logger.debug(f"Attempt {attempt}/{max_attempts} - Speed factor: {speed_factor:.2f}")
            logger.debug(f"Segment duration: {segment_duration:.2f}s")
            if speed_factor != 1.0:
                logger.debug(f"Adjusted prompt start: {adjusted_prompt[:100]}...")
            
            # 音声生成
            result = await self.generate_speech_with_prompt(adjusted_prompt, output_path)
            
            if result and output_path.exists():
                # 生成された音声の長さを取得
                audio_duration = self.get_audio_duration(output_path)
                logger.debug(f"Generated audio duration: {audio_duration:.2f}s")
                
                # 音声が字幕より10%以上長い場合
                if audio_duration > segment_duration * 1.1:
                    # 次回の速度係数を計算（最大2.0まで）
                    new_speed_factor = min(2.0, speed_factor * (audio_duration / segment_duration))
                    
                    if attempt < max_attempts:
                        logger.info(
                            f"Audio too long ({audio_duration:.2f}s > {segment_duration:.2f}s), "
                            f"retrying with speed factor {new_speed_factor:.2f}"
                        )
                        speed_factor = new_speed_factor
                        # ファイルを削除して再試行
                        output_path.unlink()
                        continue
                    else:
                        logger.warning(
                            f"Audio still too long after {max_attempts} attempts, "
                            f"using last generated audio"
                        )
                
                return output_path, audio_duration
            
            else:
                logger.error(f"Failed to generate audio on attempt {attempt}")
                if attempt < max_attempts:
                    await asyncio.sleep(1)  # 短い待機
        
        return None, 0.0
    
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
            
            # 非同期タスクを作成（タイミング調整版を使用）
            task = self.generate_speech_with_timing(prompt, segment_audio_path, segment, target_language)
            tasks.append((idx, segment, segment_audio_path, task, translated_text, prompt))
        
        # すべてのタスクを並列実行
        for idx, segment, audio_path, task, text, prompt in tasks:
            try:
                result_path, audio_duration = await task
                if result_path:
                    audio_files.append(audio_path)
                    if audio_path.exists():
                        total_size += audio_path.stat().st_size
                    
                    segments_data.append({
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "text": text,
                        "audio_path": str(audio_path),
                        "audio_duration": audio_duration
                    })
                    total_duration = max(total_duration, segment.end_time)
                    
                    # 音声が字幕より長い場合の警告
                    segment_duration = segment.end_time - segment.start_time
                    if audio_duration > segment_duration * 1.1:
                        logger.warning(
                            f"Segment {idx}: Audio duration ({audio_duration:.2f}s) "
                            f"exceeds subtitle duration ({segment_duration:.2f}s)"
                        )
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