# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 音声ミキシング機能のドキュメント追加
- CLIに音声ボリューム調整オプション（`--original-volume`、`--japanese-volume`）
- エントリーポイントの標準化（`video-translator`コマンド）
- 包括的なドキュメント（トラブルシューティング、開発ガイド、APIガイド）
- `.env.example`ファイル

### Changed
- README.mdを全面的に改訂し、より詳細で使いやすい内容に更新
- `pyproject.toml`に`[project.scripts]`セクションを追加
- 音声ミキシング機能を改善（個別ボリューム調整可能）

### Fixed
- 音声ミキシングのデフォルト値を最適化

## [0.2.0] - 2024-12-26

### Added
- YouTubeサポートを追加
- ロギング機能を追加（Rich ConsoleとPythonロギングの統合）
- バージョン管理の改善
- CLIクラス名を`TwitterVideoTranslatorCLI`から`VideoTranslatorCLI`に変更

### Changed
- より汎用的なビデオ翻訳ツールに進化
- エラーハンドリングの改善

## [0.1.0] - 2024-12-25

### Added
- 初回リリース
- Twitter/X動画のダウンロード機能
- Groq Whisper APIによる音声文字起こし
- Google Gemini APIによる日本語翻訳
- Google Gemini Flash 2.5 TTSによる日本語音声生成
- FFmpegによる動画合成
- SRT字幕生成機能
- 基本的なCLIインターフェース

[Unreleased]: https://github.com/noricha-vr/twitter-video-translator/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/noricha-vr/twitter-video-translator/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/noricha-vr/twitter-video-translator/releases/tag/v0.1.0