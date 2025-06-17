"""動画ダウンロードサービス"""

import re
from pathlib import Path
from typing import Optional, Literal
import yt_dlp
from rich.console import Console
from ..utils.logger import logger

console = Console()


class VideoDownloader:
    """動画ダウンローダー（Twitter/YouTube対応）"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def validate_url(self, url: str) -> Optional[Literal["twitter", "youtube"]]:
        """URLの検証とプラットフォーム判定"""
        twitter_pattern = r"https?://(?:www\.)?(twitter\.com|x\.com)/\w+/status/\d+"
        youtube_pattern = r"https?://(?:www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|m\.youtube\.com/watch\?v=)[\w-]+"
        
        if re.match(twitter_pattern, url):
            return "twitter"
        elif re.match(youtube_pattern, url):
            return "youtube"
        return None

    def download_video(self, url: str) -> tuple[Optional[Path], dict]:
        """動画をダウンロードし、動画情報も返す"""
        logger.debug(f"download_video called with URL: {url}")
        platform = self.validate_url(url)
        if not platform:
            logger.error(f"無効なURL: {url}")
            raise ValueError("無効なURLです。TwitterまたはYouTubeのURLを指定してください")
        
        logger.info(f"プラットフォーム: {platform}")

        # 出力ファイル名（拡張子は自動決定）
        output_template = str(self.output_dir / "original_video.%(ext)s")
        logger.debug(f"出力テンプレート: {output_template}")

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
                console.print(f"[bold blue]{platform}から動画をダウンロード中...[/bold blue]")
                logger.debug(f"yt-dlp.extract_info実行: URL={url}")
                info = ydl.extract_info(url, download=True)
                logger.debug(f"動画情報取得: タイトル='{info.get('title', 'N/A')}', 拡張子={info.get('ext', 'N/A')}")

                # 動画が含まれているか確認
                if not info.get("formats"):
                    raise ValueError("この投稿には動画が含まれていません")


                # ダウンロードされたファイルのパスを取得
                # yt-dlpは実際のファイル名を_filenameキーで返す
                if info.get("_filename"):
                    downloaded_path = Path(info["_filename"])
                    logger.debug(f"_filenameからパス取得: {downloaded_path}")
                    if downloaded_path.exists():
                        console.print(
                            f"[bold green]ダウンロード完了: {downloaded_path}[/bold green]"
                        )
                        logger.info(f"ダウンロード成功: {downloaded_path}")
                        return downloaded_path, info
                    else:
                        logger.warning(f"_filenameが指すファイルが存在しません: {downloaded_path}")
                
                # _filenameがない場合は、拡張子を推測して探す
                # 実際にダウンロードされた拡張子を取得
                ext = info.get("ext", "mp4")
                expected_path = self.output_dir / f"original_video.{ext}"
                if expected_path.exists():
                    console.print(
                        f"[bold green]ダウンロード完了: {expected_path}[/bold green]"
                    )
                    return expected_path, info

                # それでも見つからない場合は、一般的な拡張子で探す
                possible_extensions = ["mp4", "webm", "mkv", "mov", "avi"]
                for ext in possible_extensions:
                    check_path = self.output_dir / f"original_video.{ext}"
                    if check_path.exists():
                        console.print(
                            f"[bold green]ダウンロード完了: {check_path}[/bold green]"
                        )
                        return check_path, info

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
                    return new_path, info

                # ファイルが見つからない場合
                logger.error(f"ダウンロードされたファイルが見つかりません。探索したディレクトリ: {self.output_dir}")
                raise FileNotFoundError("ダウンロードされたファイルが見つかりません")

        except Exception as e:
            logger.error(f"ダウンロードエラー: {str(e)}", exc_info=True)
            console.print(f"[bold red]ダウンロードエラー: {str(e)}[/bold red]")
            raise
