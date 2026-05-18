#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gemini_video.py — 用 Gemini API 讀 YouTube 影片並產生摘要

用法:
    python gemini_video.py <YouTube URL> [prompt] [選項]

選項:
    --model MODEL          使用的模型 (預設: gemini-2.5-pro)
    --prompt-file PATH     從文字檔讀 prompt (覆蓋位置參數)
    --save PATH            把結果存成 Markdown 檔案
    --transcript-first     先嘗試抓字幕,失敗才走 Gemini (省 quota)
    --transcript-only      只抓字幕,不 fallback 到 Gemini
"""

import argparse
import os
import re
import sys
from pathlib import Path


def _find_env_file():
    """從腳本所在位置向上找 .env (走最多 6 層,涵蓋 .claude/skills/<name>/scripts/ 巢狀結構)"""
    candidates = []
    p = Path(__file__).resolve().parent
    for _ in range(6):
        candidates.append(p / ".env")
        if p.parent == p:
            break
        p = p.parent
    candidates.append(Path.cwd() / ".env")
    for c in candidates:
        if c.exists():
            return c
    return None


# 自動載入 .env
try:
    from dotenv import load_dotenv
    env_file = _find_env_file()
    if env_file:
        load_dotenv(env_file)
except ImportError:
    pass

from google import genai
from google.genai import types

DEFAULT_PROMPT = """請用繁體中文摘要這部 YouTube 影片，包含以下幾個部分:

1. **影片主題** (一句話)
2. **核心重點** (3-5 個條列)
3. **關鍵內容** (依時間順序簡述,標註時間戳)
4. **結論或可行動建議** (如有)

