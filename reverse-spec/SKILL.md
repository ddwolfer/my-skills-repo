---
name: reverse-spec
description: 從 code（math model + 前端 config + stateMeta + i18n + 已實作的 bookEvent handler）反推產出 SPEC.md 缺漏章節的 draft，對應鐵律「SPEC 追隨實作」—— 當 code 與 SPEC drift 時，SPEC 必須追隨 code 而非領先。當使用者提到 code 比 SPEC 新、SPEC 追隨、補 SPEC 章節、從實作倒推企劃書、drift 收尾、Planner 需要 base 草稿更新 SPEC、遊戲做完但 SPEC 沒跟上、送審前補齊 SPEC 章節時都應觸發。使用方式：/reverse-spec games/crystal-match 或 /reverse-spec games/crystal-match paytable 或 /reverse-spec games/crystal-match bookEvents
---

# reverse-spec

Reverse-engineer a `SPEC.md` section draft from the current code, then ask Planner to clarify design intent before writing. Implements the 鐵律 "SPEC 追隨實作" (code is authoritative; SPEC updates to match, never the other way).

**核心原則**（引用自 knowledge graph `principle/SPEC 追隨實作原則`）：
> 當實作方式與 SPEC 描述有差異時（drift），SPEC 必須追隨 code 而非領先。先 Client commit，再 Planner 更新 SPEC。

本 skill **產出 SPEC draft，但不自動寫入** `SPEC.md` — draft 需先通過 Planner 確認 design intent 後，再由 Planner 手動 commit 到 SPEC。

## 參數

- `$ARGUMENTS`: `<gamePath> [<section>]`
  - `gamePath`: 遊戲專案路徑（如 `games/crystal-match`）
  - `section` (可選): 指定要反推的章節，支援：
    - `paytable` — 符號表 + multiplier
    - `betMode` — betMode 名稱 / costMultiplier / RTP / maxWin
    - `rules` — 遊戲規則常數（grid / reels / FS count）
    - `bookEvents` — 已實作的事件清單（從 handler 逆推）
    - `layerOrder` — PIXI / DOM / HTML overlay 層次規範
    - `stateMachine` — XState state 命名與轉移
    - `all` (default) — 掃所有可偵測的章節

## 執行流程

### Step 1: 解析參數 + 定位檔案

從 `$ARGUMENTS` 取 `gamePath`，按下列順序解析真實路徑（**專案目錄通常有 `NN-` 前綴** — `games/04-crystal-match` 之類；使用者可能只打 `games/crystal-match`）：

1. 取 `gamePath` 末段為 `gameIdRaw`
2. `gameIdRaw` match `^\d+-(.+)$` → `gameId` = group(1)，否則 `gameId` = `gameIdRaw`
3. 用 Glob 定位：
   - `gamePathReal`：`games/*<gameId>` 第一個 match
   - `mathPath`：`models/*<gameId>/game_config.py`（Glob）
   - `specPath`：`specs/*<gameId>/SPEC.md`（Glob）
4. 無 match → fallback 到 bare 名（`games/<gameId>`）；全缺 → abort

推導下游檔案：
- `configPath` — `<gamePathReal>/src/game/config.ts`
- `metaPath` — `<gamePathReal>/src/game/stateMeta.ts`
- `i18nDir` — `<gamePathReal>/src/game/i18n/`
- `eventHandlerRoots` — 以下任一存在則納入掃描：
  - `<gamePathReal>/src/game/bookEventHandlerMap.ts`（常見，dispatch 表）
  - `<gamePathReal>/src/game/typesBookEvent.ts`（event type 定義）
  - `<gamePathReal>/src/game/eventHandlers/*.ts`（較新模板）
  - `<gamePathReal>/src/game/stateMachines/**/*.ts`（XState handlers）
  - `<gamePathReal>/src/game/stateXstate.ts`（單檔 XState）
- `pixiComponentDir` — `<gamePathReal>/src/components/`

驗證 `gamePath` 存在，否則 abort。

