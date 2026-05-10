---
name: audit-launch
description: 遊戲功能開發完成後進行送審前稽核。根據 Stake Engine 官方 checklist 自動檢查程式碼層級項目，標記需要人工測試的項目，生成 CHECKLIST.md（含修復計畫）和送審用 Game Details 描述（含與 PayTable/GameRules 的交叉驗證）。當使用者提到送審、上架檢查、checklist、launch audit、合規檢查、或遊戲準備好了要提交時都應觸發。使用方式：/audit-launch games/dragon-feast
---

# audit-launch

Audit a Stake Engine game against the official developer checklist. Auto-checks code-level items via Grep/Read, flags items needing manual testing or backend ops as ⚠️, and generates a structured `CHECKLIST.md` with fix plans for any ❌ items.

## Parameters

- `$ARGUMENTS`: Game project path (e.g. `games/dragon-feast`)

---

## 🚨 審查員 Round-1 高頻 5 大 issue（送審前 self-audit cheat sheet）

**根據 2026-04-26 Forge of Fortune + Crystal Match 同日 round-1 review 經驗**：以下 5 issue 高度一致出現在多款遊戲，送審前必逐項 grep 確認。詳見 knowledge graph node `5ee61ebb`。

### Issue #1 — Bet 必須 == RGS authenticate `betLevels`（snap-to-roster）
- **bug pattern**：balance < maxBet 時 + 鈕跳到 balance（off-roster），或 BetMenu grid 沒乘 active mode `costMultiplier` 算 affordability
- **必要 fix（兩層）**：
  - layer 1: `correctBetAmount` snap-to-roster — `cap = min(value, balance/costMultiplier)` 再 `best = max{opt ≤ cap}`
  - layer 2: `BetMenuAmountGrid.isDisabled = value * costMultiplier > balance`，且 onchange 走 `setBetAmount`（經 layer 1 snap），不要 `stateBet.betAmount = value` 直接 bypass
- **檔**：`sdks/web-sdk/packages/state-shared/src/stateBet.svelte.ts` + `components-ui-html/BetMenuAmountGrid.svelte`
- **Verify**：balance 1000 / cv=2 (Mythic active) → level 600+ 在 BetMenu 必 dim（600×2=1200>1000）

### Issue #2 — 字體不可載 Google API
- grep `fonts.googleapis.com` / `@import url(.*google` 在 `app.html` / +layout / global.css 必 0 命中
- Fix：`@font-face` 用 local `static/assets/fonts/*.ttf`，刪 googleapis link
- DevTools Network 跑一輪確認 0 個 googleapis 請求

### Issue #3 — RTP per game mode 必須清楚顯示 + 2 decimal
- 審查員字面：「all modes are stated in the info (except only in the case that they are exactly the same), and that the values are accurate to two decimals.」
- **判定**：math sim 撈各 mode RTP，round 2 decimals **任一不同**即必須 list per mode
- **Forge 範例**：36 betMode 95.99-96.01% 全 round = 96.00% → 單行 OK
- **Crystal Match 範例**：8 betMode 95.96-96.05% round 後各異 → 必須 8 行 table
- **同步刪舊矛盾敘述**：加 per-mode table 必同時刪 "all modes have equal returns" / "RTP for this game is 96.00%" 等聲明（詳見 knowledge node `00376b3a`）

### Issue #4 — 所有 viewport 必須功能完整
- popout S (400×225) / Mobile S (320×568) / Mobile M (375×667) 都要可見可點所有 button (info / menu / random / play / auto / balance)
- **常見 bug**：modal 寬度沒響應 / bottom-bar 被 panel 擠出 / button 太大溢出
- **Fix pattern**（詳見 knowledge node `e1eee0b3`）：
  - bottom-bar `position: absolute; bottom:0; z-index:50` 強制 pin viewport（不依賴 flex）
  - panel `align-self: flex-start` + `justify-content: flex-start` 不被父層拉滿
  - 隱藏 popout S 的 `.panel-label` 省 ~26px
  - **不要 8×1 gem grid**（panel 太窄會 clip 最後一顆）— 維持 4×2 或 6-block vertical
  - wide table 拆成多個垂直 block (per mode/section)

### Issue #5 — Social Mode 禁用詞（嚴格）
- grep 跨 7 語系 `\b(cost|cash|wager|bet)\b|Kosten|coste|costo|コスト|비용|custo|費用` 必 0 命中
- **「play cost」compound 也算違規** — `cost` 整字不能出現
- 對等替換：`cost → per play`、`cash out → settle`、`Cash → play / win`
- 跨檔位置：`src/i18n/messagesMap/*.ts` × 7 + hardcode 字串 (`NORMAL_FORGE_DIALOG`, `PAYTABLE_INTRO`, `INTRO_FEATURE_*` 等)

### Round-1 fix order 建議（最快收工順序）
1. **Issue #5 禁用詞**（30-60min）— 簡單 i18n 替換
2. **Issue #2 local font**（40min）
3. **Issue #3 per-mode RTP**（1-2h，含跑 sim 撈數據）
4. **Issue #1 bet snap two-layer**（1.5h，SDK 改影響全遊戲）
5. **Issue #4 mobile responsive**（1.5-3h，多輪 owner 截圖驗收）

### Verify checklist after fixes
```bash
# Issue #5 verify
grep -r "\b(cost|cash|wager|bet)\b" {gamePath}/src/i18n/messagesMap/ | grep -v "betWord\|costMultiplier"
# (應只剩 SDK i18n 變數名)

# Issue #2 verify
grep -r "googleapis\|@import url" {gamePath}/src/

# Issue #3 verify (跨對應 RTP table 與 single-RTP statement)
grep -ri "equal expected returns\|all.*equal.*returns\|theoretical return.*is 96" {gamePath}/src/
```

---

## Execution Flow

### Step 1: Parse arguments + pre-flight

Extract from `$ARGUMENTS`:
- `gamePath`: game project path
- `gameId`: derived from path (e.g. `dragon-feast`)

Verify:
```bash
ls {gamePath}/src/components/
ls {gamePath}/src/game/config.ts
```

