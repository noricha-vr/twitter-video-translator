"""Translation related models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    """Request for text translation."""
    
    text: str = Field(..., description="Text to translate")
    source_language: Optional[str] = Field(
        None, 
        description="Source language code (e.g., 'en', 'ja'). Auto-detect if None"
    )
    target_language: str = Field(
        default="ja", 
        description="Target language code for translation"
    )
    preserve_formatting: bool = Field(
        default=True, 
        description="Whether to preserve line breaks and formatting"
    )
    context: Optional[str] = Field(
        None, 
        description="Additional context to improve translation quality"
    )
    

class TranslationResult(BaseModel):
    """Result of text translation."""
    
    original_text: str = Field(..., description="Original text before translation")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Detected or specified source language")
    target_language: str = Field(..., description="Target language of translation")
    confidence: Optional[float] = Field(
        None, 
        description="Translation confidence score (0-1)"
    )
    alternative_translations: List[str] = Field(
        default_factory=list, 
        description="Alternative translation options if available"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata from translation service"
    )