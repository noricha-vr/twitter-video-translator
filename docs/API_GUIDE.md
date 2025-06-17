# API設定ガイド

このガイドでは、Twitter Video Translatorで使用する各APIの取得方法と設定について説明します。

## 必要なAPI

1. **Groq API** - 音声文字起こし（Whisper）
2. **Google Gemini API** - 翻訳と音声生成

## Groq API

### APIキーの取得

1. [Groq Console](https://console.groq.com/)にアクセス
2. アカウントを作成（無料）
3. ダッシュボードから「API Keys」セクションへ移動
4. 「Create API Key」をクリック
5. キーをコピーして`.env`ファイルに設定

### 料金体系

- **無料枠**: 
  - 1分あたり30リクエストまで
  - 1日あたり14,400リクエストまで
- **有料プラン**: 使用量に応じた従量課金

### 使用上の注意

- 音声ファイルは25MB以下に制限
- 25MB以上のファイルは自動的に分割処理されます
- サポート言語: 英語、日本語、中国語など98言語

## Google Gemini API

### APIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. Googleアカウントでログイン
3. 「Get API key」をクリック
4. 新しいプロジェクトを作成または既存のプロジェクトを選択
5. APIキーをコピーして`.env`ファイルに設定

### 料金体系

**Gemini 1.5 Flash** (翻訳用)
- **無料枠**: 
  - 1分あたり15リクエスト
  - 1日あたり1,500リクエスト
  - 100万トークン/分まで
- **有料**: $0.075 / 100万トークン

**Gemini 2.0 Flash** (音声生成用)
- **無料枠**: 
  - 1分あたり10リクエスト
  - 1日あたり1,000リクエスト
- **有料**: 使用量に応じた従量課金

### 使用上の注意

- レート制限を避けるため、リクエスト間に1秒の遅延を設定
- 長いテキストは自動的に分割処理
- 音声生成は日本語の女性音声（Aoede）を使用

## 環境変数の設定

### .envファイルの作成

```bash
# プロジェクトルートで実行
cp .env.example .env
```

### .envファイルの編集

```env
# Groq API キー
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx

# Google Gemini API キー
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxx

# オプション設定
LOG_LEVEL=INFO
OUTPUT_DIR=./output
TEMP_DIR=./temp
```

## APIの動作確認

### Groq APIのテスト

```python
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# APIキーの検証
try:
    # 小さなテスト音声で確認
    with open("test_audio.mp3", "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f
        )
    print("Groq API: OK")
except Exception as e:
    print(f"Groq API Error: {e}")
```

### Gemini APIのテスト

```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 翻訳機能のテスト
try:
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    response = model.generate_content("Hello, world!")
    print("Gemini Translation API: OK")
except Exception as e:
    print(f"Gemini API Error: {e}")

# TTS機能のテスト
try:
    tts_model = genai.GenerativeModel("gemini-2.0-flash-exp")
    # TTSテストコード
    print("Gemini TTS API: OK")
except Exception as e:
    print(f"Gemini TTS Error: {e}")
```

## トラブルシューティング

### よくあるエラーと対処法

#### 1. API認証エラー

```
Error: Invalid API key
```

**対処法**:
- APIキーが正しくコピーされているか確認
- `.env`ファイルが正しい場所にあるか確認
- 環境変数が読み込まれているか確認

#### 2. レート制限エラー

```
Error: Rate limit exceeded
```

**対処法**:
- 無料枠の制限を確認
- リクエスト間隔を調整
- 必要に応じて有料プランへアップグレード

#### 3. ファイルサイズエラー

```
Error: File too large (max 25MB)
```

**対処法**:
- 自動分割処理が有効になっているか確認
- 手動で音声ファイルを分割
- 動画の長さを短くする

### API使用状況の確認

#### Groq Console

1. [Groq Console](https://console.groq.com/)にログイン
2. 「Usage」タブで使用状況を確認
3. 日別・月別の使用量を確認

#### Google Cloud Console

1. [Google Cloud Console](https://console.cloud.google.com/)にログイン
2. 「APIs & Services」→「Credentials」
3. 使用しているAPIキーの統計情報を確認

## ベストプラクティス

### 1. エラーハンドリング

```python
import time
from typing import Optional

def call_api_with_retry(func, max_retries: int = 3) -> Optional[Any]:
    """APIコールをリトライ付きで実行"""
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
            else:
                raise
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
```

### 2. コスト最適化

- 不要なAPI呼び出しを避ける
- キャッシュを活用する
- バッチ処理を検討する
- 適切なモデルを選択する

### 3. セキュリティ

- APIキーをコードに直接記載しない
- `.env`ファイルを`.gitignore`に追加
- 本番環境では環境変数を使用
- APIキーを定期的に更新

## 関連リンク

- [Groq Documentation](https://console.groq.com/docs)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Google AI Studio](https://makersuite.google.com/)
- [料金計算ツール](https://ai.google.dev/pricing)