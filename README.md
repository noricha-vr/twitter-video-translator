# Twitter Video Translator

Twitter/X およびYouTubeの動画を自動的に日本語に翻訳し、字幕と音声を追加するツール

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎥 概要

このツールは、Twitter/X およびYouTubeの動画を自動的にダウンロードし、音声を文字起こしして日本語に翻訳、字幕と日本語音声を追加した動画を生成します。

### 主な機能

- 🔽 **動画ダウンロード**: Twitter/X およびYouTubeのURLから動画を自動ダウンロード
- 🎤 **音声文字起こし**: Groq Whisper APIを使用した高精度な文字起こし
- 🌐 **自動翻訳**: Google Gemini APIによる自然な日本語翻訳
- 🗣️ **音声生成**: gTTSによる日本語音声の生成
- 📝 **字幕生成**: タイムスタンプ付きのSRT字幕ファイル生成
- 🎬 **動画合成**: FFmpegを使用した字幕・音声の合成
- 🎛️ **音声ミキシング**: 原音声と日本語音声の音量を個別調整可能

## 📋 必要な環境

- Python 3.13以上
- [FFmpeg](https://ffmpeg.org/)（システムにインストール済み）
- [uv](https://github.com/astral-sh/uv)（Pythonパッケージマネージャー）
- Groq API キー（[取得はこちら](https://console.groq.com/)）
- Google Gemini API キー（[取得はこちら](https://makersuite.google.com/app/apikey)）

## 🚀 インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/noricha-vr/twitter-video-translator.git
cd twitter-video-translator
```

### 2. 依存関係のインストール

```bash
# uvがインストールされていない場合
pip install uv

# 依存関係をインストール
uv sync

# パッケージをインストール（オプション）
uv pip install .
```

### 3. 環境変数の設定

`.env` ファイルを作成し、APIキーを設定：

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## 💻 使い方

### 基本的な使用方法

#### 開発環境での実行

```bash
# Twitter/Xの動画を翻訳
uv run python main.py https://x.com/user/status/123456789

# YouTubeの動画を翻訳
uv run python main.py https://www.youtube.com/watch?v=VIDEO_ID
```

#### インストール後の実行（推奨）

```bash
# パッケージをインストール後
video-translator https://x.com/user/status/123456789

# uvを経由する場合
uv run video-translator https://x.com/user/status/123456789
```

### オプション

```bash
# 字幕のみ（音声生成をスキップ）
video-translator https://x.com/user/status/123456789 --no-tts

# 出力ファイルを指定
video-translator https://x.com/user/status/123456789 -o my_video.mp4

# 音量調整オプション（デフォルト: 原音声15%、日本語音声+80%）
video-translator https://x.com/user/status/123456789 --original-volume 0.2 --japanese-volume 2.0

# ヘルプの表示
video-translator --help
```

### 使用例

```bash
# Twitter動画URLの例
video-translator "https://x.com/yuriyurii_329/status/1927560473450561910"

# YouTube動画URLの例
video-translator "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# YouTubeショート動画URLの例  
video-translator "https://youtube.com/shorts/VIDEO_ID"

# 原音声を少し大きくし、日本語音声を控えめにする例
video-translator "https://x.com/user/status/123456789" --original-volume 0.3 --japanese-volume 1.5

# 原音声を消し、日本語音声のみにする例
video-translator "https://x.com/user/status/123456789" --original-volume 0 --japanese-volume 2.0
```

### 音声ミキシングと音量調整

このツールは、原音声と日本語音声を同時に再生する音声ミキシング機能を提供します。両方の音声の音量を個別に調整できるため、最適なバランスを設定できます。

#### 音量調整パラメータ

- `--original-volume`: 原音声の音量倍率（デフォルト: 0.15 = 15%）
  - 0.0: 原音声を完全にミュート
  - 1.0: 原音声を元の音量で再生
  - 0.1〜0.3: 背景音として原音声を残す（推奨）

- `--japanese-volume`: 日本語音声の音量倍率（デフォルト: 1.8 = +80%）
  - 1.0: 生成された音声をそのまま再生
  - 1.5〜2.0: 日本語音声を強調（推奨）
  - 2.0以上: より大きく日本語音声を再生

#### 使用シナリオ例

1. **標準的な使用（デフォルト設定）**
   ```bash
   video-translator "動画URL"
   # 原音声15%、日本語音声+80%で自動ミキシング
   ```

2. **原音声を背景に残しつつ日本語を強調**
   ```bash
   video-translator "動画URL" --original-volume 0.2 --japanese-volume 2.0
   ```

3. **日本語音声のみ（吹き替えモード）**
   ```bash
   video-translator "動画URL" --original-volume 0 --japanese-volume 1.5
   ```

4. **原音声を重視（字幕付き学習モード）**
   ```bash
   video-translator "動画URL" --original-volume 0.8 --japanese-volume 1.0
   ```

## 📁 ディレクトリ構造

```
twitter-video-translator/
├── src/
│   └── twitter_video_translator/
│       ├── services/          # 各種サービス
│       │   ├── downloader.py  # 動画ダウンロード
│       │   ├── transcriber.py # 音声文字起こし
│       │   ├── translator.py  # テキスト翻訳
│       │   ├── tts.py        # 音声生成
│       │   └── video_composer.py # 動画合成
│       ├── utils/            # ユーティリティ
│       │   └── subtitle.py   # 字幕生成
│       ├── config.py         # 設定管理
│       └── cli.py           # CLIインターフェース
├── tests/                   # テストコード
├── scripts/                 # 開発用スクリプト
├── temp/                    # 一時ファイル（自動生成）
├── output/                  # 出力ファイル（自動生成）
└── main.py                  # エントリーポイント
```

## 🔧 開発

### テストの実行

```bash
# すべてのテストを実行
uv run pytest tests/ -v

# カバレッジ付きでテスト
uv run pytest tests/ --cov=src
```

### コード品質チェック

```bash
# コードフォーマット
uv run black src/ tests/

# Lintチェック
uv run ruff check src/

# 自動修正
uv run ruff check src/ --fix
```

### ローカルテスト

```bash
# テスト用動画の生成
uv run python scripts/create_test_video.py

# ローカル動画でテスト
uv run python scripts/test_local_video.py
```

## ⚙️ 技術仕様

### API制限への対応

- **Groq API**: 25MB以上の音声ファイルは5分ごとに自動分割
- **Gemini API**: レート制限を考慮して1秒の遅延を追加

### 対応フォーマット

- **入力**: Twitter/X およびYouTubeの動画（mp4, webm, mkv等）
- **出力**: MP4形式（H.264ビデオ、AAC音声）
- **字幕**: SRT形式

## 🤝 コントリビューション

プルリクエストを歓迎します！大きな変更を行う場合は、まずissueを作成して変更内容について議論してください。

1. プロジェクトをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。

## 🙏 謝辞

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 動画ダウンロード
- [Groq](https://groq.com/) - 高速な音声文字起こし
- [Google Gemini](https://deepmind.google/technologies/gemini/) - 自然な翻訳
- [gTTS](https://github.com/pndurette/gTTS) - 音声生成
- [FFmpeg](https://ffmpeg.org/) - 動画処理

## 📧 お問い合わせ

質問や提案がある場合は、[Issues](https://github.com/noricha-vr/twitter-video-translator/issues)でお知らせください。