Read `{gamePath}/src/game/config.ts` to extract:
- `gameName` — display name
- `rtp` — configured RTP value
- `betModes` — available bet modes and their `costMultiplier`
- `symbols` — symbol definitions and paytable

---

### Step 2: Load template

Read the checklist template:
```
.claude/files/CHECKLIST_TEMPLATE.md
```

This contains all 50 checklist items grouped into 12 categories, with "How to check" instructions and "Common fix" code examples for each.

---

### Step 3: Auto-check code-level items

Use `Grep` and `Read` tools to check each item per the template's "How to check" instructions. For each item, determine ✅ / ⚠️ / ❌.

#### 3a. PreChecks (4 items)

| Check | Tool | What to search |
|-------|------|---------------|
| RGS Auth | Grep | `Authenticate` in `{gamePath}/src/routes/` |
| Play Request | Grep | `playBet\|playBookEvents` in `{gamePath}/src/` |
| Game Title | Read | `config.ts` → verify `gameName` has no trademark terms |
| Assets | — | Mark ⚠️ (manual visual review) |

#### 3b. Game Tile / Thumbnail (7 items)

根據 approval-guidelines §7 Game Tile Requirements，遊戲送審時必須附上磚圖素材。

**可自動檢查項目（來源：stake-docs/04-approval-guidelines.md §7）：**

| Check | Tool | What to search |
|-------|------|---------------|
| BG 圖片存在 | Glob | `Art/{gameId}/*-BG.png`, `Art/{gameId}/*-BG.jpg`, 或 `{gamePath}/static/assets/sprites/*-BG.*` |
| FG 圖片存在 | Glob | `Art/{gameId}/*-FG.png` 或 `{gamePath}/static/assets/sprites/*-FG.png` |
| Provider Logo 存在 | Glob | `Art/{gameId}/*-Logo.png` 或 `{gamePath}/static/assets/sprites/*-Logo.png` |
| BG+FG ≤ 3MB | Bash | `stat` 取得檔案大小，計算合計是否 ≤ 3,145,728 bytes |
| FG 為 PNG（透明背景）| — | 檢查副檔名為 `.png` |

**命名規範驗證**：
- BG: `{GameTitle}-BG.png` 或 `{GameTitle}-BG.jpg`
- FG: `{GameTitle}-FG.png`（必須透明背景）
- Logo: `{ProviderName}-Logo.png`（必須透明背景，小尺寸清晰可辨）

**自動檢查腳本**：
```bash
# 搜尋 Game Tile 素材（在 Art/ 和 gamePath/ 中）
# BG
ls Art/{gameId}/*-BG.{png,jpg} {gamePath}/static/assets/sprites/*-BG.{png,jpg} 2>/dev/null
# FG
ls Art/{gameId}/*-FG.png {gamePath}/static/assets/sprites/*-FG.png 2>/dev/null
# Logo
ls Art/{gameId}/*-Logo.png {gamePath}/static/assets/sprites/*-Logo.png 2>/dev/null
# Size check (BG + FG ≤ 3MB)
stat -c%s {bg_file} {fg_file} 2>/dev/null | awk '{s+=$1} END{if(s>3145728) print "[FAIL] BG+FG="s" bytes > 3MB"; else print "[PASS] BG+FG="s" bytes"}'
```

**判定邏輯**：
- BG/FG/Logo 都存在 + 大小合規 → ✅
- 部分素材缺失 → ❌（附 fix plan：使用 `/gen-assets` 生成，或提醒手動製作）
- 大小超過 3MB → ❌（建議壓縮 BG 為 JPG 或降低解析度）
- 素材存在但需視覺品質確認 → ⚠️

**仍需人工檢查**：
- 視覺品質（是否看起來「品質低或視覺吸引力不足」）
- FG 實際是否透明背景
- Logo 小尺寸是否清晰可辨

#### 3c. Math Requirements (1 item)

⚠️ — requires Dashboard verification.

#### 3d. RGS Requirements (5 items)

| Check | Tool | What to search |
|-------|------|---------------|
| Bet Levels ×3 | — | ⚠️ (backend config, applied during approval) |
| Bet Resume | Grep | `ResumeBet\|betToResume` in SDK |
| RGS URL | — | ✅ (SDK handles via `<Authenticate>`) |

#### 3e. Frontend Requirements (8 items)

| Check | Tool | What to search |
|-------|------|---------------|
| Symbol Payouts | Read | `PayTableContent.svelte` — verify symbols from `config.ts` are listed |
| RTP / Max Win | Grep | `RTP\|Maximum win` in `GameRulesContent.svelte` |
| Win Combos | Read | `GameRulesContent.svelte` — verify cluster/line/scatter rules |
| Mode Descriptions | Read | `GameRulesContent.svelte` — each betMode has description + cost |
| Free Spins | Grep | `Free Spins\|free spin` in `GameRulesContent.svelte` |
| Disclaimer | Grep | `Malfunction voids` in `GameRulesContent.svelte` — check completeness |
| Confirm Step | Read | `config.ts` → if any `costMultiplier > 2`, verify `buyBonusConfirm` |
| Auto Play | — | ✅ (SDK `ModalAutoSpin.svelte` handles) |

**Disclaimer completeness check** — must contain ALL of these phrases:
1. `Malfunction voids all pays and plays`
2. `consistent internet connection`
3. `reload the game`
4. `expected return is calculated`
5. `Animations are not representative`
6. `Stake Engine`

#### 3f. Sounds (1 item)

Search for `Sound.svelte` or sound-related imports in game components. SDK BrandUI handles mute control.

#### 3g. Responsive (6 items)

