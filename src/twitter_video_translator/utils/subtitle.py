"""字幕ファイル（SRT）生成ユーティリティ"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import timedelta
from rich.console import Console

console = Console()


class SubtitleGenerator:
    """字幕ファイル生成"""

    @staticmethod
    def seconds_to_srt_time(seconds: float) -> str:
        """秒数をSRT形式の時間に変換"""
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        seconds = td.total_seconds() % 60
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @staticmethod
    def generate_srt(
        segments: List[Dict[str, Any]], output_path: Path, use_translation: bool = True
    ) -> Path:
        """SRTファイルを生成"""
        console.print("[bold blue]字幕ファイルを生成中...[/bold blue]")

        srt_content = []

        for idx, segment in enumerate(segments, 1):
            # タイムスタンプ
            start_time = SubtitleGenerator.seconds_to_srt_time(segment["start"])
            end_time = SubtitleGenerator.seconds_to_srt_time(segment["end"])

            # テキスト（翻訳版または原文）
            if use_translation and "translated_text" in segment:
                text = segment["translated_text"]
            else:
                text = segment["text"]

            # SRTエントリを追加
            srt_entry = f"{idx}\n{start_time} --> {end_time}\n{text}\n"
            srt_content.append(srt_entry)

        # ファイルに書き込み
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_content))

        console.print(f"[bold green]字幕ファイル生成完了: {output_path}[/bold green]")
        return output_path
