"""Video processing related models."""

from typing import Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    """Video file metadata information."""
    
    file_path: Path = Field(..., description="Path to the video file")
    duration: float = Field(..., description="Video duration in seconds")
    width: int = Field(..., description="Video width in pixels")
    height: int = Field(..., description="Video height in pixels")
    fps: float = Field(..., description="Frames per second")
    bitrate: Optional[int] = Field(None, description="Video bitrate in bits/second")
    codec: Optional[str] = Field(None, description="Video codec (e.g., 'h264', 'h265')")
    audio_codec: Optional[str] = Field(None, description="Audio codec (e.g., 'aac', 'mp3')")
    audio_sample_rate: Optional[int] = Field(None, description="Audio sample rate in Hz")
    audio_channels: Optional[int] = Field(None, description="Number of audio channels")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Get video resolution as (width, height) tuple."""
        return (self.width, self.height)
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio."""
        return self.width / self.height if self.height > 0 else 0


class ProcessingOptions(BaseModel):
    """Options for video processing."""
    
    # Audio mixing options
    mix_original_audio: bool = Field(
        default=True, 
        description="Whether to mix original audio with translated audio"
    )
    original_audio_volume: float = Field(
        default=0.3, 
        ge=0.0, 
        le=1.0,
        description="Volume level for original audio (0.0-1.0)"
    )
    translated_audio_volume: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0,
        description="Volume level for translated audio (0.0-1.0)"
    )
    
    # Subtitle options
    add_subtitles: bool = Field(
        default=True, 
        description="Whether to add subtitles to the video"
    )
    subtitle_font: str = Field(
        default="Arial", 
        description="Font family for subtitles"
    )
    subtitle_size: int = Field(
        default=24, 
        gt=0,
        description="Font size for subtitles"
    )
    subtitle_color: str = Field(
        default="white", 
        description="Color for subtitle text"
    )
    subtitle_background: bool = Field(
        default=True, 
        description="Whether to add background to subtitles"
    )
    subtitle_position: str = Field(
        default="bottom", 
        description="Subtitle position ('bottom', 'top', 'center')"
    )
    
    # Output options
    output_format: str = Field(
        default="mp4", 
        description="Output video format"
    )
    output_quality: str = Field(
        default="high", 
        description="Output quality preset ('low', 'medium', 'high', 'best')"
    )
    preserve_original_resolution: bool = Field(
        default=True, 
        description="Whether to maintain original video resolution"
    )
    target_resolution: Optional[Tuple[int, int]] = Field(
        None, 
        description="Target resolution if not preserving original"
    )