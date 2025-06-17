"""設定と環境変数の管理"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定（環境変数から自動読み込み）"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    groq_api_key: str = Field(..., description="Groq API key for Whisper transcription")
    gemini_api_key: str = Field(..., description="Google Gemini API key for translation and TTS")
    
    # Directories
    output_dir: Path = Field(default=Path("./output"), description="Output directory for processed videos")
    temp_dir: Path = Field(default=Path("./temp"), description="Temporary directory for intermediate files")
    
    # Groq Whisper settings
    whisper_model: str = Field(default="whisper-large-v3-turbo", description="Whisper model to use")
    whisper_language: Optional[str] = Field(default=None, description="Force language detection (e.g., 'en', 'ja')")
    
    # Gemini settings
    gemini_model: str = Field(default="gemini-2.0-flash-exp", description="Gemini model for translation")
    gemini_temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Translation temperature")
    tts_voice: str = Field(default="Aoede", description="TTS voice name (Japanese voice)")
    
    # Translation settings
    target_language: str = Field(default="Japanese", description="Target language for translation")
    
    # FFmpeg settings
    video_codec: str = Field(default="libx264", description="Video codec for output")
    audio_codec: str = Field(default="aac", description="Audio codec for output")
    output_format: str = Field(default="mp4", description="Output video format")
    video_crf: int = Field(default=23, ge=0, le=51, description="Video quality (lower is better)")
    audio_bitrate: str = Field(default="192k", description="Audio bitrate")
    
    # Audio mixing settings
    default_original_volume: float = Field(default=0.15, ge=0.0, le=1.0, description="Default original audio volume")
    default_japanese_volume: float = Field(default=1.8, ge=0.0, le=3.0, description="Default Japanese audio volume")
    
    # Processing settings
    max_audio_file_size_mb: int = Field(default=25, description="Max audio file size for Groq API")
    api_retry_attempts: int = Field(default=3, description="Number of API retry attempts")
    api_retry_delay: float = Field(default=1.0, description="Delay between API retries in seconds")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    @field_validator("output_dir", "temp_dir", mode="after")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Create directories if they don't exist"""
        v.mkdir(exist_ok=True, parents=True)
        return v
    
    @field_validator("groq_api_key", "gemini_api_key")
    @classmethod
    def validate_api_keys(cls, v: str, info) -> str:
        """Validate that API keys are not empty"""
        if not v or v.strip() == "":
            field_name = info.field_name.replace("_", " ").upper()
            raise ValueError(f"{field_name} is required but not set")
        return v
    
    def validate_all(self) -> bool:
        """Validate all settings"""
        # This method is kept for backward compatibility
        # Validation now happens automatically through Pydantic
        return True


# グローバル設定インスタンス
# 環境変数が見つからない場合はエラーを発生させる
try:
    settings = Settings()
except Exception as e:
    # 開発時の便宜のため、エラーメッセージを改善
    import sys
    print(f"Error loading settings: {e}", file=sys.stderr)
    print("Please ensure .env file exists with required API keys", file=sys.stderr)
    raise


# 後方互換性のためのエイリアス
config = settings