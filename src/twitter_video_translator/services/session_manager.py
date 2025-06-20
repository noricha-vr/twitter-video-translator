"""セッション管理サービス

リクエスト単位でファイルを分離管理し、複数スレッドでの同時処理を可能にする
"""

from pathlib import Path
from datetime import datetime
import uuid
import shutil
from contextlib import contextmanager
import threading
from typing import Optional, Dict, Any
import logging
from ..config import config

logger = logging.getLogger(__name__)


class SessionError(Exception):
    """セッション関連のエラー"""
    pass


class SessionContext:
    """セッションコンテキスト
    
    各リクエストのファイルパスを管理する
    """
    
    def __init__(self, session_id: str, session_dir: Path):
        self.session_id = session_id
        self.session_dir = session_dir
        self._metadata: Dict[str, Any] = {
            "created_at": datetime.now(),
            "files": []
        }
        
    def get_path(self, filename: str) -> Path:
        """セッション内のファイルパスを取得
        
        Args:
            filename: ファイル名
            
        Returns:
            セッションディレクトリ内のファイルパス
        """
        file_path = self.session_dir / filename
        self._metadata["files"].append(str(file_path))
        return file_path
    
    @property
    def video_path(self) -> Path:
        """オリジナル動画のパス"""
        return self.get_path("original_video.mp4")
    
    @property
    def audio_path(self) -> Path:
        """抽出された音声のパス"""
        return self.get_path("audio.wav")
    
    @property
    def subtitles_path(self) -> Path:
        """字幕ファイルのパス"""
        return self.get_path("subtitles.srt")
    
    @property
    def translated_audio_path(self) -> Path:
        """翻訳された音声のパス"""
        return self.get_path("translated_audio.wav")
    
    def get_segment_audio_path(self, index: int) -> Path:
        """セグメント音声のパス"""
        return self.get_path(f"segment_{index:04d}.wav")
    
    def get_style_audio_path(self, index: int) -> Path:
        """スタイル分析用音声のパス"""
        return self.get_path(f"segment_style_{index:04d}.wav")


class SessionManager:
    """リクエスト単位のセッション管理
    
    複数のリクエストを同時に処理できるように、
    各リクエストに独自のディレクトリを割り当てる
    """
    
    def __init__(self, base_temp_dir: Optional[Path] = None):
        """初期化
        
        Args:
            base_temp_dir: ベースとなる一時ディレクトリ（デフォルト: config.temp_dir）
        """
        self.base_temp_dir = base_temp_dir or config.temp_dir
        self._lock = threading.Lock()
        self._active_sessions: Dict[str, SessionContext] = {}
        
        # ベースディレクトリを作成
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)
        
    def create_session(self) -> str:
        """新しいセッションIDを生成
        
        Returns:
            ユニークなセッションID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_id}"
    
    @contextmanager
    def session_context(self, session_id: Optional[str] = None, cleanup: bool = True):
        """セッションコンテキストマネージャー
        
        Args:
            session_id: 既存のセッションID（省略時は新規作成）
            cleanup: 終了時にクリーンアップするか
            
        Yields:
            SessionContext: セッションコンテキスト
            
        Example:
            ```python
            with session_manager.session_context() as session:
                video_path = session.get_path("video.mp4")
                # ファイル操作...
            # ここでセッションディレクトリは自動的に削除される
            ```
        """
        if session_id is None:
            session_id = self.create_session()
            
        session_dir = self.base_temp_dir / session_id
        
        try:
            # セッションディレクトリ作成
            with self._lock:
                session_dir.mkdir(parents=True, exist_ok=True)
                session = SessionContext(session_id, session_dir)
                self._active_sessions[session_id] = session
                
            logger.info(f"セッション開始: {session_id}")
            yield session
            
        except Exception as e:
            logger.error(f"セッションエラー: {session_id}, {str(e)}")
            raise SessionError(f"セッション処理中にエラーが発生しました: {str(e)}")
            
        finally:
            # クリーンアップ
            with self._lock:
                self._active_sessions.pop(session_id, None)
                
            if cleanup and session_dir.exists():
                try:
                    shutil.rmtree(session_dir)
                    logger.info(f"セッションクリーンアップ完了: {session_id}")
                except Exception as e:
                    logger.warning(f"セッションクリーンアップ失敗: {session_id}, {str(e)}")
    
    def get_active_sessions(self) -> Dict[str, SessionContext]:
        """アクティブなセッション一覧を取得
        
        Returns:
            アクティブなセッションの辞書
        """
        with self._lock:
            return self._active_sessions.copy()
    
    def cleanup_old_sessions(self, hours: int = 24):
        """古いセッションをクリーンアップ
        
        Args:
            hours: 保持時間（時間）
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        with self._lock:
            for session_dir in self.base_temp_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                    
                if not session_dir.name.startswith("session_"):
                    continue
                    
                # ディレクトリの作成時刻をチェック
                if session_dir.stat().st_mtime < cutoff_time:
                    try:
                        shutil.rmtree(session_dir)
                        logger.info(f"古いセッションを削除: {session_dir.name}")
                    except Exception as e:
                        logger.warning(f"セッション削除失敗: {session_dir.name}, {str(e)}")


# グローバルインスタンス
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """セッションマネージャーのシングルトンインスタンスを取得
    
    Returns:
        SessionManager: セッションマネージャー
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager