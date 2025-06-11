"""音声合成サービス（Gemini Flash 2.5 TTS）"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any
import google.generativeai as genai
from rich.console import Console
from ..config import config

console = Console()


class TextToSpeech:
    """テキスト音声合成サービス"""

    def __init__(self):
        genai.configure(api_key=config.gemini_api_key)

    async def generate_speech_segment(self, text: str, output_path: Path) -> Path:
        """単一セグメントの音声生成"""
        try:
            # 一時的にgTTSを使用
            # 注: Gemini 2.0 Flash-expは直接的なTTS APIを持たないため、
            # 音声ファイルは別途生成する必要があります
            from gtts import gTTS

            tts = gTTS(text=text, lang="ja", slow=False)
            tts.save(str(output_path))

            return output_path

        except Exception as e:
            console.print(f"[bold red]音声生成エラー: {str(e)}[/bold red]")
            raise

    async def generate_speech_for_segments(
        self, segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """セグメントごとに音声を生成"""
        console.print("[bold blue]日本語音声を生成中...[/bold blue]")

        segments_with_audio = []
        tasks = []

        # 各セグメントの音声生成タスクを作成
        for idx, segment in enumerate(segments):
            audio_path = config.temp_dir / f"segment_{idx:04d}.mp3"
            text = segment.get("translated_text", segment["text"])

            # 非同期タスクを作成
            task = self.generate_speech_segment(text, audio_path)
            tasks.append((idx, segment, audio_path, task))

        # すべてのタスクを並列実行
        for idx, segment, audio_path, task in tasks:
            try:
                await task
                segment_with_audio = segment.copy()
                segment_with_audio["audio_path"] = audio_path
                segments_with_audio.append(segment_with_audio)
            except Exception as e:
                console.print(
                    f"[yellow]セグメント{idx}の音声生成に失敗: {str(e)}[/yellow]"
                )
                # エラーの場合は音声なしで続行
                segments_with_audio.append(segment.copy())

        console.print(
            f"[bold green]音声生成完了（{len(segments_with_audio)}セグメント）[/bold green]"
        )
        return segments_with_audio

    def generate_speech(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """同期的に音声を生成（メインエントリポイント）"""
        # 非同期関数を同期的に実行
        return asyncio.run(self.generate_speech_for_segments(segments))
