#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
whisper_local.py — 用 faster-whisper 在地端轉錄 YouTube 音訊

獨立 CLI:
    python whisper_local.py <YouTube URL> [--model large-v3] [--language zh]

也可被 import 用:
    from whisper_local import transcribe
    text = transcribe(url, model="large-v3")  # 回傳 [MM:SS] text\\n... 字串

跟 fetch_transcript() 輸出格式對齊,所以 gemini_video.py 可以直接接。
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _seconds_to_mmss(sec):
    sec = int(sec)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def _audio_stream_url(url):
    """yt-dlp 拿 audio-only stream URL,不下載整支"""
    try:
        import yt_dlp
    except ImportError:
        print("錯誤: 需要 yt-dlp (pip install yt-dlp)", file=sys.stderr)
        sys.exit(1)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "bestaudio[ext=m4a]/bestaudio",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    audio_url = info.get("url")
    if not audio_url:
        # DASH 分軌的話,從 requested_formats 裡找音訊
        for f in info.get("requested_formats") or []:
            if f.get("acodec") and f.get("acodec") != "none":
                audio_url = f.get("url")
                break
    if not audio_url:
        raise RuntimeError("yt-dlp 沒回傳 audio stream URL")
    return audio_url, info


def _download_to_wav(audio_url, out_wav):
    """ffmpeg 把音訊串流轉成 16kHz mono wav (Whisper 偏好的格式)"""
    cmd = [
        "ffmpeg", "-loglevel", "error",
        "-i", audio_url,
        "-ac", "1",       # mono
        "-ar", "16000",   # 16 kHz
        "-y", str(out_wav),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 失敗: {result.stderr.strip()}")


def transcribe(url, model="large-v3", language=None, device=None):
    """主入口。轉錄 YouTube URL 為 [MM:SS] text 格式字串。

    - model: faster-whisper model name (large-v3 / medium / small / base)
    - language: 強制指定語言 ('zh', 'en', ...). None = auto-detect
    - device: 'cuda' / 'cpu' / None (auto-detect)
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("錯誤: 需要 faster-whisper (pip install faster-whisper)", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        print("錯誤: 找不到 ffmpeg", file=sys.stderr)
        sys.exit(1)

    print(f"[whisper] yt-dlp 取 audio stream URL...", file=sys.stderr)
    audio_url, info = _audio_stream_url(url)
    duration = info.get("duration", "?")
    title = info.get("title", "video")
    print(f"[whisper] {title} ({duration}s)", file=sys.stderr)

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "audio.wav"
        print(f"[whisper] ffmpeg 轉 16kHz mono wav...", file=sys.stderr)
        _download_to_wav(audio_url, wav_path)
        print(f"[whisper] wav 大小: {wav_path.stat().st_size / 1024 / 1024:.1f} MB",
              file=sys.stderr)

        # device auto: 試 cuda,失敗退 cpu
        if device is None:
            try:
                import torch  # faster-whisper 不一定 import torch,但 ctranslate2 會用 CUDA
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "auto"  # ctranslate2 自己會判斷
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"[whisper] 載入模型 {model} on {device} ({compute_type})...",
              file=sys.stderr)
        wm = WhisperModel(model, device=device, compute_type=compute_type)

        print(f"[whisper] 開始轉錄... (lang={language or 'auto'})", file=sys.stderr)
        segments, lang_info = wm.transcribe(
            str(wav_path),
            language=language,
            vad_filter=True,  # 過濾靜音段,大幅減少幻覺
            vad_parameters={"min_silence_duration_ms": 500},
        )
        if hasattr(lang_info, "language"):
            print(f"[whisper] 偵測語言: {lang_info.language} "
                  f"(confidence={lang_info.language_probability:.2f})", file=sys.stderr)

        lines = []
        for seg in segments:
            ts = _seconds_to_mmss(seg.start)
            text = seg.text.strip()
            if text:
                lines.append(f"[{ts}] {text}")

    print(f"[whisper] 完成,共 {len(lines)} 段", file=sys.stderr)
    return "\n".join(lines)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="用 faster-whisper 在地轉錄 YouTube 音訊")
    parser.add_argument("url", help="YouTube 影片網址")
    parser.add_argument("--model", default="large-v3",
                        help="faster-whisper 模型 (預設 large-v3,可選 medium/small/base)")
    parser.add_argument("--language", default=None,
                        help="強制指定語言 (zh/en/...) 或留空自動偵測")
    parser.add_argument("--device", default=None, choices=[None, "cuda", "cpu"],
                        help="cuda / cpu (預設自動)")
    parser.add_argument("--save", help="存到檔案而非 stdout")
    args = parser.parse_args()

    text = transcribe(args.url, model=args.model, language=args.language, device=args.device)
    if args.save:
        Path(args.save).write_text(text, encoding="utf-8")
        print(f"[whisper] 存到 {args.save}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
