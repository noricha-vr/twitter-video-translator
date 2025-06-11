# Twitter Video Translator

Twitter�;��,�k�3WWUh����Y����

## _�

- Twitter/X n�;�������
- ��WwSWGroq Whisper API	
- ƭ�Ȓ�,�k�3Google Gemini	
- �,���gTTS	
- WU�M�;�FFmpeg	

## Łj�n

- Python 3.13+
- FFmpeg����k�����	
- Groq API ��
- Google Gemini API ��

## �����

```bash
# �ݸ�꒯���
git clone https://github.com/yourusername/twitter-video-translator.git
cd twitter-video-translator

# uv�(Wf�X������
uv sync
```

## -�

`.env` ա��\WAPI���-�

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## D�

```bash
# �,�j(��WU��	
uv run python main.py https://twitter.com/user/status/123456789

# WUn�������	
uv run python main.py https://twitter.com/user/status/123456789 --no-tts

# ��ա���
uv run python main.py https://twitter.com/user/status/123456789 -o my_video.mp4

# ���
uv run python main.py --help
```

## ��

- �թ��n��H: `./output/translated_video.mp4`
- \mա��: `./temp/` ǣ���

## �z

```bash
# ƹ�n�L
uv run pytest tests/

# ���թ����
uv run black src/ tests/

# Lint��ï
uv run ruff check src/
```

## 餻�

MIT License