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

        # 出力ファイル名（拡張子は自動決定）
        output_template = str(self.output_dir / "original_video.%(ext)s")

        # yt-dlpオプション
        ydl_opts = {
            "outtmpl": output_template,
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


                # ダウンロードされたファイルのパスを取得
                # yt-dlpは実際のファイル名を_filenameキーで返す
                if info.get("_filename"):
                    downloaded_path = Path(info["_filename"])
                    if downloaded_path.exists():
                        console.print(
                            f"[bold green]ダウンロード完了: {downloaded_path}[/bold green]"
                        )
                        return downloaded_path
                
                # _filenameがない場合は、拡張子を推測して探す
                # 実際にダウンロードされた拡張子を取得
                ext = info.get("ext", "mp4")
                expected_path = self.output_dir / f"original_video.{ext}"
                if expected_path.exists():
                    console.print(
                        f"[bold green]ダウンロード完了: {expected_path}[/bold green]"
                    )
                    return expected_path

                # それでも見つからない場合は、一般的な拡張子で探す
                possible_extensions = ["mp4", "webm", "mkv", "mov", "avi"]
                for ext in possible_extensions:
                    check_path = self.output_dir / f"original_video.{ext}"
                    if check_path.exists():
                        console.print(
                            f"[bold green]ダウンロード完了: {check_path}[/bold green]"
                        )
                        return check_path

                # 最後の手段として、拡張子なしのファイルも探す
                no_ext_path = self.output_dir / "original_video"
                if no_ext_path.exists():
                    console.print(
                        f"[bold yellow]警告: 拡張子なしのファイルが見つかりました: {no_ext_path}[/bold yellow]"
                    )
                    # 適切な拡張子を付けてリネーム
                    ext = info.get("ext", "mp4")
                    new_path = no_ext_path.with_suffix(f".{ext}")
                    no_ext_path.rename(new_path)
                    console.print(
                        f"[bold green]ダウンロード完了（リネーム済み）: {new_path}[/bold green]"
                    )
                    return new_path

                # ファイルが見つからない場合
                raise FileNotFoundError("ダウンロードされたファイルが見つかりません")

        except Exception as e:
            console.print(f"[bold red]ダウンロードエラー: {str(e)}[/bold red]")
            raise
