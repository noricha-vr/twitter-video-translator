"""ロギング設定"""

import logging
from pathlib import Path
from datetime import datetime
from rich.logging import RichHandler
from rich.console import Console

# logsディレクトリの作成
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# ログファイル名（日時付き）
log_filename = LOG_DIR / f"video_translator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Richコンソール
console = Console()

# ロガーの設定
def setup_logger(name: str = "video_translator") -> logging.Logger:
    """ロガーを設定"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ファイルハンドラー（詳細ログ）
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # コンソールハンドラー（Rich）
    console_handler = RichHandler(console=console, rich_tracebacks=True)
    console_handler.setLevel(logging.INFO)
    
    # ハンドラーを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# デフォルトロガー
logger = setup_logger()