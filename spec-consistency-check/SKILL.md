---
name: spec-consistency-check
description: 掃描 SPEC.md ↔ 數學模型 (game_config.py) ↔ 前端 (config.ts / stateMeta.ts) ↔ i18n 之間的 drift，偵測同一 entity（符號/betMode/paytable/常數）在多處出現但值不一致。grep-first 掃描，只深度 read 有衝突的檔案。當使用者提到 SPEC drift、跨檔案一致性檢查、符號值不一致、paytable 不符、送審前 drift 驗證、多處 RTP 值不同、i18n 缺 key、或 stateMeta 覆寫對不上 SPEC 時都應觸發。使用方式：/spec-consistency-check games/pharaohs-cascade 或 /spec-consistency-check games/pharaohs-cascade symbol:H1
---

# spec-consistency-check

Scan for cross-file drift between **SPEC.md** (source of truth for design intent) and its downstream implementations: **math model** (`game_config.py`), **front-end config** (`config.ts`, `stateMeta.ts`), and **i18n** (`src/game/i18n/*.ts`). Uses a grep-first scan against a per-run entity registry derived from SPEC, only deep-reading files that produce conflicts.

**⚠️ 鐵律提醒**: 按 knowledge graph `principle/SPEC 追隨實作原則`，當 code 與 SPEC drift 時，**SPEC 必須追隨 code**，而非反之。此 skill 報告 drift，**不自動修 SPEC**；修正方向交 Planner 判斷。

## 參數

- `$ARGUMENTS`: `<gamePath> [<filter>]`
  - `gamePath`: 遊戲專案路徑（如 `games/pharaohs-cascade`）
  - `filter` (可選): `full` | `symbol:<name>` | `betMode:<name>` | `constant:<name>`

## 執行流程

### Step 1: 解析參數 + pre-flight

從 `$ARGUMENTS` 取得 `gamePath` 後，按下列順序解析真實路徑（**專案目錄通常有 `NN-` 前綴**，如 `games/04-crystal-match`；使用者可能只打 `games/crystal-match`）：

1. 取 `gamePath` 末段作為 `gameIdRaw`（e.g. `crystal-match` 或 `04-crystal-match`）
2. 若 `gameIdRaw` 符合 `^\d+-(.+)$` → `gameId` = group(1)，否則 `gameId` = `gameIdRaw`
3. 用 Glob 定位真實目錄：
   - `gamePathReal`：`games/*<gameId>` 第一個 match（期望唯一）
   - `mathPathReal`：`models/*<gameId>/game_config.py`（Glob）
   - `specPathReal`：`specs/*<gameId>/SPEC.md`（Glob）
4. 若某個 Glob 無 match，用 **bare** 版本作 fallback（`games/<gameId>`），都無則標記 `missing` 並納入報告。

推導下游檔案：
- `frontendConfigPath` — `<gamePathReal>/src/game/config.ts`
- `frontendMetaPath` — `<gamePathReal>/src/game/stateMeta.ts`（可能不存在）
- `i18nDir` — `<gamePathReal>/src/game/i18n/`

驗證這四個資源至少 SPEC.md 存在，否則 abort：
```
SPEC.md not found at <specPath>. Cannot build entity registry without source of truth.
```

---

### Step 2: 從 SPEC.md 抽出 entity registry

Read SPEC.md，從下列 section 抽出結構化資料（純記憶體，不寫檔）：

| Entity 類型 | SPEC section 關鍵字（中英混合） | 抽取欄位 |
|-------------|------------------------------------|----------|
| **symbol** | `Symbols` / `符號` / `Paytable` / `賠率表` / `符號定義` | name, multipliers (per count), category (slot: H/L/W/S；match-3: G1-G8 等) |
| **betMode** | `Bet Modes` / `betMode` / `下注模式` / `Bet Modes & Paytables` | name, costMultiplier, rtp, maxWin, displayName |
| **constant** | `Game Rules` / `遊戲規則` / `遊戲概覽` / `玩法摘要` | gridSize, reelCount, freeSpinCount, scatterTrigger, maxMultiplier |

**非 slot 遊戲彈性化**：
- match-3 / cluster 用 G1-G8、C1-Cn 之類命名 → 用 `^([A-Z])(\d+)\s*[–—-]` 或表格首欄 pattern 抽取
- progression（如 Forge of Fortune）可能無傳統 paytable，改看 `Iron / Silver / Dragon` × `Normal / Unbreakable` 組合
- dice / table game 無 symbol 概念 → 跳過 symbol scan，只掃 betMode + constant

抽取策略：**以 markdown 表格為主**（大多數 SPEC 採用 `| name | value |` 格式）。若找不到表格則用 `Grep -n "^\|"` 搭配 heading 上下文。

建出三張 lookup table：
```
symbol_map:    { H1: {mult_3: 5, mult_4: 10, mult_5: 50}, ... }
betmode_map:   { BONUS: {costMultiplier: 80, rtp: 0.9650, displayName: "..."}, ... }
constant_map:  { gridSize: "5x3", freeSpinCount: 10, ... }
```

**初始報告：**
```
SPEC registry loaded from <specPath>:
- N symbols  (H1-H4, L1-L5, W, S)
- N betModes (BASE, BONUS, ...)
- N constants
Scope: full | symbol:NAME | ...
```

---

### Step 3: grep-first 跨檔 drift 掃描

對 registry 每一個 entity name，在下游檔案做 targeted grep，`output_mode: content`, `-C: 3`。

#### 3a. Symbol 掃描

