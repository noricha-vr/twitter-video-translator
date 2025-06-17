"""Transcription related models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SubtitleSegment(BaseModel):
    """Individual subtitle segment with timing information."""
    
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Subtitle text content")
    confidence: Optional[float] = Field(None, description="Transcription confidence score (0-1)")
    
    @property
    def duration(self) -> float:
        """Calculate duration of the segment in seconds."""
        return self.end_time - self.start_time
    
    def to_srt_timestamp(self, timestamp: float) -> str:
        """Convert timestamp to SRT format (HH:MM:SS,mmm)."""
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        milliseconds = int((timestamp % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def to_srt_format(self, index: int) -> str:
        """Convert segment to SRT subtitle format."""
        start_time = self.to_srt_timestamp(self.start_time)
        end_time = self.to_srt_timestamp(self.end_time)
        return f"{index}\n{start_time} --> {end_time}\n{self.text}\n"


class TranscriptionResult(BaseModel):
    """Result of audio transcription."""
    
    full_text: str = Field(..., description="Complete transcribed text")
    segments: List[SubtitleSegment] = Field(
        default_factory=list, 
        description="List of subtitle segments with timing"
    )
    language: str = Field(..., description="Detected or specified language code")
    duration: float = Field(..., description="Total audio duration in seconds")
    confidence: Optional[float] = Field(
        None, 
        description="Overall transcription confidence score (0-1)"
    )
    
    def to_srt(self) -> str:
        """Convert transcription result to SRT subtitle format."""
        srt_content = []
        for i, segment in enumerate(self.segments, 1):
            srt_content.append(segment.to_srt_format(i))
        return "\n".join(srt_content)