讀目前 `SPEC.md`（若存在）抽 **已有章節標題**（`^##` lines），建立 `existing_sections` set。反推時針對 `existing_sections` **中缺漏** 或 **相較 code 明顯過時** 的章節才產出 draft。

---

### Step 2: 從 code 抽取事實（per section）

#### 2a. `paytable`

讀 `configPath` 找 `paytable` / `symbols` / `symbolPayouts` 的定義：
```typescript
Grep pattern="paytable|symbols[:\s]*=|payout" path="<configPath>" -C 10
```

讀 `mathPath` 找 `paytable` Python dict：
```
Grep pattern="paytable|sym_info|symbol_info" path="<mathPath>" -C 10
```

抽出結構：
```
{ symbol_name: { count_3: N, count_4: N, count_5: N } }
```

標記 **code 兩邊若不一致** → 在 draft 中用 🔴 註記，要 Planner 定奪。

#### 2b. `betMode`

```
Grep pattern="bet_modes|BetMode|betMode" path="<mathPath>" -C 8
Grep pattern="betModeMeta|BET_MODES|costMultiplier" path="<metaPath>|<configPath>" -C 8
```

抽每個 betMode 的：
- `name`（internal key）
- `costMultiplier`（1 for BASE, 80 for BONUS, 3 for UNBREAKABLE_* 等）
- `rtp` 目標值（從 math config）
- `maxWin` 上限
- `displayName`（從 i18n / stateMeta）
- `is_buy_bonus` / `is_feature_buy` 旗標

#### 2c. `rules`

抽遊戲基本參數：
```
Grep pattern="num_reels|num_rows|reel_count|grid|rows|cols" path="<mathPath>|<configPath>" -C 3
Grep pattern="free_spin_count|fs_count|retrigger|scatter_trigger" path="<mathPath>" -C 3
Grep pattern="max_mult|max_multiplier" path="<mathPath>|<configPath>" -C 3
```

#### 2d. `bookEvents`

掃 event handler 檔案：
```
Glob pattern="<eventHandlerDir>/*.ts"
Glob pattern="<gamePath>/src/game/stateMachines/**/handlers.ts"
```

每個 handler 檔抽：
- 處理的 event type（從檔名或 `bookEvent.type === '...'` 檢查）
- 該 event 的 payload shape（interface / type 定義）
- 動畫 / 副作用（broadcast / broadcastAsync 呼叫）

產出表格：
| Event Type | Payload 欄位 | 動畫 / 副作用 | broadcastAsync？ |

#### 2e. `layerOrder`

掃 PIXI component + HTML overlay：
```
Grep pattern="zIndex|z-index|sortableChildren|Layer" path="<pixiComponentDir>" -C 2
Grep pattern="position:\s*(fixed|absolute)" path="<gamePath>/src" glob="*.svelte" -C 2
```

產出 z-index 清單（背景 → 捲軸 → UI → overlay）+ 標記 DOM vs PIXI。
**引用 knowledge graph principle `DOM/PIXI 混合分層規範 — HTML overlay 永遠蓋 PIXI canvas` 當作 draft 預設規範。**

#### 2f. `stateMachine`

```
Glob pattern="<gamePath>/src/game/stateMachines/**/*.ts"
```

抽 XState `states` block 的 key + `on` transition。產出 mermaid flowchart draft：
```
stateDiagram-v2
  [*] --> idle
  idle --> spinning: SPIN
  spinning --> revealing: REVEAL
  ...
```

---

### Step 3: 列出不明確的「intent」問題

**核心原則**（引自原 skill）：*"Never assume intent. Always ask before documenting 'why'."*

對每一組抽到的事實，判斷「what」清楚但「why」不清楚的地方，產出 Clarifying Questions 清單。例如：

- 「偵測到 `BONUS.costMultiplier = 80`，而 `UNBREAKABLE_IRON.costMultiplier = 3`。為什麼 Unbreakable 便宜這麼多？是 Progression 折扣還是純數學調整？」
- 「偵測到 `updateGlobalMult` handler 播 `sfx_mult_up` 但 grid 上不顯示動畫。是故意不演出、還是缺失動畫？」
- 「layerOrder 看到 `WinOverlay` z-index=100，但 `ErrorModal` z-index=50，這合理嗎？錯誤彈窗不應蓋過 Win？」

