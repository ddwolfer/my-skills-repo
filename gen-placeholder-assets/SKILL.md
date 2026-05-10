---
name: gen-placeholder-assets
description: 為前端遊戲生成 placeholder 素材（sprites、spines、audio），讓遊戲能 build 和部署到 Stake。讀取 config.ts 自動判斷需要哪些符號，用 Python + Pillow 生成帶顏色的 WebP 圖片和最小 Spine 動畫檔。當使用者在 init-game 後想讓遊戲能 build、想產生暫代素材、想在 Stake 上預覽、或提到 placeholder assets 時都應觸發。使用方式：/gen-placeholder-assets games/pharaohs-cascade
---

# gen-placeholder-assets

init-game 完成後，生成最小可用的 placeholder 素材，讓遊戲可以 `pnpm run build` 並部署到 Stake 上預覽。

## 參數

- `$ARGUMENTS`: 遊戲路徑（例如：`games/pharaohs-cascade`）

## 產出物

| 目錄 | 產出 |
|------|------|
| `static/assets/sprites/` | 各符號 WebP + 背景 + 邊框 + Logo |
| `static/assets/spines/symbols/` | 各符號 Spine（.json + .atlas + symbols.png） |
| `src/game/assets.ts` | 完整素材清單 |
| `src/game/constants.ts` | SYMBOL_INFO_MAP 更新 |

## 執行流程

### Step 1: 讀取遊戲配置

讀取 `{game_path}/src/game/config.ts`，提取：

1. **符號列表**：`config.symbols` 的所有 key（如 H1, H2, L1, W, S）
2. **特殊符號**：`SPECIAL_SYMBOLS.wild` 和 `SPECIAL_SYMBOLS.scatter`
3. **版面大小**：`numReels` × `numRows`

分類符號：
- **H 系列**（高賠）：key 以 `H` 開頭
- **L 系列**（低賠）：key 以 `L` 開頭
- **W**：Wild
- **S**：Scatter
- **其他**：M（乘數）等

### Step 2: 生成 Python 腳本並執行

在遊戲根目錄生成 `_gen_placeholders.py`，然後用 `python _gen_placeholders.py` 執行。

腳本內容根據 Step 1 提取的符號列表動態生成，核心邏輯如下：

#### 2.1 符號靜態圖（WebP）

每個符號生成一張 200×200 帶顏色的 WebP 圖片，中心印上符號名稱：

```python
from PIL import Image, ImageDraw, ImageFont

# 配色方案
COLORS = {
    'H1': '#E74C3C',  # 紅
    'H2': '#E67E22',  # 橙
    'H3': '#F39C12',  # 琥珀
    'H4': '#D4AC0D',  # 金
    'L1': '#3498DB',  # 藍
    'L2': '#2ECC71',  # 綠
    'L3': '#1ABC9C',  # 青
    'L4': '#9B59B6',  # 紫
    'L5': '#5B7DB1',  # 灰藍
    'W':  '#F1C40F',  # 亮金（Wild）
    'S':  '#8E44AD',  # 深紫（Scatter）
    'M':  '#16A085',  # 翠綠（Multiplier）
}

def gen_symbol(name, color, size=200):
    img = Image.new('RGBA', (size, size), color)
    draw = ImageDraw.Draw(img)
    # 白色文字標記符號名稱
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), name, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2), name, fill='white', font=font)
    return img
```

#### 2.2 背景、邊框、Logo

```python
def gen_background(w, h, top_color, bot_color):
    """漸層背景"""
    img = Image.new('RGB', (w, h))
    for y in range(h):
        r = int(top_color[0] + (bot_color[0] - top_color[0]) * y / h)
        g = int(top_color[1] + (bot_color[1] - top_color[1]) * y / h)
        b = int(top_color[2] + (bot_color[2] - top_color[2]) * y / h)
        for x in range(w):
            img.putpixel((x, y), (r, g, b))
    return img

# bg_desktop: 2039×1000 深藍漸層
# bg_portrait: 1242×2208 深藍漸層
# frame: 800×600 帶金色邊框的透明圖
# LOGO: 400×200 帶遊戲名稱的圖
```

#### 2.3 Spine 動畫（JSON 格式）

每個符號生成 3 個檔案 + 1 個共享紋理：

| 檔案 | 說明 |
|------|------|
| `symbols.png` | 所有符號的 atlas 紋理（並排） |
| `{SYMBOL}.atlas` | 各符號的 atlas 描述（指向 symbols.png） |
| `{SYMBOL}.json` | Spine skeleton + 3 個動畫（land/win/explosion） |

**Atlas 格式**（Spine 4.2）：

```
symbols.png
size:{total_w},{total_h}
filter:Linear,Linear
pma:false
{symbol_name}
  bounds:{x},{y},{w},{h}
```

**Spine JSON 最小結構**：