| Check | Tool | What to search |
|-------|------|---------------|
| Desktop | Read | Layout config for landscape dimensions |
| Mobile | Read | Layout config for portrait dimensions |
| Popout S/M | — | ⚠️ (manual testing) |
| 10 Wins | — | ⚠️ (manual testing) |
| Replay UI 小螢幕 | Grep | `scale` or `landingScale` in `BrandUIReplay.svelte` — landing screen 需有響應式縮放以適配 Popout S (400×225) / Mobile S (320×568) |
| **Popout S bottom-bar pin** | Grep | game overlay svelte 中 `position:\s*absolute` + `bottom:\s*0` 在 `.bottom-bar` 或同效 selector — 不能依賴 flex 否則 panel 撐高會擠出 |
| **Popout S panel align-self** | Grep | `align-self:\s*flex-start` + `justify-content:\s*flex-start` 在 popout @media block — 防 panel 被父層 stretch 拉滿 |
| **Mobile wide table 拆 block** | Read | PayTable / GameRules 5+ column wide table 必須改用 vertical block layout (per mode/section) for popout S responsive — 避免 horizontal scroll 醜化 |
| **All viewport features visible** | — | ⚠️ (manual testing — popout S 必含 info button / random / play / auto / balance 全部 button) — 不可砍功能 |
| 直橫版切換 | — | ⚠️ (manual testing — 從直版切回橫版時底部 UI 是否穿透到前面) |

#### 3h. Stake.US Jurisdiction (11 items)

**Critical auto-checks:**

| Check | Tool | What to search |
|-------|------|---------------|
| Social import | Grep | `stateUrlDerived` in game's `.svelte` files |
| Hardcoded "bet" | Grep | Case-insensitive `"bet"` in `GameRulesContent.svelte`, `PayTableContent.svelte` (excluding `{betWord}`) |
| Hardcoded "BUY" | Grep | `"BUY"` in `GameRulesContent.svelte`, `Game.svelte` (excluding conditional) |
| **嚴格 cost / cash 跨 7 lang grep** | Grep | `\b(cost\|cash\|wager)\b` 跨 `src/i18n/messagesMap/{en,de,es,ja,ko,pt,zh}.ts` 必 0 命中（**`play cost` compound 也算違規** — `cost` 整字不能出現）|
| **Locale 等同詞 grep** | Grep | `Kosten\|coste\|costo\|コスト\|비용\|custo\|費用` 跨對應 lang 必 0 命中 |
| **Hardcode 字串排除** | Grep | `NORMAL_FORGE_DIALOG\|PAYTABLE_INTRO\|INTRO_FEATURE_*` 等 dialog 字串內也要 grep cost/cash |
| betModeMeta social | Read | `Game.svelte` → check `betModeMeta.BONUS.text` uses `isSocial` conditional |
| SDK i18n | Read | `sdks/web-sdk/packages/components-ui-html/src/i18n/i18nDerived.ts` → check `betMenu`, `insufficientFunds` have social handling |
| SC/GC | — | ⚠️ (manual testing) |
| No $ prefix | — | ⚠️ (manual testing) |
| Replay words | — | ⚠️ (SDK handles, manual confirm) |

#### 3k. Console Log Hygiene (5 items)

**Purpose**: Stake Engine 部署後 console 不應有紅色 error 或大量 warning 洗版。審核時會被標記。

| Check | Tool | What to search |
|-------|------|---------------|
| CSP compliance | Grep | `typekit\|cdn.jsdelivr\|unpkg\|cdnjs` in all `app.html` — 外部資源必須來自 CSP 白名單 |
| Font source | Grep | `fontFamily` in SDK + game — 確認字體來源是 CSP 允許的（`fonts.googleapis.com` 或 self-hosted） |
| i18n completeness | Read | 比對 `i18nDerived.ts` 所有 `translate('KEY')` vs `messagesMap/en.ts` 的 key — 缺少 = Lingui fallback 警告 |
| Lingui compiler | Grep | `_messageCompiler` in `stateI18n.svelte.ts` — 未設定則所有 string 觸發 "Uncompiled message" 警告 |
| dist/source sync | Read | 有 `dist/` 的 package（pixi-svelte）— `dist/utils.svelte.js` 的 `preloadFont` 是否與 source 一致 |

**Stake Engine CSP 白名單（已知）：**
- `style-src`: `'self'`, `'unsafe-inline'`, `https://fonts.googleapis.com`
- `script-src`: `'self'`, `'unsafe-inline'`, `'unsafe-eval'`, `blob:`
- **不允許**: `use.typekit.net`, `cdn.jsdelivr.net`, `unpkg.com`

**Common fix: CSP font violation**

1. `app.html` — typekit → Google Fonts:
```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,200..900;1,200..900&display=swap" />
```

2. `pixi-svelte/src/lib/utils.svelte.ts` — WebFont.load 改 google:
```typescript
WebFont.load({
    google: { families: ['Source Sans 3:200,300,400,500,600,700,800,900'] },
});
```

3. 全域 `fontFamily: 'proxima-nova'` → `'Source Sans 3'`

4. **陷阱**: `pixi-svelte` exports from `dist/`。改完 source 必須同步 `dist/utils.svelte.js`，否則 game build 仍用舊 dist。

**Common fix: Lingui _messageCompiler**

`state-shared/src/stateI18n.svelte.ts`:
```typescript
import { i18n } from '@lingui/core';
// @ts-ignore
i18n._messageCompiler = (message: string) => message;
```

**Common fix: i18n messagesMap 缺 key**

補齊 `components-ui-pixi/src/i18n/messagesMap/en.ts` 所有 `translate()` 用到的 key。同步更新 `zh.ts`。`components-ui-html` 的 messagesMap 也需補齊。

---

#### 3l. Bet / Currency Correctness (3 items)

**Purpose**: 確保各幣種的預設下注、最大下注、BET MENU 顯示正確。這些是 SDK 層面的問題，影響所有遊戲。

