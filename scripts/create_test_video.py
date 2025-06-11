#!/usr/bin/env python3
"""テスト用の短い動画を作成"""

import subprocess
from pathlib import Path

# テスト用の音声を生成（10秒）
test_audio = Path("test_audio.wav")
subprocess.run([
    "ffmpeg", "-f", "lavfi", 
    "-i", "sine=frequency=440:duration=10",
    "-ar", "16000", "-ac", "1",
    "-y", str(test_audio)
], check=True)

# テスト用の動画を生成（10秒、黒画面）
test_video = Path("test_video.mp4")
subprocess.run([
    "ffmpeg",
    "-f", "lavfi", "-i", "color=c=black:s=640x480:d=10",
    "-i", str(test_audio),
    "-c:v", "libx264", "-c:a", "aac",
    "-y", str(test_video)
], check=True)

print(f"テスト動画を作成しました: {test_video}")

# 音声ファイルを削除
test_audio.unlink()