```json
{
  "skeleton": { "spine": "4.2", "width": 200, "height": 200 },
  "bones": [{ "name": "root" }],
  "slots": [{ "name": "symbol", "bone": "root", "attachment": "{symbol_name}" }],
  "skins": [{
    "name": "default",
    "attachments": {
      "symbol": {
        "{symbol_name}": { "width": 200, "height": 200 }
      }
    }
  }],
  "animations": {
    "land": {
      "slots": { "symbol": { "attachment": [{ "time": 0, "name": "{symbol_name}" }] } }
    },
    "win": {
      "slots": { "symbol": { "attachment": [{ "time": 0, "name": "{symbol_name}" }] } }
    },
    "explosion": {
      "slots": { "symbol": { "attachment": [
        { "time": 0, "name": "{symbol_name}" },
        { "time": 0.3, "name": null }
      ] } }
    }
  }
}
```

> **為什麼用 JSON？** JSON 格式易於生成且 SDK 的 Spine loader 兩種都支援。正式美術交付也用 .json，所以 placeholder → 正式替換時格式一致，不需改 assets.ts 的路徑。

#### 2.4 音效

檢查 `static/assets/audio/` 是否有 `sounds.json`。如果有（init-game 會保留模板音效），不做任何修改。如果沒有，從模板複製：

```bash
cp sdks/web-sdk/apps/{template}/static/assets/audio/* {game_path}/static/assets/audio/
```

### Step 3: 更新 assets.ts

根據生成的檔案，重寫 `src/game/assets.ts`：

```typescript
export default {
    // ===== 背景 =====
    bg_desktop: {
        type: 'sprite',
        src: new URL('../../assets/sprites/bg_desktop.webp', import.meta.url).href,
        preload: true,
    },
    bg_portrait: {
        type: 'sprite',
        src: new URL('../../assets/sprites/bg_portrait.webp', import.meta.url).href,
        preload: true,
    },

    // ===== 邊框 =====
    frame: {
        type: 'sprite',
        src: new URL('../../assets/sprites/frame.webp', import.meta.url).href,
    },

    // ===== LOGO =====
    logo: {
        type: 'sprite',
        src: new URL('../../assets/sprites/LOGO.webp', import.meta.url).href,
    },

    // ===== 符號靜態圖 =====
    // 對每個符號生成 {NAME}_static entry
    {NAME}_static: {
        type: 'sprite',
        src: new URL('../../assets/sprites/{NAME}.webp', import.meta.url).href,
    },

    // ===== 符號 Spine 動畫 =====
    // 對每個符號生成 spine entry（JSON 格式）
    {NAME}: {
        type: 'spine',
        src: {
            atlas: new URL('../../assets/spines/symbols/{NAME}.atlas', import.meta.url).href,
            skeleton: new URL('../../assets/spines/symbols/{NAME}.json', import.meta.url).href,
            scale: 1,
        },
    },

    // ===== 音效 =====
    sound: {
        type: 'audio',
        src: new URL('../../assets/audio/sounds.json', import.meta.url).href,
        preload: true,
    },
} as const;
```

### Step 4: 更新 constants.ts

更新 `SYMBOL_INFO_MAP`，為每個符號設定 6 個狀態：

```typescript
const {name}Static = { type: 'sprite', assetKey: '{NAME}_static', sizeRatios: { width: 1, height: 1 } };

// SYMBOL_INFO_MAP entry:
{NAME}: {
    static: {name}Static,
    spin: {name}Static,
    postWinStatic: {name}Static,
    land: { type: 'spine', assetKey: '{NAME}', animationName: 'land', sizeRatios: { width: 0.5, height: 0.5 } },
    win: { type: 'spine', assetKey: '{NAME}', animationName: 'win', sizeRatios: { width: 0.5, height: 0.5 } },
    explosion: { type: 'spine', assetKey: '{NAME}', animationName: 'explosion', sizeRatios: { width: 1, height: 1 } },
},
```

同時確認：
- `INITIAL_BOARD` 只使用 config.ts 中定義的符號
- `HIGH_SYMBOLS` 只列出存在的 H 系列
- 沒有遊戲用不到的符號（如模板的 H5、L5、M）
- `MULTIPLIER_BACKGROUND_INFO_MAP` 若沒有 M 符號則留空 `{}`

### Step 5: 清理

```bash
# 刪除生成腳本
rm {game_path}/_gen_placeholders.py
```

### Step 6: 驗證

提醒使用者執行：

```bash
cd sdks/web-sdk && pnpm install
cd ../../games/{game_id} && pnpm run build
```

> **不要在 Bash 中執行 build**（Vite watch mode 會卡住），提醒使用者自行在終端執行。

### Step 7: Commit

```bash
cd games/{game_id}
git add static/assets/ src/game/assets.ts src/game/constants.ts
git commit -m "feat: 生成 placeholder 素材（sprites + spines + 音效）"
```

## 注意事項

- **WebP 格式**：使用 `img.save(path, 'WEBP', quality=80)` 壓縮
- **Spine JSON 格式**：placeholder 和正式美術都用 .json，格式一致免改 assets.ts
- **Atlas 紋理共享**：所有符號 spine 共用一張 `symbols.png`，各自的 `.atlas` 檔指向它
- **配色一致性**：同一符號的 sprite 和 spine atlas 紋理使用相同顏色
- **不要修改 sound.ts**：音效名稱定義由模板提供，placeholder 音效已覆蓋
- **Windows 相容**：Python 腳本用 `os.path.join()` 處理路徑
