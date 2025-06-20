# 複数スレッド処理対応設計書

## 概要
現在、すべての一時ファイルが単一の`temp`ディレクトリに保存されているため、複数のリクエストを同時に処理できません。本設計では、リクエスト単位でディレクトリを分離し、複数スレッドでの同時処理を可能にします。

## 現状の問題点

1. **ファイル競合**: 複数リクエストが同じファイル名を使用
2. **データ混在**: 異なるリクエストのデータが混在する可能性
3. **クリーンアップ**: 一括削除により他のリクエストのファイルも削除される
4. **スケーラビリティ**: 単一プロセスでしか処理できない

## 提案する解決策

### 1. リクエスト単位のディレクトリ管理

```python
# 現在の構造
temp/
├── original_video.mp4
├── audio.wav
├── subtitles.srt
└── translated_audio.wav

# 新しい構造
temp/
├── session_20250118_123456_abc123/
│   ├── original_video.mp4
│   ├── audio.wav
│   ├── subtitles.srt
│   └── translated_audio.wav
└── session_20250118_123457_def456/
    ├── original_video.mp4
    ├── audio.wav
    ├── subtitles.srt
    └── translated_audio.wav
```

### 2. セッション管理クラスの実装

```python
from pathlib import Path
from datetime import datetime
import uuid
import shutil
from contextlib import contextmanager
import threading
from typing import Optional

class SessionManager:
    """リクエスト単位のセッション管理"""
    
    def __init__(self, base_temp_dir: Path):
        self.base_temp_dir = base_temp_dir
        self._lock = threading.Lock()
        
    def create_session(self) -> str:
        """新しいセッションIDを生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:6]
        return f"session_{timestamp}_{unique_id}"
    
    @contextmanager
    def session_context(self, session_id: Optional[str] = None):
        """セッションコンテキストマネージャー"""
        if session_id is None:
            session_id = self.create_session()
            
        session_dir = self.base_temp_dir / session_id
        
        try:
            # セッションディレクトリ作成
            with self._lock:
                session_dir.mkdir(parents=True, exist_ok=True)
            
            yield SessionContext(session_id, session_dir)
            
        finally:
            # クリーンアップ
            if session_dir.exists():
                shutil.rmtree(session_dir)

class SessionContext:
    """セッションコンテキスト"""
    
    def __init__(self, session_id: str, session_dir: Path):
        self.session_id = session_id
        self.session_dir = session_dir
        
    def get_path(self, filename: str) -> Path:
        """セッション内のファイルパスを取得"""
        return self.session_dir / filename
```

### 3. 既存コードの修正案

#### 3.1 CLIクラスの修正

```python
class CLI:
    def __init__(self):
        # ... 既存のコード ...
        self.session_manager = SessionManager(config.temp_dir)
    
    def run(self, url: str, output_path: Optional[Path] = None, ...):
        """動画翻訳のメインエントリポイント"""
        with self.session_manager.session_context() as session:
            # すべての処理をセッションコンテキスト内で実行
            self._process_video(session, url, output_path, ...)
    
    def _process_video(self, session: SessionContext, url: str, ...):
        """セッション内で動画を処理"""
        # ダウンロード
        video_path = session.get_path("original_video.mp4")
        self.downloader.download_video(url, video_path)
        
        # 音声抽出
        audio_path = session.get_path("audio.wav")
        self.audio_extractor.extract_audio(video_path, audio_path)
        
        # ... 以降の処理も同様にセッションパスを使用
```

#### 3.2 各サービスクラスの修正

```python
class VideoDownloader:
    def download_video(self, url: str, output_path: Path) -> Tuple[Path, Dict]:
        """指定されたパスに動画をダウンロード"""
        # output_pathを使用してダウンロード
        # ...

class AudioExtractor:
    def extract_audio(self, video_path: Path, audio_path: Path) -> Path:
        """指定されたパスに音声を抽出"""
        # audio_pathを使用して抽出
        # ...
```

