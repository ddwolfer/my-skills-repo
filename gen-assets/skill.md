---
name: gen-assets
description: 從遊戲企劃書生成 ComfyUI 全素材批量產生腳本。讀取 SPEC.md，產生包含背景、Logo、贏分彈窗等多批次的 Python 腳本。當使用者需要生成背景圖、Logo、贏分彈窗、邊框、Grid Frame、乘數格底圖、Game Tile 等非符號美術素材的 AI 生成腳本時使用。即使使用者只說「幫我做背景」「需要 ComfyUI prompt」「產生美術素材」或「生成送審磚圖」也應觸發。使用方式：/gen-assets specs/01-dragon-feast
---

# gen-assets

從遊戲企劃書（SPEC.md）讀取美術風格定義與素材需求清單，自動生成一個 Python 腳本，
包含多個批次（背景、Logo、贏分彈窗等），供使用者在 Windows ComfyUI 機器上批量產生遊戲美術素材。

> **注意**：符號圖片（H1–H4、L1–L5、W、S）由 `/gen-symbols` skill 負責，本 skill 不重複生成。

## 參數

- `$ARGUMENTS`: SPEC 目錄路徑（例如：`specs/01-dragon-feast`）

---

## 涵蓋素材

| 批次 | 素材 | 輸出尺寸 | ComfyUI 生成尺寸 | 後續處理 |
|------|------|---------|--------------------|----|
| Batch 1: Backgrounds | 桌面版背景 | 1920x1080 | 768x432 | Pillow LANCZOS 放大 |
| Batch 1: Backgrounds | 直向版背景 | 1080x1920 | 432x768 | Pillow LANCZOS 放大（prompt 要寫 front-facing） |
| Batch 2: Logo | 遊戲 Logo 視覺元素 | 800x400 | 512x256 | rembg 去背 + Pillow 放大 |
| Batch 3: Win Popups | 贏分彈窗背景（Big/Mega/Epic） | 800x600 | 512x384 | Pillow 放大 |
| Batch 4: Multiplier Marks | 乘數格標記底圖 | 100x100 | 512x512 | Pillow 縮小 |
| Batch 5: Grid Frame | 盤面邊框（格子區域外框） | 512x512 | Pillow 程式繪製 | 九宮格框用 Pillow 不用 ComfyUI（精確幾何） |
| Batch 5b: Frame Decorations | 邊框裝飾組件 | 各異 | 512x512 | rembg 去背 + Pillow 縮放（角飾/寶石/象形文字帶） |
| Batch 6: Game Tiles | 審核用磚圖背景（BG） | 1920x1080 | 768x432 | Pillow 放大，命名 `GameTitle-BG.png` |
| Batch 6: Game Tiles | 審核用磚圖前景（FG） | 透明 PNG | 512x512 | rembg 去背，命名 `GameTitle-FG.png` |
| Batch 6: Game Tiles | 供應商 Logo | 透明 PNG | 512x512 | rembg 去背，命名 `ProviderName-Logo.png` |

> **效能注意**：RTX 4060 (8GB VRAM) 跑 Flux 模型，512 寬度約 3-5 分鐘/張。不要用 1024+ 解析度直接生成，改用 512 生成 + Pillow LANCZOS 放大。

### 不涵蓋的素材（不適合 AI 生成）

| 素材 | 原因 | 建議方式 |
|------|------|---------|
| UI 按鈕（120x60） | 太小、需精確文字與多狀態 | PS 手工製作 |
| Spine 動畫骨架 | 需要 Spine 編輯器製作 | Spine 4.x |
| 符號圖片 | 已由 `/gen-symbols` 負責 | `/gen-symbols` |

---

## 執行流程

### Step 1: 解析參數

從 `$ARGUMENTS` 提取：
- `SPEC_DIR`: SPEC 目錄路徑（例如 `specs/01-dragon-feast`）
- `spec_folder`: SPEC 目錄名稱（例如 `01-dragon-feast`，從 SPEC_DIR 取最後一段）
- `game_id`: 從目錄名推導（例如 `dragon-feast`，去除數字前綴）
- `GamePascalCase`: 轉為 PascalCase（例如 `DragonFeast`）