| Check | Tool | What to search |
|-------|------|---------------|
| defaultBetLevel applied | Read | `Authenticate.svelte` — 確認 `authenticateData.config.defaultBetLevel` 有被讀取並套用到 `stateBet.betAmount` |
| BetMenu MAX = actual max | Read | `BetMenuAmountGrid.svelte` — MAX 按鈕應用 `betAmountOptions` 的最後一項，而非 `betMenuOptions` 的最後一項 |
| **correctBetAmount snap-to-roster** | Read | `state-shared/stateBet.svelte.ts` — `correctBetAmount` 必須 `cap = min(value, balance/costMultiplier)` 再 `best = max{opt ∈ betAmountOptions \| opt ≤ cap}`，不能直接 clamp 到 balance |
| **BetMenu cell affordability uses costMultiplier** | Read | `BetMenuAmountGrid.svelte` — `isDisabled` 必須 `value * costMultiplier > balance`（從 `stateBetDerived.betCostMultiplier()` 取），不能只比 `value > balance` |
| **BetMenu onchange 走 setBetAmount** | Read | `BetMenuAmountGrid.svelte` — onchange 必須走 `stateBetDerived.setBetAmount(value)` 經過 correctBetAmount，不能 `stateBet.betAmount = value` 直接 bypass |
| Clean build after SDK change | — | ⚠️ 提醒使用者：修改 SDK 後必須 clean build（刪除 dist/、.svelte-kit/），否則 Vite cache 會導致舊代碼殘留 |

**Bug 背景**:

1. **defaultBetLevel 被忽略**: RGS authenticate 回傳 `defaultBetLevel`（如 JPY ¥100），但 SDK 的 `stateBet.betAmount` 硬編碼為 `1`，導致所有幣種進場預設 bet 都是 1（而非後台設定的預設值）。
2. **BET MENU MAX 不是真正最大值**: `MOST_USED_BET_INDEXES` 是硬編碼的 index 清單（最大到 38），但某些幣種（如 JPY）的 betLevels 有 40 項（index 0~39）。`betMenuOptions` 過濾後漏掉了真正的最大值（index 39）。MAX 按鈕顯示的是 betMenuOptions 的最後一項（¥100,000）而非 betAmountOptions 的最大值（¥150,000）。

**Common fix: defaultBetLevel**

`components-shared/src/components/Authenticate.svelte` — 在設定 betAmountOptions/betMenuOptions 之後加入：
```typescript
// Apply defaultBetLevel from RGS config
if (authenticateData.config?.defaultBetLevel) {
    const defaultBet = authenticateData.config.defaultBetLevel / API_AMOUNT_MULTIPLIER;
    if (stateConfig.betAmountOptions.includes(defaultBet)) {
        stateBet.betAmount = defaultBet;
    }
}
```

注意：此段必須在 `round` 檢查之前。如果有 active round，`round.amount` 會覆蓋（優先級正確）。

**Common fix: BetMenu MAX**

`components-ui-html/src/components/BetMenuAmountGrid.svelte`:
```typescript
// 用 betAmountOptions 的真正最大值，而非 betMenuOptions 的最後一項
const actualMax = $derived(stateConfig.betAmountOptions[stateConfig.betAmountOptions.length - 1]);
const options = $derived(
    [
        ...stateConfig.betMenuOptions.slice(0, count - 1),
        actualMax,
    ].filter((value, index, array) => array.indexOf(value) === index),
);
const isMaxValue = (value: number) => value === actualMax;
```

---

#### 3m. Session Duration / Game Time（遊戲時長合規）

**Purpose**: Stake Engine 審查員會測試 Max Win Replay。如果 replay 播放超過 2-3 分鐘（例如需要數百輪 free spin），會被退件要求修正。此類問題應在數學模型階段就預防。

**檢查項目（需讀取數學模型）：**

前提：確認 `models/{gameId}/` 存在。如不存在（submodule 未 clone），標記 ⚠️ 提醒使用者。

| Check | Tool | What to search |
|-------|------|---------------|
| `max_free_spins` 存在 | Read | `models/{gameId}/game_config.py` — 搜尋 `max_free_spins` |
| `max_free_spins` ≤ 50 | Read | 確認值 ≤ 50，推薦 30 |
| Scatter 壓制邏輯 | Grep | `_suppress_scatters` in `models/{gameId}/game_override.py` |
| Wincap bypass | Grep | `force_wincap` in `models/{gameId}/gamestate.py` |
| 乘數封頂 | Read | `models/{gameId}/game_config.py` — 搜尋 `mult_levels`，確認最大值 ≤ 128 |
| 前端 hard cap 說明 | Grep | `最多\|上限\|maximum` in `GameRulesContent.svelte` — 確認有告知玩家 |

**判定邏輯：**
- `max_free_spins` 存在且 ≤ 50 + scatter 壓制存在 + wincap bypass 存在 → ✅
- `max_free_spins` 不存在 → ❌（附 fix plan：在 game_config.py 加入 `self.max_free_spins = 30`）
- `max_free_spins` > 50 → ⚠️（警告 replay 可能過長，建議降為 30）
- Scatter 壓制缺失（Tumble 類遊戲）→ ❌（附 fix plan：在 game_override.py 加入 `draw_board()` override + `_suppress_scatters()`）
- Wincap bypass 缺失 → ❌（附 fix plan：在 gamestate.py 的 `check_fs_condition` 後加入 `force_wincap` 判斷）
- 乘數無封頂 → ⚠️（建議加入 mult_levels 等級表，推薦封頂 ×64）

**Common fix: max_free_spins**

`models/{gameId}/game_config.py`：
```python
# 免費旋轉硬上限（Stake Engine 審核要求）
self.max_free_spins = 30
```

**Common fix: Scatter 壓制**

`models/{gameId}/game_override.py`：
```python
from src.events.events import reveal_event

def draw_board(self, emit_event=True, trigger_symbol="scatter"):
    """覆寫 SDK 的 draw_board()，加入 scatter 壓制。"""
    is_wincap_sim = self.get_current_distribution_conditions().get("force_wincap", False)
    if (self.gametype == self.config.freegame_type
            and self.tot_fs >= self.config.max_free_spins
            and not is_wincap_sim):
        super().draw_board(emit_event=False, trigger_symbol=trigger_symbol)
        self._suppress_scatters()
        if emit_event:
            reveal_event(self)
    else:
        super().draw_board(emit_event=emit_event, trigger_symbol=trigger_symbol)

def _suppress_scatters(self):
    """將盤面上所有 S 替換為隨機一般符號。"""
    import random
    normal_symbols = [s for s in self.config.paytable_symbols if s not in ["W", "S"]]
    for reel in range(self.config.num_reels):
        for row in range(self.config.num_rows[reel]):
            if self.board[reel][row].name == "S":
                self.board[reel][row] = self.create_symbol(random.choice(normal_symbols))
    self.get_special_symbols_on_board()
```

