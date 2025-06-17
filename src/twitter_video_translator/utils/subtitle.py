"""字幕ファイル（SRT）生成ユーティリティ"""

from pathlib import Path
from typing import List
from rich.console import Console

from ..models.transcription import SubtitleSegment

console = Console()


class SubtitleGenerator:
    """字幕ファイル生成"""

    @staticmethod
    def generate_srt(
        segments: List[SubtitleSegment], output_path: Path
    ) -> Path:
        """SRTファイルを生成
        
        Args:
            segments: SubtitleSegmentのリスト
            output_path: 出力ファイルパス
            
        Returns:
            生成されたSRTファイルのパス
        """
        console.print("[bold blue]字幕ファイルを生成中...[/bold blue]")

        srt_content = []

        for idx, segment in enumerate(segments, 1):
            # SubtitleSegmentの組み込みメソッドを使用
            srt_entry = segment.to_srt_format(idx)
            srt_content.append(srt_entry)

        # ファイルに書き込み
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_content))

        console.print(f"[bold green]字幕ファイル生成完了: {output_path}[/bold green]")
        return output_path
