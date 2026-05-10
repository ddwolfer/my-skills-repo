---
name: add-event
description: 在前端遊戲中新增 bookEvent 處理器。根據 stake-docs 的標準流程，自動建立/修改所有相關檔案（type、handler、emitterEvent、story）。當使用者要加新事件、新增 bookEvent、建立事件處理器、或提到需要新的遊戲演出效果（如乘數更新、免費旋轉觸發、勝利展示、連鎖消除、最大獎展示等）時都應觸發。使用方式：/add-event games/dragon-feast updateGlobalMult
---

# add-event

在前端遊戲中新增 bookEvent 處理器，遵循 Stake Engine 官方文件的標準流程。
自動掃描現有程式碼結構，建立/修改所有相關檔案。

> 來源：stake-docs/02-front-end.md §Adding New Events

## 參數

- `$ARGUMENTS`: `{gamePath} {eventName}` — 遊戲路徑 + 新事件名稱
  - 例如：`games/dragon-feast updateGlobalMult`
  - 例如：`games/dragon-feast tumbleBoard`

---

## 執行流程

### Step 1: 解析參數 + Pre-flight

從 `$ARGUMENTS` 提取：
- `gamePath`: 遊戲專案路徑（例如 `games/dragon-feast`）
- `eventName`: 新 bookEvent 的 type 名稱（例如 `updateGlobalMult`）

驗證遊戲專案存在：
```bash
ls {gamePath}/src/game/bookEventHandlerMap.ts
ls {gamePath}/src/game/typesBookEvent.ts
```

### Step 2: 收集 Event 規格

使用 AskUserQuestion 詢問：

#### 2.1 BookEvent 資料欄位
```
問題：這個 bookEvent 從 RGS 回傳什麼資料？
提示：列出欄位名稱和類型，例如：
  - globalMult: number
  - positions: {reel: number, row: number}[]
```

#### 2.2 EmitterEvent 類型
```
問題：這個事件需要廣播哪些 emitterEvent？（每個 emitterEvent 做一件事）
提示：遵循 Single Responsibility Principle，例如：
  - globalMultiplierShow（顯示乘數 UI）
  - globalMultiplierUpdate { multiplier: number }（更新乘數值）
  - globalMultiplierHide（隱藏乘數 UI）
```

#### 2.3 是否需要 async（等待動畫完成）
```
問題：哪些 emitterEvent 需要 broadcastAsync（等待動畫完成後才繼續）？
選項：
- 列出 Step 2.2 中的 emitterEvent，讓使用者勾選需要 async 的
```

#### 2.4 目標 Svelte 元件
```
問題：哪個 Svelte 元件會處理這些 emitterEvent？
選項：
- 現有元件（輸入元件名稱）
- 新建元件（輸入元件名稱，例如 GlobalMultiplier）
```

---

### Step 3: 修改 typesBookEvent.ts（Step 4 in stake-docs）

讀取 `{gamePath}/src/game/typesBookEvent.ts`，新增 BookEvent type：

```typescript
type BookEvent{PascalCase} = {
    index: number;
    type: '{eventName}';
    {field1}: {type1};
    {field2}: {type2};
    // ... 從 Step 2.1 收集的欄位
};

// 加入 union type
export type BookEvent = | ... | BookEvent{PascalCase} | ...;
```

**PascalCase 轉換**：`updateGlobalMult` → `UpdateGlobalMult`

---

### Step 4: 新增 bookEventHandler（Step 5 in stake-docs）

讀取 `{gamePath}/src/game/bookEventHandlerMap.ts`，新增 handler：

```typescript
{eventName}: async (bookEvent) => {
    // 根據 Step 2.2 的 emitterEvent 清單生成
    eventEmitter.broadcast({ type: '{emitterEvent1}' });
    // 如果是 async（Step 2.3）：
    await eventEmitter.broadcastAsync({ type: '{emitterEvent2}', {field}: bookEvent.{field} });
    eventEmitter.broadcast({ type: '{emitterEvent3}' });
},
```

---

### Step 5: 定義 EmitterEvent 類型（Step 6 in stake-docs）

