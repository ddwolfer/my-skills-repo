---
name: refine-asset
description: 用 ComfyUI img2img 或 CLIPSeg inpainting 修改現有圖片素材。img2img 做風格轉換（保留構圖改風格），inpainting 做局部重繪（自動遮罩不需手動畫）。當使用者需要修改現有圖片風格、統一色調、局部替換某個元素、修正圖片細節、或提到 img2img / inpainting / 風格轉換 / 局部重繪時都應觸發。使用方式：/refine-asset img2img path/to/image.png 或 /refine-asset inpaint path/to/image.png
---

# refine-asset

用 ComfyUI 的 img2img 或 CLIPSeg auto-inpainting 修改現有圖片素材。
不需要從零生成，基於已有圖片做風格轉換或局部重繪。

## 參數

- `$ARGUMENTS`: `<mode> <image_path> [options]`
  - `mode`: `img2img` 或 `inpaint`
  - `image_path`: 要修改的圖片路徑（相對或絕對）

## 前置條件

- ComfyUI 需以 `--listen` 模式運行（localhost:8188）
- img2img 模式：無額外需求
- inpaint 模式：需安裝 `ComfyUI-CLIPSeg` 自定義節點
- Python `requests` 套件

---

## 執行流程

### Step 1: 解析參數

從 `$ARGUMENTS` 提取：
- `MODE`: `img2img` 或 `inpaint`
- `IMAGE_PATH`: 圖片路徑（驗證檔案存在）

如果參數不完整，提示使用者：
```
用法：/refine-asset <img2img|inpaint> <image_path>
範例：
  /refine-asset img2img Art/02-pharaohs-cascade/sprites/backgrounds/bg_desktop.png
  /refine-asset inpaint Art/02-pharaohs-cascade/sprites/_drafts/H1_raw.png
```

---

### Step 2: 收集必要資訊

根據模式向使用者確認參數：

#### img2img 模式

問使用者：
1. **Positive prompt** — 描述想要的輸出結果（風格、色調、氛圍）
2. **Denoise 強度**（預設 0.7）— 說明選擇指引：
   - `0.3~0.5`: 微調色調，構圖完全保留
   - `0.5~0.7`: 保留結構，明顯風格改動
   - `0.7~0.85`: 構圖保留但風格完全轉換
3. **Negative prompt**（預設 `"blurry, low quality, text, watermark"`）
4. **Guidance**（預設 3.5）
5. **Seed**（預設隨機）— 固定 seed 可重現結果

#### inpaint 模式

問使用者：
1. **遮罩目標描述**（CLIPSeg text）— 描述圖片中要修改的區域是什麼
   - 用英文，描述物件本身，不要描述動作
   - 好：`"the sun disk above the head"`
   - 壞：`"remove the sun disk"`
2. **Positive prompt** — 描述該區域要變成什麼
3. **Denoise 強度**（預設 0.75）— 範圍 0.65~0.85
4. **CLIPSeg threshold**（預設 0.4）— 越低選取越多區域
5. **Dilation factor**（預設 4）— 遮罩膨脹，讓遮罩比偵測區域大一圈
6. **Negative prompt**（預設 `"blurry, low quality, text, watermark"`）
7. **Seed**（預設隨機）

如果使用者沒指定可選參數，用預設值。不要逐一追問每個參數。

---

### Step 3: 驗證環境

在生成腳本前確認：

1. **ComfyUI 是否運行** — `curl http://localhost:8188/queue`
2. **inpaint 模式** — 額外檢查 CLIPSeg 節點是否可用：
   `curl http://localhost:8188/object_info` 中有 `CLIPSeg`
3. **圖片檔案是否存在** — 確認 IMAGE_PATH 有效

任一失敗則提示使用者修正，不要繼續。

---

### Step 4: 生成並執行 Python 腳本

生成一個 Python 腳本到 `Art/_shared/` 目錄下，命名為 `refine_{timestamp}.py`。

#### 腳本結構

```python
import sys
import json
import random
import time
import urllib.request
import urllib.parse
from pathlib import Path

# 加入 Art/_shared 到 path 以使用 comfyui_utils
sys.path.insert(0, str(Path(__file__).parent))
from comfyui_utils import upload_image, queue_prompt, wait_and_download, load_workflow

# === 設定 ===
IMAGE_PATH = r"{image_path}"
OUTPUT_DIR = Path(IMAGE_PATH).parent
OUTPUT_NAME = Path(IMAGE_PATH).stem + "_refined.png"

# === 載入 workflow ===
WORKFLOW_DIR = Path(__file__).parent
workflow = load_workflow(str(WORKFLOW_DIR / "{workflow_json}"))

# === 上傳圖片 ===
print(f"上傳圖片: {IMAGE_PATH}")
image_name = upload_image(IMAGE_PATH)
workflow["30"]["inputs"]["image"] = image_name

# === 設定參數 ===
{parameter_block}

# === 提交 ===
print("提交到 ComfyUI...")
prompt_id = queue_prompt(workflow)
print(f"Prompt ID: {prompt_id}")

# === 等待並下載 ===
print("等待生成...")
output_path = wait_and_download(prompt_id, str(OUTPUT_DIR / OUTPUT_NAME))
print(f"完成！輸出: {output_path}")
```

#### img2img 的 parameter_block

