---
name: gen-symbols
description: 從遊戲企劃書生成 ComfyUI 符號圖片批量產生腳本。讀取 SPEC.md 的符號表與美術風格，自動產生 Python 腳本供 ComfyUI 批量生成 symbol 圖片。當使用者提到符號圖片、symbol 生成、ComfyUI 符號 prompt、老虎機圖標設計、需要產出 H1-H4/L1-L5/W/S 的圖片、或想批量生成 slot 符號時都應觸發。使用方式：/gen-symbols specs/01-dragon-feast
---

# gen-symbols

從遊戲企劃書（SPEC.md）讀取符號定義與美術風格，自動生成一個專屬的 Python 腳本，
供使用者在 Windows ComfyUI 機器上批量產生 slot game 的 symbol 圖片。

## 參數

- `$ARGUMENTS`: SPEC 目錄路徑（例如：`specs/01-dragon-feast`）

---

## 執行流程

### Step 1: 解析參數

從 `$ARGUMENTS` 提取：
- `SPEC_DIR`: SPEC 目錄路徑（例如 `specs/01-dragon-feast`）
- `spec_folder`: SPEC 目錄名稱（例如 `01-dragon-feast`，從 SPEC_DIR 取最後一段）
- `game_id`: 從目錄名推導（例如 `dragon-feast`，去除數字前綴）
- `GamePascalCase`: 轉為 PascalCase（例如 `DragonFeast`）

```
specs/01-dragon-feast → spec_folder = "01-dragon-feast", game_id = "dragon-feast", GamePascalCase = "DragonFeast"
specs/06-dragon-fortune → spec_folder = "06-dragon-fortune", game_id = "dragon-fortune", GamePascalCase = "DragonFortune"
```

---

### Step 2: 讀取 SPEC.md

讀取 `{SPEC_DIR}/SPEC.md`，提取以下章節的資訊：

| SPEC 章節 | 提取內容 | 用途 |
|-----------|---------|------|
| § 1 遊戲概覽 | 主題描述（如「傳統中華節慶」） | 判斷整體美學方向 |
| § 2 美術風格與配色 | 整體風格定義、色彩配置（色碼表）、視覺元素指引 | 組合 `style_base` |
| § 3.1 符號一覽表 | 所有符號的 ID、中文名稱、英文名稱、說明 | 組合每個符號的 prompt |

具體需要提取的欄位：

**從 § 2 提取：**
- `art_style`: 整體風格定義的文字描述
- `color_palette`: 主色和輔色的色名與用途
- `visual_guide`: 視覺元素指引的描述（如「金箔質感」「中國工筆畫質感」）

**從 § 3.1 提取：**
- 每個符號的 `id`（H1, H2, ..., L1, L2, ..., W, S）
- 每個符號的 `english_name`
- 每個符號的 `description`（說明欄位）

---

### Step 3: 組合 Prompt

#### 3a. 組合 `style_base`（全域風格描述）

將 § 2 的資訊轉化為一句英文 prompt，格式：

```
"High-end slot game symbol, {art_style_keywords}, {color_palette_keywords}, {texture_keywords}, isolated on solid white background, clean edges, 8k resolution."
```

**轉化規則：**
- `art_style` 翻譯為對應的英文描述（如「半寫實」→ `semi-realistic`）
- `color_palette` 提取主色名（如「中國紅 + 金色 + 玉綠」→ `vibrant imperial red and jade green palette`）
- `visual_guide` 提取材質描述（如「金箔質感」→ `shimmering gold foil outlines`）
- 固定加入：`no depth of field, no shadows`（確保白底乾淨）
- 固定結尾：`isolated on solid white background, clean edges, 8k resolution`

**範例（dragon-feast）：**
```
"High-end slot game symbol, traditional Chinese Gongbi illustration style, semi-realistic, flat vector-like aesthetic with intricate details, shimmering gold foil outlines, vibrant imperial red and jade green palette, no depth of field, no shadows, isolated on solid white background, clean edges, 8k resolution."
```

#### 3b. 組合 `symbols` dict（各符號個別描述）

根據 § 3.1 每個符號的「說明」欄位，擴寫為英文 image prompt。

**擴寫規則（按符號層級）：**

| 層級 | 擴寫方向 | 描述長度 |
|------|---------|---------|
| H 系列（高付費） | 強調氣勢、華麗、精緻、材質感 | 較長（30-50 字） |
| L 系列（低付費） | 強調簡潔、可愛、辨識度高 | 中等（20-35 字） |
| W（Wild） | 強調特殊感、替代功能的視覺暗示 | 較長（30-50 字） |
| S（Scatter） | 強調觸發感、爆發力、節日感 | 較長（30-50 字） |

**每個符號 prompt 的結構：**
```
"a {adjective} {english_name}, {visual_details}, {material_texture}, {pose_or_composition}, center-aligned."
```

**擴寫範例（dragon-feast H1 龍 Dragon）：**

SPEC 說明：「最高價值符號，中國傳統祥龍」
→ 擴寫為：
```
"a majestic imperial golden dragon, dynamic but 2D silhouette, ornate scales with gold leaf texture, auspicious clouds around the tail, center-aligned."
```

**擴寫範例（dragon-feast L1 桃 Peach）：**

SPEC 說明：「桃子，長壽之果」
→ 擴寫為：
```
"a ripe longevity peach fruit (shoutao), warm pink-red skin with soft gradient, two jade green leaves on top, gold foil outline around the whole fruit, stylized 2D slot game illustration, festive Chinese motif, center-aligned."
```

---

### Step 4: 生成 Python 腳本

