# セッション管理移行プラン

## 概要
既存のコードをセッション管理に対応させるための段階的な移行プランです。

## 移行ステップ

### ステップ1: 最小限の変更で動作確認（互換性重視）

CLIクラスのみを修正し、他のサービスクラスはそのまま使用：

```python
# cli.py の修正例
from .services.session_manager import get_session_manager

class CLI:
    def __init__(self):
        # 既存のコード...
        self.session_manager = get_session_manager()
        
    def run(self, url: str, ...):
        """動画翻訳のメインエントリポイント"""
        # セッションコンテキストを使用
        with self.session_manager.session_context() as session:
            # 一時的に現在のtemp_dirをセッションディレクトリに変更
            original_temp_dir = config.temp_dir
            config.temp_dir = session.session_dir
            
            try:
                # 既存の処理をそのまま実行
                self._run_original(url, ...)
            finally:
                # temp_dirを元に戻す
                config.temp_dir = original_temp_dir
```

### ステップ2: 各サービスクラスの段階的な修正

#### 2.1 ダウンローダーの修正
```python
# downloader.py
def download_video(self, url: str, output_path: Optional[Path] = None) -> Tuple[Path, Dict]:
    """動画をダウンロード
    
    Args:
        url: 動画のURL
        output_path: 出力パス（オプション）
    """
    if output_path is None:
        # 後方互換性のため、デフォルトパスを使用
        output_path = config.temp_dir / "original_video.mp4"
    
    # 既存の処理...
```

#### 2.2 他のサービスも同様に修正
- AudioExtractor
- Transcriber
- Translator
- TTSService
- VideoComposer

### ステップ3: セッション対応の完全な実装

```python
# cli.py の最終形
class CLI:
    def run(self, url: str, ...):
        """動画翻訳のメインエントリポイント"""
        with self.session_manager.session_context() as session:
            # ダウンロード
            video_path, video_info = self.downloader.download_video(
                url, session.video_path
            )
            
            # 音声抽出
            audio_path = self.audio_extractor.extract_audio(
                video_path, session.audio_path
            )
            
            # 文字起こし
            transcription = self.transcriber.transcribe(audio_path)
            
            # 翻訳
            translations = self.translator.translate_segments(
                transcription.segments, target_language
            )
            
            # 字幕生成
            subtitles_path = session.subtitles_path
            transcription.to_srt(subtitles_path, translations)
            
            # TTS
            if use_tts:
                tts_result = self.tts.generate_speech(
                    transcription.segments,
                    translations,
                    audio_path,
                    session  # セッションを渡す
                )
            
            # 動画合成
            output_path = self.video_composer.compose(
                video_path,
                subtitles_path,
                session.translated_audio_path if use_tts else None,
                output_path,
                original_volume,
                japanese_volume
            )
            
            return output_path
```

## テスト戦略

### 1. 単体テスト
```python
def test_session_isolation():
    """セッション間のファイル分離をテスト"""
    manager = SessionManager()
    
    with manager.session_context() as session1:
        file1 = session1.get_path("test.txt")
        file1.write_text("session1")
        
        with manager.session_context() as session2:
            file2 = session2.get_path("test.txt")
            file2.write_text("session2")
            
            # ファイルが別々であることを確認
            assert file1 != file2
            assert file1.read_text() == "session1"
            assert file2.read_text() == "session2"
```

### 2. 統合テスト
```python
def test_concurrent_video_processing():
    """複数の動画を同時に処理"""
    urls = [
        "https://example.com/video1",
        "https://example.com/video2",
        "https://example.com/video3"
    ]
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for url in urls:
            future = executor.submit(process_video, url)
            futures.append(future)
        
        results = [f.result() for f in futures]
        assert len(results) == 3
```

## 移行スケジュール

### フェーズ1（1週間）
- [ ] SessionManagerクラスの実装
- [ ] CLIクラスの最小限の修正
- [ ] 基本的な動作確認

### フェーズ2（1週間）
- [ ] 各サービスクラスの修正
- [ ] セッション対応のテスト実装
- [ ] エラーハンドリングの強化

### フェーズ3（オプション）
- [ ] 非同期処理の実装
- [ ] バッチ処理APIの実装
- [ ] パフォーマンステスト

## リスクと対策

### リスク1: 既存機能への影響
**対策**: 段階的な移行と十分なテストカバレッジ

### リスク2: パフォーマンスの低下
**対策**: ディスク I/O の最適化、必要に応じてメモリキャッシュの導入

### リスク3: ディスク容量の枯渇
**対策**: 自動クリーンアップ機能の実装、モニタリングの追加

## まとめ

この移行プランに従うことで、既存の機能を維持しながら、段階的に複数スレッド処理に対応できるようになります。最初は最小限の変更から始め、徐々に完全なセッション管理システムに移行することで、リスクを最小限に抑えることができます。