# 複数スレッドで処理できるようにする

## 問題
今は文字起こしされたファイルや音声ファイルがtempに保存される
リクエスト単位でtempに保存されるように変更する

## 現状の問題点（実測結果）
2つのリクエストを同時実行した結果、以下の干渉が確認されました：

1. **ファイル名競合によるエラー**
   - `FileNotFoundError: 'temp/original_video.mp4.part' -> 'temp/original_video.mp4'`
   - 一方のスレッドがダウンロード中に、他方がファイルを削除

2. **tempディレクトリの競合**
   - 各リクエスト開始時に`temp`ディレクトリ全体をクリア
   - 実行中の他リクエストのファイルも削除される

3. **データの混在**
   - セグメントファイル（segment_0000.wav等）が混在
   - 字幕ファイル（subtitles.srt）の上書き

詳細な分析結果: [concurrent_issue_analysis.md](concurrent_issue_analysis.md)

## 解決策
セッション管理システムの実装により、各リクエストに独立したディレクトリを割り当てる

- 設計書: [concurrent_processing_design.md](concurrent_processing_design.md)
- 実装: [session_manager.py](../src/twitter_video_translator/services/session_manager.py)
- 移行計画: [migration_plan.md](migration_plan.md)
