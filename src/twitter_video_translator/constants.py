"""定数定義"""

# Gemini TTS利用可能な音声一覧
AVAILABLE_VOICES = {
    # Voice Name: Description
    "Zephyr": "Bright",
    "Puck": "Upbeat",
    "Charon": "Informative",
    "Kore": "Firm",
    "Fenrir": "Excitable",
    "Leda": "Youthful",
    "Orus": "Firm",
    "Aoede": "Breezy",
    "Callirrhoe": "Easy-going",
    "Autonoe": "Bright",
    "Enceladus": "Breathy",
    "Iapetus": "Clear",
    "Umbriel": "Easy-going",
    "Algieba": "Smooth",
    "Despina": "Smooth",
    "Erinome": "Clear",
    "Algenib": "Gravelly",
    "Rasalgethi": "Informative",
    "Laomedeia": "Upbeat",
    "Achernar": "Soft",
    "Alnilam": "Firm",
    "Schedar": "Even",
    "Gacrux": "Mature",
    "Pulcherrima": "Forward",
    "Achird": "Friendly",
    "Zubenelgenubi": "Casual",
    "Vindemiatrix": "Gentle",
    "Sadachbia": "Lively",
    "Sadaltager": "Knowledgeable",
    "Sulafat": "Warm",
}

# 日本語音声として推奨される音声
RECOMMENDED_JAPANESE_VOICES = [
    "Aoede",  # Breezy - デフォルト
    "Kore",   # Firm
    "Schedar", # Even
    "Vindemiatrix", # Gentle
    "Sulafat", # Warm
]

# TTSがサポートしている言語（24言語）
TTS_SUPPORTED_LANGUAGES = {
    # Language: (BCP-47 Code, Display Name)
    "Arabic": ("ar-EG", "Arabic (Egyptian)"),
    "Bengali": ("bn-BD", "Bengali (Bangladesh)"),
    "Dutch": ("nl-NL", "Dutch (Netherlands)"),
    "English": ("en-US", "English (US)"),
    "English_India": ("en-IN", "English (India)"),
    "French": ("fr-FR", "French (France)"),
    "German": ("de-DE", "German (Germany)"),
    "Hindi": ("hi-IN", "Hindi (India)"),
    "Indonesian": ("id-ID", "Indonesian (Indonesia)"),
    "Italian": ("it-IT", "Italian (Italy)"),
    "Japanese": ("ja-JP", "Japanese (Japan)"),
    "Korean": ("ko-KR", "Korean (Korea)"),
    "Marathi": ("mr-IN", "Marathi (India)"),
    "Polish": ("pl-PL", "Polish (Poland)"),
    "Portuguese": ("pt-BR", "Portuguese (Brazil)"),
    "Romanian": ("ro-RO", "Romanian (Romania)"),
    "Russian": ("ru-RU", "Russian (Russia)"),
    "Spanish": ("es-US", "Spanish (US)"),
    "Tamil": ("ta-IN", "Tamil (India)"),
    "Telugu": ("te-IN", "Telugu (India)"),
    "Thai": ("th-TH", "Thai (Thailand)"),
    "Turkish": ("tr-TR", "Turkish (Turkey)"),
    "Ukrainian": ("uk-UA", "Ukrainian (Ukraine)"),
    "Vietnamese": ("vi-VN", "Vietnamese (Vietnam)"),
}

# サポートされている言語（TTSがサポートする言語のみ）
SUPPORTED_LANGUAGES = list(TTS_SUPPORTED_LANGUAGES.keys())

# 翻訳のみサポートされている言語（TTSは非対応）
TRANSLATION_ONLY_LANGUAGES = [
    "Chinese",  # 中国語は翻訳のみ対応
]

# 翻訳でサポートされているすべての言語
ALL_SUPPORTED_LANGUAGES = SUPPORTED_LANGUAGES + TRANSLATION_ONLY_LANGUAGES

# 言語コードマッピング（ファイル名用）
LANGUAGE_CODES = {
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese": "zh",
    "Dutch": "nl",
    "English": "en",
    "English_India": "en-IN",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Marathi": "mr",
    "Polish": "pl",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Russian": "ru",
    "Spanish": "es",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Vietnamese": "vi",
}