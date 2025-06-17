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
        self.model = "gemini-2.5-flash-preview-05-20"
        
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
            
            # Gemini APIで分析
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
                raise Exception("分析結果が空です")
                
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