請用平易近人的中文,避免艱深詞彙。"""

SYSTEM_INSTRUCTION = (
    "You are a multimodal assistant with full video understanding capabilities. "
    "When the user provides a video (including YouTube URLs as fileData), you can "
    "and must analyze its visual frames and audio. Never refuse on the grounds "
    "that you cannot see videos — you can. Always respond in the language the "
    "user uses (default 繁體中文)."
)

# prep 任務專用 system: 強硬告訴模型這次不是摘要任務
PREP_SYSTEM_INSTRUCTION = (
    "你是字幕整理員,不是摘要員。你的唯一任務是把破碎的字幕重組成可讀的長文章,"
    "完整保留原文內容。不要 summarize、不要簡化、不要加 emoji 跟「核心觀點」這類標題。"
    "輸出長度應接近輸入長度。任何把 N 點論述濃縮成 1 點結論的行為都是任務失敗。"
    "嚴格依照 user prompt 的格式要求輸出。"
)


def _extract_video_id(url):
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    m = re.search(r"(?:shorts|embed|live)/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    return None


def fetch_transcript(url):
    video_id = _extract_video_id(url)
    if not video_id:
        return None
    # 套件已在 main() 檢查過,這裡放心 import
    from youtube_transcript_api import YouTubeTranscriptApi

    preferred_langs = ["zh-Hant", "zh-TW", "zh-Hans", "zh", "en"]
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        try:
            transcript = transcript_list.find_transcript(preferred_langs)
        except Exception:
            transcript = next(iter(transcript_list), None)
            if transcript is None:
                return None
        snippets = transcript.fetch()
        lines = []
        for s in snippets:
            ts = int(getattr(s, "start", 0))
            mm, ss = divmod(ts, 60)
            text = getattr(s, "text", "")
            lines.append(f"[{mm:02d}:{ss:02d}] {text}")
        return "\n".join(lines)
    except Exception:
        pass
    try:
        from youtube_transcript_api import YouTubeTranscriptApi as _Y
        data = _Y.get_transcript(video_id, languages=preferred_langs)
        lines = []
        for s in data:
            ts = int(s.get("start", 0))
            mm, ss = divmod(ts, 60)
            lines.append(f"[{mm:02d}:{ss:02d}] {s.get('text','')}")
        return "\n".join(lines)
    except Exception as e2:
        print(f"[字幕] 抓不到字幕: {e2}", file=sys.stderr)
        return None


def _missing_key():
    print("錯誤: 找不到 GEMINI_API_KEY", file=sys.stderr)
    print('  方式 1: export GEMINI_API_KEY="你的 key"', file=sys.stderr)
    print("  方式 2: 在專案根目錄放 .env 檔,內容: GEMINI_API_KEY=你的 key", file=sys.stderr)
    print("  取得 key: https://aistudio.google.com/apikey", file=sys.stderr)
    sys.exit(1)


def _print_usage(response):
    try:
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            um = response.usage_metadata
            pt = getattr(um, "prompt_token_count", None)
            tt = getattr(um, "total_token_count", None)
            print(f"[token 用量] prompt={pt} total={tt}", file=sys.stderr)
    except Exception:
        pass


def summarize_with_text(transcript, prompt, model, system=None):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        _missing_key()
    client = genai.Client(api_key=api_key)
    sys_inst = system if system is not None else SYSTEM_INSTRUCTION
    full_prompt = f"{prompt}\n\n以下是要處理的影片字幕(含時間戳):\n\n{transcript}"
    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config=types.GenerateContentConfig(system_instruction=sys_inst),
    )
    _print_usage(response)
    return response.text


def _extract_entities(transcript):
    """從原始字幕用簡單 regex 抽常見實體 (公司/股票代號/數字/百分比)。

    粗略但比 gemma 抽得穩。Opus 拿到後會自己再精煉。
    """
    import re
    # 抓: 4-5 位數字股票代號、英文公司名 (Capitalized 或全大寫)、百分比、金額
    patterns = {
        "股票代號": re.findall(r"\b\d{4,5}(?=[\s一-鿿])", transcript),
        "百分比": re.findall(r"\d+(?:\.\d+)?%", transcript),
        "英文機構/公司": re.findall(r"\b[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]+)*\b", transcript),
    }
    lines = ["## 提到的實體 (regex 自動抽取,僅供參考)\n",
             "| 類型 | 名稱 | 出現次數 |", "|---|---|---|"]
    seen_any = False
    for kind, items in patterns.items():
        if not items:
            continue
        from collections import Counter
        counts = Counter(items)
        for name, n in counts.most_common(20):
            if n >= 1 and len(name) >= 2:
                lines.append(f"| {kind} | {name} | {n} |")
                seen_any = True
    return "\n".join(lines) if seen_any else ""


def summarize_with_text_local(transcript, prompt, model, host=None, system=None):
    """走地端 Ollama 做純文字任務 (摘要或 prep)。用 /api/generate。

    為什麼不用 OpenAI 相容端點: Ollama 的 /v1/chat/completions 對中文字串編碼
    有時會掉字 (1.x 版本實測過),原生 /api/generate 直接餵 UTF-8 byte 最穩。

    system 參數: 不傳就用 SYSTEM_INSTRUCTION (摘要用); prep 任務應傳 PREP_SYSTEM_INSTRUCTION。
    """
    import json
    import urllib.request

    host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    sys_inst = system if system is not None else SYSTEM_INSTRUCTION
    full_prompt = (
        f"{sys_inst}\n\n{prompt}\n\n以下是要處理的影片字幕(含時間戳):\n\n{transcript}"
    )
    body = json.dumps(
        {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            # num_predict=8192: Ollama 部分版本預設只給 128~4096 tokens,長 prep 任務
            # 會被截斷; 這裡開大避免「寫到一半被腰斬還以為是模型偷懶」的誤判
            "options": {"num_predict": 8192},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"錯誤: 連不到 Ollama ({host}): {e}", file=sys.stderr)
        print("  確認 Ollama 已啟動: ollama serve", file=sys.stderr)
        sys.exit(1)
    if "error" in data:
        print(f"錯誤: Ollama 回傳錯誤: {data['error']}", file=sys.stderr)
        sys.exit(1)
    eval_count = data.get("eval_count", 0)
    eval_dur = data.get("eval_duration", 1) / 1e9
    rate = eval_count / eval_dur if eval_dur > 0 else 0
    print(f"[token 用量] eval_count={eval_count} rate={rate:.1f} tok/s", file=sys.stderr)
    return data.get("response", "")


def summarize_video(url, prompt, model="gemini-2.5-pro"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        _missing_key()
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_uri(file_uri=url, mime_type="video/mp4"),
            prompt,
        ],
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
    )
    _print_usage(response)
    return response.text


def main():
    # Windows 預設 cp950 stdout 印不出 emoji / 罕見 CJK,模型輸出常含這些
    # 字元時會 UnicodeEncodeError 整個 crash。強制 UTF-8 + replace 才安全。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    parser = argparse.ArgumentParser(
        description="用 Gemini 摘要 YouTube 影片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="YouTube 影片網址")
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="給 Gemini 的指令 (可省略,使用預設;若同時用 --prompt-file 以檔案為準)",
    )
    parser.add_argument(
        "--backend",
        choices=["gemini", "ollama"],
        default=os.environ.get("BACKEND", "gemini"),
        help="選擇 backend: gemini (雲端,可讀影片) 或 ollama (地端,只吃文字字幕). "
             "也可用 .env 的 BACKEND 設預設 (預設: gemini)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="使用的模型. backend=gemini 預設 gemini-2.5-pro; backend=ollama 預設 "
             "讀 .env 的 OLLAMA_MODEL,再預設 gemma4:e4b",
    )
    parser.add_argument(
        "--prompt-file",
        help="從文字檔讀 prompt (UTF-8),會覆蓋位置參數",
    )
    parser.add_argument(
        "--save",
        help="把結果存成 Markdown 檔案",
    )
    parser.add_argument(
        "--transcript-first",
        action="store_true",
        help="先試抓字幕(免費快),沒字幕才用 Gemini 讀影片",
    )
    parser.add_argument(
        "--transcript-only",
        action="store_true",
        help="只抓字幕,不 fallback 到 Gemini 影片模式",
    )
    parser.add_argument(
        "--mode",
        choices=["summarize", "prep"],
        default="summarize",
        help="summarize=產出最終摘要 (預設); prep=只整理字幕成結構化中介檔, "
             "給之後 Opus/Claude 做最終合成 (搭配 prompts/prep_transcript.txt)",
    )
    parser.add_argument(
        "--whisper-fallback",
        action="store_true",
        help="抓不到 YouTube 字幕時,自動 fallback 到 faster-whisper 在地轉錄",
    )
    parser.add_argument(
        "--whisper-model",
        default=os.environ.get("WHISPER_MODEL", "large-v3"),
        help="whisper 模型 (預設讀 .env WHISPER_MODEL,再預設 large-v3)",
    )
    args = parser.parse_args()

    # 決定 prompt: prompt-file > positional > mode-specific 預設
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    elif args.prompt:
        prompt = args.prompt
    elif args.mode == "prep":
        # prep 模式自動載 prep_transcript.txt (在 prompts/ 資料夾)
        prep_path = Path(__file__).resolve().parent.parent / "prompts" / "prep_transcript.txt"
        if not prep_path.exists():
            print(f"錯誤: 找不到 prep prompt: {prep_path}", file=sys.stderr)
            sys.exit(1)
        prompt = prep_path.read_text(encoding="utf-8").strip()
    else:
        prompt = DEFAULT_PROMPT

    # 決定模型: 沒指定就依 backend 給預設
    if args.model is None:
        if args.backend == "ollama":
            args.model = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
        else:
            args.model = "gemini-2.5-pro"

    # mode=prep 走 ollama 比較合理 (gemma 在地、免費、做機械工適合);
    # 用 gemini 也行但浪費。提示一下不擋
    if args.mode == "prep" and args.backend == "gemini":
        print("[提示] mode=prep 通常搭 backend=ollama 用 (在地、免費),"
              "你用 gemini 也可以但會花 token", file=sys.stderr)

    # mode=prep 預設行為: 強制走字幕路徑 (prep 對影片模式沒意義 — Gemini video 已經在做高層理解了)
    if args.mode == "prep" and not (args.transcript_first or args.transcript_only):
        print("[mode=prep] 自動啟用 --transcript-first", file=sys.stderr)
        args.transcript_first = True

    result = None
    used = ""

    if args.transcript_first or args.transcript_only:
        try:
            import youtube_transcript_api  # noqa: F401
        except ImportError:
            print(
                "錯誤: 使用 --transcript-first / --transcript-only 需要安裝 youtube-transcript-api",
                file=sys.stderr,
            )
            print("  pip install youtube-transcript-api", file=sys.stderr)
            print("  或 pip install -r .claude/skills/youtube-video-research/requirements.txt", file=sys.stderr)
            sys.exit(1)

        print(f"[字幕模式] 嘗試抓字幕... (backend={args.backend}, mode={args.mode})",
              file=sys.stderr)
        transcript = fetch_transcript(args.url)

        # 沒抓到 + 啟用 whisper fallback → 在地轉錄
        if not transcript and args.whisper_fallback:
            print("[字幕模式] 抓不到字幕,fallback 到 faster-whisper 在地轉錄", file=sys.stderr)
            try:
                # 把 scripts/ 加進 sys.path 以便 import sibling 模組
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                from whisper_local import transcribe as whisper_transcribe
                transcript = whisper_transcribe(args.url, model=args.whisper_model)
            except ImportError as e:
                print(f"錯誤: whisper-fallback 需要 faster-whisper: {e}", file=sys.stderr)
                print("  pip install faster-whisper", file=sys.stderr)
                sys.exit(1)

        if transcript:
            print(f"[字幕模式] 取得字幕 ({len(transcript)} 字),mode={args.mode}",
                  file=sys.stderr)
            if args.mode == "prep":
                # 實測 gemma4:e4b 規模模型無法做 prep (instruction following 不夠強,
                # 一定會 collapse 成 summarize 或 hallucinate 模板句)。所以 prep mode
                # 直接輸出 raw transcript + regex 抽出的實體表,讓 Opus 在 Claude Desktop
                # 端做合成 — 這才是真正能用的 pipeline。
                # 用 Gemini 做 prep 也沒意義 (Gemini 直接 summarize 品質就夠好)。
                print("[prep] 直接輸出 raw transcript + 實體表 (不過 LLM,gemma e4b 做不來 prep)",
                      file=sys.stderr)
                entity_section = _extract_entities(transcript)
                result = (
                    "## 原始字幕 (transcript)\n\n"
                    "Opus 處理建議: 用 prompts/synthesize_from_prep.txt 結合下方字幕做最終研究筆記。\n\n"
                    "```\n" + transcript + "\n```\n\n"
                    + (entity_section if entity_section else "")
                )
                used = f"transcript-only (mode=prep, no LLM)"
            else:
                # summarize 模式: 走 LLM
                sys_inst = None
                if args.backend == "ollama":
                    result = summarize_with_text_local(
                        transcript, prompt, args.model, system=sys_inst,
                    )
                else:
                    result = summarize_with_text(transcript, prompt, args.model, system=sys_inst)
                used = f"transcript + {args.backend}:{args.model} (mode={args.mode})"
        else:
            if args.transcript_only or args.mode == "prep":
                print("[字幕模式] 抓不到字幕,放棄。可加 --whisper-fallback 用在地語音轉錄",
                      file=sys.stderr)
                sys.exit(2)
            if args.backend == "ollama":
                print("[字幕模式] 抓不到字幕。backend=ollama 不支援直接讀影片,放棄。"
                      "可加 --whisper-fallback 用在地語音轉錄", file=sys.stderr)
                sys.exit(2)
            print("[字幕模式] 抓不到字幕,fallback 到 Gemini 讀影片", file=sys.stderr)

    if result is None:
        if args.backend == "ollama":
            print("錯誤: backend=ollama 不支援影片模式,請加 --transcript-first 或 --transcript-only",
                  file=sys.stderr)
            sys.exit(1)
        if args.mode == "prep":
            print("錯誤: mode=prep 不支援影片模式 (Gemini video 已是高層理解,不需要再 prep)",
                  file=sys.stderr)
            sys.exit(1)
        print(f"[影片模式] 直接讓 {args.model} 讀影片", file=sys.stderr)
        result = summarize_video(args.url, prompt, args.model)
        used = f"video + gemini:{args.model}"

    print(result)

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write("# YouTube 影片摘要\n\n")
            f.write(f"來源: {args.url}\n\n")
            f.write(f"模式: {used}\n\n")
            f.write("---\n\n")
            f.write(result)
        print(f"\n已存檔: {args.save}", file=sys.stderr)


if __name__ == "__main__":
    main()