---

### Step 2: 讀取 SPEC.md

提取以下章節：

| SPEC 章節 | 提取內容 | 用途 |
|-----------|---------|------|
| § 1 遊戲概覽 | 遊戲名稱（中英文）、主題 | 推導整體視覺方向 |
| § 2 美術風格與配色 | 整體風格定義、色彩配置、背景設計、視覺元素指引 | 所有 batch 的風格基底 |
| § 4 美術素材尺寸規格 | 背景與 UI 素材表 | 確認尺寸、格式需求 |
| § 5 動畫規格 | 贏分動畫等級（Big/Mega/Epic Win 條件） | Win Popup 的分級設計 |
| § 7 核心玩法 | 乘數格系統說明 | 乘數格標記的設計方向 |

---

### Step 3: 組合 Prompt

#### 3a. `style_base`（全域場景風格）

與 gen-symbols 的 style_base 不同，這裡的 style_base 是場景導向，不需要白底：

```
"{art_style_from_spec}, {color_palette}, {atmosphere_description}, cinematic lighting, high detail, 8k resolution."
```

**範例（dragon-feast）：**
```
"Traditional Chinese festival aesthetic, rich imperial red and gold palette, warm ambient glow, ornate golden decorations, cinematic lighting, high detail, 8k resolution."
```

#### 3b. 各批次 Prompt 組合

**Batch 1: Backgrounds（背景）**

從 SPEC § 2「背景設計」提取場景、動態元素、氛圍、分層建議，轉化為英文 prompt：

```python
backgrounds = {
    "bg_desktop": {
        "width": 1920, "height": 1080,
        "prompt": "{style_base}, {scene_description}, wide panoramic composition, desktop game background, no UI elements, no text."
    },
    "bg_portrait": {
        "width": 1080, "height": 1920,
        "prompt": "{style_base}, {scene_description}, tall vertical composition, mobile portrait game background, no UI elements, no text."
    },
}
```

Prompt 擴寫規則：
- 直接翻譯 § 2「背景設計」的「場景」欄位（如「紅燈籠高掛的廟宇庭院」→ `"a grand Chinese temple courtyard with hanging red lanterns"`）
- 加入「氛圍」描述（如「溫暖的紅金色調」→ `"warm red-gold ambiance"`）
- 桌面版強調 `wide panoramic composition`
- 直向版強調 `tall vertical composition`
- 固定加入 `no UI elements, no text`（避免 AI 生成文字或按鈕）

**Batch 2: Logo（遊戲標誌視覺元素）**

⚠️ AI 不擅長生成精確文字，所以 Logo prompt 應聚焦在「視覺元素/裝飾框架」而非文字本身。

```python
logos = {
    "logo_base": {
        "width": 1024, "height": 512,
        "prompt": "{style_base}, ornate golden frame with {theme_motifs}, decorative emblem design, symmetrical composition, isolated on solid white background, no text, no letters, no characters."
    },
}
```

Prompt 擴寫規則：
- 從遊戲主題提取代表性視覺元素（如「龍鳳呈祥」「金色祥雲」）
- 強調裝飾性、對稱構圖
- **必須加入 `no text, no letters, no characters`**（文字由 PS 後製）
- 白底方便去背

**Batch 3: Win Popup Backgrounds（贏分彈窗背景）**

從 SPEC § 5.3「贏分動畫等級」提取各級別的視覺描述：

```python
win_popups = {
    "winbg_big": {
        "width": 1024, "height": 768,
        "prompt": "{style_base}, celebratory golden frame, {level_specific_elements}, radial light burst, festive atmosphere, no text."
    },
    "winbg_mega": {
        "width": 1024, "height": 768,
        "prompt": "{style_base}, epic celebration scene, {level_specific_elements}, dramatic golden light rays, fireworks, no text."
    },
    "winbg_epic": {
        "width": 1024, "height": 768,
        "prompt": "{style_base}, legendary victory scene, {level_specific_elements}, full screen golden explosion, dragon and phoenix, no text."
    },
}
```

