#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_frames.py — 從 YouTube 影片在指定時間戳抓 frame (不下載整支影片)

用法:
    # 指定時間戳
    python extract_frames.py <URL> --timestamps 00:36,03:13,06:20 --output-dir frames/

    # 從 gemini_video.py 產出的 summary.md 解析 [MM:SS] 自動抓
    python extract_frames.py <URL> --from-summary 2026-04-29/summary.md

設計:
    - yt-dlp 拿 stream URL (不下載整支)
    - ffmpeg -ss 放在 -i 前 (fast seek, 不解碼整段)
    - 一個時間戳一張圖,檔名 frame_<idx>_<HHMMSS>.jpg
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


TS_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]")


def parse_timestamp(ts):
    """'00:36' / '03:13' / '01:23:45' → seconds (int)"""
    parts = ts.strip().split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)
    raise ValueError(f"無法解析時間戳: {ts!r} (格式應為 MM:SS 或 HH:MM:SS)")


def seconds_to_label(sec):
    """seconds → '012345' (HHMMSS, 不含冒號, 適合當檔名)"""
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}{m:02d}{s:02d}"


def seconds_to_ffmpeg_ts(sec):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_summary(path):
    """從 markdown 檔抓所有 [MM:SS] / [HH:MM:SS], 回傳排序去重後的秒數列表"""
    text = Path(path).read_text(encoding="utf-8")
    seconds_set = set()
    for m in TS_RE.finditer(text):
        h_or_m = int(m.group(1))
        mid = int(m.group(2))
        last = m.group(3)
        if last is not None:
            sec = h_or_m * 3600 + mid * 60 + int(last)
        else:
            sec = h_or_m * 60 + mid
        seconds_set.add(sec)
    return sorted(seconds_set)


def _seconds_in_match(m):
    h_or_m = int(m.group(1))
    mid = int(m.group(2))
    last = m.group(3)
    return h_or_m * 3600 + mid * 60 + int(last) if last is not None else h_or_m * 60 + mid


def embed_images_into_summary(summary_path, sec_to_image, width=760):
    """把 frame 以 HTML <img> 插在 summary.md 對應時間戳那行下面。

    用 <img> 而不是 ![](...) 是為了能控制顯示寬度 — 原圖 1920px 在 md viewer
    裡會撐滿整頁,讀者看不出畫面細節跟內文的對應關係。預設 760px 對閱讀
    剛好 (約 markdown 預設行寬),圖表上的數字也看得清楚;太小會看不到細節,
    太大會喧賓奪主。width=0 表示不加 width 屬性 (原始大小)。

    冪等: 如果接下來幾行內已經有引用同一張圖的標籤(任何形式),跳過不重複插。
    路徑以 summary.md 所在目錄為基準算相對路徑。
    """
    summary_path = Path(summary_path)
    base_dir = summary_path.parent
    text = summary_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    out_lines = []
    inserted = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        m = TS_RE.search(line)
        if m:
            sec = _seconds_in_match(m)
            img = sec_to_image.get(sec)
            if img:
                rel = os.path.relpath(img, base_dir).replace(os.sep, "/")
                width_attr = f' width="{width}"' if width > 0 else ""
                img_md = f'<img src="{rel}"{width_attr} alt="frame @ {seconds_to_ffmpeg_ts(sec)}">'
                # 冪等: 看接下來 3 行內有沒有已經引用這張圖了 (容忍 md / html 兩種語法)
                lookahead = "\n".join(lines[i + 1 : i + 4])
                already = rel in lookahead
                if not already:
                    out_lines.append("")
                    out_lines.append(img_md)
                    inserted += 1
        i += 1

    summary_path.write_text("\n".join(out_lines), encoding="utf-8")
    return inserted


