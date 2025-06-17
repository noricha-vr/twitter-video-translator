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
from ..models.tts import TTSRequest, TTSResult
from ..models.transcription import SubtitleSegment

console = Console()


class TextToSpeech:
    """テキスト音声合成サービス"""

    def __init__(self):
        self.client = genai.Client(api_key=config.gemini_api_key)
        self.model = "gemini-2.5-flash-preview-tts"
        self.voice_name = config.tts_voice  # 設定から音声を取得

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
        self, segments: List[SubtitleSegment], translated_texts: Optional[List[str]] = None
    ) -> TTSResult:
        """セグメントごとに音声を生成
        
        Args:
            segments: 字幕セグメントのリスト
            translated_texts: 翻訳されたテキストのリスト（オプション）
        """
        console.print("[bold blue]日本語音声を生成中...[/bold blue]")

        audio_files = []
        total_duration = 0.0
        total_size = 0
        segments_data = []
        tasks = []
        full_text_parts = []

        # 各セグメントの音声生成タスクを作成
        for idx, segment in enumerate(segments):
            audio_path = config.temp_dir / f"segment_{idx:04d}.wav"
            
            # テキストを決定（翻訳テキストがあればそれを使用）
            if translated_texts and idx < len(translated_texts):
                text = translated_texts[idx]
            else:
                text = segment.text
            
            full_text_parts.append(text)

            # 非同期タスクを作成
            task = self.generate_speech_segment(text, audio_path)
            tasks.append((idx, segment, audio_path, task, text))

        # すべてのタスクを並列実行
        for idx, segment, audio_path, task, text in tasks:
            try:
                result = await task
                if result:
                    audio_files.append(audio_path)
                    # ファイルサイズを取得
                    if audio_path.exists():
                        total_size += audio_path.stat().st_size
                    
                    segments_data.append({
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "text": text,
                        "audio_path": str(audio_path)
                    })
                    total_duration = max(total_duration, segment.end_time)
            except Exception as e:
                console.print(
                    f"[yellow]セグメント{idx}の音声生成に失敗: {str(e)}[/yellow]"
                )

        console.print(
            f"[bold green]音声生成完了（{len(audio_files)}セグメント）[/bold green]"
        )
        
        # 最初の音声ファイルをメインとして返す（後で結合処理が必要な場合）
        main_audio_file = audio_files[0] if audio_files else config.temp_dir / "empty.wav"
        
        return TTSResult(
            audio_file=main_audio_file,
            duration=total_duration,
            text=" ".join(full_text_parts),
            language="ja",
            voice=self.voice_name,
            format="wav",
            sample_rate=24000,
            file_size=total_size,
            segments=segments_data,
            metadata={"audio_files": [str(f) for f in audio_files]}
        )

    def generate_speech(self, segments: List[SubtitleSegment], translated_texts: Optional[List[str]] = None) -> TTSResult:
        """同期的に音声を生成（メインエントリポイント）
        
        Args:
            segments: 字幕セグメントのリスト
            translated_texts: 翻訳されたテキストのリスト（オプション）
        """
        # 非同期関数を同期的に実行
        return asyncio.run(self.generate_speech_for_segments(segments, translated_texts))
    
    async def generate_async(self, request: TTSRequest) -> TTSResult:
        """TTSRequestから音声を生成（非同期）"""
        # 単一テキストの音声生成
        audio_path = config.temp_dir / f"tts_{hash(request.text)}.wav"
        
        # 音声設定を上書き（リクエストで指定されている場合）
        original_voice = self.voice_name
        if request.voice:
            self.voice_name = request.voice
        
        try:
            result = await self.generate_speech_segment(request.text, audio_path)
            
            if result and audio_path.exists():
                file_size = audio_path.stat().st_size
                
                # 音声ファイルから継続時間を推定（サンプルレートとファイルサイズから）
                # WAVヘッダーは44バイト、16ビット（2バイト）モノラル音声と仮定
                audio_data_size = file_size - 44
                duration = audio_data_size / (request.sample_rate * 2)
                
                return TTSResult(
                    audio_file=audio_path,
                    duration=duration,
                    text=request.text,
                    language=request.language,
                    voice=self.voice_name,
                    format="wav",
                    sample_rate=request.sample_rate,
                    file_size=file_size,
                    segments=[],
                    metadata={
                        "speed": request.speed,
                        "pitch": request.pitch,
                        "volume": request.volume,
                        "emotion": request.emotion
                    }
                )
            else:
                raise Exception("音声生成に失敗しました")
                
        finally:
            # 音声設定を元に戻す
            self.voice_name = original_voice
    
    def generate(self, request: TTSRequest) -> TTSResult:
        """TTSRequestから音声を生成（同期）"""
        return asyncio.run(self.generate_async(request))