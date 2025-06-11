
# Twitter video translator

Pythonのアプリを作成してください。

ローカルで動くアプリを想定しています。

Twitterの海外の動画を日本語に翻訳、文字起こし、字幕をつける、日本語の音声をつける、動画としてエンコードするアプリです

## 入力
- TwitterのポストURLをユーザーは入力します。

※ 動画が含まれていることが条件(バリデーション)

## 出力
- 日本語音声字幕付きの動画

## 要件
- 音声認識はGroq API Whisper https://console.groq.com/docs/speech-to-text
- TTSはGemini Flash 2.5 https://googleapis.github.io/python-genai/

## 条件
- uvを使うこと
- ffmpegを使うこと
