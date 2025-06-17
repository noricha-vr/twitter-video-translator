"""動画合成サービス（FFmpeg）"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import ffmpeg
import subprocess
from rich.console import Console
from ..config import config
from ..utils.logger import logger

console = Console()


class VideoComposer:
    """動画合成サービス"""

    def __init__(self):
        self.temp_dir = config.temp_dir

    def merge_audio_segments(
        self, segments: List[Dict[str, Any]], output_path: Path
    ) -> Path:
        """音声セグメントを結合（正しいタイミングで配置）"""
        console.print("[bold blue]音声セグメントを結合中...[/bold blue]")

        # 音声ファイルがあるセグメントのみ抽出
        audio_segments = [
            seg for seg in segments
            if "audio_path" in seg and seg["audio_path"].exists()
        ]
        
        if not audio_segments:
            raise ValueError("音声ファイルが見つかりません")

        # 全体の長さを計算
        total_duration = max(seg["end"] for seg in segments)

        # FFmpegコマンドを構築
        cmd = ["ffmpeg", "-y"]
        
        # 各音声ファイルを入力として追加
        for seg in audio_segments:
            cmd.extend(["-i", str(seg["audio_path"].absolute())])
        
        # フィルターグラフを構築
        filter_parts = []
        for i, seg in enumerate(audio_segments):
            # 各音声の開始時刻をミリ秒単位で計算
            delay_ms = int(seg["start"] * 1000)
            filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")
        
        # すべての音声をミックス
        input_labels = "".join(f"[a{i}]" for i in range(len(audio_segments)))
        filter_parts.append(f"{input_labels}amix=inputs={len(audio_segments)}:duration=longest[out]")
        
        filter_complex = ";".join(filter_parts)
        
        # フィルターグラフと出力設定を追加
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-t", str(total_duration),  # 全体の長さを指定
            "-ar", "44100",  # サンプリングレート
            "-ac", "2",  # ステレオ
            str(output_path)
        ])

        # ffmpegで結合
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            console.print(f"[bold green]音声結合完了: {output_path}[/bold green]")
            return output_path
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]音声結合エラー: {e.stderr}[/bold red]")
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

            # 音声ストリーム処理
            video_stream = input_video.video
            
            if audio_file and audio_file.exists():
                # 日本語音声がある場合：元の音声を30%に下げて、日本語音声とミックス
                logger.info("日本語音声とオリジナル音声をミックス（オリジナル音声：30%）")
                original_audio = input_video.audio.filter("volume", 0.3)  # 元の音声を30%に
                japanese_audio = ffmpeg.input(str(audio_file)).audio
                
                # 音声をミックス
                audio_stream = ffmpeg.filter(
                    [original_audio, japanese_audio], 
                    "amix", 
                    inputs=2, 
                    duration="longest",
                    dropout_transition=2
                )
            else:
                # 日本語音声がない場合：オリジナルの音声をそのまま使用
                logger.info("日本語音声なし、オリジナル音声を使用")
                audio_stream = input_video.audio

            # 字幕フィルターを適用
            # 日本語フォントの指定（FontSize=15は元のサイズの約60%）
            video_stream = video_stream.filter(
                "subtitles",
                str(subtitle_file),
                force_style="FontName=Hiragino Sans,FontSize=15,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2",
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
