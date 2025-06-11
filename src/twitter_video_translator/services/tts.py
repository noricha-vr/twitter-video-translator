"""音声合成サービス（Gemini 2.5 Flash Preview TTS）"""

import asyncio
import struct
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from rich.console import Console
from ..config import config

console = Console()


class TextToSpeech:
    """テキスト音声合成サービス"""

    def __init__(self):
        self.client = genai.Client(api_key=config.gemini_api_key)
        self.model = "gemini-2.5-flash-preview-tts"
        self.voice_name = "Kore"  # 日本語対応の音声

    def convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """WAVファイルヘッダーを生成して音声データに追加"""
        # MIMEタイプから音声パラメータを解析
        parameters = self.parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size

        # WAVヘッダーを作成
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",          # ChunkID
            chunk_size,       # ChunkSize
            b"WAVE",          # Format
            b"fmt ",          # Subchunk1ID
            16,               # Subchunk1Size (16 for PCM)
            1,                # AudioFormat (1 for PCM)
            num_channels,     # NumChannels
            sample_rate,      # SampleRate
            byte_rate,        # ByteRate
            block_align,      # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",          # Subchunk2ID
            data_size         # Subchunk2Size
        )
        return header + audio_data

    def parse_audio_mime_type(self, mime_type: str) -> dict[str, int]:
        """MIMEタイプから音声パラメータを解析"""
        bits_per_sample = 16
        rate = 24000

        # パラメータから rate を抽出
        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass

        return {"bits_per_sample": bits_per_sample, "rate": rate}

    async def generate_speech_segment(self, text: str, output_path: Path) -> Optional[Path]:
        """単一セグメントの音声生成"""
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=text),
                    ],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                response_modalities=["audio"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name
                        )
                    )
                ),
            )

            # ストリーミングで音声を生成
            audio_data = bytearray()
            mime_type = None
            
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if (chunk.candidates is None or 
                    chunk.candidates[0].content is None or 
                    chunk.candidates[0].content.parts is None):
                    continue
                    
                part = chunk.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    audio_data.extend(part.inline_data.data)
                    if mime_type is None:
                        mime_type = part.inline_data.mime_type

            if audio_data and mime_type:
                # WAVファイルとして保存
                wav_data = self.convert_to_wav(bytes(audio_data), mime_type)
                with open(output_path, "wb") as f:
                    f.write(wav_data)
                return output_path
            
            return None

        except Exception as e:
            console.print(f"[bold red]音声生成エラー: {str(e)}[/bold red]")
            return None

    async def generate_speech_for_segments(
        self, segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """セグメントごとに音声を生成"""
        console.print("[bold blue]日本語音声を生成中...[/bold blue]")

        segments_with_audio = []
        tasks = []

        # 各セグメントの音声生成タスクを作成
        for idx, segment in enumerate(segments):
            audio_path = config.temp_dir / f"segment_{idx:04d}.wav"
            text = segment.get("translated_text", segment["text"])

            # 非同期タスクを作成
            task = self.generate_speech_segment(text, audio_path)
            tasks.append((idx, segment, audio_path, task))

        # すべてのタスクを並列実行
        for idx, segment, audio_path, task in tasks:
            try:
                result = await task
                segment_with_audio = segment.copy()
                if result:
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