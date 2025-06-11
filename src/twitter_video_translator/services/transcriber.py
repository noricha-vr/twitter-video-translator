"""音声文字起こしサービス（Groq Whisper API）"""

from pathlib import Path
from typing import Dict, Any
import ffmpeg
from groq import Groq
from rich.console import Console
from ..config import config

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

    def transcribe_audio(self, audio_path: Path) -> Dict[str, Any]:
        """音声を文字起こし（Groq Whisper API）"""
        try:
            console.print("[bold blue]音声を文字起こし中...[/bold blue]")

            # 音声ファイルを読み込み
            with open(audio_path, "rb") as audio_file:
                # Groq Whisper APIで文字起こし
                transcription = self.client.audio.transcriptions.create(
                    model=config.whisper_model,
                    file=audio_file,
                    language="en",  # 自動検出のため指定なし
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            # 結果を辞書形式に変換
            result = {
                "text": transcription.text,
                "language": transcription.language,
                "segments": [],
            }

            # セグメント情報を整理
            if hasattr(transcription, "segments"):
                for segment in transcription.segments:
                    result["segments"].append(
                        {
                            "start": segment["start"],
                            "end": segment["end"],
                            "text": segment["text"].strip(),
                        }
                    )

            console.print(
                f"[bold green]文字起こし完了（言語: {result['language']}）[/bold green]"
            )
            return result

        except Exception as e:
            console.print(f"[bold red]文字起こしエラー: {str(e)}[/bold red]")
            raise