**Common fix: Wincap bypass**

`models/{gameId}/gamestate.py` — 在 `check_fs_condition()` 後：
```python
if self.check_fs_condition():
    self.update_fs_retrigger_amt()
    is_wincap_sim = self.get_current_distribution_conditions().get("force_wincap", False)
    if not is_wincap_sim:
        self.tot_fs = min(self.tot_fs, self.config.max_free_spins)
```

---

#### 3n. Math Model vs Frontend Cross-Validation（數學模型 vs 前端文字交叉驗證）

**Purpose**: 驗證 PayTableContent / GameRulesContent 中的文字描述是否與數學模型的實際值完全一致。這類錯誤審查員不一定能發現，但一旦玩家體驗與說明不符會產生客訴風險。

**前提**：確認 `models/{gameId}/` 存在。如不存在，標記 ⚠️ 提醒使用者 clone submodule。

**檢查項目：**

| Check | 來源 A（前端） | 來源 B（數學模型） | 比對方式 |
|-------|--------------|-----------------|---------|
| Paytable 數值 | `config.ts` symbols paytable | `game_config.py` `_cluster_pays` | 逐符號逐 tier 比對 |
| Free Spin 觸發表 | `GameRulesContent.svelte` 表格 | `game_config.py` `_base_fs` | 逐行比對 scatter count → FS count |
| Free Spin 重觸發表 | `GameRulesContent.svelte` 表格 | `game_config.py` `_free_fs` | 逐行比對 |
| Wild 乘數值 | `PayTableContent.svelte` Wild 區塊 | `game_override.py` `assign_mult_property` 註解 + `game_config.py` `mult_values` distribution keys | 比對可能的乘數值集合 |
| Wild 乘數組合方式 | `PayTableContent.svelte` 文字 | `game_calculations.py` `wild_mult_product` 邏輯 | "added" vs "multiplied" |
| 位置乘數組合方式 | `GameRulesContent.svelte` 文字 | `game_calculations.py` `board_mult` 邏輯 | "added" vs "multiplied" |
| 位置乘數等級表 | `GameRulesContent.svelte` 文字 | `game_config.py` `mult_levels` | 比對升級序列 |
| Buy Bonus 費用 | `GameRulesContent.svelte` | `game_config.py` bonus `cost` | 數值比對 |
| Max Win | `GameRulesContent.svelte` | `game_config.py` `wincap` | 數值比對 |
| RTP | `GameRulesContent.svelte` | `game_config.py` `rtp` | 數值比對 |
| Max Free Spins | `GameRulesContent.svelte` | `game_config.py` `max_free_spins` | 數值比對 |

**執行流程：**

1. Read `models/{gameId}/game_config.py` → 提取 `_cluster_pays`, `_base_fs`, `_free_fs`, `wincap`, `rtp`, bonus `cost`, `mult_levels`, `max_free_spins`
2. Read `models/{gameId}/game_override.py` → 提取 wild multiplier values（看 `assign_mult_property` 的 `mult_values` keys，排除 key=1）
3. Read `models/{gameId}/game_calculations.py` → 確認 wild mult 是 `*=`（乘積）還是 `+=`（加總）；position mult 同理
4. Read `{gamePath}/src/components/PayTableContent.svelte` → 提取 Wild 乘數描述文字
5. Read `{gamePath}/src/components/GameRulesContent.svelte` → 提取 FS 觸發表、retrigger 表、Buy Bonus 費用、RTP、Max Win、Max FS、乘數升級描述
6. Read `{gamePath}/src/game/config.ts` → 提取 paytable 數值、betModes

**判定邏輯：**
- 所有數值完全一致 → ✅
- 任一數值不一致 → ❌（詳列差異 + 修正建議）
- 文字描述模糊但不矛盾 → ⚠️（建議精確化）
- 數學模型不存在 → ⚠️（提醒 clone submodule）

**常見問題模式：**
- Wild 乘數值遺漏（如 base game 只有 ×2/×3/×5 但 free spin 多了 ×10）
- 乘數組合方式寫反（Wild = product，Position = sum，容易混淆）
- Buy Bonus FS 範圍描述不準（需要從 scatter_triggers 分佈推算）
- Free Spin 重觸發表漏列（如 7+ 但模型有 8+ 防禦值）

---

#### 3n-2. Per-mode RTP precision + remove contradicting statements（送審 issue #3 真正點）

**Purpose**: 審查員 round-1 高頻抓「The RTP values displayed in the game (96.00%) are different than the values in the math (95.96-96.05%)」。原因不只是「沒列 per mode」，更常是**新增 per-mode table 後沒清舊單行 RTP 聲明**，UI 自相矛盾。

**Step 1 — 跑 sim 撈各 mode RTP 4 decimals**:
從 `models/{gameId}/library/publish_files/lookUpTable_*.csv` 算每個 betMode 加權平均 payout/cost：
```bash
awk -F', ' '{sw+=$2*$3; w+=$2} END{printf "%.4f\n", sw/w/100}' lookUpTable_{mode}_0.csv
```

**Step 2 — 判定**:
- 全 mode round 到 2 decimals 都相同 → 可單行（如 Forge 36 betMode 全 = 96.00%）
- 任一 mode round 後不同 → 必須 list per mode（如 Crystal Match 8 betMode 95.96-96.05% round 後各異）

**Step 3 — 新增 per-mode table 同時 grep 清舊矛盾敘述**:
```bash
# 必 0 命中（除非全 mode 真的 equal）
grep -ri "equal expected returns\|all.*equal.*returns" {gamePath}/src/i18n/messagesMap/
grep -ri "theoretical return.*is 96\.00\|RTP.*is 96\.00%" {gamePath}/src/i18n/messagesMap/

# 等同詞跨語系
grep -ri "gleiche.*Erträge\|retornos.*iguales\|期待リターン.*同\|기대 수익률.*동일\|retornos.*iguais\|預期回報相同\|预期回报相同" {gamePath}/src/i18n/messagesMap/
```

