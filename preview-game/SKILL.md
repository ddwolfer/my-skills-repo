---
name: preview-game
description: 讓前端遊戲在開發模式下顯示第一個靜態畫面。使用時機：init-game 完成後、基本素材（符號圖片、背景、邊框）已放入 static/assets/ 時。掃描實際素材並改寫程式碼，繞過缺失的 RGS 後端和進階動畫資源。使用方式：/preview-game games/dragon-feast
---

# preview-game

將 init-game 產生的模板專案接上實際素材，讓 `npm run dev` 顯示第一個靜態畫面（背景 + 邊框 + 符號格子）。

## 參數

- `$ARGUMENTS`: 遊戲專案路徑（例如：`games/dragon-feast`）

## 前置條件

使用者已完成：
1. `/init-game` 建立專案骨架
2. 符號圖片放入 `static/assets/sprites/`（如 H1.png ~ W.png）
3. 背景圖放入 `static/assets/sprites/`（如 bg_desktop.png）
4. 邊框圖放入 `static/assets/sprites/`（如 frame.png）
5. （可選）Spine 動畫放入 `static/assets/spines/symbols/`（.skel/.json + .atlas + .png）

## 執行流程

### Step 1: 讀取遊戲配置

讀取 `$ARGUMENTS/src/game/config.ts`，提取：
- 所有符號 ID（config.symbols 的 keys，例如 W, S, H1-H4, L1-L5）
- numReels、numRows
- gameName

### Step 2: 掃描實際素材

掃描 `$ARGUMENTS/static/assets/` 下所有存在的檔案：

```
sprites/     → *.png, *.jpg, *.webp
spines/      → **/*.skel, **/*.json, **/*.atlas, **/*.png
```

建立「存在清單」和「缺失清單」（對比模板 assets.ts 的引用）。

### Step 3: 重寫 assets.ts

`$ARGUMENTS/src/game/assets.ts`

**規則：只註冊實際存在的素材，不引用任何不存在的檔案。**

#### 3.1 背景圖

掃描 `sprites/` 找到背景圖（bg_desktop.png 或類似名稱），註冊為 `preload: true` 的 sprite：
```ts
bg_desktop: {
    type: 'sprite',
    src: new URL('../../assets/sprites/bg_desktop.png', import.meta.url).href,
    preload: true,
},
```

#### 3.2 邊框圖

```ts
frame: {
    type: 'sprite',
    src: new URL('../../assets/sprites/frame.png', import.meta.url).href,
},
```

#### 3.3 符號 Spine 動畫

如果 `spines/symbols/` 中存在 .skel 或 .json 檔案，為每個符號註冊 spine 資源。

**自動偵測格式**：SDK 的 `assetLoad.ts` 會根據 `Uint8Array` 判斷是否為二進制（.skel），無需手動指定。

```ts
H1: {
    type: 'spine',
    src: {
        atlas: new URL('../../assets/spines/symbols/H1.atlas', import.meta.url).href,
        skeleton: new URL('../../assets/spines/symbols/H1.skel', import.meta.url).href,
        scale: 1,
    },
},
```

**注意事項：**
- 如果所有符號共用一個 atlas（如 `symbols.atlas`），使用該共用路徑
- 如果每個符號有獨立 atlas（如 `H1.atlas`），使用各自路徑
- scale 設為 1（符號通常 200x200，顯示時由組件縮放到 SYMBOL_SIZE）

#### 3.4 符號靜態 PNG

為每個符號的 PNG 圖片註冊獨立的 sprite（用於 static 狀態顯示）：

```ts
H1_static: {
    type: 'sprite',
    src: new URL('../../assets/sprites/H1.png', import.meta.url).href,
},
```

#### 3.5 移除所有不存在的素材

完全移除以下模板殘留（除非對應檔案真的存在）：
- loader, pressToContinueText, progressBar（LoadingScreen 用）
- foregroundAnimation, foregroundFeatureAnimation（Background Spine 用）
- reelsFrame, reelhouse（BoardFrame Spine 用）
- payFrame, anticipation（Win Frame 用）
- 所有 fonts（goldFont, goldBlur, silverFont, purpleFont）
- bigwin, globalMultiplier, fsIntro/Number/Outro
- tumble_multiplier, tumble_win, clusterWin
- transition, symbolsStatic, coins, sound
- explosion（如果 explosion 動畫已內嵌在每個符號的 skel 中）
- symbols2/, symbols3/ 資料夾引用

### Step 4: 重寫 constants.ts 的 SYMBOL_INFO_MAP

根據 config.ts 的符號列表和實際素材，重新生成 `SYMBOL_INFO_MAP`。

**每個符號 6 種狀態：**

| 狀態 | 有 Spine 時 | 無 Spine 時 |
|------|------------|------------|
| static | sprite → `{NAME}_static` | sprite → `{NAME}_static` |
| spin | sprite → `{NAME}_static` | sprite → `{NAME}_static` |
| land | spine → animationName `'land'` | sprite → `{NAME}_static` |
| win | spine → animationName `'win'` | sprite → `{NAME}_static` |
| postWinStatic | sprite → `{NAME}_static` | sprite → `{NAME}_static` |
| explosion | spine → animationName `'explosion'` | sprite → `{NAME}_static` |

