"""CLIインターフェース"""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .config import config
from .services.downloader import VideoDownloader
from .services.transcriber import AudioTranscriber
from .services.translator import TextTranslator
from .services.tts import TextToSpeech
from .services.video_composer import VideoComposer
from .utils.subtitle import SubtitleGenerator
from .utils.logger import logger, console


class VideoTranslatorCLI:
    """動画翻訳CLIアプリケーション（Twitter/YouTube対応）"""

    def __init__(self):
        self.downloader = VideoDownloader(config.temp_dir)
        self.transcriber = AudioTranscriber()
        self.translator = TextTranslator()
        self.tts = TextToSpeech()
        self.composer = VideoComposer()
        self.subtitle_gen = SubtitleGenerator()

    def run(self, url: str, output_path: Path = None, use_tts: bool = True, 
             original_volume: float = 0.15, japanese_volume: float = 1.8):
        """メイン処理"""
        try:
            logger.info(f"処理開始: URL={url}")
            
            # tempディレクトリをクリア
            import shutil
            if config.temp_dir.exists():
                logger.info("tempディレクトリをクリア")
                shutil.rmtree(config.temp_dir)
            config.temp_dir.mkdir(exist_ok=True)
            
            # APIキーの検証
            config.validate_all()

            console.print(
                Panel.fit(
                    f"[bold cyan]Video Translator[/bold cyan]\n" f"URL: {url}",
                    title="開始",
                )
            )

            # 1. 動画ダウンロード
            logger.info("動画ダウンロード開始")
            video_path, video_info = self.downloader.download_video(url)
            logger.info(f"動画ダウンロード完了: {video_path}")
            logger.debug(f"動画情報: タイトル='{video_info.get('title', 'N/A')}', 長さ={video_info.get('duration', 'N/A')}秒")

            # 2. 音声抽出
            logger.info("音声抽出開始")
            audio_path = self.transcriber.extract_audio(video_path)
            logger.info(f"音声抽出完了: {audio_path}")

            # 3. 文字起こし
            logger.info("文字起こし開始")
            transcription = self.transcriber.transcribe_audio(audio_path)
            logger.info(f"文字起こし完了: 言語={transcription.language}, セグメント数={len(transcription.segments)}")

            # 4. 翻訳
            logger.info("翻訳開始")
            translated_segments = self.translator.translate_segments(
                transcription.segments, transcription.language
            )
            logger.info(f"翻訳完了: セグメント数={len(translated_segments)}")

            # 5. 字幕ファイル生成
            subtitle_path = config.temp_dir / "subtitles.srt"
            logger.info(f"字幕ファイル生成: {subtitle_path}")
            self.subtitle_gen.generate_srt(translated_segments, subtitle_path)

            # 6. 音声生成（オプション）
            audio_file = None
            if use_tts:
                logger.info("音声生成開始")
                tts_result = self.tts.generate_speech(translated_segments)
                if tts_result.segments and any("audio_path" in seg for seg in tts_result.segments):
                    audio_file = config.temp_dir / "translated_audio.wav"
                    # segmentsをPath型を含む辞書に変換（キー名も変換）
                    segments_for_merge = []
                    for seg in tts_result.segments:
                        seg_dict = {
                            "start": seg["start_time"],
                            "end": seg["end_time"],
                            "text": seg["text"],
                            "audio_path": Path(seg["audio_path"])
                        }
                        segments_for_merge.append(seg_dict)
                    self.composer.merge_audio_segments(segments_for_merge, audio_file)
                    logger.info(f"音声生成完了: {audio_file}")
            else:
                logger.info("音声生成スキップ")

            # 7. 動画合成
            if output_path is None:
                # 元のファイル名に基づいて出力ファイル名を生成
                original_filename = video_path.stem  # 拡張子なしのファイル名
                # video_infoからタイトルを取得できる場合は使用
                if video_info.get("title"):
                    # タイトルをファイル名として使用（安全な文字のみ）
                    import re
                    safe_title = re.sub(r'[^\w\s-]', '', video_info["title"])
                    safe_title = re.sub(r'[-\s]+', '-', safe_title)[:50]  # 最大50文字
                    if safe_title:
                        original_filename = safe_title
                
                output_path = config.output_dir / f"{original_filename}_ja.mp4"
            
            logger.info(f"出力ファイル名: {output_path}")

            logger.info("動画合成開始")
            final_video = self.composer.compose_video(
                video_path, subtitle_path, audio_file, output_path,
                original_volume=original_volume,
                japanese_volume=japanese_volume
            )
            logger.info(f"動画合成完了: {final_video}")

            console.print(
                Panel.fit(
                    f"[bold green]処理完了！[/bold green]\n"
                    f"出力ファイル: {final_video}",
                    title="完了",
                )
            )

            logger.info("処理完了")
            return final_video

        except Exception as e:
            logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
            console.print(f"[bold red]エラーが発生しました: {str(e)}[/bold red]")
            raise


@click.command()
@click.argument("url")
@click.option(
    "-o", "--output", type=click.Path(path_type=Path), help="出力ファイルパス"
)
@click.option("--no-tts", is_flag=True, help="音声生成をスキップ（字幕のみ）")
@click.option(
    "--original-volume", 
    type=float, 
    default=0.15, 
    help="元の音声のボリューム（0.0-1.0、デフォルト: 0.15 = 15%）"
)
@click.option(
    "--japanese-volume", 
    type=float, 
    default=1.8, 
    help="日本語音声のボリューム倍率（デフォルト: 1.8 = +80%）"
)
def main(url: str, output: Path = None, no_tts: bool = False, 
         original_volume: float = 0.15, japanese_volume: float = 1.8):
    """動画を日本語に翻訳します（Twitter/YouTube対応）"""
    cli = VideoTranslatorCLI()
    cli.run(url, output, use_tts=not no_tts, 
            original_volume=original_volume, japanese_volume=japanese_volume)


if __name__ == "__main__":
    main()
