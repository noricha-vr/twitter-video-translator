"""音声合成サービス（Gemini 2.5 Flash Preview TTS）"""

import asyncio
import struct
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional
import google.genai as genai
from google.genai import types
from rich.console import Console
from ..config import config
from ..models.tts import TTSRequest, TTSResult
from ..models.transcription import SubtitleSegment
from .audio_style_analyzer import AudioStyleAnalyzer

console = Console()


class TextToSpeech:
    """テキスト音声合成サービス"""

    def __init__(self):
        self.client = genai.Client(api_key=config.gemini_api_key)
        self.model = "gemini-2.5-flash-preview-tts"
        self.voice_name = config.tts_voice  # 設定から音声を取得
        self.style_analyzer = AudioStyleAnalyzer()

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

    async def generate_speech_segment(
        self, 
        text: str, 
        output_path: Path,
        style_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """単一セグメントの音声生成
        
        Args:
            text: 生成するテキスト
            output_path: 出力パス
            style_params: 音声スタイルパラメータ（オプション）
        """
        try:
            # スタイル情報からプロンプトを構築
            style_prompt = ""
            if style_params:
                style = style_params.get("style", "neutral")
                intensity = style_params.get("style_intensity", "moderate")
                speed = style_params.get("speed", 1.0)
                
                # Style descriptions in English
                style_descriptions = {
                    "cheerful": "cheerful and happy",
                    "sad": "sad",
                    "angry": "angry",
                    "worried": "worried",
                    "excited": "excited",
                    "dissatisfied": "dissatisfied",
                    "confident": "confident",
                    "neutral": "neutral"
                }
                
                style_desc = style_descriptions.get(style, "neutral")
                
                # Intensity modifiers
                intensity_modifiers = {
                    "weak": "slightly",
                    "moderate": "",
                    "strong": "very"
                }
                intensity_modifier = intensity_modifiers.get(intensity, "")
                
                # Speed modifiers
                speed_modifier = ""
                if speed is not None and speed < 0.8:
                    speed_modifier = "slowly"
                elif speed is not None and speed > 1.2:
                    speed_modifier = "quickly"
                
                # Build style prompt in English
                style_components = []
                if speed_modifier:
                    style_components.append(f"Read {speed_modifier}")
                else:
                    style_components.append("Read")
                
                style_components.append("the following text in a")
                
                if intensity_modifier:
                    style_components.append(f"{intensity_modifier} {style_desc}")
                else:
                    style_components.append(style_desc)
                
                style_components.append("tone:")
                
                style_prompt = f"{' '.join(style_components)}\n\n"
            
            # プロンプトとテキストを結合
            full_text = style_prompt + text if style_prompt else text
            
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=full_text),
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

            # ストリーミングで音声を生成（リトライ機能付き）
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
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
                    
                    # 音声データが生成されなかった場合もリトライ
                    retry_count += 1
                    if retry_count < max_retries:
                        console.print(f"[yellow]音声データが生成されませんでした。リトライ {retry_count}/{max_retries}[/yellow]")
                        import asyncio
                        await asyncio.sleep(1)  # 1秒待機
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        console.print(f"[yellow]Gemini TTS エラー: {str(e)}. リトライ {retry_count}/{max_retries}[/yellow]")
                        import asyncio
                        await asyncio.sleep(1)  # 1秒待機
                    else:
                        raise  # 最後のリトライでも失敗した場合は例外を再発生
            
            return None

        except Exception as e:
            console.print(f"[bold red]音声生成エラー: {str(e)}[/bold red]")
            return None

    async def generate_speech_for_segments(
        self, 
        segments: List[SubtitleSegment], 
        translated_texts: Optional[List[str]] = None,
        audio_path: Optional[Path] = None,
        analyze_style: bool = True
    ) -> TTSResult:
        """セグメントごとに音声を生成
        
        Args:
            segments: 字幕セグメントのリスト
            translated_texts: 翻訳されたテキストのリスト（オプション）
            audio_path: 元の音声ファイルのパス（スタイル分析用）
            analyze_style: 音声スタイルを分析するかどうか
        """
        console.print("[bold blue]日本語音声を生成中...[/bold blue]")

        audio_files = []
        total_duration = 0.0
        total_size = 0
        segments_data = []
        tasks = []
        full_text_parts = []
        
        # 期待されるセグメント数を計算
        expected_count = len(translated_texts) if translated_texts else len(segments)
        
        # 音声スタイル分析（必要な場合）
        style_params_cache = {}
        if analyze_style and audio_path and audio_path.exists():
            console.print("[bold blue]音声スタイルを分析中...[/bold blue]")
            
            # 各セグメントの音声スタイルを分析
            for idx, segment in enumerate(segments):
                try:
                    # セグメントの音声を抽出（ffmpegを使用）
                    segment_audio_path = config.temp_dir / f"segment_style_{idx:04d}.wav"
                    
                    import subprocess
                    extract_cmd = [
                        "ffmpeg",
                        "-i", str(audio_path),
                        "-ss", str(segment.start_time),
                        "-t", str(segment.end_time - segment.start_time),
                        "-acodec", "pcm_s16le",
                        "-ar", "16000",
                        "-ac", "1",
                        "-y",
                        str(segment_audio_path)
                    ]
                    
                    result = subprocess.run(extract_cmd, capture_output=True)
                    if result.returncode == 0 and segment_audio_path.exists():
                        # スタイル分析を実行
                        analysis = await self.style_analyzer.analyze_audio_style(
                            segment_audio_path,
                            segment.text,  # 文字起こしされたテキストを使用
                            segment
                        )
                        
                        # TTSスタイルパラメータに変換
                        style_params = self.style_analyzer.convert_to_tts_style(analysis)
                        style_params_cache[idx] = style_params
                        
                        # 一時ファイルを削除
                        segment_audio_path.unlink()
                        
                        console.print(f"[green]セグメント{idx}のスタイル分析完了: {analysis['summary']}[/green]")
                    
                except Exception as e:
                    console.print(f"[yellow]セグメント{idx}のスタイル分析失敗: {str(e)}[/yellow]")
            
            # チェック1: スタイル分析後のセグメント数確認
            style_count = len(style_params_cache)
            if style_count != expected_count:
                console.print(
                    f"[yellow]警告: スタイル分析されたセグメント数が不一致: "
                    f"期待値={expected_count}, 実際={style_count}[/yellow]"
                )

        # 各セグメントの音声生成タスクを作成
        for idx, segment in enumerate(segments):
            segment_audio_path = config.temp_dir / f"segment_{idx:04d}.wav"
            
            # テキストを決定（翻訳テキストがあればそれを使用）
            if translated_texts and idx < len(translated_texts):
                text = translated_texts[idx]
            else:
                text = segment.text
            
            full_text_parts.append(text)
            
            # スタイルパラメータを取得（なければデフォルト）
            style_params = style_params_cache.get(idx)

            # 非同期タスクを作成
            task = self.generate_speech_segment(text, segment_audio_path, style_params)
            tasks.append((idx, segment, segment_audio_path, task, text))

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
        
        # チェック2: 音声生成後のファイル数確認と不足分の再生成
        generated_count = len(audio_files)
        if generated_count != expected_count:
            console.print(
                f"[yellow]警告: 生成された音声ファイル数が不一致: "
                f"期待値={expected_count}, 実際={generated_count}[/yellow]"
            )
            
            # 不足セグメントのインデックスを特定
            generated_indices = set()
            for seg in segments_data:
                # audio_pathからインデックスを抽出
                path = Path(seg["audio_path"])
                idx_str = path.stem.split("_")[-1]  # segment_0000.wav -> 0000
                try:
                    generated_indices.add(int(idx_str))
                except ValueError:
                    pass
            
            missing_indices = []
            for idx in range(expected_count):
                if idx not in generated_indices:
                    missing_indices.append(idx)
            
            if missing_indices:
                console.print(
                    f"[yellow]不足セグメントを再生成中: {missing_indices}[/yellow]"
                )
                
                # リトライ処理（最大2回）
                retry_count = 0
                max_retries = 2
                
                while missing_indices and retry_count < max_retries:
                    retry_count += 1
                    console.print(f"[blue]リトライ {retry_count}/{max_retries}[/blue]")
                    
                    # 不足セグメントのみ再生成
                    retry_tasks = []
                    for idx in missing_indices:
                        if idx < len(segments):
                            segment = segments[idx]
                            segment_audio_path = config.temp_dir / f"segment_{idx:04d}.wav"
                            
                            # テキストを決定
                            if translated_texts and idx < len(translated_texts):
                                text = translated_texts[idx]
                            else:
                                text = segment.text
                            
                            # スタイルパラメータを取得
                            style_params = style_params_cache.get(idx)
                            
                            # 再生成タスクを作成
                            task = self.generate_speech_segment(text, segment_audio_path, style_params)
                            retry_tasks.append((idx, segment, segment_audio_path, task, text))
                    
                    # 再生成実行
                    newly_generated = []
                    for idx, segment, audio_path, task, text in retry_tasks:
                        try:
                            result = await task
                            if result and audio_path.exists():
                                audio_files.append(audio_path)
                                total_size += audio_path.stat().st_size
                                
                                segments_data.append({
                                    "start_time": segment.start_time,
                                    "end_time": segment.end_time,
                                    "text": text,
                                    "audio_path": str(audio_path)
                                })
                                total_duration = max(total_duration, segment.end_time)
                                newly_generated.append(idx)
                                
                                console.print(f"[green]セグメント{idx}の再生成成功[/green]")
                        except Exception as e:
                            console.print(
                                f"[red]セグメント{idx}の再生成失敗: {str(e)}[/red]"
                            )
                    
                    # 新たに生成されたインデックスを不足リストから削除
                    missing_indices = [idx for idx in missing_indices if idx not in newly_generated]
                
                # 最終チェック
                if missing_indices:
                    console.print(
                        f"[bold red]警告: {len(missing_indices)}個のセグメントが生成できませんでした: "
                        f"{missing_indices}[/bold red]"
                    )
                    console.print("[yellow]部分的な音声ファイルで処理を続行します[/yellow]")
        
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

    def generate_speech(
        self, 
        segments: List[SubtitleSegment], 
        translated_texts: Optional[List[str]] = None,
        audio_path: Optional[Path] = None,
        analyze_style: bool = True
    ) -> TTSResult:
        """同期的に音声を生成（メインエントリポイント）
        
        Args:
            segments: 字幕セグメントのリスト
            translated_texts: 翻訳されたテキストのリスト（オプション）
            audio_path: 元の音声ファイルのパス（スタイル分析用）
            analyze_style: 音声スタイルを分析するかどうか
        """
        # 非同期関数を同期的に実行
        return asyncio.run(
            self.generate_speech_for_segments(
                segments, translated_texts, audio_path, analyze_style
            )
        )
    
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