def get_stream_url(url, prefer_mp4=True):
    """用 yt-dlp 拿 video-only stream URL (省頻寬,反正只要 frame)"""
    try:
        import yt_dlp
    except ImportError:
        print("錯誤: 需要 yt-dlp", file=sys.stderr)
        print("  pip install yt-dlp", file=sys.stderr)
        sys.exit(1)

    fmt = "bestvideo[ext=mp4]/bestvideo/best[ext=mp4]/best" if prefer_mp4 else "bestvideo/best"
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "format": fmt}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    stream_url = info.get("url")
    if not stream_url:
        # 有時 info 結構是 requested_formats (DASH 分軌)
        formats = info.get("requested_formats") or []
        for f in formats:
            if f.get("vcodec") and f.get("vcodec") != "none":
                stream_url = f.get("url")
                break
    if not stream_url:
        raise RuntimeError("yt-dlp 沒回傳 stream URL,可能格式選擇不對")
    return stream_url, info


def extract_frame(stream_url, sec, out_path, quality=2):
    """ffmpeg fast-seek 一張 frame。-ss 放 -i 前是關鍵 (input seek, 不解碼整段)"""
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-ss", seconds_to_ffmpeg_ts(sec),
        "-i", stream_url,
        "-frames:v", "1",
        "-q:v", str(quality),
        "-y",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 失敗 ({sec}s): {result.stderr.strip()}")


_face_cascade = None


def _get_face_cascade():
    global _face_cascade
    if _face_cascade is None:
        import cv2
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _face_cascade = cv2.CascadeClassifier(path)
        if _face_cascade.empty():
            raise RuntimeError(f"無法載入 Haar cascade: {path}")
    return _face_cascade


def face_ratio(image_path):
    """回傳臉佔畫面比例 (0~1)。沒臉 = 0。多張臉就加總。"""
    import cv2
    img = cv2.imread(str(image_path))
    if img is None:
        return 0.0
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = _get_face_cascade().detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) == 0:
        return 0.0
    total = sum(fw * fh for (_, _, fw, fh) in faces)
    return total / (w * h)


def find_informative_frame(stream_url, target_sec, out_path, video_duration,
                           window=30, step=3, threshold=0.04, quality=2):
    """從 target_sec 開始往外掃,找第一個臉佔比 < threshold 的 frame。

    策略: 先試原秒;若是 talking head,以 step 秒為單位往前/往後交錯掃,
    範圍 ±window 秒。掃完都找不到非頭像就退回原秒。

    回傳 (chosen_sec, ratio_at_chosen)。
    """
    extract_frame(stream_url, target_sec, out_path, quality=quality)
    r = face_ratio(out_path)
    if r < threshold:
        return target_sec, r

    best_sec, best_r = target_sec, r
    for d in range(step, window + 1, step):
        for cand in (target_sec - d, target_sec + d):
            if cand < 0 or cand >= video_duration:
                continue
            extract_frame(stream_url, cand, out_path, quality=quality)
            cr = face_ratio(out_path)
            if cr < threshold:
                return cand, cr
            if cr < best_r:
                best_sec, best_r = cand, cr
    extract_frame(stream_url, best_sec, out_path, quality=quality)
    return best_sec, best_r