輸出檔案路徑：`Art/{spec_folder}/comfyUI/queue_symbol.py`

使用以下模板（完全複製 `comfyUI/queue_generate.py` 的架構）：

```python
import json
import urllib.request
import os

# 遊戲：{chinese_name} ({english_name})
# 生成日期：{today_date}
# 來源：{SPEC_DIR}/SPEC.md

# 1. 全域風格描述
style_base = "{style_base}"

# 2. 各符號描述
symbols = {
    "H1": "{h1_prompt}",
    "H2": "{h2_prompt}",
    ...
    "W": "{wild_prompt}",
    "S": "{scatter_prompt}",
}

# 3. 讀取 ComfyUI workflow API JSON
with open(os.path.join(os.path.dirname(__file__), "../../_shared/flux_workflow_api.json"), "rb") as f:
    workflow_data = json.load(f)

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    return urllib.request.urlopen(req).read()

# 4. 循環修改並發送請求
# 節點 ID 對照：
#   "19" → CLIPTextEncode（prompt 文字）
#   "16" → SaveImage（filename_prefix）
for filename, desc in symbols.items():
    full_prompt = f"{style_base}, {desc}"
    workflow_data["19"]["inputs"]["text"] = f"White background, {style_keyword}, {full_prompt}"
    workflow_data["16"]["inputs"]["filename_prefix"] = f"{GamePascalCase}_{filename}"
    print(f"正在排隊產生: {filename}...")
    queue_prompt(workflow_data)

print("所有請求已發送至 ComfyUI 隊列！")
```

**模板中的變數說明：**

| 變數 | 來源 | 範例 |
|------|------|------|
| `{chinese_name}` | SPEC § 1 遊戲中文名 | 金玉滿堂 |
| `{english_name}` | SPEC § 1 遊戲英文名 | Dragon Feast |
| `{today_date}` | 執行日期 | 2025-02-10 |
| `{SPEC_DIR}` | 參數 | specs/01-dragon-feast |
| `{style_base}` | Step 3a 的結果 | "High-end slot game symbol, ..." |
| `{style_keyword}` | 從 style_base 提取的 1-2 個風格關鍵字 | "gongbi style" |
| `{GamePascalCase}` | Step 1 推導 | DragonFeast |
| `{h1_prompt}` 等 | Step 3b 的結果 | "a majestic imperial golden dragon, ..." |

**關鍵節點 ID 對照（來自 `flux_workflow_api.json`）：**
- `"19"` → CLIPTextEncode 節點（寫入 prompt 文字）
- `"16"` → SaveImage 節點（設定 filename_prefix）

⚠️ 如果使用者更換了 workflow JSON，節點 ID 可能改變，需確認後調整。

---

### Step 5: 輸出報告

```
=== 符號生成腳本已建立 ===

檔案位置：Art/{spec_folder}/comfyUI/queue_symbol.py
符號數量：{N} 個（H: {n_high}, L: {n_low}, Special: {n_special}）
風格基底：{style_base 前 60 字}...

--- 符號列表 ---
H1: {english_name} — {prompt 前 40 字}...
H2: {english_name} — {prompt 前 40 字}...
...
W:  {english_name} — {prompt 前 40 字}...
S:  {english_name} — {prompt 前 40 字}...

--- 使用方式 ---
1. 將專案同步到 Windows ComfyUI 機器
2. cd Art/{spec_folder}/comfyUI/
3. 確認 ComfyUI 已啟動（http://127.0.0.1:8188）
4. python queue_symbol.py
5. 等待 ComfyUI 完成所有圖片生成
6. 產出圖片位於 ComfyUI 的 output/ 目錄

--- 後續處理（Art Agent 自動執行）---
1. rembg 去背（rembg i input.png output.png）
2. Pillow LANCZOS resize 為 200x200px
3. 存為 PNG（保留 alpha）+ WebP（quality=90）
4. 放到 games/{game_id}/static/assets/sprites/
5. 檔案命名：{H1.webp, H2.webp, ..., W.webp, S.webp}
```

---

## 注意事項

1. **Prompt 語言必須用英文** — Flux/Stable Diffusion 對英文 prompt 效果最好
2. **style_base 是最重要的部分** — 決定整套圖片的風格一致性，需仔細從 SPEC § 2 提煉
3. **每個符號 prompt 需要有足夠的視覺區分度** — 避免 H1 和 H2 生出來長得太像
4. **固定使用 `flux_workflow_api.json`** — 如果使用者更換 workflow，需手動確認節點 ID
5. **filename_prefix 格式** — `{GamePascalCase}_{symbol_id}`，確保 ComfyUI 輸出檔名可辨識
6. **解析度設 512×512** — 修改 workflow node "14" 的 width/height（1024 太慢，512 夠用→Pillow 放大）
7. **風格一致性三層策略**：
   - 第一層：統一 style_base + 負面 prompt
   - 第二層：相近 seed（H 系列 base_seed+1~4, L 系列 base_seed+10~13）
   - 第三層（備用）：IPAdapter Style Reference（weight 0.3-0.5）
8. **先跑 1 張測試** — 確認風格後再批次，避免全部重做
9. **去背用 rembg 不用 PS** — `rembg i input.png output.png`（Agent 可直接呼叫）
10. **一張一張排隊** — 避免 RTX 4060 8GB VRAM 卡住

---

## 參考

- 模板檔案：`comfyUI/queue_generate.py`（dragon-feast 的實作範例）
- Workflow JSON：`Art/_shared/flux_workflow_api.json`
- SPEC 模板：參考 `specs/01-dragon-feast/SPEC.md` 的 § 2 和 § 3.1 結構
