"""音声文字起こしサービス（Groq Whisper API）"""

from pathlib import Path
from typing import List
import ffmpeg
from groq import Groq
from rich.console import Console
from ..config import config
from ..models.transcription import TranscriptionResult, SubtitleSegment

console = Console()


class AudioTranscriber:
    """音声文字起こしサービス"""

    def __init__(self):
        self.client = Groq(api_key=config.groq_api_key)
        self.temp_dir = config.temp_dir

    def extract_audio(self, video_path: Path) -> Path:
        """動画から音声を抽出"""
        audio_path = self.temp_dir / "audio.wav"

        try:
            console.print("[bold blue]音声を抽出中...[/bold blue]")

            # ffmpegで音声抽出（WAV形式、16kHz）
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(
                stream, str(audio_path), acodec="pcm_s16le", ar="16000", ac=1
            )
            ffmpeg.run(
                stream, overwrite_output=True, capture_stdout=True, capture_stderr=True
            )

            console.print(f"[bold green]音声抽出完了: {audio_path}[/bold green]")
            return audio_path

        except Exception as e:
            console.print(f"[bold red]音声抽出エラー: {str(e)}[/bold red]")
            raise

    def split_audio(self, audio_path: Path, max_duration: int = 300) -> List[Path]:
        """音声を分割（5分ごと）"""
        import subprocess
        import json
        
        # 音声の長さを取得
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_format",
            "-print_format", "json",
            str(audio_path)
        ]
        
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration_info = json.loads(probe_result.stdout)
        total_duration = float(duration_info["format"]["duration"])
        
        if total_duration <= max_duration:
            return [audio_path]
        
        console.print(f"[yellow]音声が長いため分割します（{total_duration:.1f}秒）[/yellow]")
        
        # 分割数を計算
        num_segments = int(total_duration / max_duration) + 1
        segment_paths = []
        
        for i in range(num_segments):
            start_time = i * max_duration
            segment_path = self.temp_dir / f"audio_segment_{i}.wav"
            
            # ffmpegで分割
            split_cmd = [
                "ffmpeg",
                "-i", str(audio_path),
                "-ss", str(start_time),
                "-t", str(max_duration),
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                str(segment_path)
            ]
            
            subprocess.run(split_cmd, capture_output=True, check=True)
            segment_paths.append(segment_path)
            
        console.print(f"[green]音声を{len(segment_paths)}個のセグメントに分割しました[/green]")
        return segment_paths

    def transcribe_audio(self, audio_path: Path) -> TranscriptionResult:
        """音声を文字起こし（Groq Whisper API）"""
        try:
            console.print("[bold blue]音声を文字起こし中...[/bold blue]")
            
            # ファイルサイズをチェック
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb > 20:  # 20MB以上なら分割
                audio_segments = self.split_audio(audio_path)
            else:
                audio_segments = [audio_path]
            
            all_segments: List[SubtitleSegment] = []
            detected_language = None
            full_text = []
            total_duration = 0.0
            
            for i, segment_path in enumerate(audio_segments):
                if len(audio_segments) > 1:
                    console.print(f"[blue]セグメント {i+1}/{len(audio_segments)} を処理中...[/blue]")
                
                # 音声ファイルを読み込み
                with open(segment_path, "rb") as audio_file:
                    # Groq Whisper APIで文字起こし
                    transcription = self.client.audio.transcriptions.create(
                        model=config.whisper_model,
                        file=audio_file,
                        language="en",  # 自動検出のため指定なし
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                    )
                
                # 最初のセグメントから言語を取得
                if detected_language is None:
                    detected_language = transcription.language
                
                full_text.append(transcription.text)
                
                # セグメント情報を整理（時間をオフセット）
                if hasattr(transcription, "segments"):
                    time_offset = i * 300  # 5分ごとのオフセット
                    for segment in transcription.segments:
                        subtitle_segment = SubtitleSegment(
                            start_time=segment["start"] + time_offset,
                            end_time=segment["end"] + time_offset,
                            text=segment["text"].strip(),
                            confidence=segment.get("confidence")
                        )
                        all_segments.append(subtitle_segment)
                        # 最大のend_timeを追跡
                        if subtitle_segment.end_time > total_duration:
                            total_duration = subtitle_segment.end_time
                
                # 一時ファイルを削除
                if segment_path != audio_path:
                    segment_path.unlink()

            # TranscriptionResultオブジェクトを作成
            result = TranscriptionResult(
                full_text=" ".join(full_text),
                segments=all_segments,
                language=detected_language or "unknown",
                duration=total_duration
            )

            console.print(
                f"[bold green]文字起こし完了（言語: {result.language}）[/bold green]"
            )
            return result

        except Exception as e:
            console.print(f"[bold red]文字起こしエラー: {str(e)}[/bold red]")
            raise

    def transcribe(self, video_path: Path) -> TranscriptionResult:
        """動画から音声を抽出して文字起こし"""
        # 音声を抽出
        audio_path = self.extract_audio(video_path)
        
        # 文字起こしを実行
        result = self.transcribe_audio(audio_path)
        
        # 一時音声ファイルを削除
        if audio_path.exists():
            audio_path.unlink()
        
        return result

    def transcribe_segments(self, video_path: Path) -> List[SubtitleSegment]:
        """動画から音声を抽出して文字起こしし、セグメントのリストを返す"""
        result = self.transcribe(video_path)
        return result.segments
