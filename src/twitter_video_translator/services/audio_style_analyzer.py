"""音声スタイル分析サービス"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import google.genai as genai
from google.genai import types
from rich.console import Console
from ..config import config
from ..models.transcription import SubtitleSegment

console = Console()


class AudioStyleAnalyzer:
    """音声スタイルを分析し、言語化するサービス"""
    
    def __init__(self):
        self.client = genai.Client(api_key=config.gemini_api_key)
        self.model = "gemini-2.0-flash-exp"
        
    async def analyze_audio_style(
        self, 
        audio_path: Path,
        transcribed_text: str,
        segment: Optional[SubtitleSegment] = None
    ) -> Dict[str, Any]:
        """音声ファイルから話者のスタイルを分析
        
        Args:
            audio_path: 分析する音声ファイルのパス
            transcribed_text: 文字起こしされたテキスト
            segment: 分析対象のセグメント情報（オプション）
            
        Returns:
            分析結果を含む辞書
        """
        try:
            # 音声ファイルを読み込み
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            
            # プロンプトを構築
            prompt = f"""この音声を分析して、話者の感情、速度、トーンを詳細に分析してください。

分析対象のテキスト: "{transcribed_text}"

以下の観点から分析してください：

1. **感情（emotion）**: 話者の感情状態を分析してください
   - 基本感情: happy, sad, angry, fear, surprise, disgust, neutral
   - 感情の強度: 弱い、中程度、強い
   - 複合的な感情がある場合は併記

2. **話速（speed）**: 話す速度を分析してください
   - very slow, slow, normal, fast, very fast
   - 数値で表現する場合: 0.5（遅い）〜2.0（速い）の範囲

3. **トーン（tone）**: 声のトーンや調子を分析してください
   - 明るい/暗い
   - 高い/低い
   - 力強い/弱い
   - フォーマル/カジュアル

4. **抑揚（intonation）**: 声の抑揚やイントネーションを分析してください
   - flat（平坦）, moderate（標準的）, expressive（表現豊か）
   - 特徴的なパターンがあれば具体的に

5. **その他の特徴**: 
   - 声の震え
   - 間の取り方
   - 強調の仕方
   - 特殊な発話スタイル

