# Twitter Video Translator 🎬

Twitter/X およびYouTubeの動画を自動的に日本語に翻訳し、字幕と音声を追加する強力なツール

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎥 概要

このツールは、Twitter/X およびYouTubeの動画を自動的にダウンロードし、音声を文字起こしして日本語に翻訳、字幕と日本語音声を追加した動画を生成します。原音声と日本語音声のミキシング機能により、学習用途から完全吹き替えまで幅広い用途に対応します。

### ✨ 主な機能

- 🔽 **動画ダウンロード**: Twitter/X およびYouTubeのURLから動画を自動ダウンロード
- 🎤 **音声文字起こし**: Groq Whisper APIを使用した高精度な文字起こし
- 🌐 **自動翻訳**: Google Gemini APIによる自然な日本語翻訳
- 🗣️ **音声生成**: Google Gemini Flash 2.5 TTSによる高品質な日本語音声生成
- 📝 **字幕生成**: タイムスタンプ付きのSRT字幕ファイル生成
- 🎬 **動画合成**: FFmpegを使用した字幕・音声の合成
- 🎛️ **音声ミキシング**: 原音声と日本語音声の音量を個別調整可能

## 📋 必要な環境

### システム要件
- Python 3.13以上
- [FFmpeg](https://ffmpeg.org/)（システムにインストール済み）
- macOS、Linux、またはWindows

### 必要なAPIキー
- **Groq API キー**: [Groq Console](https://console.groq.com/)から取得
- **Google Gemini API キー**: [Google AI Studio](https://makersuite.google.com/app/apikey)から取得

## 🚀 クイックスタート

### 1. インストール

```bash
# リポジトリをクローン
git clone https://github.com/noricha-vr/twitter-video-translator.git
cd twitter-video-translator

# uvをインストール（未インストールの場合）
pip install uv

# 依存関係をインストール
uv sync

# パッケージをインストール（推奨）
uv pip install .
```

### 2. 環境設定

`.env` ファイルを作成し、APIキーを設定：

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. 使用開始

```bash
# Twitter/Xの動画を翻訳
video-translator https://x.com/user/status/123456789

# YouTubeの動画を翻訳
video-translator https://www.youtube.com/watch?v=VIDEO_ID
```

## 💻 使い方

### 基本コマンド

```bash
# インストール後の実行（推奨）
video-translator <URL> [オプション]

# 開発環境での実行
uv run python main.py <URL> [オプション]
```

### コマンドラインオプション

| オプション | 説明 | デフォルト |
|---------|------|----------|
| `-o, --output` | 出力ファイルパス | 自動生成 |
| `--no-tts` | 音声生成をスキップ（字幕のみ） | False |
| `--original-volume` | 原音声の音量（0.0-1.0） | 0.15 |
| `--japanese-volume` | 日本語音声の音量倍率 | 1.8 |
| `--help` | ヘルプを表示 | - |

### 📚 使用例

#### 基本的な使用

```bash
# Twitter動画を翻訳
video-translator "https://x.com/elonmusk/status/1234567890"

# YouTube動画を翻訳
video-translator "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# YouTubeショートを翻訳
video-translator "https://youtube.com/shorts/ABC123"
```

#### 音声ミキシングの調整

```bash
# 原音声を背景に残す（デフォルト）
video-translator <URL> --original-volume 0.15 --japanese-volume 1.8

# 日本語音声のみ（完全吹き替え）
video-translator <URL> --original-volume 0 --japanese-volume 2.0

# 原音声重視（学習モード）
video-translator <URL> --original-volume 0.8 --japanese-volume 1.0

# カスタム出力ファイル名
video-translator <URL> -o translated_video.mp4
```

### 🎛️ 音声ミキシング機能

#### 音量パラメータ詳細

**`--original-volume`** (0.0 - 1.0)
- `0.0`: 原音声を完全にミュート
- `0.15`: デフォルト設定（背景音として残す）
- `1.0`: 原音声を元の音量で再生

**`--japanese-volume`** (0.5 - 3.0)
- `1.0`: 生成音声をそのまま再生
- `1.8`: デフォルト設定（+80%増幅）
- `2.0+`: より大きく日本語音声を再生

#### 推奨設定

| 用途 | original-volume | japanese-volume |
|-----|----------------|-----------------|
| 標準視聴 | 0.15 | 1.8 |
| 完全吹き替え | 0.0 | 2.0 |
| 言語学習 | 0.6 | 1.2 |
| 背景音重視 | 0.8 | 1.0 |

## 🛠️ トラブルシューティング

### よくある問題と解決方法

#### FFmpegが見つからない

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# FFmpeg公式サイトからダウンロードしてPATHに追加
```

#### APIキーエラー

```bash
# .envファイルが正しく設定されているか確認
cat .env

# 環境変数を再読み込み
source .env
```

#### メモリ不足エラー

長い動画の処理時にメモリ不足が発生する場合：
- 動画を短いセグメントに分割して処理
- システムのスワップ領域を増やす

#### 音声同期の問題

音声と字幕がずれる場合：
- `--no-tts`オプションで字幕のみ生成して確認
- FFmpegのバージョンを最新に更新

## 📁 プロジェクト構造

```
twitter-video-translator/
├── src/
│   └── twitter_video_translator/
│       ├── __init__.py
│       ├── cli.py                # CLIエントリーポイント
│       ├── config.py             # 設定管理
│       ├── services/             # コアサービス
│       │   ├── __init__.py
│       │   ├── downloader.py    # 動画ダウンロード
│       │   ├── transcriber.py   # 音声文字起こし
│       │   ├── translator.py    # テキスト翻訳
│       │   ├── tts.py          # 音声生成
│       │   └── video_composer.py # 動画合成
│       └── utils/               # ユーティリティ
│           ├── __init__.py
│           ├── logger.py        # ロギング
│           └── subtitle.py      # 字幕生成
├── tests/                       # テストコード
├── scripts/                     # 開発用スクリプト
├── docs/                        # ドキュメント
├── .env.example                 # 環境変数サンプル
├── pyproject.toml              # プロジェクト設定
├── README.md                   # このファイル
└── LICENSE                     # ライセンス
```

## 🔧 開発者向け情報

### 開発環境のセットアップ

```bash
# 開発用依存関係をインストール
uv sync --dev

# pre-commitフックをセットアップ（オプション）
pre-commit install
```

### テストの実行

```bash
# 全テストを実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=src --cov-report=html

# 特定のテストを実行
uv run pytest tests/test_downloader.py -v
```

### コード品質

```bash
# フォーマット
uv run black src/ tests/

# Lintチェック
uv run ruff check src/

# 型チェック
uv run mypy src/
```

### リリース手順

1. バージョンを更新: `pyproject.toml`
2. CHANGELOGを更新
3. タグを作成: `git tag v0.2.0`
4. プッシュ: `git push origin v0.2.0`

## 🤝 コントリビューション

プルリクエストを歓迎します！貢献方法：

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### コーディング規約

- [Black](https://github.com/psf/black)でフォーマット
- [Ruff](https://github.com/charliermarsh/ruff)でLintチェック
- 型ヒントを使用
- テストを書く
- ドキュメントを更新

## 📄 ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

## 🙏 謝辞

このプロジェクトは以下の素晴らしいツールとサービスを使用しています：

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 動画ダウンロード
- [Groq](https://groq.com/) - 高速音声文字起こし
- [Google Gemini](https://deepmind.google/technologies/gemini/) - 翻訳と音声生成
- [FFmpeg](https://ffmpeg.org/) - 動画処理
- [Rich](https://github.com/Textualize/rich) - 美しいCLI出力
- [Click](https://click.palletsprojects.com/) - CLIフレームワーク

## 📞 サポート

- **バグ報告**: [GitHub Issues](https://github.com/noricha-vr/twitter-video-translator/issues)
- **機能リクエスト**: [GitHub Discussions](https://github.com/noricha-vr/twitter-video-translator/discussions)
- **質問**: [GitHub Discussions](https://github.com/noricha-vr/twitter-video-translator/discussions)

---

Made with ❤️ by [noricha-vr](https://github.com/noricha-vr)