# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Twitter video translator application that:
- Downloads videos from Twitter posts
- Transcribes audio using Groq API Whisper
- Translates content to Japanese
- Adds Japanese subtitles and audio using Gemini Flash 2.5 TTS
- Outputs a new video with Japanese audio and subtitles

## Development Setup

### Package Management
- This project uses `uv` for Python package management
- Python 3.13+ is required

### Required External Tools
- ffmpeg (for video processing)

### API Dependencies
- Groq API for speech-to-text (Whisper)
- Google Gemini Flash 2.5 for text-to-speech

## Common Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py
```

## Architecture Notes

The application flow:
1. Accept Twitter post URL as input
2. Validate that the post contains video
3. Download video from Twitter
4. Extract audio and transcribe using Groq Whisper API
5. Translate transcription to Japanese
6. Generate Japanese audio using Gemini Flash 2.5 TTS
7. Create subtitles
8. Encode final video with Japanese audio and subtitles using ffmpeg

## Important Implementation Details

- Input validation must ensure the Twitter URL contains video content
- The app is designed to run locally
- All video processing should be done using ffmpeg
- API credentials for Groq and Google will need to be configured