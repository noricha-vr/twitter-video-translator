"""CLIインターフェース"""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .config import config
from .services.downloader import TwitterDownloader
from .services.transcriber import AudioTranscriber
from .services.translator import TextTranslator
from .services.tts import TextToSpeech
from .services.video_composer import VideoComposer
from .utils.subtitle import SubtitleGenerator

console = Console()


class TwitterVideoTranslatorCLI:
    """Twitter動画翻訳CLIアプリケーション"""

    def __init__(self):
        self.downloader = TwitterDownloader(config.temp_dir)
        self.transcriber = AudioTranscriber()
        self.translator = TextTranslator()
        self.tts = TextToSpeech()
        self.composer = VideoComposer()
        self.subtitle_gen = SubtitleGenerator()

    def run(self, url: str, output_path: Path = None, use_tts: bool = True):
        """メイン処理"""
        try:
            # APIキーの検証
            config.validate_api_keys()

            console.print(
                Panel.fit(
                    f"[bold cyan]Twitter Video Translator[/bold cyan]\n" f"URL: {url}",
                    title="開始",
                )
            )

            # 1. 動画ダウンロード
            video_path = self.downloader.download_video(url)

            # 2. 音声抽出
            audio_path = self.transcriber.extract_audio(video_path)

            # 3. 文字起こし
            transcription = self.transcriber.transcribe_audio(audio_path)

            # 4. 翻訳
            translated_segments = self.translator.translate_segments(
                transcription["segments"], transcription["language"]
            )

            # 5. 字幕ファイル生成
            subtitle_path = config.temp_dir / "subtitles.srt"
            self.subtitle_gen.generate_srt(translated_segments, subtitle_path)

            # 6. 音声生成（オプション）
            audio_file = None
            if use_tts:
                segments_with_audio = self.tts.generate_speech(translated_segments)
                if any("audio_path" in seg for seg in segments_with_audio):
                    audio_file = config.temp_dir / "translated_audio.mp3"
                    self.composer.merge_audio_segments(segments_with_audio, audio_file)

            # 7. 動画合成
            if output_path is None:
                output_path = config.work_dir / "translated_video.mp4"

            final_video = self.composer.compose_video(
                video_path, subtitle_path, audio_file, output_path
            )

            console.print(
                Panel.fit(
                    f"[bold green]処理完了！[/bold green]\n"
                    f"出力ファイル: {final_video}",
                    title="完了",
                )
            )

            return final_video

        except Exception as e:
            console.print(f"[bold red]エラーが発生しました: {str(e)}[/bold red]")
            raise


@click.command()
@click.argument("url")
@click.option(
    "-o", "--output", type=click.Path(path_type=Path), help="出力ファイルパス"
)
@click.option("--no-tts", is_flag=True, help="音声生成をスキップ（字幕のみ）")
def main(url: str, output: Path = None, no_tts: bool = False):
    """Twitter動画を日本語に翻訳します"""
    cli = TwitterVideoTranslatorCLI()
    cli.run(url, output, use_tts=not no_tts)


if __name__ == "__main__":
    main()