```python
workflow["19"]["inputs"]["text"] = "{positive_prompt}"
workflow["29"]["inputs"]["text"] = "{negative_prompt}"
workflow["17"]["inputs"]["denoise"] = {denoise}
workflow["17"]["inputs"]["seed"] = {seed}
workflow["18"]["inputs"]["guidance"] = {guidance}
workflow["16"]["inputs"]["filename_prefix"] = "{prefix}"
```

使用 `flux_img2img_api.json` 作為 workflow。

#### inpaint 的 parameter_block

```python
# CLIPSeg 遮罩設定
workflow["33"]["inputs"]["text"] = "{mask_target}"
workflow["33"]["inputs"]["threshold"] = {threshold}
workflow["33"]["inputs"]["dilation_factor"] = {dilation_factor}
workflow["33"]["inputs"]["blur"] = {blur}

# 重繪內容
workflow["19"]["inputs"]["text"] = "{positive_prompt}"
workflow["29"]["inputs"]["text"] = "{negative_prompt}"
workflow["17"]["inputs"]["denoise"] = {denoise}
workflow["17"]["inputs"]["seed"] = {seed}
workflow["16"]["inputs"]["filename_prefix"] = "{prefix}"
```

使用 `flux_inpainting_auto_api.json` 作為 workflow。

---

### Step 5: 執行腳本

用 PowerShell 執行生成的腳本：

```
powershell.exe -Command "cd 'Art/_shared'; python refine_{timestamp}.py"
```

**重要：一次只提交一張到 ComfyUI**（RTX 4060 8GB VRAM 限制）。

---

### Step 6: 驗證結果

腳本執行完成後：
1. 確認輸出檔案存在且非空（`ls -la` 檢查大小）
2. 告訴使用者輸出位置
3. 詢問是否需要：
   - 調整參數重新生成（改 denoise / prompt / seed）
   - 將結果替換原始檔案
   - 進一步用 Pillow 後處理（縮放、格式轉換 WebP）

---

## 節點 ID 對照表

兩個 workflow 共用相同的節點 ID 結構：

| 節點 ID | 功能 | 兩個 workflow 都有 |
|---------|------|-------------------|
| `30` | LoadImage — 輸入圖片 | ✅ |
| `19` | CLIPTextEncode — Positive prompt | ✅ |
| `29` | CLIPTextEncode — Negative prompt | ✅ |
| `18` | FluxGuidance — guidance 值 | ✅ |
| `17` | KSampler — seed, denoise, steps | ✅ |
| `16` | SaveImage — 輸出 | ✅ |
| `33` | CLIPSeg — 遮罩目標（僅 inpaint） | inpaint only |

---

## Denoise 決策指引

提供給使用者參考：

### img2img
| denoise | 效果 | 適用場景 |
|---------|------|---------|
| 0.3 | 微調色調，幾乎不變 | 統一一批符號的色溫 |
| 0.5 | 保留結構，風格微調 | 調整氛圍（暖→冷） |
| 0.7 | 推薦起始值，風格可轉換 | 照片→插畫、寫實→卡通 |
| 0.85 | 大幅重繪，只保留大致方向 | 需要大改但想保留構圖 |

### inpaint
| denoise | 效果 | 適用場景 |
|---------|------|---------|
| 0.65 | 保守，融合原圖 | 微調細節 |
| 0.75 | 推薦起始值 | 替換物件 |
| 0.85 | 大幅重繪遮罩區域 | 完全替換 |

---

## 注意事項

- **VRAM 限制**（RTX 4060 8GB）：一次只提交一張，不要批量排隊
- **ComfyUI 冷啟動** 首次載入 Flux 模型需 10-15 分鐘，之後每張 3-5 分鐘
- **CLIPSeg 遮罩效果不佳時**：降低 threshold（0.2）+ 提高 dilation_factor（6）
- **inpaint 結果與周圍不融合**：提高 blur（10-15）讓遮罩邊緣更柔和
- **輸出是 PNG**：如果最終素材需要 WebP，後續用 Pillow 轉換（quality=90）
- **迭代修改**：可以對同一張圖多次 inpaint，每次改一個區域（用輸出作為下次輸入）

---

## 範例用法

### 風格統一 — 讓 L1-L4 石板符號色調對齊 H1

```
/refine-asset img2img Art/02-pharaohs-cascade/sprites/_drafts/L1_composite.png
→ prompt: "golden sandstone tablet with ancient Egyptian hieroglyph, warm amber lighting, gold and lapis lazuli color palette, luxurious temple aesthetic"
→ denoise: 0.4（保留構圖，統一色調）
```

### 背景變體 — 從桌面背景生成 FS 暗色變體

```
/refine-asset img2img Art/02-pharaohs-cascade/sprites/backgrounds/bg_desktop.png
→ prompt: "dark mysterious Egyptian temple interior, deep purple and midnight blue atmosphere, mystical glowing hieroglyphs, ethereal fog"
→ denoise: 0.5（保留房間結構，改變氛圍）
```

### 局部修正 — 修改 Ra 太陽盤

```
/refine-asset inpaint Art/02-pharaohs-cascade/sprites/_drafts/H1_raw.png
→ mask target: "the golden disk above the eagle head"
→ prompt: "a magnificent radiant sun disk with golden rays emanating outward, ancient Egyptian solar symbol"
→ denoise: 0.75
```
