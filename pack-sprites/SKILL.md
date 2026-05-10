---
name: pack-sprites
description: 打包/解包 TexturePacker 格式的 spritesheet（JSON + PNG）。使用方式：/pack-sprites pack <目錄> [名稱] 或 /pack-sprites unpack <json檔案> [輸出目錄]
---

# pack-sprites

打包散圖為 spritesheet 或將 spritesheet 解包為散圖。輸出格式與 TexturePacker 相容（JSON + PNG），可直接供 PixiJS 使用。

## 參數

- `$ARGUMENTS`: `pack <目錄> [名稱]` 或 `unpack <json檔案> [輸出目錄]`

## 用法範例

```
/pack-sprites pack Art/01-dragon-feast/sprites/font
/pack-sprites pack Art/01-dragon-feast/sprites/font myAtlas
/pack-sprites unpack games/dragon-feast/static/assets/sprites/winSmall/MM_Localisation_winsmall.json
/pack-sprites unpack games/dragon-feast/static/assets/sprites/winSmall/MM_Localisation_winsmall.json ./output
```

---

## 執行流程

### 1. 解析參數

從 `$ARGUMENTS` 解析：
- 第 1 個參數：`pack` 或 `unpack`
- 第 2 個參數：目錄路徑（pack）或 JSON 檔案路徑（unpack）
- 第 3 個參數（選填）：輸出名稱（pack）或輸出目錄（unpack）

路徑如果是相對路徑，以專案根目錄為基準解析。

### 2. 前置檢查

- 確認 Python 3 可用：`python --version`
- 確認 Pillow 已安裝：`python -c "from PIL import Image"`
- 如果 Pillow 未安裝，提示使用者執行 `pip install Pillow`

### 3. 執行腳本

腳本位置：`.claude/scripts/spritesheet.py`（相對於專案根目錄）

```bash
python .claude/scripts/spritesheet.py <command> <path> [name_or_output]
```

### 4. 回報結果

#### Pack 模式
- 顯示產出的 JSON + PNG 路徑與尺寸
- 列出所有打包的 frame 名稱與原始尺寸
- 用 Read 工具顯示產出的 PNG 預覽

#### Unpack 模式
- 顯示解包的圖片數量與輸出目錄
- 列出所有解包的 frame 名稱與尺寸

---

## 腳本功能說明

### Pack（打包）

- 讀取目錄下所有 `.png` 散圖（排除與輸出同名的檔案）
- 自動 trim 透明邊緣，記錄 `trimmed` / `spriteSourceSize` 供還原
- Shelf packing 演算法，最大寬度 1024px
- 輸出 `{name}.json` + `{name}.png`，預設名稱為目錄名

### Unpack（解包）

- 讀取 TexturePacker 格式的 JSON + 同名 PNG
- 還原 trimmed 圖片為原始 sourceSize（含透明邊距）
- 輸出到 `unpacked/` 子目錄（或指定目錄）

## 依賴

- Python 3
- Pillow（`pip install Pillow`）
