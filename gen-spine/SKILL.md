---
name: gen-spine
description: 用 Python + Pillow 生成 Spine 4.2 運行時檔案（.json + .atlas + .png）。提供格式規範、Atlas 打包模板、常見陷阱。使用方式：/gen-spine（查看規範）或 /gen-spine Art/01-dragon-feast/spine/newAnim
---

# gen-spine

用 Python + Pillow 從散圖生成 Spine 4.2 runtime 檔案。此 skill 是格式參考手冊 + 工作流程 SOP，不是全自動腳本。

## 參數

- `$ARGUMENTS`（選填）：目標目錄路徑，例如 `Art/01-dragon-feast/spine/fsRetrigger`
- 無參數時：顯示格式規範摘要

---

## 產出檔案

每個 Spine 動畫需要 3 個檔案：

| 檔案 | 說明 |
|------|------|
| `{name}.png` | Atlas 圖集（所有散圖打包成一張） |
| `{name}.atlas` | Atlas 描述檔（區域座標、濾鏡、PMA 設定） |
| `{name}.json` | Spine skeleton（骨架、插槽、皮膚、動畫） |

---

## 1. Atlas PNG 打包

用 Pillow 把 `images/` 目錄下的散圖打包成一張 atlas。

### 模板 code

```python
from PIL import Image
import os

IMAGES_DIR = "./images"
PAD = 2  # 區域間距

# 載入散圖
image_files = {"key_name": "filename.png", ...}
images = {}
for key, filename in image_files.items():
    img = Image.open(os.path.join(IMAGES_DIR, filename)).convert("RGBA")
    images[key] = img

# 手動排版（根據圖片大小規劃行列）
regions = {}
# regions["key"] = (x, y, width, height)
# ... 根據實際尺寸排列

# 建立 atlas
atlas_img = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
for key, (rx, ry, rw, rh) in regions.items():
    atlas_img.paste(images[key], (rx, ry))

# 佔位 slot（給 BitmapText 等動態內容用）
regions["slot_name"] = (0, 0, 1, 1)  # 1x1 透明像素

atlas_img.save("output.png", "PNG")
```

### 注意事項
- 散圖之間留 2px padding 避免 bleeding
- 佔位 slot（如 `slot_number`）用 1x1 透明像素，座標 (0,0,1,1)
- Atlas 尺寸不需要是 2 的冪次

---

## 2. Atlas 描述檔格式

```
{name}.png
size:{width},{height}
filter:Linear,Linear
pma:false
region_name_1
bounds:{x},{y},{width},{height}
region_name_2
bounds:{x},{y},{width},{height}
```

### 欄位說明

| 欄位 | 說明 |
|------|------|
| 第一行 | 對應的 PNG 檔名 |
| `size` | Atlas PNG 的像素尺寸 |
| `filter` | 縮放濾鏡，通常 `Linear,Linear` |
| `pma` | **重要！** Premultiplied Alpha。散圖未經預乘處理時必須設 `false` |
| `bounds` | 區域在 atlas 中的 `x,y,width,height` |

### ⚠️ PMA 地雷

- **`pma:false`** — 散圖是標準 RGBA（Photoshop / AI 生成的圖都是這種）
- **`pma:true`** — 散圖已經過預乘處理（RGB 已乘以 Alpha）
- 設錯會導致：additive blend 過亮、半透明邊緣出現白邊或黑邊
- **經驗法則：除非確定圖片已預乘，一律用 `pma:false`**

---

## 3. Spine JSON 格式

### 頂層結構

```json
{
    "skeleton": { ... },
    "bones": [ ... ],
    "slots": [ ... ],
    "skins": [ ... ],
    "animations": { ... }
}
```

### 3.1 skeleton

```json
{
    "hash": "uniqueId01",
    "spine": "4.2.43",
    "x": -400, "y": -400,
    "width": 800, "height": 800,
    "images": "./images/",
    "audio": "./audio"
}
```

- `spine`: 版本號，必須與 runtime 相容（專案用 4.2）
- `x, y, width, height`: bounding box，影響 Spine Editor 預覽範圍
- `images`: 散圖來源目錄（Spine Editor 用，runtime 不需要）