對每個 symbol name（如 `H1`, `SCATTER`, `WILD`）：
```
Grep pattern="<symbol>" path="<mathPath>" -C 3
Grep pattern="<symbol>" path="<frontendConfigPath>" -C 3
Grep pattern="<symbol>" glob="<i18nDir>/*.ts" -C 3
```

抽出鄰近數值 → 與 SPEC registry 比對：
- Paytable multiplier mismatch → 🔴 CONFLICT
- 符號在 SPEC 但 i18n 沒 key → ⚠️ MISSING i18n
- 符號在 code 但 SPEC 沒列 → ⚠️ SPEC STALE（code → SPEC 需更新）

#### 3b. betMode 掃描

對每個 betMode name（如 `BASE`, `BONUS`, `UNBREAKABLE_IRON`）：
```
Grep pattern="<betMode>" path="<mathPath>" -C 3
Grep pattern="<betMode>" path="<frontendConfigPath>" -C 3
Grep pattern="<betMode>|costMultiplier|displayName" path="<frontendMetaPath>" -C 3
```

抽出：
- `cost` / `cost_multiplier` / `costMultiplier` 數值
- `rtp` 目標值
- `max_win` / `maxWin` 上限
- `displayName` / i18n key

比對：
- costMultiplier SPEC 80x，`stateMeta.ts` 覆寫成 100x → 🔴 CONFLICT
- RTP SPEC 0.9650，`game_config.py` 寫 0.9500 → 🔴 CONFLICT
- displayName SPEC `"BUY BONUS"`，stateMeta `"GET BONUS"` → ⚠️ INTENTIONAL（Social Mode 禁用詞，記為 expected drift，不算 conflict）

**Social Mode 用語白名單**（不算 CONFLICT）：
- `BUY BONUS` ↔ `GET BONUS`
- `bet` ↔ `play`
- `wager` ↔ `play`

#### 3c. Constant 掃描

對每個 constant name（如 `gridSize`, `freeSpinCount`, `maxMultiplier`）：
```
Grep pattern="<constant_keyword>" path="<mathPath>" -C 3
Grep pattern="<constant_keyword>" path="<frontendConfigPath>" -C 3
```

numeric diff → 🔴 CONFLICT。

---

### Step 4: 深度驗證（只看衝突檔）

對 Step 3 產生的 conflict，用 Read 打開該檔案具體 section 確認：
1. **確認衝突為真** — 有時 grep context 誤導（例如 `H1` 也可能是 heading 不是符號）
2. **判斷權威來源** — 按鐵律，code 通常是 authoritative，SPEC 可能 stale
3. **檢查 git 時間戳** — `git log -1 --format=%ci <file>` 看 code vs SPEC 何者較新

---

### Step 5: 產出報告

輸出到 stdout + 寫入 `specs/<gameId>/DRIFT_REPORT.md`：

```markdown
# Drift Report — <gameId>
Date: YYYY-MM-DD
SPEC version: <從 SPEC.md 頂部抽 version>
Files scanned:
- SPEC: specs/<gameId>/SPEC.md
- Math: models/<gameId>/game_config.py
- Front-end: games/<gameId>/src/game/config.ts, stateMeta.ts
- i18n: N locale files

---

## 🔴 Conflicts (N) — 必須由 Planner 裁決

### [symbol] H1 — paytable mismatch
- SPEC (§ Paytable):        mult_5 = 50x
- game_config.py:L123:       H1 payout 5 = 100
- config.ts:L45:             H1 paytable { 5: 50 }

> code 兩處不一致，且 SPEC 偏向 config.ts。建議由 Planner 確認哪個為準，再同步另一邊 + 更新 SPEC。

### [betMode] BONUS — costMultiplier mismatch
- SPEC:                      costMultiplier = 80
- stateMeta.ts:L22:           BONUS.costMultiplier = 100

---

## ⚠️ SPEC stale vs code (N)

### [symbol] H5 — 僅存在於 code
- SPEC 未列 H5
- config.ts:L78: H5 = { mult_5: 30 }
→ **按鐵律，code 是權威。請 Planner 補 SPEC § Paytable H5 列**

---

## ⚠️ Missing downstream (N)

### [symbol] WILD — i18n key 缺失
- SPEC § Paytable 有 WILD
- i18n/en.ts 無對應 key `paytable.wild.description`

---

## ℹ️ Informational (N)

- [constant] gridSize 僅在 SPEC 提及，code 未 reference（可能動態計算）

---

Verdict: PASS | CONFLICTS FOUND (N 🔴 + N ⚠️)
```

---

### Step 6: 結尾建議

**如果 verdict = PASS：** 建議繼續 `/audit-launch <gamePath>` 進入送審稽核。

**如果 CONFLICTS FOUND：**
- 🔴 項目 → 先由 Planner 討論裁決（按 rule: Spec Changes Must Go Through Planner First）
- ⚠️ SPEC stale → 指派 Planner 按 code 追隨 SPEC
- ⚠️ Missing downstream → 指派 Client / Server 補齊

**禁止行為：**
- 本 skill **不自動修改** SPEC.md / game_config.py / config.ts / i18n
- 僅報告 + 建議路徑。所有修改必須透過 Planner → Supervisor → Client/Server 正規流程

---

## 可與其他 skill 串接

- 上游：`/write-spec` 完成後先跑一次
- 下游：drift 清空後跑 `/audit-launch`
- 姊妹：`/reverse-spec`（從 code 反推 SPEC 缺漏章節）、`/propagate-spec-change`（SPEC 升版時掃影響）