Prompt 擴寫規則：
- Big Win：簡單慶祝（金幣飛散、光暈）
- Mega Win：中等華麗（龍飛鳳舞、全螢幕光效）
- Epic Win：最高規格（全螢幕慶典、金幣雨、主題終極元素）
- 所有等級加入 `no text`（文字由前端程式動態渲染）

**Batch 4: Multiplier Marks（乘數格底圖）**

```python
multiplier_marks = {
    "mult_base": {
        "width": 512, "height": 512,
        "prompt": "{style_base}, glowing magical tile marker, golden ornate border, translucent center, energy aura effect, game UI element, isolated on solid white background, no text, no numbers."
    },
}
```

Prompt 擴寫規則：
- 只生成一個底圖模板（數字由 PS 後加）
- 強調光暈、能量感、邊框裝飾
- 白底方便去背

**Batch 5: Grid Frame（盤面邊框）**

```python
grid_frame = {
    "grid_frame": {
        "width": 1024, "height": 1024,
        "prompt": "{style_base}, an ornate square game board frame border for a {cols}x{rows} slot grid, elaborate golden traditional border with intricate scrollwork and {theme_motifs}, corner ornaments, the center area is completely empty and transparent, {frame_material_texture}, thick luxurious border frame only, isolated on solid white background, no grid lines, no symbols, no text, no characters."
    },
}
```

Prompt 擴寫規則：
- 正方形 1024x1024（因為大部分 grid 都是正方形或接近正方形）
- 強調「中間完全空白」（`center area is completely empty and transparent`）
- 邊框風格匹配遊戲主題（中式雲紋、北歐符文、賽博霓虹等）
- 白底方便去背，後續疊在格子區域上方當裝飾外框
- 不需要格線（格線由 CSS 處理）

**Batch 6: Game Tiles（審核提交用磚圖素材）**

> 根據 Stake Engine Approval Guidelines §7，每次提交審核必須附上 BG Image + FG Image + Provider Logo。
> BG+FG 合計不得超過 **3MB**。

```python
game_tiles = {
    "tile_bg": {
        "width": 1920, "height": 1080,
        "prompt": "{style_base}, {scene_description}, cinematic wide shot, vibrant game world environment, rich atmosphere, high resolution promotional artwork, no UI elements, no text, no frame."
    },
    "tile_fg": {
        "width": 1024, "height": 1024,
        "prompt": "{style_base}, {main_character_or_key_object}, single iconic character or object, centered composition, dynamic pose, detailed rendering, isolated on solid white background, no text, no frame, no background scenery."
    },
    "tile_logo": {
        "width": 1024, "height": 1024,
        "prompt": "{style_base}, a professional game studio logo emblem, clean modern design with {theme_accent_color}, minimalist iconic symbol, vector-style, must be legible at small sizes, isolated on solid white background, no text, no letters."
    },
}
```

Prompt 擴寫規則：
- **tile_bg**：與 bg_desktop 風格一致但更強調宣傳感（promotional artwork），展示遊戲世界的環境氛圍
- **tile_fg**：提取遊戲中最具代表性的角色或物件（如金龍、法老面具、維京戰士），必須白底方便去背為透明 PNG
- **tile_logo**：供應商/工作室 Logo 的視覺元素，小尺寸仍可辨識（`legible at small sizes`），白底方便去背
- 命名規範（PS 導出時）：
  - BG: `{GameTitle}-BG.png` 或 `.jpg`（如 `DragonFeast-BG.png`）
  - FG: `{GameTitle}-FG.png`（**必須透明背景**）
  - Logo: `{ProviderName}-Logo.png`（**必須透明背景**）
- ⚠️ BG + FG 合計檔案大小不超過 3MB

---

### Step 4: 生成 Python 腳本