### 3.2 bones

```json
[
    { "name": "root" },
    { "name": "panel_bone", "parent": "root" },
    { "name": "text_bone", "parent": "panel_bone", "y": -40 }
]
```

- 第一個必須是 `root`（無 parent）
- `x, y`: 相對於 parent 的偏移
- `rotation`, `scaleX`, `scaleY`: 初始變換

### 3.3 slots

```json
[
    { "name": "bg", "bone": "root", "attachment": "bg_image" },
    { "name": "glow", "bone": "root", "color": "ffa50060", "attachment": "glow_image", "blend": "additive" },
    { "name": "slot_number", "bone": "number_bone", "attachment": "slot_number" }
]
```

- **渲染順序**：陣列前面的先畫（最底層），後面的蓋在上面
- `color`: RRGGBBAA hex，AA 是初始透明度
- `blend`: `"normal"`（預設）或 `"additive"`（光芒、粒子用）
- `attachment`: 對應 skins 中的 attachment 名稱

### 3.4 skins

```json
[{
    "name": "default",
    "attachments": {
        "slot_name": {
            "attachment_name": {
                "width": 310, "height": 239,
                "scaleX": 1.5, "scaleY": 1.5,
                "x": 0, "y": 0,
                "rotation": 0
            }
        }
    }
}]
```

- `width, height`: **必填**，對應 atlas 中該區域的原始像素尺寸
- `scaleX, scaleY`: attachment 級別的縮放
- 佔位 slot 的 width/height 設為 1

### 3.5 animations

```json
{
    "intro": {
        "bones": {
            "bone_name": {
                "rotate": [ { "value": 0 }, { "time": 2.5, "value": 360 } ],
                "translate": [ { "x": 0, "y": 0 }, { "time": 0.5, "x": 100 } ],
                "scale": [ { "x": 0, "y": 0 }, { "time": 0.3, "x": 1, "y": 1 } ]
            }
        },
        "slots": {
            "slot_name": {
                "rgba": [ { "color": "ffffff00" }, { "time": 0.5, "color": "ffffffff" } ],
                "rgb": [ { "color": "ffd700" } ],
                "alpha": [ { "value": 0 }, { "time": 0.5, "value": 1 } ]
            }
        }
    }
}
```

#### Bone 動畫軌道

| 軌道 | 關鍵幀欄位 | 說明 |
|------|-----------|------|
| `rotate` | `value`（角度） | 旋轉，正值逆時針 |
| `translate` | `x`, `y` | 位移 |
| `scale` | `x`, `y` | 縮放，省略 = 1.0 |

#### Slot 動畫軌道

| 軌道 | 關鍵幀欄位 | 說明 |
|------|-----------|------|
| `rgba` | `color`（RRGGBBAA） | 同時控制顏色+透明度 |
| `rgb` | `color`（RRGGBB） | 只控制顏色 |
| `alpha` | `value`（0-1） | 只控制透明度 |

#### 關鍵幀通用欄位

- `time`: 秒數（省略 = 0）
- `curve`: Bezier 控制點，格式 `[cx1, cy1, cx2, cy2]`（bone 的 scale 有 8 個值，x/y 各 4 個）
- 省略 `curve` = 線性插值

---

## 4. 遊戲整合 Checklist

完成 Spine 檔案後，整合到遊戲的步驟：

### 4.1 複製素材
```
{name}.json + {name}.atlas + {name}.png
→ games/{game}/static/assets/spines/{key}/
```

### 4.2 註冊素材 — `src/game/assets.ts`
```ts
{key}: {
    type: 'spine',
    src: {
        atlas: new URL('../../assets/spines/{key}/{name}.atlas', import.meta.url).href,
        skeleton: new URL('../../assets/spines/{key}/{name}.json', import.meta.url).href,
        scale: 2,
    },
},
```

### 4.3 建立元件 — `src/components/{Component}.svelte`

