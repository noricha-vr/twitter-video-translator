# Twitter Video Translator ドキュメント

## 📚 ドキュメント一覧

### ユーザー向けドキュメント

- [README](../README.md) - プロジェクトの概要とクイックスタート
- [API設定ガイド](API_GUIDE.md) - APIキーの取得と設定方法
- [CHANGELOG](../CHANGELOG.md) - バージョン履歴と変更内容

### 開発者向けドキュメント

- [開発ガイド](DEVELOPMENT.md) - 開発環境の構築とコーディング規約
- [CLAUDE.md](../CLAUDE.md) - Claude AIアシスタント用の指示書

### 設計ドキュメント

- [処理フロー詳細](processing-flow.md) - URLから動画生成までの完全な処理フロー
- [TTSプロンプト生成設計](tts-prompt-generation-design.md) - 新しいプロンプト直接生成方式の設計
- [複数スレッド処理対応設計](concurrent_processing_design.md) - 並行処理を可能にするための設計
- [セッション管理移行プラン](migration_plan.md) - 既存コードの段階的な移行計画
- [音声処理アーキテクチャ](audio-processing-architecture.md) - 音声処理の詳細設計

## 🔗 関連リンク

### プロジェクト

- [GitHub リポジトリ](https://github.com/noricha-vr/twitter-video-translator)
- [Issues](https://github.com/noricha-vr/twitter-video-translator/issues)
- [Discussions](https://github.com/noricha-vr/twitter-video-translator/discussions)

### 外部リソース

- [Groq Console](https://console.groq.com/)
- [Google AI Studio](https://makersuite.google.com/)
- [Gemini Speech Generation Documentation](https://ai.google.dev/gemini-api/docs/speech-generation?hl=ja)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)

## 📖 ドキュメントの構成

```
docs/
├── index.md                            # このファイル
├── API_GUIDE.md                        # API設定の詳細ガイド
├── DEVELOPMENT.md                      # 開発者向けガイド
├── processing-flow.md                  # 処理フロー詳細
├── audio-processing-architecture.md    # 音声処理アーキテクチャ
├── concurrent_processing_design.md     # 複数スレッド処理設計
├── migration_plan.md                   # セッション管理移行計画
└── issue.md                           # 課題・改善要望
```

## 🤝 ドキュメントへの貢献

ドキュメントの改善提案やエラーの報告は、[GitHub Issues](https://github.com/noricha-vr/twitter-video-translator/issues)でお知らせください。
