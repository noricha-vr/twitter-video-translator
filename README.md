# Twitter Video Translator

TwitterÕ;’å,kû3WWUhóğ’ı Y‹Äüë

## _ı

- Twitter/X nÕ;’À¦óíüÉ
- óğ’‡WwSWGroq Whisper API	
- Æ­¹È’å,kû3Google Gemini	
- å,óğ’gTTS	
- WUØMÕ;’FFmpeg	

## Åj‚n

- Python 3.13+
- FFmpeg·¹Æàk¤ó¹Èüë	
- Groq API ­ü
- Google Gemini API ­ü

## ¤ó¹Èüë

```bash
# êİ¸Èê’¯íüó
git clone https://github.com/yourusername/twitter-video-translator.git
cd twitter-video-translator

# uv’(WfX¢Â’¤ó¹Èüë
uv sync
```

## -š

`.env` Õ¡¤ë’\WAPI­ü’-š

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## D¹

```bash
# ú,„j(¹ÕWUóğ	
uv run python main.py https://twitter.com/user/status/123456789

# WUnóğ’¹­Ã×	
uv run python main.py https://twitter.com/user/status/123456789 --no-tts

# ú›Õ¡¤ë’š
uv run python main.py https://twitter.com/user/status/123456789 -o my_video.mp4

# Øë×
uv run python main.py --help
```

## ú›

- ÇÕ©ëÈnú›H: `./output/translated_video.mp4`
- \mÕ¡¤ë: `./temp/` Ç£ì¯Èê

## ‹z

```bash
# Æ¹ÈnŸL
uv run pytest tests/

# ³üÉÕ©üŞÃÈ
uv run black src/ tests/

# LintÁ§Ã¯
uv run ruff check src/
```

## é¤»ó¹

MIT License