"""Twitter動画ダウンロードサービス"""

import re
from pathlib import Path
from typing import Optional
import yt_dlp
from rich.console import Console

console = Console()


class TwitterDownloader:
    """Twitter動画ダウンローダー"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def validate_url(self, url: str) -> bool:
        """Twitter URLの検証"""
        twitter_pattern = r"https?://(?:www\.)?(twitter\.com|x\.com)/\w+/status/\d+"
        return bool(re.match(twitter_pattern, url))

    def download_video(self, url: str) -> Optional[Path]:
        """Twitter動画をダウンロード"""
        if not self.validate_url(url):
            raise ValueError("無効なTwitter URLです")

        # 出力ファイル名
        output_path = self.output_dir / "original_video.mp4"

        # yt-dlpオプション
        ydl_opts = {
            "outtmpl": str(output_path.with_suffix("")),
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "force_generic_extractor": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                console.print("[bold blue]動画をダウンロード中...[/bold blue]")
                info = ydl.extract_info(url, download=True)

                # 動画が含まれているか確認
                if not info.get("formats"):
                    raise ValueError("この投稿には動画が含まれていません")

                # ダウンロードされたファイルを探す
                possible_extensions = [".mp4", ".webm", ".mkv"]
                for ext in possible_extensions:
                    check_path = output_path.with_suffix(ext)
                    if check_path.exists():
                        console.print(
                            f"[bold green]ダウンロード完了: {check_path}[/bold green]"
                        )
                        return check_path

                # ファイルが見つからない場合
                raise FileNotFoundError("ダウンロードされたファイルが見つかりません")

        except Exception as e:
            console.print(f"[bold red]ダウンロードエラー: {str(e)}[/bold red]")
            raise
