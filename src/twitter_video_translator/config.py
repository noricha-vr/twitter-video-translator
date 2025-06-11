"""設定と環境変数の管理"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Config(BaseModel):
    """アプリケーション設定"""

    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    # 作業ディレクトリ
    work_dir: Path = Path("./output")
    temp_dir: Path = Path("./temp")

    # Groq Whisper設定
    whisper_model: str = "whisper-large-v3-turbo"

    # Gemini設定
    gemini_model: str = "gemini-2.0-flash-exp"
    tts_voice: str = "Pebble"  # 日本語対応の音声

    # FFmpeg設定
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    output_format: str = "mp4"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ディレクトリ作成
        self.work_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

    def validate_api_keys(self) -> bool:
        """APIキーの検証"""
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEYが設定されていません")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEYが設定されていません")
        return True


# グローバル設定インスタンス
config = Config()
