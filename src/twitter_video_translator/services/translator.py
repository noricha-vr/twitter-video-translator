"""翻訳サービス（Gemini API）"""

from typing import List, Dict, Any
import time
import google.generativeai as genai
from rich.console import Console
from ..config import config
from ..models.translation import TranslationRequest, TranslationResult
from ..models.transcription import SubtitleSegment

console = Console()


class TextTranslator:
    """テキスト翻訳サービス"""

    def __init__(self):
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel(config.gemini_model)

    def translate_segments(
        self, segments: List[SubtitleSegment], source_lang: str, target_language: str = None
    ) -> List[SubtitleSegment]:
        """セグメントごとに翻訳"""
        if target_language is None:
            target_language = config.target_language
        console.print(f"[bold blue]テキストを{target_language}に翻訳中...[/bold blue]")

        translated_segments = []

        # セグメントをバッチで翻訳（API呼び出し削減のため）
        batch_size = 10
        for i in range(0, len(segments), batch_size):
            batch = segments[i : i + batch_size]

            # バッチのテキストを準備
            texts_to_translate = []
            for idx, segment in enumerate(batch):
                texts_to_translate.append(f"[{idx}] {segment.text}")

            # プロンプト作成
            prompt = f"""以下の{source_lang}のテキストを自然な{target_language}に翻訳してください。
各行の番号（[0], [1]など）は保持してください。
映像の字幕として使用するため、短く簡潔に翻訳してください。

{chr(10).join(texts_to_translate)}"""

            try:
                # レート制限を考慮して遅延を追加
                if i > 0:
                    time.sleep(1)  # 1秒待機
                
                # Geminiで翻訳
                response = self.model.generate_content(prompt)
                translated_text = response.text

                # 翻訳結果を解析
                translations = {}
                for line in translated_text.strip().split("\n"):
                    if line.strip() and line.startswith("["):
                        try:
                            idx_end = line.index("]")
                            idx = int(line[1:idx_end])
                            translation = line[idx_end + 1 :].strip()
                            translations[idx] = translation
                        except (ValueError, IndexError):
                            continue

                # セグメントに翻訳を追加
                for idx, segment in enumerate(batch):
                    # 新しいSubtitleSegmentを作成（翻訳されたテキストで）
                    translated_segment = SubtitleSegment(
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        text=translations.get(idx, segment.text),
                        confidence=segment.confidence
                    )
                    translated_segments.append(translated_segment)

            except Exception as e:
                console.print(
                    f"[yellow]翻訳エラー（バッチ {i//batch_size + 1}）: {str(e)}[/yellow]"
                )
                # エラーの場合は元のテキストを使用
                for segment in batch:
                    translated_segment = SubtitleSegment(
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        text=segment.text,
                        confidence=segment.confidence
                    )
                    translated_segments.append(translated_segment)

        console.print(
            f"[bold green]翻訳完了（{len(translated_segments)}セグメント）[/bold green]"
        )
        return translated_segments

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """単一テキストの翻訳"""
        # ソース言語の自動検出または指定
        source_lang = request.source_language or "auto"
        
        # プロンプト作成
        prompt_parts = []
        
        if source_lang != "auto":
            prompt_parts.append(f"以下の{source_lang}のテキストを")
        else:
            prompt_parts.append("以下のテキストを")
            
        prompt_parts.append(f"自然な{request.target_language}に翻訳してください。")
        
        if request.preserve_formatting:
            prompt_parts.append("改行やフォーマットは保持してください。")
        
        if request.context:
            prompt_parts.append(f"\n\n文脈: {request.context}")
            
        prompt_parts.append(f"\n\nテキスト:\n{request.text}")
        
        prompt = "".join(prompt_parts)
        
        try:
            # Geminiで翻訳
            response = self.model.generate_content(prompt)
            translated_text = response.text.strip()
            
            # 言語検出（簡易的な実装）
            detected_source_lang = source_lang if source_lang != "auto" else "en"
            
            return TranslationResult(
                original_text=request.text,
                translated_text=translated_text,
                source_language=detected_source_lang,
                target_language=request.target_language,
                confidence=0.95,  # Geminiは信頼度スコアを提供しないので固定値
                alternative_translations=[],
                metadata={"model": config.gemini_model}
            )
            
        except Exception as e:
            console.print(f"[red]翻訳エラー: {str(e)}[/red]")
            # エラーの場合は元のテキストを返す
            return TranslationResult(
                original_text=request.text,
                translated_text=request.text,
                source_language=source_lang if source_lang != "auto" else "unknown",
                target_language=request.target_language,
                confidence=0.0,
                alternative_translations=[],
                metadata={"error": str(e)}
            )