**判定邏輯**:
- 加 per-mode table + 同步刪舊矛盾敘述 → ✅
- 加 per-mode table 但保留舊「all modes equal」聲明 → ❌（**round-2 必被退**，這是 Crystal Match T7 教訓）
- 全 mode 真的 equal 且只有單行 RTP 聲明 → ✅（Forge 案例）

**範例修正（i18n key 全 7 lang 刪除）**:
```ts
// en.ts — 刪除這行
GR_WISH_3: 'All Wish Gem choices have equal expected returns.',  // ❌ 刪
GR_RTP_DESC: 'The theoretical return to player (RTP) for this game is 96.00%.',  // ❌ 刪（per-mode table 已取代）
```

**並更新 component**:
```svelte
<!-- GameRulesContent.svelte 刪除 -->
<li>{t('GR_WISH_3')}</li>  <!-- ❌ 刪 -->

<!-- 改用 per-mode table -->
{#each MODES as mode}
  <tr><td>{t(`PT_${mode.id}`)}</td><td>{mode.rtp.toFixed(2)}%</td></tr>
{/each}
```

---

#### 3o. Math Model Quality — Bonus 體驗品質驗證 (5 items)

**Purpose**: 防止 bonus mode 數值合規但玩家體驗惡劣的情況通過送審（歷史案例：Pharaohs Cascade bonus zero win 62.34%，M1-M9 全過但被退件）。這是送審前的**最後防線**。

**前提**：確認 `models/{gameId}/` 存在且 `library/publish_files/lookUpTable_bonus_0.csv` 非空。如不存在，標記 ❌ 提醒使用者先跑 `/optimize-rtp`。

**檢查項目：**

| # | Check | Tool | 標準 | 類型 |
|---|-------|------|------|------|
| B1 | Bonus Zero Win Rate | Read LUT | **= 0%** | ❌ 阻擋 |
| B2 | Bonus Below-Cost Rate | Read LUT | ≤ 75%（WARNING ≤ 65%） | ❌ 阻擋 |
| B4 | Optimizer Zero Weight | Read LUT | ≤ 35% | ⚠️ WARNING |
| B5 | FR0 vs BR0 獨立性 | Read CSVs | FR0 ≠ BR0 | ❌ 阻擋 |
| — | Bonus LUT 存在且非空 | Glob + Read | 檔案存在，行數 > 0 | ❌ 阻擋 |

**驗證腳本：**

```python
import csv, os

game_id = "{gameId}"
model_dir = f"models/{game_id}"
lut_path = f"{model_dir}/library/publish_files/lookUpTable_bonus_0.csv"

# 前提檢查：LUT 存在
if not os.path.exists(lut_path):
    print("[FAIL] Bonus LUT 不存在 — 請先跑 /optimize-rtp")
else:
    with open(lut_path) as f:
        rows = list(csv.reader(f))
    if len(rows) == 0:
        print("[FAIL] Bonus LUT 為空")
    else:
        tw = sum(int(r[1]) for r in rows)
        zw = sum(int(r[1]) for r in rows if float(r[2]) == 0)
        
        # 從 game_config.py 讀取 bonus cost（需手動提取）
        cost = {bonus_cost} * 100  # 例如 80 * 100 = 8000
        bcw = sum(int(r[1]) for r in rows if 0 < float(r[2]) < cost)
        
        # B1: Zero Win Rate
        zr = zw / tw * 100
        print(f"[{'PASS' if zw == 0 else 'FAIL'}] B1: Bonus Zero Win = {zr:.2f}%")
        
        # B2: Below-Cost Rate
        bcr = bcw / tw * 100
        if bcr <= 65:
            print(f"[PASS] B2: Below-Cost = {bcr:.1f}%")
        elif bcr <= 75:
            print(f"[WARNING] B2: Below-Cost = {bcr:.1f}% (65-75% 邊界)")
        else:
            print(f"[FAIL] B2: Below-Cost = {bcr:.1f}% > 75%")
        
        # B4: Optimizer Zero Weight
        zwr = zw / tw * 100
        print(f"[{'PASS' if zwr <= 35 else 'WARNING'}] B4: Zero Weight = {zwr:.2f}%")

# B5: FR0 vs BR0 獨立性
fr0 = f"{model_dir}/reels/FR0.csv"
br0 = f"{model_dir}/reels/BR0.csv"
if os.path.exists(fr0) and os.path.exists(br0):
    with open(fr0) as f: fr0_data = f.read()
    with open(br0) as f: br0_data = f.read()
    if fr0_data == br0_data:
        print("[FAIL] B5: FR0 與 BR0 完全相同 — FS 輪帶必須獨立調整")
    else:
        print("[PASS] B5: FR0 與 BR0 分佈不同")
else:
    print("[WARNING] B5: 輪帶檔案不存在，無法比對")
```

**判定邏輯：**
- B1 > 0% → **❌ 阻擋送審**。修復：在 `game_override.py` override `check_repeat()`，bonus mode `final_win < 0.01` 時設 `self.repeat = True`
- B2 > 75% → **❌ 阻擋送審**。修復：調整 FR0 輪帶降低 FS 贏率，或降低 mult_cap / wild mult
- B2 65-75% → **⚠️ WARNING**。可送審但建議優化
- B4 > 35% → **⚠️ WARNING**。通常是 B1/B3 的下游症狀，先修 B1
- B5 FR0 = BR0 → **❌ 阻擋送審**。修復：為 FS 設計獨立 FR0（降 H1/H2 密度，補 L3/L4）
- Bonus LUT 不存在 → **❌ 阻擋送審**。修復：跑 `/optimize-rtp`

---

#### 3h-2. Win Display Quality (2 items)

**Purpose**: 審查員會在實際遊戲中觀察贏分演出。常見問題是多個 cluster win 的金額文字重疊（特別是共用 Wild 時多個 cluster 中心在同一位置）。

| Check | Tool | What to search |
|-------|------|---------------|
| Cluster win overlap prevention | Grep | `resolveOverlaps\|yOffset` in `ClusterWinAmounts.svelte` — 同位置的 wins 必須有垂直展開邏輯 |
| Win text readability | — | ⚠️ (manual testing — 在 Storybook 跑 winInfoOverlap story 或實際遊戲觀察多 cluster 同時出現時文字是否清晰) |

