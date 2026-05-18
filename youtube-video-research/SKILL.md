---
name: youtube-video-research
description: "Use this skill whenever the user provides a YouTube URL (youtube.com/watch, youtu.be, /shorts/, /live/) and wants any kind of summary, analysis, research notes, key points, transcript-based digest, or content extraction from the video. Triggers include phrases like '幫我看這部影片', '摘要這支 YouTube', '整理重點', '研究筆記', '財經影片分析', 'summarize this video', or any task that requires understanding what's IN a YouTube video (visuals + audio, not just metadata). Also use when the user says 'use gemini_video.py' or refers to video research workflows in this project. Do NOT use for: video downloads, video editing/conversion, audio extraction, or non-YouTube video files (use other tools for those)."
---

# YouTube Video Research

This skill summarizes and analyzes YouTube videos using Google Gemini's video understanding (it reads visual frames + audio, not just transcripts). It supports a transcript-first fast path for cost savings, custom prompt templates for different research domains, and outputs structured Markdown notes.

## Quick Reference

| Task | Command |
|------|---------|
| 一般摘要 | `python scripts/gemini_video.py "<URL>"` |
| 存檔摘要 | `python scripts/gemini_video.py "<URL>" --save out.md` |
| 字幕優先(省 quota) | `python scripts/gemini_video.py "<URL>" --transcript-first --save out.md` |
| 用範本 prompt | `python scripts/gemini_video.py "<URL>" --prompt-file prompts/finance_research.txt --save out.md` |
| 只用字幕(不 fallback) | `python scripts/gemini_video.py "<URL>" --transcript-only --save out.md` |
| 地端 gemma4 摘要(免雲端) | `python scripts/gemini_video.py "<URL>" --transcript-only --backend ollama --save out.md` |
| 從 summary.md 自動抓圖 | `python scripts/extract_frames.py "<URL>" --from-summary out.md --output-dir frames/` |
| 指定時間戳抓圖 | `python scripts/extract_frames.py "<URL>" --timestamps 00:36,03:13 --output-dir frames/` |

(指令裡的路徑相對於 skill 資料夾。從專案根目錄執行時,記得把 `scripts/` 跟 `prompts/` 改成完整路徑,例如 `.claude/skills/youtube-video-research/scripts/gemini_video.py`。)

## When and how to use

### Default behaviour
直接給 Gemini 2.5 Pro 看影片。穩、能讀畫面、繁中輸出格式固定(主題/重點/時間戳/結論)。
缺點是 token 用很多(一支 10 分鐘以上影片動輒 50 萬 token+),會吃 quota。

### Transcript-first (推薦給有字幕的影片)
Pass `--transcript-first`。腳本會先用 `youtube-transcript-api` 抓字幕,抓到就把字幕餵給 Gemini 做純文字摘要,token 用量降一個數量級;抓不到字幕(純畫面影片、字幕關閉、區域鎖)就自動退回讀影片。

字幕模式對「**講話為主**」的影片特別划算 — podcast、財經分析、教學課程、會議錄影。對「**畫面有資訊**」的影片(GDC 演講有 slides、產品開箱、操作教學)就還是要走影片模式,字幕拿不到視覺資訊。

### Custom prompts
透過 `--prompt-file` 指向 `prompts/` 裡的範本。為什麼用檔案而不是直接寫在指令裡:**長 prompt 寫在 shell 字串會難維護**,改一個分節要重打整段;放檔案裡可以版本控管、可以多個範本切換。

現有範本:
- `prompts/default.txt` — 通用摘要(主題/重點/時間戳/結論)
- `prompts/finance_research.txt` — 財經/投資/產業分析(標的表格、邏輯鏈、數據引用、風險、講者觀點 vs 事實)

需要新領域?**新增一個 .txt 到 `prompts/`,不要改 `gemini_video.py`**。腳本只負責呼叫 Gemini,prompt 是內容,分開維護才不會互相污染。

## Setup

第一次在新專案用之前:

```bash
pip install -r .claude/skills/youtube-video-research/requirements.txt
```

API key 設定(擇一):
- 在專案根目錄放 `.env`,內容: `GEMINI_API_KEY=你的_key`(腳本會自動向上找,涵蓋深度到 6 層)
- 或設環境變數: `export GEMINI_API_KEY="..."`

key 從 https://aistudio.google.com/apikey 取得(免費,有大方額度)。

## 已知陷阱(別繞回去踩)

寫腳本時試過好幾條死路,結論都已經寫進腳本/SKILL.md。**不要嘗試以下「優化」**,它們都是壞路徑:

1. ❌ `FileData(file_uri=url)` 不帶 `mime_type` → Gemini 會當作沒收到影片,回「請提供連結」
2. ❌ `mime_type="video/*"` (wildcard) → 不被接受
3. ❌ 預設改用 `gemini-2.5-flash` 省 quota → Flash 模型常常**收到了 50 萬 token 影片卻說自己看不到**(訓練幻覺,用 Pro 才穩)
4. ❌ 沒給 `system_instruction` 強制視覺承認 → Flash 變更愛拒絕,Pro 偶爾也會抗拒

正確配方就是現在腳本裡的:`Part.from_uri(file_uri=url, mime_type="video/mp4")` + `gemini-2.5-pro` + `SYSTEM_INSTRUCTION` 三件套。

## 三階段 Pipeline (prep mode + Opus 合成)

針對「想要 Gemini 等級研究筆記但不想全程上雲」的場景,設計了一個三階段 pipeline:

```
Stage 1: 抓 transcript (字幕優先,沒字幕用 faster-whisper)
   ↓
Stage 2: prep mode 輸出結構化中介檔 (raw transcript + regex 抽取的實體表)
   ↓
Stage 3: Opus 在 Claude Desktop 讀中介檔做最終研究筆記
```

用法:

```bash
# 完整 pipeline (有字幕的影片)
python scripts/gemini_video.py "<URL>" --mode prep --backend ollama \
    --save inbox/$(date +%Y-%m-%d)_prepped.md

# 沒字幕的影片,加 whisper fallback
python scripts/gemini_video.py "<URL>" --mode prep --backend ollama \
    --whisper-fallback --save inbox/$(date +%Y-%m-%d)_prepped.md
```

然後在 Claude Desktop 開 `inbox/<date>_prepped.md`,告訴 Opus:「請依 `prompts/synthesize_from_prep.txt` 寫成研究筆記」。

### 重要實作經驗 (踩過的坑)

**原本想讓 gemma4:e4b 做 prep (合併碎片、加標點、分章節、抽實體),失敗。**
原因: 4b 級小模型對長 context 中文 prep 任務的 instruction following 太弱 — 不論
prompt 寫多嚴格、加 system instruction、加 few-shot、切 chunk 處理,gemma 都會:
1. 自動 collapse 成 summarize (寫 39 行就交差,原始 20K 字)
2. 從第 2 個 chunk 開始 hallucinate 跟模板化重複「週期、護城河」之類字眼
3. 自己加「總結成一句話」這種 user 沒要求的 section

實測結論: **gemma4:e4b 規模做不來 prep**。正確架構是直接 dump raw transcript +
regex 抽取的實體表,讓 Opus 在 Stage 3 做合成 — Opus 拿 raw transcript 完全 OK。
gemma 在這個 pipeline 沒角色。

如果之後試到 12B+ 規模、instruction following 較強的模型,可以重新評估 prep 路徑。
保留 `prompts/prep_transcript.txt` 給未來嘗試用。

### 為什麼這樣還是值得做

- 自動化: scheduled task 跑 prep,outputs 落到 inbox/ 等 Opus 處理
- 隱私: Stage 1+2 全在地,只有 Stage 3 上雲 (而且只給字幕,不給原始影片)
- 對 Claude Desktop / scheduled task 流程友善: 純檔案 I/O
- 抽出來的實體表減輕 Opus 工作 (regex 找股票代號/百分比/英文公司名相當穩)

## faster-whisper (沒字幕的影片才需要)

當 youtube-transcript-api 抓不到字幕時 (純畫面/字幕關閉/區域鎖),加 `--whisper-fallback`
會自動用 faster-whisper 在地轉錄音訊。

第一次用前安裝:

```bash
pip install faster-whisper
```

### Windows GPU 警告

`pip install faster-whisper` 不會自動裝 CUDA runtime。如果你的 Windows 沒裝
CUDA 12.x toolkit,跑 GPU 模式會 `RuntimeError: Library cublas64_12.dll is not found`。
腳本會 auto-detect device,**但偵測邏輯目前不夠嚴謹** — 它只看 torch.cuda.is_available()
不檢查 ctranslate2 的 cublas 是否真的能載入。

解決方案二擇一:
1. 強制走 CPU: `python whisper_local.py URL --device cpu`,small 模型約 3x realtime
2. 補裝 cublas: 從 https://developer.nvidia.com/cudnn 下載 cuDNN for CUDA 12.x,
   把裡面的 `cublas64_12.dll` / `cudnn_*.dll` 複製到 Python site-packages 的
   ctranslate2 資料夾,或加進 PATH

實測 RTX 4060 GPU large-v3 大約 10x realtime,CPU small 約 3x realtime。
中文影片 small 模型字幕品質尚可,large-v3 明顯更精準 (尤其專有名詞跟數字)。

## 地端 backend (Ollama / Gemma)

