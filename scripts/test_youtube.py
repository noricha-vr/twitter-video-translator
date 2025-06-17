#!/usr/bin/env python3
"""YouTube動画のテストスクリプト"""

from pathlib import Path
import sys

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.twitter_video_translator.cli import VideoTranslatorCLI


def test_youtube_video():
    """YouTube動画の翻訳テスト"""
    # YouTube動画のサンプルURL（短い動画推奨）
    youtube_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - 最初のYouTube動画（18秒）
    
    print(f"YouTube動画をテスト中: {youtube_url}")
    print("注意: これは短い動画（18秒）のテストです")
    
    cli = VideoTranslatorCLI()
    
    # TTSを無効にして高速化（字幕のみ）
    # output_pathを指定しない場合、自動的に動画タイトル_ja.mp4で保存される
    result = cli.run(youtube_url, output_path=None, use_tts=False)
    
    print(f"完了: {result}")


if __name__ == "__main__":
    test_youtube_video()