**同時修正：**
- `HIGH_SYMBOLS` 陣列：只包含 config.ts 中存在的 H 系列符號
- `INITIAL_BOARD`：確認所有引用的符號名稱都存在於 SYMBOL_INFO_MAP
- 移除模板中不存在的符號（如 H5、M 等）
- 移除乘數相關的靜態定義（m2Static, m4Static 等），除非遊戲有乘數符號

### Step 5: 簡化 Background.svelte

將 Spine 動畫替換為靜態背景圖：

```svelte
<script lang="ts">
    import { Sprite, Rectangle } from 'pixi-svelte';
    import { getContext } from '../game/context';
    const context = getContext();
</script>

<Rectangle {...context.stateLayoutDerived.canvasSizes()} backgroundColor={0x000000} zIndex={-3} />

<Sprite
    key="bg_desktop"
    anchor={0.5}
    x={context.stateLayoutDerived.canvasSizes().width / 2}
    y={context.stateLayoutDerived.canvasSizes().height / 2}
    width={context.stateLayoutDerived.canvasSizes().width}
    height={context.stateLayoutDerived.canvasSizes().height}
    zIndex={-2}
/>
```

### Step 6: 簡化 BoardFrame.svelte

保留 module script 的 type export（其他組件可能依賴），但用靜態圖片替代 Spine：

```svelte
<script lang="ts" module>
    export type EmitterEventBoardFrame =
        | { type: 'boardFrameGlowShow' }
        | { type: 'boardFrameGlowHide' };
</script>

<script lang="ts">
    import { Sprite } from 'pixi-svelte';
    import { getContext } from '../game/context';
    const context = getContext();
    const FRAME_SCALE = 1.15;
</script>

<Sprite
    key="frame"
    anchor={0.5}
    x={context.stateGameDerived.boardLayout().x}
    y={context.stateGameDerived.boardLayout().y}
    width={context.stateGameDerived.boardLayout().width * FRAME_SCALE}
    height={context.stateGameDerived.boardLayout().height * FRAME_SCALE}
/>
```

**FRAME_SCALE 調整說明**：邊框圖需要稍大於盤面區域。如果邊框圖 800x800、盤面 560x560，1.15 是合理的起始值。可能需要根據實際圖片微調。

### Step 7: 修改 Game.svelte

1. **移除 LoadingScreen**：刪除 import 和相關邏輯（沒有 loader spine）
2. **改用 `context.stateApp.loaded`** 作為條件渲染（替代 showLoadingScreen）
3. **註解掉 Sound 相關**：`EnableSound`、`Sound`（無 audio 素材）
4. **移除缺素材的組件**：`FreeSpinIntro`、`FreeSpinOutro`、`FreeSpinCounter`、`Transition`、`I18nTest`
5. **保留事件驅動組件**：Board、TumbleBoard、Anticipations、ClusterWinAmounts、TumbleWinAmount、GlobalMultiplier、Win — 這些由事件觸發，初始畫面不會渲染
6. **更新遊戲名稱**：改為 config.ts 中的 gameName

### Step 8: 繞過 Authenticate

修改 `$ARGUMENTS/src/routes/+layout.svelte`：

```svelte
<GlobalStyle>
    <!-- 開發模式：跳過 Authenticate（無 RGS 後端） -->
    <!-- <Authenticate> -->
        <LoadI18n {messagesMap}>
            <Game />
        </LoadI18n>
    <!-- </Authenticate> -->
</GlobalStyle>

<!-- <LoaderStakeEngine ... /> -->
<!-- {#if showYourLoader} ... {/if} -->
```

### Step 9: 修正 Vite 配置

檢查 `$ARGUMENTS/vite.config.js`，確保 `server.fs.allow` 涵蓋 monorepo 根目錄：

```js
import config from 'config-vite';
import path from 'path';

const baseConfig = config();

export default {
    ...baseConfig,
    server: {
        ...baseConfig.server,
        host: true,
        port: 3001,
        fs: {
            allow: [
                path.resolve(__dirname, '../..'),
            ],
        },
    },
};
```

**為什麼需要這個**：遊戲專案在 `games/{id}/`，但 SDK 的 SvelteKit runtime 在 `sdks/web-sdk/node_modules/` 中。Vite 預設只允許專案目錄和 node_modules，不包含 monorepo 根目錄的其他路徑。

### Step 10: 啟動並驗證

```bash
cd $ARGUMENTS && npm run dev
```

1. 在瀏覽器中開啟 dev server URL
2. 確認顯示：背景圖 + 邊框 + 符號格子 + UI 底欄
3. 確認 console 無嚴重錯誤
4. 輸出驗證報告

## 常見問題

| 問題 | 原因 | 解法 |
|------|------|------|
| 全黑畫面 | Authenticate error modal 覆蓋 | Step 8 繞過 Authenticate |
| 404 素材錯誤 | assets.ts 引用不存在檔案 | Step 3 只註冊存在的素材 |
| Vite fs.allow 錯誤 | SDK 路徑超出允許範圍 | Step 9 擴展 allow 列表 |
| 符號不顯示 | SYMBOL_INFO_MAP 的 assetKey 錯誤 | Step 4 確認 key 對應 assets.ts |
| 邊框位置偏移 | FRAME_SCALE 不匹配 | 微調 FRAME_SCALE 數值 |

## 注意事項

1. 此 skill 產生的是**開發預覽版本**，Authenticate 和 Sound 被停用
2. 事件驅動組件（Win, Tumble 等）保留但不會在初始畫面觸發
3. 後續加入進階素材（Spine 背景、音效等）時需要逐步恢復被註解的程式碼