輸出路徑：`Art/{spec_folder}/comfyUI/queue_assets.py`

模板結構：

```python
import json
import urllib.request
import copy
import os

# 遊戲：{chinese_name} ({english_name})
# 生成日期：{today_date}
# 來源：{SPEC_DIR}/SPEC.md
# 用途：背景、Logo、贏分彈窗、乘數格等非符號素材

# ============================================================
# 全域風格
# ============================================================
style_base = "..."

# ============================================================
# 素材定義（每個素材包含 width, height, prompt）
# ============================================================
assets = {
    # --- Batch 1: Backgrounds ---
    "bg_desktop": {
        "width": 1920, "height": 1080,
        "prompt": "..."
    },
    "bg_portrait": {
        "width": 1080, "height": 1920,
        "prompt": "..."
    },

    # --- Batch 2: Logo ---
    "logo_base": {
        "width": 1024, "height": 512,
        "prompt": "..."
    },

    # --- Batch 3: Win Popup Backgrounds ---
    "winbg_big": {
        "width": 1024, "height": 768,
        "prompt": "..."
    },
    "winbg_mega": {
        "width": 1024, "height": 768,
        "prompt": "..."
    },
    "winbg_epic": {
        "width": 1024, "height": 768,
        "prompt": "..."
    },

    # --- Batch 4: Multiplier Marks ---
    "mult_base": {
        "width": 512, "height": 512,
        "prompt": "..."
    },

    # --- Batch 5: Grid Frame ---
    "grid_frame": {
        "width": 1024, "height": 1024,
        "prompt": "..."
    },

    # --- Batch 6: Game Tiles（審核提交用） ---
    "tile_bg": {
        "width": 1920, "height": 1080,
        "prompt": "..."
    },
    "tile_fg": {
        "width": 1024, "height": 1024,
        "prompt": "..."
    },
    "tile_logo": {
        "width": 1024, "height": 1024,
        "prompt": "..."
    },
}

# ============================================================
# ComfyUI API
# ============================================================
with open(os.path.join(os.path.dirname(__file__), "../../_shared/flux_workflow_api.json"), "rb") as f:
    workflow_template = json.load(f)

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    return urllib.request.urlopen(req).read()

# ============================================================
# 批次生成
# ============================================================
for asset_name, asset_cfg in assets.items():
    workflow_data = copy.deepcopy(workflow_template)

    # 設定解析度（Node "14": EmptyLatentImage）
    workflow_data["14"]["inputs"]["width"] = asset_cfg["width"]
    workflow_data["14"]["inputs"]["height"] = asset_cfg["height"]

    # 設定 prompt（Node "19": CLIPTextEncode）
    workflow_data["19"]["inputs"]["text"] = asset_cfg["prompt"]

    # 設定檔名（Node "16": SaveImage）
    workflow_data["16"]["inputs"]["filename_prefix"] = f"{GamePascalCase}_{asset_name}"

    print(f"正在排隊產生: {asset_name} ({asset_cfg['width']}x{asset_cfg['height']})...")
    queue_prompt(workflow_data)

print(f"\n所有 {len(assets)} 個素材請求已發送至 ComfyUI 隊列！")
```

**與 gen-symbols 的關鍵差異：**

| 差異 | gen-symbols | gen-assets |
|------|-------------|-----------|
| workflow 複製 | 直接修改同一份 workflow_data | 每次 `copy.deepcopy`（因為改 resolution） |
| Node "14" | 不修改（固定 1024x1024） | 每個素材不同 resolution |
| Node "19" | `style_base + 符號描述` | 各素材獨立的完整 prompt |
| 輸出數量 | 11 個（固定符號數） | 7+ 個（依 SPEC 需求） |

**Workflow 節點 ID 對照（來自 `flux_workflow_api.json`）：**
- `"14"` → EmptyLatentImage（width, height）
- `"19"` → CLIPTextEncode（prompt 文字）
- `"16"` → SaveImage（filename_prefix）

---

### Step 5: 輸出報告

