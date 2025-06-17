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

# サポートされている言語
SUPPORTED_LANGUAGES = [
    "Japanese",
    "English", 
    "Chinese",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Russian",
    "Korean",
    "Arabic",
    "Hindi",
    "Turkish",
    "Polish",
    "Dutch",
    "Swedish",
    "Danish",
    "Norwegian",
    "Finnish",
    "Czech",
    "Greek",
    "Hebrew",
    "Indonesian",
    "Malay",
    "Thai",
    "Vietnamese",
    "Filipino",
    "Bengali",
    "Tamil",
    "Telugu",
    "Urdu",
]