def main():
    parser = argparse.ArgumentParser(
        description="從 YouTube 影片在指定時間戳抓 frame",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="YouTube 影片網址")
    parser.add_argument(
        "--timestamps",
        help="逗號分隔的時間戳,例如: 00:36,03:13,06:20 或 01:23:45,02:00",
    )
    parser.add_argument(
        "--from-summary",
        help="從 summary.md 解析所有 [MM:SS] / [HH:MM:SS] 時間戳",
    )
    parser.add_argument(
        "--output-dir",
        default="frames",
        help="輸出資料夾 (預設: ./frames)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=2,
        help="ffmpeg JPEG 品質, 1=最佳 31=最差 (預設: 2)",
    )
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="搭配 --from-summary 時,不要把圖片插回 summary.md (預設會插)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=760,
        help="嵌入到 summary.md 的圖片顯示寬度 px (預設 760, 0=原始大小)",
    )
    parser.add_argument(
        "--skip-talking-head",
        action="store_true",
        help="偵測人臉佔畫面比例,若原時間戳是講者頭像就在 ±window 秒內找替代 frame",
    )
    parser.add_argument(
        "--scan-window",
        type=int,
        default=30,
        help="--skip-talking-head 啟用時,前後掃描秒數 (預設 30)",
    )
    parser.add_argument(
        "--scan-step",
        type=int,
        default=3,
        help="--skip-talking-head 啟用時,每隔幾秒抽一張候選 (預設 3)",
    )
    parser.add_argument(
        "--face-threshold",
        type=float,
        default=0.04,
        help="人臉佔畫面比例多少以上算 talking head (預設 0.04 = 4%。Haar Cascade "
             "只框臉部不含頭髮/肩膀,1920x1080 講者中近景的臉框約佔 6-8%,所以 0.04 "
             "是合理閾值)",
    )
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        print("錯誤: 找不到 ffmpeg, 請先安裝並加入 PATH", file=sys.stderr)
        sys.exit(1)

    if not args.timestamps and not args.from_summary:
        print("錯誤: 至少要提供 --timestamps 或 --from-summary", file=sys.stderr)
        sys.exit(2)

    seconds_list = []
    if args.from_summary:
        seconds_list.extend(parse_summary(args.from_summary))
        print(f"[解析] 從 {args.from_summary} 抓到 {len(seconds_list)} 個時間戳",
              file=sys.stderr)
    if args.timestamps:
        for ts in args.timestamps.split(","):
            seconds_list.append(parse_timestamp(ts))
    seconds_list = sorted(set(seconds_list))

    if not seconds_list:
        print("錯誤: 沒解析到任何時間戳", file=sys.stderr)
        sys.exit(3)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[yt-dlp] 取得 stream URL...", file=sys.stderr)
    stream_url, info = get_stream_url(args.url)
    title = info.get("title", "video")
    duration = int(info.get("duration") or 99999)
    print(f"[yt-dlp] {title} ({duration}s)", file=sys.stderr)

    if args.skip_talking_head:
        print(f"[掃描] 啟用 talking-head 偵測 (window=±{args.scan_window}s, "
              f"step={args.scan_step}s, threshold={args.face_threshold})", file=sys.stderr)

    ok, fail = 0, 0
    sec_to_image = {}
    for idx, sec in enumerate(seconds_list, 1):
        label = seconds_to_label(sec)
        out_path = out_dir / f"frame_{idx:02d}_{label}.jpg"
        try:
            if args.skip_talking_head:
                chosen_sec, ratio = find_informative_frame(
                    stream_url, sec, out_path, duration,
                    window=args.scan_window, step=args.scan_step,
                    threshold=args.face_threshold, quality=args.quality,
                )
                shift = chosen_sec - sec
                tag = f"face={ratio:.2f}"
                if shift != 0:
                    tag = f"shift {shift:+d}s, " + tag
                print(f"  [{idx:02d}/{len(seconds_list)}] {seconds_to_ffmpeg_ts(sec)} "
                      f"→ {out_path} ({tag})", file=sys.stderr)
            else:
                extract_frame(stream_url, sec, out_path, quality=args.quality)
                print(f"  [{idx:02d}/{len(seconds_list)}] {seconds_to_ffmpeg_ts(sec)} → {out_path}",
                      file=sys.stderr)
            sec_to_image[sec] = out_path
            ok += 1
        except Exception as e:
            print(f"  [{idx:02d}/{len(seconds_list)}] {seconds_to_ffmpeg_ts(sec)} 失敗: {e}",
                  file=sys.stderr)
            fail += 1

    print(f"\n完成: {ok} 張成功, {fail} 張失敗 → {out_dir}", file=sys.stderr)

    if args.from_summary and not args.no_embed and sec_to_image:
        inserted = embed_images_into_summary(args.from_summary, sec_to_image, width=args.width)
        print(f"[嵌入] 在 {args.from_summary} 插入 {inserted} 張圖片 (width={args.width})",
              file=sys.stderr)

    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