```svelte
<script lang="ts" module>
    export type EmitterEvent{Component} =
        | { type: '{key}Show' }
        | { type: '{key}Hide' }
        | { type: '{key}Play'; ... };
</script>

<script lang="ts">
    import { FadeContainer } from 'components-pixi';
    import { waitForResolve } from 'utils-shared/wait';
    import { SpineProvider, SpineTrack, SpineSlot } from 'pixi-svelte';

    let show = $state(false);
    let animationName = $state('');
    let oncomplete: () => void = () => {};  // ⚠️ 不要用 $state！

    context.eventEmitter.subscribeOnMount({
        {key}Show: () => (show = true),
        {key}Hide: () => { show = false; animationName = ''; },
        {key}Play: async (event) => {
            animationName = '';
            await new Promise((r) => requestAnimationFrame(r));
            animationName = 'intro';
            await waitForResolve((resolve) => (oncomplete = resolve));
        },
    });
</script>

<FadeContainer {show}>
    <SpineProvider key="{key}" width={...}>
        {#if animationName}
            <SpineTrack trackIndex={0} {animationName}
                listener={{ complete: () => oncomplete() }} />
        {/if}
        <SpineSlot slotName="slot_name">
            <!-- BitmapText 或其他動態內容 -->
        </SpineSlot>
    </SpineProvider>
</FadeContainer>
```

### 4.4 註冊事件類型 — `src/game/typesEmitterEvent.ts`
```ts
import type { EmitterEvent{Component} } from '../components/{Component}.svelte';

export type EmitterEventGame =
    | ...existing...
    | EmitterEvent{Component};
```

### 4.5 加入渲染樹 — `src/components/Game.svelte`
```svelte
import {Component} from './{Component}.svelte';
// 放在適當的渲染層級
<{Component} />
```

### 4.6 加入 handler — `src/game/bookEventHandlerMap.ts`
```ts
{eventName}: async (bookEvent: BookEventOfType<'{eventName}'>) => {
    eventEmitter.broadcast({ type: '{key}Show' });
    await eventEmitter.broadcastAsync({ type: '{key}Play', ... });
    eventEmitter.broadcast({ type: '{key}Hide' });
},
```

---

## 5. 常見陷阱

| 陷阱 | 說明 |
|------|------|
| `pma:true` 用在非預乘圖 | additive blend 過亮、半透明邊緣異常。用 `pma:false` |
| `oncomplete` 用 `$state` | Svelte 5 reactivity 導致 listener prop 重建 → 動畫重播。用普通變數 |
| `animationName` 寫死 | SpineTrack mount 時立即播放，導致 show 前就播完。用 `$state('')` + 條件渲染 |
| `width/height` 漏填 | skins attachments 的 width/height 是必填，漏掉會導致圖片不顯示 |
| slot 渲染順序錯 | slots 陣列順序 = 渲染順序（前面底層，後面頂層） |
| `blend: "additive"` 位置 | 寫在 slot 定義中，不是 skin 或 animation 中 |
| atlas region 名稱不匹配 | atlas 中的 region 名必須與 json skin attachment 名一致 |
| Spine 版本不匹配 | skeleton.spine 版本必須與 runtime 相容（專案用 4.2） |
| **slot default attachment 陷阱** | slot 直接設 `attachment: "xxx"` → 未播動畫時 setup pose 就顯示，多 slot 全顯示=「定格爆炸」。**修法**：slot 不設 `attachment` 欄位（或設 null），動畫在 t=0 顯式 `"attachment": [{"name": "xxx"}]` 指定。Crystal Match wish_ritual 實測踩過（2026-04-17）。 |
| animation key 順序 fallback | Spine 4.2 skeleton JSON 無 `defaultAnimation` 欄位；若 runtime fallback「第一個 animation as default」則看 `animations` object key 順序。把安全動畫（`land`/`idle`）放第一個，危險動畫（`explosion`）放最後。 |

---

## 6. 範例

完整範例參考：`Art/01-dragon-feast/spine/fsRetrigger/generate_spine.py`

該腳本生成了 fsRetrigger 動畫（2.5 秒）：
- 3 層 radial 光芒（additive blend，緩慢旋轉）
- 面板 bounce 進場 + 淡出
- "FREE SPINS" 文字淡入淡出
- `slot_number` 佔位給 BitmapText（`+N`）

## 依賴

- Python 3
- Pillow（`pip install Pillow`）
