# 開発ガイド

## 開発環境のセットアップ

### 前提条件

- Python 3.13以上
- FFmpeg
- Git
- uv (Pythonパッケージマネージャー)

### 環境構築

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/noricha-vr/twitter-video-translator.git
   cd twitter-video-translator
   ```

2. **開発用依存関係のインストール**
   ```bash
   # 開発用パッケージを含めてインストール
   uv sync --dev
   ```

3. **環境変数の設定**
   ```bash
   cp .env.example .env
   # .envファイルを編集してAPIキーを設定
   ```

4. **pre-commitフックのセットアップ**（推奨）
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## アーキテクチャ

### モジュール構成

```
twitter_video_translator/
├── cli.py              # CLIエントリーポイント
├── config.py           # 設定管理
├── services/           # コアサービス層
│   ├── downloader.py   # 動画ダウンロード（yt-dlp使用）
│   ├── transcriber.py  # 音声文字起こし（Groq API）
│   ├── translator.py   # テキスト翻訳（Gemini API）
│   ├── tts.py         # 音声生成（Gemini TTS）
│   └── video_composer.py # 動画合成（FFmpeg）
└── utils/             # ユーティリティ
    ├── logger.py      # ロギング設定
    └── subtitle.py    # 字幕生成
```

### データフロー

1. **動画ダウンロード**: URLから動画をダウンロード
2. **音声抽出**: FFmpegで動画から音声を抽出
3. **文字起こし**: Groq Whisper APIで音声をテキスト化
4. **翻訳**: Gemini APIで日本語に翻訳
5. **音声生成**: Gemini TTSで日本語音声を生成
6. **字幕生成**: タイムスタンプ付きSRTファイル作成
7. **動画合成**: FFmpegで字幕と音声を動画に合成

## コーディング規約

### スタイルガイド

- **フォーマッター**: Black（行長88文字）
- **Linter**: Ruff
- **型ヒント**: 必須（mypy準拠）
- **docstring**: Google Style

### コード例

```python
from typing import Optional, List
from pathlib import Path

class VideoProcessor:
    """動画処理クラス
    
    動画のダウンロード、処理、出力を管理します。
    
    Attributes:
        output_dir: 出力ディレクトリ
        temp_dir: 一時ファイルディレクトリ
    """
    
    def __init__(self, output_dir: Path, temp_dir: Path) -> None:
        """初期化
        
        Args:
            output_dir: 出力ディレクトリパス
            temp_dir: 一時ファイルディレクトリパス
        """
        self.output_dir = output_dir
        self.temp_dir = temp_dir
    
    def process(self, url: str) -> Optional[Path]:
        """動画を処理
        
        Args:
            url: 動画のURL
            
        Returns:
            処理済み動画のパス、失敗時はNone
            
        Raises:
            ValueError: 無効なURLの場合
        """
        # 実装
        pass
```

## テスト

### テストの実行

```bash
# 全テストを実行
uv run pytest

# 特定のテストファイルを実行
uv run pytest tests/test_downloader.py

# カバレッジレポート付き
uv run pytest --cov=src --cov-report=html

# 詳細出力
uv run pytest -vv

# 失敗したテストのみ再実行
uv run pytest --lf
```

### テストの書き方

```python
import pytest
from pathlib import Path
from twitter_video_translator.services.downloader import VideoDownloader

class TestVideoDownloader:
    """VideoDownloaderのテスト"""
    
    @pytest.fixture
    def downloader(self, tmp_path):
        """テスト用のダウンローダーインスタンス"""
        return VideoDownloader(temp_dir=tmp_path)
    
    def test_download_twitter_video(self, downloader, mocker):
        """Twitter動画のダウンロードテスト"""
        # yt-dlpをモック
        mock_ydl = mocker.patch("yt_dlp.YoutubeDL")
        
        # テスト実行
        result = downloader.download("https://x.com/test/status/123")
        
        # アサーション
        assert result is not None
        assert result.suffix == ".mp4"
        mock_ydl.assert_called_once()
