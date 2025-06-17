# 音声処理アーキテクチャと問題分析

## 概要
このドキュメントでは、Twitter Video Translatorの音声処理の仕組みと、日本語音声の最後のセグメントだけボリュームが大きくなる問題について分析します。

## 音声処理の流れ

### 1. 音声生成フロー
```
1. 動画から音声抽出 (transcriber.py)
   ↓
2. 音声を文字起こし (Groq Whisper API)
   ↓
3. テキストを翻訳 (Google Gemini API)
   ↓
4. 翻訳テキストから音声生成 (tts.py - Google Gemini TTS)
   ↓
5. 音声セグメントを結合 (video_composer.py - merge_audio_segments)
   ↓
6. 元音声と日本語音声をミックス (video_composer.py - compose_video)
```

### 2. 音声セグメントの処理 (tts.py)

#### 現在の実装
```python
# tts.pyでの音声生成
for i, segment in enumerate(segments):
    # 各セグメントごとに音声を生成
    audio_path = self._generate_audio(segment["text"], i)
    segment["audio_path"] = audio_path
```

各セグメントは個別のmp3ファイルとして生成されます：
- `segment_0000.mp3`
- `segment_0001.mp3`
- `segment_0002.mp3`
- ...

### 3. 音声セグメントの結合 (video_composer.py)

#### merge_audio_segments メソッドの実装
```python
def merge_audio_segments(self, segments: List[Dict[str, Any]], output_path: Path) -> Path:
    # FFmpegコマンドを構築
    cmd = ["ffmpeg", "-y"]
    
    # 各音声ファイルを入力として追加
    for seg in audio_segments:
        cmd.extend(["-i", str(seg["audio_path"].absolute())])
    
    # フィルターグラフを構築
    filter_parts = []
    for i, seg in enumerate(audio_segments):
        # 各音声の開始時刻をミリ秒単位で計算
        delay_ms = int(seg["start"] * 1000)
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")
    
    # すべての音声をミックス
    input_labels = "".join(f"[a{i}]" for i in range(len(audio_segments)))
    filter_parts.append(f"{input_labels}amix=inputs={len(audio_segments)}:duration=longest[out]")
```

### 4. 最終的な音声ミックス (compose_video)

#### 現在の実装
```python
if audio_file and audio_file.exists():
    # 元の音声を15%に下げる
    original_audio = input_video.audio.filter("volume", original_volume)  # 0.15
    # 日本語音声を1.8倍にする
    japanese_audio = ffmpeg.input(str(audio_file)).audio.filter("volume", japanese_volume)  # 1.8
    
    # 音声をミックス
    audio_stream = ffmpeg.filter(
        [original_audio, japanese_audio], 
        "amix", 
        inputs=2, 
        duration="longest",
        dropout_transition=2
    )
```

## 問題の分析

### 症状
- 日本語音声の最後のセグメントだけボリュームが大きくなる

### 考えられる原因

#### 1. **amixフィルターの正規化問題** （最も可能性が高い）
FFmpegの`amix`フィルターは、デフォルトで音声を正規化します。セグメントが重なっていない場合、最後のセグメントだけが単独で再生され、正規化により音量が上がる可能性があります。

#### 2. **セグメント結合時の音量累積**
`merge_audio_segments`で複数のセグメントをミックスする際、最後のセグメントが他のセグメントと重ならない場合、相対的に音量が大きくなる可能性があります。

#### 3. **音声生成時の音量不均一**
Google Gemini TTSが生成する音声セグメントごとに音量レベルが異なる可能性があります。

#### 4. **adelayフィルターの影響**
遅延を加える`adelay`フィルターが音量に影響を与えている可能性があります。

### 解決策の提案

#### 1. amixフィルターの正規化を無効化
```python
# amixに normalize=0 を追加
filter_parts.append(f"{input_labels}amix=inputs={len(audio_segments)}:duration=longest:normalize=0[out]")
```

#### 2. 各セグメントの音量を個別に正規化
```python
# 各セグメントにvolume filterを追加
filter_parts.append(f"[{i}:a]volume=1.0,adelay={delay_ms}|{delay_ms}[a{i}]")
```

#### 3. 音声レベルの事前分析
生成された音声ファイルの音量レベルを分析し、必要に応じて調整する。

#### 4. コンプレッサーの使用
音量の急激な変化を抑えるため、`acompressor`フィルターを追加する。

## 推奨される修正

最も効果的と思われる修正は、`amix`フィルターの正規化を無効にすることです：

```python
# video_composer.py の merge_audio_segments メソッド
filter_parts.append(
    f"{input_labels}amix=inputs={len(audio_segments)}:"
    f"duration=longest:normalize=0[out]"
)
```

これにより、各セグメントの音量が保持され、最後のセグメントだけが大きくなる問題を防げるはずです。