**常見問題**: `bookEventHandlerMap.ts` 的 `winInfo` handler 用 `Promise.all` 同時顯示所有 cluster wins。如果多個 cluster 共用 Wild 符號，它們的 `meta.overlay` 中心點可能相同，導致贏分文字 100% 重疊。

**Common fix**: 在 `ClusterWinAmounts.svelte` 加入 `resolveOverlaps()` 函數：
1. 按 `(reel, row)` 分組
2. 同位置多個 wins 垂直等距展開（間距 `SYMBOL_SIZE * 0.55`）
3. 傳 `yOffset` 給每個 `ClusterWinAmount` 元件套用

#### 3i. Replay Support (12 items)

**Architecture**: SDK `Authenticate.svelte` 偵測 `?replay=true` 並呼叫 `requestReplay()`。但 Replay UI 需在遊戲層實作。使用 `BrandUI` 的遊戲需自訂 `BrandUIReplay.svelte`，純 SDK 遊戲使用 `UIReplay.svelte`。

| Check | Tool | What to search |
|-------|------|---------------|
| Detect replay mode | Grep | `replay` in SDK `Authenticate.svelte` + `stateUrl.svelte.ts` |
| Fetch replay data | Grep | `requestReplay` in SDK `rgs-requests` |
| Landing screen | Grep | `replayStarted` in `stateUi.svelte.ts` — 必須有此 gate |
| Landing screen info | Read | Replay UI — 須顯示 Mode / Base Bet / Cost Mult / Total Bet Cost / Payout Mult / Total Win |
| Disable betting UI | Read | Replay UI — MENU/TURBO 隱藏，SPIN 用 `eventMode="none"` |
| No session calls | — | ✅ SDK handles |
| Play animation | — | ⚠️ manual testing |
| Replay Again button | Grep | `replayCompleted` in `stateUi.svelte.ts` |
| No normal play entry | — | ⚠️ manual testing |
| Social mode wording | Grep | `stateUrlDerived.social()` in replay i18nDerived |
| Event IDs for reviewer | — | 見下方 Step 7b |
| Playback UI layering | Grep | WIN/SPIN 標籤必須包在 `{#if stateUi.replayStarted}` 內 — 在 landing screen 階段不應顯示，避免穿透 replay overlay |

**ResumeBet guard**: `ResumeBet.svelte` 必須在 replay mode 時 `return`（不自動 broadcast `resumeBet`），等使用者點 Start Replay 後才觸發。

**payoutMultiplier 陷阱**: `stateBet.betToResume.payoutMultiplier` 在 state machine 開始跑後會被清掉。Replay UI 必須用 `$effect` 在 landing screen 階段先 capture 到 local 變數。

**Playback UI layering 陷阱**: BrandUIReplay 中的 WIN 顯示和 SPIN 標籤如果沒有用 `{#if stateUi.replayStarted}` 包裹，會在 landing screen 階段就渲染出來，穿透到 replay overlay 前面（特別是直橫版切換後）。

#### 3j. Final Approval (4 items)

All ⚠️ — backend operations.

---

### Step 4: Generate fix plans for ❌ items

For each ❌ item, generate a fix plan referencing the template's "Common fix" section:

Format per fix:
```markdown
### ❌ N. {Item description}

**Current state:**
{What was found in the code}

**Fix:**
{Specific file to modify + code example from template}

**Estimated effort:** ~{time}
```

---

### Step 5: Write CHECKLIST.md

Use `Write` tool to generate `{gamePath}/CHECKLIST.md`:

1. Replace template placeholders:
   - `{gameName}` → from config.ts
   - `{date}` → today's date
   - `{version}` → from package.json
   - `{passCount}` / `{warnCount}` / `{failCount}` → computed counts
   - `{fixPlans}` → generated in Step 4

2. Fill in each item's Status and Notes columns based on Step 3 results.

3. For ⚠️ items: include a "Manual Verification Checklist" section at the bottom listing each item with instructions.

---

### Step 6: Output summary

Display in terminal:
```
=== Stake Engine Launch Audit ===

Game: {gameName} ({gameId})
RTP:  {rtp}%
Modes: {betModeList}

Results:
  ✅ Pass:              {N} items
  ⚠️ Needs verification: {N} items (manual testing / backend ops)
  ❌ Not implemented:    {N} items (code changes needed)

Output: {gamePath}/CHECKLIST.md

Next steps:
1. Fix all ❌ items (see fix plans in CHECKLIST.md)
2. Manually verify all ⚠️ items on Stake Dashboard
3. Re-run /audit-launch after fixes to update status
```

---

### Step 7b: Generate Event IDs for Reviewer（審查員 Event ID）

審查員會要求提供每個 bet mode 的 Event ID 來測試 replay。Event ID = LUT 的 **bookIndex**。

#### 讀取 LUT 檔案

從數學模型的 `library/publish_files/` 目錄取得：
- `index.json` — 列出所有 modes 和對應的 LUT 檔名
- `lookUpTable_{mode}_0.csv` — 格式：`bookIndex, weight, payout`（payout 100 = 1x bet）

#### 分析 LUT 並挑選 Event ID

用 Bash `awk` 或 subagent 分析 LUT，為每個 mode 找出：

| 場景 | 方法 |
|------|------|
| **Max Win** | `payout == 1000000`（win cap 10,000x）— 取第一筆 bookIndex |
| **High Payout** | 按 payout 排序取 90-95th percentile（高但非 max） |
| **Average Payout** | 計算加權平均 `sum(weight*payout)/sum(weight)`，取最接近的 bookIndex |
| **Loss** | `payout == 0`（僅 BASE mode 有） |

**Max Win Replay 時長估算：**

從 wincap event 的 book 檔案（`books_{mode}.jsonl.zst`）讀取實際 free spin 輪數：
- 每輪 tumble 動畫約 3-5 秒
- 加上開場/結算動畫約 10-15 秒
- 預估公式：`total_seconds = fs_rounds × 4 + 15`

