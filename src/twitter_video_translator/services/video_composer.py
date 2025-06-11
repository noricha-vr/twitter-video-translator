"""動画合成サービス（FFmpeg）"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import ffmpeg
import subprocess
from rich.console import Console
from ..config import config

console = Console()


class VideoComposer:
    """動画合成サービス"""

    def __init__(self):
        self.temp_dir = config.temp_dir

    def merge_audio_segments(
        self, segments: List[Dict[str, Any]], output_path: Path
    ) -> Path:
        """音声セグメントを結合"""
        console.print("[bold blue]音声セグメントを結合中...[/bold blue]")

        # 音声ファイルリストを作成
        concat_list = self.temp_dir / "concat_list.txt"
        with open(concat_list, "w") as f:
            for segment in segments:
                if "audio_path" in segment and segment["audio_path"].exists():
                    # 各セグメントの長さに合わせて音声を調整
                    duration = segment["end"] - segment["start"]
                    # 絶対パスを使用
                    f.write(f"file '{segment['audio_path'].absolute()}'\n")
                    f.write(f"duration {duration}\n")

        # ffmpegで結合
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            console.print(f"[bold green]音声結合完了: {output_path}[/bold green]")
            return output_path
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]音声結合エラー: {e.stderr.decode()}[/bold red]")
            raise

    def compose_video(
        self,
        original_video: Path,
        subtitle_file: Path,
        audio_file: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """動画、音声、字幕を合成"""
        console.print("[bold blue]動画を合成中...[/bold blue]")

        if output_path is None:
            output_path = config.work_dir / "translated_video.mp4"

        try:
            # 入力ストリーム
            input_video = ffmpeg.input(str(original_video))

            # 音声ストリーム（新しい音声がある場合は置き換え）
            if audio_file and audio_file.exists():
                input_audio = ffmpeg.input(str(audio_file))
                video_stream = input_video.video
                audio_stream = input_audio.audio
            else:
                # オリジナルの音声を使用
                video_stream = input_video.video
                audio_stream = input_video.audio

            # 字幕フィルターを適用
            # 日本語フォントの指定
            video_stream = video_stream.filter(
                "subtitles",
                str(subtitle_file),
                force_style="FontName=Hiragino Sans,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2",
            )

            # 出力
            output = ffmpeg.output(
                video_stream,
                audio_stream,
                str(output_path),
                vcodec=config.video_codec,
                acodec=config.audio_codec,
                **{"b:v": "2M", "b:a": "192k"},
            )

            # 実行
            ffmpeg.run(
                output, overwrite_output=True, capture_stdout=True, capture_stderr=True
            )

            console.print(f"[bold green]動画合成完了: {output_path}[/bold green]")
            return output_path

        except ffmpeg.Error as e:
            console.print(
                f"[bold red]動画合成エラー: {e.stderr.decode() if e.stderr else str(e)}[/bold red]"
            )
            raise
