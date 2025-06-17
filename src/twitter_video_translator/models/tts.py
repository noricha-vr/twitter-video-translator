"""Text-to-Speech related models."""

from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Request for text-to-speech synthesis."""
    
    text: str = Field(..., description="Text to convert to speech")
    language: str = Field(
        default="ja", 
        description="Language code for TTS (e.g., 'ja' for Japanese)"
    )
    voice: Optional[str] = Field(
        None, 
        description="Voice ID or name for TTS synthesis"
    )
    speed: float = Field(
        default=1.0, 
        gt=0.1, 
        le=3.0,
        description="Speech speed multiplier (1.0 is normal speed)"
    )
    pitch: float = Field(
        default=0.0, 
        ge=-20.0, 
        le=20.0,
        description="Pitch adjustment in semitones"
    )
    volume: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0,
        description="Output volume level (0.0-1.0)"
    )
    output_format: str = Field(
        default="mp3", 
        description="Output audio format (e.g., 'mp3', 'wav', 'ogg')"
    )
    sample_rate: int = Field(
        default=24000, 
        description="Output sample rate in Hz"
    )
    emotion: Optional[str] = Field(
        None, 
        description="Emotion style for synthesis if supported"
    )
    

class TTSResult(BaseModel):
    """Result of text-to-speech synthesis."""
    
    audio_file: Path = Field(..., description="Path to generated audio file")
    duration: float = Field(..., description="Duration of generated audio in seconds")
    text: str = Field(..., description="Text that was synthesized")
    language: str = Field(..., description="Language used for synthesis")
    voice: Optional[str] = Field(None, description="Voice ID or name used")
    format: str = Field(..., description="Audio format of output file")
    sample_rate: int = Field(..., description="Sample rate of audio in Hz")
    file_size: int = Field(..., description="Size of audio file in bytes")
    segments: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Timing segments if available from TTS service"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata from TTS service"
    )