| 預估時長 | 判定 |
|---------|------|
| ≤ 3 分鐘 | ✅ 合規 |
| 3-5 分鐘 | ⚠️ 接近上限，建議優化 |
| > 5 分鐘 | ❌ 審查員會退件，必須縮減 free spin 輪次或加速乘數成長 |

```bash
# 加權平均 payout
awk -F', ' '{sw+=$2*$3; w+=$2} END{printf "%.2f\n", sw/w}' lookUpTable_base_0.csv

# 找 max win 的第一筆
awk -F', ' '$3==1000000{print $1; exit}' lookUpTable_base_0.csv

# 按 payout 排序取 top 20
sort -t', ' -k3 -n -r lookUpTable_base_0.csv | head -20
```

#### 輸出格式

在 CHECKLIST.md 和終端輸出中加入 Event ID 表：

```markdown
## Replay Event IDs

| Mode | Scenario | Event ID | Payout Multiplier |
|------|----------|----------|-------------------|
| BASE | Max Win | {id} | 10,000x |
| BASE | High Payout | {id} | {mult}x |
| BASE | Average Payout | {id} | {mult}x |
| BONUS | Max Win | {id} | 10,000x |
| BONUS | High Payout | {id} | {mult}x |
| BONUS | Average Payout | {id} | {mult}x |

Bet Amount: $1.00 (default)
```

**注意**: 如果 `models/{gameId}/` 目錄不存在（submodule 未 clone），提醒使用者需先 clone 數學模型 submodule。

---

### Step 7: Generate Game Details（送審描述）

Stake Engine 送審表單有一個 "Game Details" 欄位，需要提供遊戲描述給審核團隊。此步驟自動生成該描述並驗證與遊戲內 Info/PayTable 的一致性。

#### 7a. 收集資料來源

| 來源 | 讀取項目 |
|------|---------|
| `config.ts` | gameName, rtp, max_win, betModes, symbols (名稱 + 賠率) |
| `GameRulesContent.svelte` | 機制描述、Free Spin 觸發/重觸發表、Buy Bonus 費用、Disclaimer |
| `PayTableContent.svelte` | 符號英文名、特殊符號描述（Wild/Scatter 功能） |
| `SPEC.md`（如存在） | 主題、波動性、Hit Frequency 等補充資訊 |

#### 7b. 生成送審描述

格式範本（英文）：

```markdown
**{gameName}** is a {gridSize} {mechanic} slot game with a {theme} theme.

**Core Mechanics:**
- {mechanic description — cluster/lines/ways + min count}
- Tumble/Cascade: {if applicable}
- {unique feature — e.g. Position Multiplier Grid}

**Symbols:**
- {highPayCount} High-pay symbols: {H1 name} (H1), {H2 name} (H2), ...
- {lowPayCount} Low-pay symbols: {L1 name} (L1), {L2 name} (L2), ...
- Wild ({wildName}): {wild description from PayTable}
- Scatter ({scatterName}): {scatter description from PayTable}

**Free Spins Feature:**
- {trigger conditions from GameRules}
- {special mechanics during free spins}
- Retrigger: {retrigger conditions}

**Buy Bonus:**
- Cost: {cost}× bet
- {buy bonus description}

**Technical Details:**
- Target RTP: {rtp}%
- Volatility: {volatility}
- Max Win: {maxWin}× bet
- Hit Frequency: ~{hitFreq}% (if available from SPEC)
- Max Free Spins: {max_free_spins} (hard cap)
- Max Win Replay Duration: ~{estimated_minutes} min
- Responsive layouts: Desktop, Landscape, Portrait, Tablet
- Localization: English
```

#### 7c. 交叉驗證

自動比對送審描述 vs 遊戲內容，檢查以下項目是否一致：

| 驗證項目 | 來源 A（送審描述） | 來源 B（遊戲內） |
|---------|-----------------|----------------|
| 符號名稱 | 生成文 | PayTableContent.svelte |
| Wild 功能 | 生成文 | PayTableContent + GameRules |
| Scatter 觸發表 | 生成文 | GameRulesContent.svelte |
| Retrigger 表 | 生成文 | GameRulesContent.svelte |
| Buy Bonus 費用 | 生成文 | GameRulesContent.svelte |
| RTP / Max Win | 生成文 | GameRulesContent.svelte |
| 賠率表數值 | SPEC.md | config.ts |

若有不一致，在 CHECKLIST.md 末尾追加 `## 送審描述一致性報告` 標記差異。

#### 7d. 輸出

1. 在終端顯示生成的送審描述，供使用者複製貼上
2. 將描述同時寫入 `{gamePath}/GAME_DETAILS.md` 備存
3. 若 SPEC.md 賠率表與 config.ts 不一致，提醒使用者更新 SPEC.md

---

### Step 8: Propose commit

```bash
git add {gamePath}/CHECKLIST.md {gamePath}/GAME_DETAILS.md
git commit -m "docs: Stake Engine launch audit + 送審描述 — {gameId}"
```

Push if user approves.

---

## Notes

1. **Re-run safe** — each run overwrites `CHECKLIST.md`, can be re-run at any stage
2. **SDK checks** — some items check SDK source at `sdks/web-sdk/packages/`. If SDK path differs, adapt accordingly
3. **Template updates** — if Stake Engine adds new checklist items, update `.claude/files/CHECKLIST_TEMPLATE.md`
4. **Language** — output CHECKLIST.md in Traditional Chinese (matching existing convention)
5. **Don't build** — never run `pnpm run build` (Vite watch mode hangs terminal). Remind user to build/test manually
6. **送審描述** — Step 7 生成的 GAME_DETAILS.md 可直接複製貼到 Stake Engine 送審表單的 "Game Details" 欄位。交叉驗證會比對 config.ts（實際賠率）vs SPEC.md（企劃書賠率）vs 遊戲內 PayTable/GameRules，若有不一致會提醒更新
7. **Portrait FS 測試** — checklist 必須包含：`[ ] Portrait mode FS 完整流程測試（進入→spin→tumble→win→結束→UI 恢復）` 和 `[ ] Console 無 broadcastAsync TIMEOUT warning`