`--backend ollama` 走本地 Ollama (預設 `gemma4:e4b`),純文字字幕摘要,不上雲、無 API 費用。設定:

```bash
# .env
BACKEND=ollama              # 不設預設 gemini
OLLAMA_HOST=http://localhost:11434  # 預設值,本機免設
OLLAMA_MODEL=gemma4:e4b     # 預設值
```

**限制(已實測 Ollama 0.22.0)**:
- 不支援讀 video URL / 影片檔 (Ollama API 沒 video routing)
- 不支援 audio bytes,雖然 gemma4 model card 寫 audio capability,但 runtime 還沒接通 (送進去會回 `image: unknown format` 500 error)
- 所以**沒字幕的影片地端版會直接失敗**,要等 Ollama 加 audio routing,或自己接 faster-whisper 在地轉錄當 fallback (TODO)

**品質落差(實測 RTX 4060 + gemma4:e4b vs gemini-2.5-pro)**:
- 速度: gemma4 約 30 tok/s,30 分鐘影片字幕摘要約 25 秒
- 細節: gemma4 傾向**過度抽象化** — 會講「AI 應用很廣」「商業模式變遷」,但抓不到具體公司名 / 數字 / 時間戳; Gemini 版會帶出 OpenAI 營收、Anthropic 競爭、IGV ETF 這些獨特內容
- 結論: gemma4 適合「我只想知道這影片大概在講什麼」,要做研究筆記、要時間戳跟具體事件還是 Gemini 強

## 抓畫面截圖 (extract_frames.py)

`gemini_video.py` 摘要會帶時間戳；`extract_frames.py` 直接吃這個 summary,在每個時間戳抓一張 frame 出來,適合做圖文並茂的研究筆記。

實作走 `yt-dlp` 拿 stream URL → `ffmpeg -ss` fast seek 抓單張 frame,**不下載整支影片**,9 個時間戳的 30 分鐘影片大約 10 秒內跑完。

兩個來源擇一(也可同時):
- `--from-summary path/to/summary.md` — 解析所有 `[MM:SS]` / `[HH:MM:SS]`,**並自動把圖片以 `<img src="..." width="760">` 插回 summary.md 對應時間戳下方**(冪等,重跑不會重複插)。不想嵌入加 `--no-embed`,改寬度加 `--width 1000` (0=原尺寸)。
- `--timestamps "00:36,03:13,06:20"` — 直接列

為什麼用 HTML `<img>` 而不是 `![](...)`: Markdown 標準語法不支援指定寬度,原圖 1920px 在 viewer 裡會撐滿整頁,讀者反而看不出畫面細節跟內文的對應關係。HTML img 在 GitHub / VS Code preview / Obsidian 都能渲染。

### 人工複核 (推薦做最後一步)

抓回來後**請逐張看**圖片內容跟段落文字是否對得上。常見不對應的情況:
- 講者談 A 主題時鏡頭其實對到他自己的人頭(談話節目最常見) — 圖片是頭像,跟文字無關,**移除**
- 講者談 B 主題但畫面還停在上一段的 A 圖 — 移除或調整時間戳重抓
- 字幕段落本身被 LLM 摘要時微調過時間戳,實際畫面偏前/偏後 1-3 秒就差很多

逐張看→刪除無對應的 `<img>` 那行→把對應的 jpg 也從 frames/ 刪掉。這一步沒辦法完全自動化(LLM 判斷視覺對應有難度),但對一篇正式的研究筆記值得花這 1-2 分鐘。

依賴:
- Python: `yt-dlp` (在 requirements.txt)
- 系統: `ffmpeg` 必須在 PATH

別嘗試的死路:
1. ❌ 把 `-ss` 放在 `-i` 後面 → 變成 output seek,會解碼整段才丟掉前面的,30 分鐘影片要等 5 分鐘以上
2. ❌ 用 `format='best'` 抓有聲音的合併流 → 多花頻寬,反正只要 frame,`bestvideo` 就好

## 偵錯

如果 Gemini 回答看起來沒看到影片,**先看 stderr 的 `[token 用量] prompt=...` 那行**:
- `prompt < 1000` → 影片真的沒被送進去,檢查 URL 跟 mime_type
- `prompt > 100000` → 影片有送到,但模型在耍懶。換 Pro,或在 prompt 裡更直接命令它「直接描述你看到的畫面內容」

token 用量是判斷「沒給它」vs「給了它但裝不會」最快的工具,任何 LLM 拒絕視覺任務時都先看這個。

## 移植到其他專案

整包 `.claude/skills/youtube-video-research/` 自包含。複製 `.claude/` 整個資料夾到新專案就能用,只需要:
1. 在新專案根放 `.env`(API key)
2. `pip install -r .claude/skills/youtube-video-research/requirements.txt`

不需要改任何程式碼或設定。