---

### Step 4: 產出 SPEC draft

寫 draft 到 `specs/<gameId>/SPEC_REVERSE_DRAFT.md`（**不覆蓋** SPEC.md，等 Planner 併入）：

```markdown
# SPEC Reverse-Engineered Draft — <gameId>
Source: reverse-spec skill
Date: YYYY-MM-DD
Scanned:
- math: models/<gameId>/game_config.py (commit <sha>)
- front-end: games/<gameId>/src/game/ (commit <sha>)
- i18n: N locale files
- handlers: N event handler files

> ⚠️ **本檔案是 draft**，不自動併入 SPEC.md。Planner 請人工比對既有 SPEC 章節 → 決定 ADOPT / MERGE / IGNORE → 再 commit 到 SPEC.md。

---

## 🔍 Clarifying Questions（送給 Planner）

1. [intent] 為什麼 BONUS.costMultiplier = 80 而不是行業常見的 100？
2. [intent] `updateGlobalMult` 播 sfx 但無畫面動畫，是 MVP 取捨還是永久設計？
...

---

## § Paytable（reverse-engineered）

| Symbol | ×3 | ×4 | ×5 |
|--------|-----|-----|-----|
| H1     | 2.0 | 5.0 | 20.0 |
| ...    | ... | ... | ...  |

Source: `config.ts:L45-L78` (primary), `game_config.py:L120-L160` (cross-checked)
🔴 Drift: `H3` ×5 config.ts=10, game_config.py=12 — Planner 請裁決

---

## § Bet Modes

| Internal | Display | costMult | RTP | maxWin |
|----------|---------|----------|-----|--------|
| BASE     | Play    | 1x       | 0.9600 | 5000x |
| BONUS    | Get Bonus | 80x    | 0.9650 | 5000x |
| ...      | ...     | ...      | ...    | ...   |

...（後續章節同格式）

---

## § Layer Order（DOM/PIXI 混合分層）

（根據 principle `DOM/PIXI 混合分層規範 — HTML overlay 永遠蓋 PIXI canvas`）

| Layer | Type | z-index | Purpose |
|-------|------|---------|---------|
| Background | PIXI | 0 | 靜態背景 sprite |
| Reels | PIXI | 10 | 捲軸 |
| WinParticles | PIXI | 20 | 勝利粒子 |
| UIButtons | DOM (Svelte) | 100 | SPIN / BET / MENU |
| ErrorModal | DOM | 999 | 錯誤彈窗（最上層）|

Source: 掃 `<pixiComponentDir>` + `*.svelte` position rules
```

---

### Step 5: 結尾建議

**給 Planner：**
> SPEC draft 已寫入 `specs/<gameId>/SPEC_REVERSE_DRAFT.md`。請：
> 1. 先回答 Clarifying Questions 的 intent 問題
> 2. 逐節比對既有 SPEC → 決定 ADOPT / MERGE / IGNORE
> 3. 併入 SPEC.md 後刪除 draft 檔
> 4. 跑 `/spec-consistency-check <gamePath>` 驗證 drift 清零

**禁止行為：**
- 本 skill **不**修改 `SPEC.md`、`game_config.py`、`config.ts` 或任何 source file
- 只寫 `SPEC_REVERSE_DRAFT.md`（可覆蓋舊 draft）

**不適用情況：**
- 全新專案還沒 code → 請用 `/write-spec` 而非本 skill
- SPEC 完全對得上 code（drift = 0）→ 本 skill 會輸出「No drift detected, no draft generated」並 early exit

---

## 可與其他 skill 串接

- 通常流程：`/spec-consistency-check` 報 drift → `/reverse-spec` 出 draft → Planner 併入 SPEC.md → `/spec-consistency-check` 再驗
- 新遊戲：`/write-spec`（前端）→ `/init-math` → `/init-game`（不需 `/reverse-spec`）