### 4. 並行処理の実装

#### 4.1 非同期処理対応

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncCLI:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.session_manager = SessionManager(config.temp_dir)
        
    async def process_multiple_videos(self, urls: List[str]):
        """複数の動画を並行処理"""
        tasks = []
        for url in urls:
            task = asyncio.create_task(self.process_video_async(url))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def process_video_async(self, url: str):
        """非同期で動画を処理"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._process_video_sync,
            url
        )
```

#### 4.2 バッチ処理API

```python
from typing import List, Dict
import queue
import threading

class BatchProcessor:
    """バッチ処理クラス"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.queue = queue.Queue()
        self.results = {}
        self.session_manager = SessionManager(config.temp_dir)
        
    def add_job(self, job_id: str, url: str, options: Dict):
        """ジョブをキューに追加"""
        self.queue.put((job_id, url, options))
        
    def process_batch(self):
        """バッチ処理を実行"""
        threads = []
        
        for _ in range(self.max_workers):
            thread = threading.Thread(target=self._worker)
            thread.start()
            threads.append(thread)
        
        # すべてのワーカーの完了を待つ
        for thread in threads:
            thread.join()
            
    def _worker(self):
        """ワーカースレッド"""
        while True:
            try:
                job_id, url, options = self.queue.get(timeout=1)
                result = self._process_single_job(job_id, url, options)
                self.results[job_id] = result
                self.queue.task_done()
            except queue.Empty:
                break
```

### 5. 設定の追加

```python
# config.py
class Settings(BaseSettings):
    # ... 既存の設定 ...
    
    # 並行処理設定
    max_concurrent_jobs: int = Field(
        default=4,
        description="最大同時処理ジョブ数"
    )
    
    session_cleanup_enabled: bool = Field(
        default=True,
        description="セッション自動クリーンアップの有効化"
    )
    
    session_retention_hours: int = Field(
        default=24,
        description="セッションデータの保持時間（時間）"
    )
```

### 6. エラーハンドリング

```python
class SessionError(Exception):
    """セッション関連のエラー"""
    pass

class ConcurrentProcessingError(Exception):
    """並行処理関連のエラー"""
    pass

def with_retry(max_retries: int = 3):
    """リトライデコレーター"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2 ** attempt)  # 指数バックオフ
            return None
        return wrapper
    return decorator
```

### 7. テスト戦略

```python
# tests/test_concurrent_processing.py
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TestConcurrentProcessing:
    def test_multiple_sessions_isolation(self):
        """複数セッションのファイル分離をテスト"""
        # ...
        
    def test_concurrent_video_processing(self):
        """同時動画処理をテスト"""
        # ...
        
    def test_session_cleanup(self):
        """セッションクリーンアップをテスト"""
        # ...
        
    @pytest.mark.asyncio
    async def test_async_processing(self):
        """非同期処理をテスト"""
        # ...
```

## 実装フェーズ

### フェーズ1: 基本的なセッション管理（必須）
1. SessionManagerクラスの実装
2. 既存コードのセッション対応
3. 基本的なテストの実装

### フェーズ2: 並行処理対応（オプション）
1. AsyncCLIクラスの実装
2. バッチ処理APIの実装
3. 並行処理テストの実装

### フェーズ3: 高度な機能（将来的な拡張）
1. 分散処理対応（Redis等を使用）
2. ジョブキューシステム（Celery等）
3. WebAPIサーバー化

## まとめ

この設計により、以下が実現できます：

1. **安全な並行処理**: リクエスト単位でファイルを分離
2. **スケーラビリティ**: 複数ワーカーでの処理が可能
3. **エラー耐性**: 個別のリクエストが失敗しても他に影響しない
4. **拡張性**: 将来的な分散処理への対応が容易

実装の優先順位としては、まずフェーズ1の基本的なセッション管理を実装し、その後必要に応じてフェーズ2以降を実装することを推奨します。