```

## デバッグ

### ログレベルの設定

```bash
# 環境変数で設定
export LOG_LEVEL=DEBUG

# または.envファイルに追加
LOG_LEVEL=DEBUG
```

### デバッグモードでの実行

```python
# cli.pyにデバッグオプションを追加
@click.option("--debug", is_flag=True, help="デバッグモードで実行")
def main(url: str, debug: bool = False):
    if debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
```

### よくあるデバッグポイント

1. **API呼び出しエラー**
   - APIキーの確認
   - レート制限の確認
   - リクエストペイロードのログ出力

2. **FFmpegエラー**
   - FFmpegコマンドのログ出力
   - 中間ファイルの確認
   - コーデックの互換性

3. **メモリ問題**
   - 大きなファイルの分割処理
   - 一時ファイルの削除確認

## API仕様

### Groq API (Whisper)

```python
# 音声ファイルサイズ制限: 25MB
# 25MB以上の場合は分割処理が必要

segments = []
for chunk in audio_chunks:
    with open(chunk, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            language="en",
            response_format="verbose_json"
        )
    segments.extend(response.segments)
```

### Gemini API

```python
# テキスト翻訳
model = genai.GenerativeModel("gemini-1.5-flash-latest")
response = model.generate_content(
    f"Translate to Japanese: {text}",
    generation_config=genai.GenerationConfig(
        temperature=0.3,
        max_output_tokens=8192
    )
)

# 音声生成（TTS）
tts_model = genai.GenerativeModel("gemini-2.0-flash-exp")
audio_response = tts_model.generate_content(
    [japanese_text],
    generation_config=genai.GenerationConfig(
        response_modalities=["audio"],
        speech_config=SpeechConfig(voice_config=VoiceConfig(
            prebuilt_voice_config=PrebuiltVoiceConfig(
                voice_name="Aoede"
            )
        ))
    )
)
```

## リリース手順

### バージョニング

セマンティックバージョニング（SemVer）に従います：
- **MAJOR**: 互換性のない変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正

### リリースプロセス

1. **バージョン更新**
   ```bash
   # pyproject.tomlのversionを更新
   vim pyproject.toml
   ```

2. **CHANGELOG更新**
   ```bash
   # CHANGELOG.mdに変更内容を記載
   vim CHANGELOG.md
   ```

3. **テスト実行**
   ```bash
   uv run pytest
   uv run black --check src/ tests/
   uv run ruff check src/
   ```

4. **コミット&タグ**
   ```bash
   git add -A
   git commit -m "chore: release v0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

5. **GitHubリリース作成**
   - GitHubのReleasesページから新規リリース作成
   - CHANGELOGの内容をコピー
   - アセットは自動生成される

## トラブルシューティング

### 開発時の一般的な問題

1. **import エラー**
   ```bash
   # パッケージを再インストール
   uv pip install -e .
   ```

2. **型チェックエラー**
   ```bash
   # mypyで詳細確認
   uv run mypy src/ --show-error-codes
   ```

3. **テスト失敗**
   ```bash
   # 特定のテストをデバッグ
   uv run pytest tests/test_specific.py -vv --pdb
   ```

## 貢献ガイドライン

### Pull Requestの作成

1. フィーチャーブランチを作成
2. コードを実装
3. テストを追加
4. ドキュメントを更新
5. すべてのチェックをパス
6. PRを作成（テンプレートに従う）

### コードレビューのポイント

- [ ] テストが追加されているか
- [ ] 型ヒントが適切か
- [ ] エラーハンドリングが適切か
- [ ] ドキュメントが更新されているか
- [ ] パフォーマンスへの影響はないか

## 参考リンク

- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Groq API Reference](https://console.groq.com/docs)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Click Documentation](https://click.palletsprojects.com/)