#### 5a. 如果是新建元件

建立 `{gamePath}/src/components/{ComponentName}.svelte`，包含：

```svelte
<script lang="ts">
    import { getContextEventEmitter } from 'utils-event-emitter';
    import type { EmitterEvent } from '../game/typesEmitterEvent';

    const { eventEmitter } = getContextEventEmitter<EmitterEvent>();

    // State
    let visible = $state(false);
    // ... 其他狀態

    // EmitterEvent handlers
    eventEmitter.subscribeOnMount({
        {emitterEvent1}: () => {
            visible = true;
        },
        {emitterEvent2}: async (emitterEvent) => {
            // 處理邏輯
            // 如果是 async，用 waitForResolve
        },
        {emitterEvent3}: () => {
            visible = false;
        },
    });
</script>

{#if visible}
    <!-- 元件 UI -->
{/if}
```

#### 5b. 如果是現有元件

讀取目標元件，在 `subscribeOnMount` 中新增 handler。

---

### Step 6: 註冊 EmitterEvent 類型（Step 7-8 in stake-docs）

#### 6a. typesEmitterEvent.ts

讀取 `{gamePath}/src/game/typesEmitterEvent.ts`，新增：

```typescript
// 如果是新元件，新增 type export
export type EmitterEvent{ComponentName} =
    | { type: '{emitterEvent1}' }
    | { type: '{emitterEvent2}'; {field}: {type} }
    | { type: '{emitterEvent3}' };

// 加入 union type
export type EmitterEvent = | ... | EmitterEvent{ComponentName} | ...;
```

#### 6b. eventEmitter.ts（如果獨立存在）

讀取 `{gamePath}/src/game/eventEmitter.ts`，確認 EmitterEvent import 和 union type 包含新增類型。

---

### Step 7: 新增 Story 測試資料（Step 1-3 in stake-docs）

#### 7a. bonus_books.ts / base_books.ts

讀取 `{gamePath}/src/stories/data/` 中對應的 books 檔案。

在適當的位置加入 bookEvent 測試資料：

```typescript
// 在 events 陣列中加入
{ type: '{eventName}', {field1}: {testValue1}, {field2}: {testValue2} }
```

**位置決策**：
- 如果是 basegame 事件 → 加入 `base_books.ts`
- 如果是 freegame 事件 → 加入 `bonus_books.ts`
- `reveal` 之後、`setTotalWin` 之前

#### 7b. bonus_events.ts / base_events.ts

```typescript
{eventName}: { type: '{eventName}', {field1}: {testValue1}, {field2}: {testValue2} }
```

#### 7c. Story 檔案

讀取 `{gamePath}/src/stories/` 中的 Stories 檔案（`ModeBonusBookEvent.stories.svelte` 或 `ModeBaseBookEvent.stories.svelte`），新增：

```svelte
<Story name="{eventName}" args={templateArgs({
    skipLoadingScreen: true,
    data: events.{eventName},
    action: async (data) => await playBookEvent(data, { bookEvents: [] })
})} />
```

---

### Step 8: 整合到 Game.svelte（如果是新元件）

讀取 `{gamePath}/src/components/Game.svelte`：

1. 新增 import：
```typescript
import {ComponentName} from './{ComponentName}.svelte';
```

2. 在 `<App>` 內適當位置放置元件：
```svelte
<{ComponentName} />
```

---

### Step 9: 輸出報告

```
=== BookEvent 新增完成 ===

Event: {eventName}
Game: {gamePath}

修改的檔案：
  ✅ src/game/typesBookEvent.ts — 新增 BookEvent{PascalCase} type
  ✅ src/game/bookEventHandlerMap.ts — 新增 {eventName} handler
  ✅ src/game/typesEmitterEvent.ts — 新增 EmitterEvent{ComponentName} type
  ✅ src/game/eventEmitter.ts — 更新 union type
  ✅ src/components/{ComponentName}.svelte — {新建/修改} 元件
  ✅ src/stories/data/{mode}_books.ts — 新增測試資料
  ✅ src/stories/data/{mode}_events.ts — 新增單一事件資料
  ✅ src/stories/{StoryFile} — 新增 Story

驗證步驟：
1. 啟動 Storybook：pnpm run storybook --filter={gameId}
2. 開啟 MODE_{MODE}/bookEvent/{eventName} — 確認事件獨立運作
3. 開啟 MODE_{MODE}/book/random — 確認事件在完整流程中正確觸發
4. 確認元件 UI 顯示正確、動畫完成後正確 resolve
```