```
=== 遊戲素材生成腳本已建立 ===

檔案位置：Art/{spec_folder}/comfyUI/queue_assets.py
素材數量：{N} 個

--- 素材清單 ---
[Backgrounds]
  bg_desktop:   1920x1080 — {prompt 前 40 字}...
  bg_portrait:  1080x1920 — {prompt 前 40 字}...

[Logo]
  logo_base:    1024x512  — {prompt 前 40 字}...

[Win Popups]
  winbg_big:    1024x768  — {prompt 前 40 字}...
  winbg_mega:   1024x768  — {prompt 前 40 字}...
  winbg_epic:   1024x768  — {prompt 前 40 字}...

[Multiplier]
  mult_base:    512x512   — {prompt 前 40 字}...

[Grid Frame]
  grid_frame:   1024x1024 — {prompt 前 40 字}...

[Game Tiles — 審核提交用]
  tile_bg:      1920x1080 — {prompt 前 40 字}...
  tile_fg:      1024x1024 — {prompt 前 40 字}...
  tile_logo:    1024x1024 — {prompt 前 40 字}...

--- 使用方式 ---
1. 將專案同步到 Windows ComfyUI 機器
2. cd Art/{spec_folder}/comfyUI/
3. 確認 ComfyUI 已啟動（http://127.0.0.1:8188）
4. python queue_assets.py
5. 等待 ComfyUI 完成所有圖片生成
6. 產出圖片位於 ComfyUI 的 output/ 目錄

--- 後續 PS 處理清單 ---
| 素材 | PS 處理 | 最終尺寸 | 放置路徑 |
|------|--------|---------|---------|
| bg_desktop | 微調色彩/裁切 | 1920x1080 | games/{game_id}/static/assets/bg/ |
| bg_portrait | 微調色彩/裁切 | 1080x1920 | games/{game_id}/static/assets/bg/ |
| logo_base | 去背 + 疊加遊戲名稱文字 | 800x400 | games/{game_id}/static/assets/ |
| winbg_* | resize + 疊加贏分文字 | 800x600 | games/{game_id}/static/assets/win/ |
| mult_base | 去背 + 加數字(x2/x3/x5) | 100x100 (每個) | games/{game_id}/static/assets/multiplier/ |
| grid_frame | 去背（中間保持透明） | 依格子區域大小 | games/{game_id}/static/assets/ |
| tile_bg | 微調色彩，確認高畫質 | 1920x1080 | 提交審核用（`GameTitle-BG.png/jpg`） |
| tile_fg | **去背為透明 PNG** | 原尺寸 | 提交審核用（`GameTitle-FG.png`） |
| tile_logo | **去背為透明 PNG**，確認小尺寸清晰 | 原尺寸 | 提交審核用（`ProviderName-Logo.png`） |

⚠️ **Game Tile 注意**：BG + FG 合計檔案大小不超過 3MB（Stake Engine 審核規範 §7）

--- 搭配使用 ---
符號圖片請用：/gen-symbols {SPEC_DIR}
```

---

## 注意事項

1. **每個素材的 resolution 不同** — 腳本使用 `copy.deepcopy` 避免 workflow 狀態汙染
2. **背景不需要白底** — 場景類素材直接渲染完整場景
3. **Logo 和 Win Popup 不加文字** — prompt 中明確加入 `no text, no letters`，文字全部由 PS 後製
4. **乘數格只生成一個底圖** — 數字 (x2/x3/x5) 由 PS 後加，確保清晰度
5. **Flux 模型對超大尺寸可能不穩定** — 如果 1920x1080 品質不佳，可改為 1024x576 再 PS upscale
6. **`flux_workflow_api.json` 必須支援動態 resolution** — 確認 Node "14" 的 width/height 可被覆寫

---

## 依賴

- `/gen-symbols` skill（符號圖片）
- `Art/_shared/flux_workflow_api.json`（共用 workflow）
- ComfyUI 伺服器運行在 `http://127.0.0.1:8188`
