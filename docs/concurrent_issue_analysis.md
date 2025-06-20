# 並行実行時の干渉問題分析レポート

## 実行テスト結果

### テスト環境
- 2つの動画翻訳リクエストを同時実行
- 同じ`temp`ディレクトリを使用

### 確認された問題

#### 1. **ファイル名の競合**
```
FileNotFoundError: [Errno 2] No such file or directory: 
'temp/original_video.mp4.part' -> 'temp/original_video.mp4'
```
- 両方のスレッドが同じファイル名（`original_video.mp4`）を使用
- 一方がダウンロード中に、他方がファイルを削除または上書き

#### 2. **tempディレクトリのクリア競合**
```python
# cli.py:48
INFO     tempディレクトリをクリア
```
- 各リクエストの開始時に`temp`ディレクトリ全体をクリア
- 実行中の他のリクエストのファイルも削除される

#### 3. **セグメントファイルの混在**
```
tempディレクトリのファイル数: 12
  - segment_0000.wav (0.15MB)
  - segment_0001.wav (0.13MB)
  - segment_0002.wav (0.28MB)
  ...
```
- 複数のリクエストのセグメントファイルが同じディレクトリに混在
- どのリクエストのファイルか区別できない

#### 4. **字幕ファイルの上書き**
- `subtitles.srt`が固定名のため、後から実行されたリクエストが上書き

## 影響範囲

### 致命的な影響
1. **プロセスの失敗**: 一方のリクエストが必ず失敗する
2. **データの混在**: 異なる動画の音声・字幕が混ざる可能性
3. **予期しない出力**: 間違った言語や音声で出力される可能性

### 影響を受けるファイル
- `temp/original_video.mp4`
- `temp/audio.wav`
- `temp/subtitles.srt`
- `temp/translated_audio.wav`
- `temp/segment_*.wav`
- `temp/segment_style_*.wav`

## 根本原因

### 1. グローバルな一時ディレクトリ
```python
# config.py
temp_dir: Path = Field(
    default=Path("temp"),
    description="一時ファイル保存ディレクトリ"
)
```

### 2. 固定ファイル名
```python
# 各サービスで固定のファイル名を使用
video_path = config.temp_dir / "original_video.mp4"
audio_path = config.temp_dir / "audio.wav"
```

### 3. 開始時の一括クリア
```python
# cli.py
if config.temp_dir.exists():
    shutil.rmtree(config.temp_dir)
config.temp_dir.mkdir(exist_ok=True)
```

## 解決策

### 短期的解決策（最小限の変更）
1. **プロセスレベルのロック**
   ```python
   import fcntl
   
   lock_file = Path(".video_translator.lock")
   with open(lock_file, 'w') as f:
       fcntl.flock(f, fcntl.LOCK_EX)
       # 処理を実行
   ```

2. **タイムスタンプ付きファイル名**
   ```python
   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
   video_path = config.temp_dir / f"original_video_{timestamp}.mp4"
   ```

### 推奨解決策（セッション管理）
すでに設計した`SessionManager`を使用：
```python
with session_manager.session_context() as session:
    video_path = session.video_path  # session_xxx/original_video.mp4
    audio_path = session.audio_path  # session_xxx/audio.wav
    # 各ファイルは独立したディレクトリに保存される
```

## テスト結果のまとめ

| ケース | 結果 | 問題 |
|--------|------|------|
| 同じ動画を異なる言語で同時処理 | 1つ成功、1つ失敗 | ファイル名競合でダウンロード失敗 |
| 異なる動画を同時処理 | 不安定 | ファイルの上書き、データ混在の可能性 |

## 結論

**現在の実装では複数リクエストの同時処理は不可能**です。ファイル名の競合とディレクトリクリアにより、必ず干渉が発生します。

セッション管理システムの実装が必須であり、各リクエストに独立したディレクトリを割り当てることで、安全な並行処理が可能になります。