---

## 架構參考

### BookEvent → EmitterEvent → Component 的資料流

```
RGS Response (book.events)
    ↓
playBookEvents() — 逐一處理 events
    ↓
bookEventHandlerMap[event.type](event)
    ↓
eventEmitter.broadcast/broadcastAsync({ type, ...data })
    ↓
Component.subscribeOnMount({ type: handler })
    ↓
UI 更新 / 動畫播放
```

### 命名慣例

| 項目 | 慣例 | 範例 |
|------|------|------|
| bookEvent type | camelCase | `updateGlobalMult` |
| BookEvent TS type | `BookEvent` + PascalCase | `BookEventUpdateGlobalMult` |
| emitterEvent type | camelCase，以元件名開頭 | `globalMultiplierUpdate` |
| EmitterEvent TS type | `EmitterEvent` + ComponentName | `EmitterEventGlobalMultiplier` |
| Svelte 元件 | PascalCase | `GlobalMultiplier.svelte` |

### emitterEvent 設計原則（Single Responsibility）

每個 emitterEvent handler 只做一件事：
- `Show` — 顯示元件
- `Hide` — 隱藏元件
- `Update` — 更新數值
- `Init` — 初始化狀態
- `Reset` — 重置狀態
- `Explode` — 播放爆炸動畫（async）
- `SlideDown` — 播放滑落動畫（async）
- `Settle` — 設定最終狀態

### 常見 Event 類型參考

| BookEvent | 用途 | 常見 EmitterEvents |
|-----------|------|-------------------|
| `reveal` | 顯示轉盤結果 | `boardReveal`, `boardSettle` |
| `winInfo` | 顯示獲勝資訊 | `winHighlight`, `winCounter` |
| `setWin` | 設定本次獲勝 | `winAmountUpdate` |
| `setTotalWin` | 設定總獲勝 | `totalWinUpdate` |
| `finalWin` | 最終結算 | `finalWinShow`, `finalWinHide` |
| `tumbleBoard` | 連鎖消除 | `tumbleBoardExplode`, `tumbleBoardSlideDown` |
| `updateFreeSpin` | 更新免費旋轉 | `freeSpinCounterUpdate` |
| `updateGlobalMult` | 更新全域乘數 | `globalMultiplierUpdate` |
| `fsTrigger` | 觸發免費旋轉 | `freeSpinIntroShow` |
| `fsEnd` | 結束免費旋轉 | `freeSpinOutroShow` |
| `wincap` | 達到最大獎 | `wincapShow` |

---

## 注意事項

1. **Event 順序很重要** — `reveal` 必須在 `winInfo` 之前，`setTotalWin` 在 `finalWin` 之前
2. **async vs sync** — 需要等待動畫完成再繼續的用 `broadcastAsync`，純狀態更新用 `broadcast`
3. **不要 build** — 修改完成後提醒使用者自行在終端執行 `pnpm run storybook` 驗證
4. **Story 資料真實性** — 測試資料的欄位結構要和 RGS 回傳一致，可參考 `library/books/` 中的真實資料
5. **數學模型對齊** — 前端事件命名應與 `game_events.py` 中的 event type 一致
6. **broadcastAsync subscriber 必須有 timeout** — 新增的 broadcastAsync 事件，subscriber 的 `waitForResolve` 和 `await tween.set()` 都要搭配 `Promise.race([..., waitForTimeout(2000)])`
7. **Drawer 類 UI 事件禁用 broadcastAsync** — `drawerButtonShow`/`drawerButtonHide`/`drawerUnfold`/`drawerFold` 及類似純 UI 裝飾事件必須用 `broadcast`，不能用 `broadcastAsync`
