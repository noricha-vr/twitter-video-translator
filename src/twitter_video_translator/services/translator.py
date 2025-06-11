"""翻訳サービス（Gemini API）"""

from typing import List, Dict, Any
import google.generativeai as genai
from rich.console import Console
from ..config import config

console = Console()


class TextTranslator:
    """テキスト翻訳サービス"""

    def __init__(self):
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel(config.gemini_model)

    def translate_segments(
        self, segments: List[Dict[str, Any]], source_lang: str
    ) -> List[Dict[str, Any]]:
        """セグメントごとに翻訳"""
        console.print("[bold blue]テキストを翻訳中...[/bold blue]")

        translated_segments = []

        # セグメントをバッチで翻訳（API呼び出し削減のため）
        batch_size = 10
        for i in range(0, len(segments), batch_size):
            batch = segments[i : i + batch_size]

            # バッチのテキストを準備
            texts_to_translate = []
            for idx, segment in enumerate(batch):
                texts_to_translate.append(f"[{idx}] {segment['text']}")

            # プロンプト作成
            prompt = f"""以下の{source_lang}のテキストを自然な日本語に翻訳してください。
各行の番号（[0], [1]など）は保持してください。
映像の字幕として使用するため、短く簡潔に翻訳してください。

{chr(10).join(texts_to_translate)}"""

            try:
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
                    translated_segment = segment.copy()
                    translated_segment["translated_text"] = translations.get(
                        idx, segment["text"]
                    )
                    translated_segments.append(translated_segment)

            except Exception as e:
                console.print(
                    f"[yellow]翻訳エラー（バッチ {i//batch_size + 1}）: {str(e)}[/yellow]"
                )
                # エラーの場合は元のテキストを使用
                for segment in batch:
                    translated_segment = segment.copy()
                    translated_segment["translated_text"] = segment["text"]
                    translated_segments.append(translated_segment)

        console.print(
            f"[bold green]翻訳完了（{len(translated_segments)}セグメント）[/bold green]"
        )
        return translated_segments
