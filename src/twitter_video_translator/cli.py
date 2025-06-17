"""CLIインターフェース"""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .config import config
from .constants import (
    AVAILABLE_VOICES, 
    ALL_SUPPORTED_LANGUAGES,
    SUPPORTED_LANGUAGES, 
    RECOMMENDED_JAPANESE_VOICES,
    TTS_SUPPORTED_LANGUAGES,
    TRANSLATION_ONLY_LANGUAGES,
    LANGUAGE_CODES
)
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
        self.tts = None  # Will be initialized with voice parameter
        self.composer = VideoComposer()
        self.subtitle_gen = SubtitleGenerator()

    def run(self, url: str, output_path: Path = None, use_tts: bool = True, 
             original_volume: float = 0.15, japanese_volume: float = 1.8,
             target_language: str = "Japanese", voice: str = "Aoede"):
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
            logger.info(f"翻訳開始: ターゲット言語={target_language}")
            translated_segments = self.translator.translate_segments(
                transcription.segments, transcription.language, target_language
            )
            logger.info(f"翻訳完了: セグメント数={len(translated_segments)}")

            # 5. 字幕ファイル生成
            subtitle_path = config.temp_dir / "subtitles.srt"
            logger.info(f"字幕ファイル生成: {subtitle_path}")
            self.subtitle_gen.generate_srt(translated_segments, subtitle_path)

            # 6. 音声生成（オプション）
            audio_file = None
            # TTSがサポートしていない言語の場合は自動的に無効化
            if target_language in TRANSLATION_ONLY_LANGUAGES:
                logger.info(f"{target_language}はTTSをサポートしていません。字幕のみ生成します。")
                console.print(f"[yellow]注意: {target_language}はTTSをサポートしていないため、字幕のみ生成されます。[/yellow]")
                use_tts = False
            
            if use_tts:
                logger.info(f"音声生成開始: 音声={voice}")
                # TTSを初期化（音声パラメータを設定）
                self.tts = TextToSpeech()
                self.tts.voice_name = voice
                # 翻訳されたテキストを抽出
                translated_texts = [seg.text for seg in translated_segments]
                # 音声スタイル分析を有効にして音声生成
                tts_result = self.tts.generate_speech(
                    transcription.segments,  # 元の文字起こしセグメント
                    translated_texts,        # 翻訳されたテキスト
                    audio_path,             # 元の音声ファイル
                    analyze_style=True      # スタイル分析を有効化
                )
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
                
                # 言語コードを取得
                lang_code = LANGUAGE_CODES.get(target_language, target_language[:2].lower())
                output_path = config.output_dir / f"{original_filename}_{lang_code}.mp4"
            
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


# カスタムヘルプフォーマッター
class CustomCommand(click.Command):
    def format_help(self, ctx, formatter):
        super().format_help(ctx, formatter)
        
        # 推奨音声の追加情報
        formatter.write("\n")
        formatter.write_heading("推奨音声 (--voice/-v)")
        with formatter.indentation():
            for voice in RECOMMENDED_JAPANESE_VOICES:
                desc = AVAILABLE_VOICES.get(voice, "")
                formatter.write_text(f"{voice}: {desc}")
        
        formatter.write("\n")
        formatter.write_heading("利用可能な全音声")
        with formatter.indentation():
            for voice, desc in AVAILABLE_VOICES.items():
                formatter.write_text(f"{voice}: {desc}")
        
        formatter.write("\n")
        formatter.write_heading("サポート言語 (--target-language/-l)")
        formatter.write_text("TTSは以下の24言語をサポートしています：")
        with formatter.indentation():
            for lang, (code, display_name) in TTS_SUPPORTED_LANGUAGES.items():
                formatter.write_text(f"{lang}: {display_name} ({code})")
        
        if TRANSLATION_ONLY_LANGUAGES:
            formatter.write("\n")
            formatter.write_text("翻訳のみサポート（字幕のみ生成）：")
            with formatter.indentation():
                for lang in TRANSLATION_ONLY_LANGUAGES:
                    formatter.write_text(f"{lang}: 字幕のみ対応")


@click.command(cls=CustomCommand)
@click.argument("url")
@click.option(
    "-o", "--output", type=click.Path(path_type=Path), help="出力ファイルパス"
)
@click.option("--no-tts", is_flag=True, help="音声生成をスキップ（字幕のみ）")
@click.option(
    "-l", "--target-language",
    type=click.Choice(ALL_SUPPORTED_LANGUAGES),
    default="Japanese",
    help="翻訳先の言語（中国語は字幕のみ）"
)
@click.option(
    "-v", "--voice",
    type=click.Choice(list(AVAILABLE_VOICES.keys())),
    default="Aoede",
    help="TTS音声の選択（推奨音声は下記参照）"
)
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
    help="翻訳音声のボリューム倍率（デフォルト: 1.8 = +80%）"
)
def main(url: str, output: Path = None, no_tts: bool = False, 
         target_language: str = "Japanese", voice: str = "Aoede",
         original_volume: float = 0.15, japanese_volume: float = 1.8):
    """動画を指定言語に翻訳します（Twitter/YouTube対応）"""
    cli = VideoTranslatorCLI()
    cli.run(url, output, use_tts=not no_tts, 
            original_volume=original_volume, japanese_volume=japanese_volume,
            target_language=target_language, voice=voice)


if __name__ == "__main__":
    main()