JSONフォーマットで回答してください：
{{
    "emotion": {{
        "primary": "感情名",
        "intensity": "強度",
        "secondary": "副次的な感情（あれば）"
    }},
    "speed": {{
        "label": "速度ラベル",
        "value": 数値（0.5-2.0）
    }},
    "tone": {{
        "brightness": "明るさ",
        "pitch": "高さ",
        "strength": "力強さ",
        "formality": "フォーマル度"
    }},
    "intonation": {{
        "pattern": "抑揚パターン",
        "expressiveness": "表現力レベル"
    }},
    "special_features": ["特徴1", "特徴2"],
    "summary": "全体的な話し方の要約"
}}"""
            
            # Gemini APIで分析（リトライ機能付き）
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(
                            data=audio_data,
                            mime_type="audio/wav"
                        )
                    ],
                ),
            ]
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    response = await self.client.aio.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                            response_mime_type="application/json"
                        ),
                    )
                    
                    # レスポンスをパース
                    if response.text:
                        import json
                        analysis_result = json.loads(response.text)
                        
                        # セグメント情報を追加
                        if segment:
                            analysis_result["segment_info"] = {
                                "start_time": segment.start_time,
                                "end_time": segment.end_time,
                                "text": segment.text
                            }
                        
                        return analysis_result
                    else:
                        retry_count += 1
                        if retry_count < max_retries:
                            console.print(f"[yellow]分析結果が空です。リトライ {retry_count}/{max_retries}[/yellow]")
                            import asyncio
                            await asyncio.sleep(1)
                        else:
                            raise Exception("分析結果が空です")
                
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        console.print(f"[yellow]Gemini API エラー: {str(e)}. リトライ {retry_count}/{max_retries}[/yellow]")
                        import asyncio
                        await asyncio.sleep(1)
                    else:
                        raise  # 最後のリトライでも失敗した場合は例外を再発生
                
        except Exception as e:
            console.print(f"[yellow]音声スタイル分析エラー: {str(e)}[/yellow]")
            # デフォルトスタイルを返す
            return self._get_default_style()
    
    def _get_default_style(self) -> Dict[str, Any]:
        """デフォルトの音声スタイル"""
        return {
            "emotion": {
                "primary": "neutral",
                "intensity": "moderate",
                "secondary": None
            },
            "speed": {
                "label": "normal",
                "value": 1.0
            },
            "tone": {
                "brightness": "neutral",
                "pitch": "medium",
                "strength": "moderate",
                "formality": "neutral"
            },
            "intonation": {
                "pattern": "moderate",
                "expressiveness": "standard"
            },
            "special_features": [],
            "summary": "標準的な読み上げスタイル"
        }
    
    def convert_to_tts_style(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析結果をGemini TTSのスタイルパラメータに変換
        
        Gemini TTSのcontrollable機能に対応したパラメータに変換
        参考: https://ai.google.dev/gemini-api/docs/speech-generation?hl=ja#controllable
        """
        # 感情を声のスタイルに変換
        emotion = analysis.get("emotion", {})
        primary_emotion = emotion.get("primary", "neutral")
        intensity = emotion.get("intensity", "moderate")
        
        # 感情マッピング（Gemini TTSがサポートするスタイルに変換）
        emotion_to_style = {
            "happy": "cheerful",
            "sad": "sad",
            "angry": "angry",
            "fear": "worried",
            "surprise": "excited",
            "disgust": "dissatisfied",
            "neutral": "neutral"
        }
        
        # 速度の調整
        speed = analysis.get("speed", {}).get("value", 1.0)
        
        # トーンの変換
        tone = analysis.get("tone", {})
        
        # TTSスタイルパラメータを構築
        tts_style = {
            "style": emotion_to_style.get(primary_emotion, "neutral"),
            "style_intensity": intensity,
            "speed": speed,
            "pitch_shift": 0,  # 後で実装可能
            "volume_gain_db": 0,  # 後で実装可能
            "emphasis": [],  # 強調する単語のリスト（後で実装可能）
        }
        
        # 特殊な特徴を反映（感情の強度が高い場合は感情を優先）
        special_features = analysis.get("special_features", [])
        if intensity != "strong":  # 感情の強度が強くない場合のみ特殊処理
            if "声の震え" in special_features:
                tts_style["style"] = "worried"
            elif "力強い" in tone.get("strength", ""):
                tts_style["style"] = "confident"
        
        return tts_style
    
    async def generate_tts_prompt(
        self, 
        audio_path: Path,
        transcribed_text: str,
        target_language: str,
        target_text: str,
        segment: Optional[SubtitleSegment] = None
    ) -> str:
        """音声を分析し、ターゲット言語のTTSプロンプトを直接生成
        
        Args:
            audio_path: 分析する音声ファイル
            transcribed_text: 元の文字起こしテキスト
            target_language: ターゲット言語コード（ja, en, zh, ko等）
            target_text: 読み上げるターゲット言語のテキスト
            segment: 字幕セグメント情報（オプション）
            
        Returns:
            ターゲット言語で書かれたTTSプロンプト
        """
        try:
            # 音声ファイルを読み込み
            audio_data = audio_path.read_bytes()
            mime_type = "audio/wav"
            
            # プロンプトを言語に応じて作成
            analysis_prompt = self._create_analysis_prompt_for_tts(
                target_language, transcribed_text, target_text
            )
            
            # Gemini APIで分析とプロンプト生成を同時に実行
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type=mime_type,
                                    data=audio_data
                                )
                            ),
                            types.Part.from_text(text=analysis_prompt)
                        ]
                    )
                ]
            )
            
            if response.text:
                return response.text.strip()
            else:
                # フォールバック: デフォルトプロンプト
                return self._get_default_tts_prompt(target_language, target_text)
                
        except Exception as e:
            console.print(f"[yellow]TTSプロンプト生成エラー: {str(e)}[/yellow]")
            # エラー時はデフォルトプロンプトを返す
            return self._get_default_tts_prompt(target_language, target_text)
    
    def _create_analysis_prompt_for_tts(
        self, target_language: str, transcribed_text: str, target_text: str
    ) -> str:
        """音声分析とTTSプロンプト生成用のプロンプトを作成"""
        
        prompts = {
            "ja": f"""
この音声を分析して、話者の特徴を再現するための日本語のTTSプロンプトを生成してください。

元のテキスト: {transcribed_text}

以下の要素を分析して、自然な日本語でTTSへの指示を作成してください：
1. 話者の性別、年齢層、声質
2. 話速、リズム、間の取り方
3. 感情、トーン、雰囲気
4. 特徴的な話し方（方言、癖など）
5. 声の震えや強弱などの特殊効果

生成するプロンプトは「あなたは〜」で始め、話者の特徴を詳細に説明し、
最後に「次のテキストを読んでください：」で終わるようにしてください。

読み上げるテキスト: {target_text}
""",
            "en": f"""
Analyze this audio and generate an English TTS prompt to reproduce the speaker's characteristics.

Original text: {transcribed_text}

Analyze the following elements and create natural English instructions for TTS:
1. Speaker's gender, age range, voice quality
2. Speaking pace, rhythm, pauses
3. Emotions, tone, atmosphere
4. Distinctive speaking style (accent, habits)
5. Special effects like voice tremor or emphasis

Start the prompt with "You are..." and describe the speaker's characteristics in detail,
ending with "Please read the following text:"

Text to read: {target_text}
""",
            "zh": f"""
分析这段音频并生成中文TTS提示词来再现说话者的特征。

原文: {transcribed_text}

分析以下要素并为TTS创建自然的中文指示：
1. 说话者的性别、年龄段、音质
2. 语速、节奏、停顿
3. 情感、语调、氛围
4. 独特的说话风格（口音、习惯）
5. 声音颤抖或强调等特殊效果

提示词以"你是..."开头，详细描述说话者的特征，
以"请朗读以下文本："结尾。

要朗读的文本: {target_text}
""",
            "ko": f"""
이 음성을 분석하여 화자의 특징을 재현하는 한국어 TTS 프롬프트를 생성해주세요.

원본 텍스트: {transcribed_text}

다음 요소들을 분석하여 TTS를 위한 자연스러운 한국어 지시를 만들어주세요:
1. 화자의 성별, 연령대, 음성 특징
2. 말하는 속도, 리듬, 쉼
3. 감정, 톤, 분위기
4. 독특한 말하기 스타일 (사투리, 습관)
5. 음성 떨림이나 강조 같은 특수 효과

프롬프트는 "당신은..."으로 시작하여 화자의 특징을 자세히 설명하고,
"다음 텍스트를 읽어주세요:"로 끝내주세요.

읽을 텍스트: {target_text}
"""
        }
        
        # デフォルトは英語
        return prompts.get(target_language, prompts["en"])
    
    def _get_default_tts_prompt(self, target_language: str, target_text: str) -> str:
        """デフォルトのTTSプロンプトを返す"""
        
        defaults = {
            "ja": f"自然な日本語で次のテキストを読んでください：\n\n{target_text}",
            "en": f"Please read the following text in a natural voice:\n\n{target_text}",
            "zh": f"请用自然的声音朗读以下文本：\n\n{target_text}",
            "ko": f"자연스러운 목소리로 다음 텍스트를 읽어주세요:\n\n{target_text}"
        }
        
        return defaults.get(target_language, defaults["en"])
