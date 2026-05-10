---
name: gen-game-text
description: 從 SPEC.md 生成遊戲內 PayTable 和 GameRules 文字（含禁用詞處理）。讀取 SPEC 的符號表、賠率表、遊戲規則、免費旋轉觸發表等章節，產出前端可直接使用的文字內容。統一套用 Social Mode 用語（不分模式）。當使用者提到 PayTable 文字、GameRules 文字、遊戲規則撰寫、賠率表文字、合規文字、或需要產出前端顯示用的遊戲說明時都應觸發。使用方式：/gen-game-text specs/02-pharaohs-cascade
---

# gen-game-text

從 SPEC.md 生成遊戲內 PayTable 和 GameRules 文字，含 Stake 禁用詞統一處理。

## Parameters

- `$ARGUMENTS`: SPEC 資料夾路徑（例如：`specs/02-pharaohs-cascade`）

---

## Execution Flow

### Step 1: 讀取 SPEC + 判斷遊戲類型

Read `$ARGUMENTS/SPEC.md`，提取以下章節：
- Chapter 1: 遊戲概覽（grid size、min_scatter_count、wincap、SDK 計算類型）
- Chapter 3: 符號/賠率定義
- Chapter 7: 核心玩法
- Chapter 12: 投注模式
- Chapter 17: Social Mode 合規
- Chapter 19: 免責聲明

**判斷遊戲類型（決定 Step 4 走哪條分支）：**

- **Slot 類**（cluster / lines / ways / scatter）：有 reels / symbols / paytable / FS trigger → 走 Step 4A
- **Non-slot 類**（table game / dice / progression / binary）：`win_type = "other"`，無 reels/symbols，靠 betMode + Near Miss/Push/多級 payout → 走 Step 4B

Slot 類額外讀取：
- Chapter 9: 免費旋轉觸發表 + 特殊功能（Wild/Scatter/Tumble/Multiplier）

Non-slot 類額外讀取：
- Chapter 3: betMode 列表 + 賠率公式（Near Miss / Push / 多級 payout）
- Chapter 7: 遊戲模式 / 玩法類型 / 特殊機制

### Step 2: 讀取 Dragon Feast 用詞基準

Read `games/01-dragon-feast/src/components/PayTableContent.svelte` 和 `GameRulesContent.svelte`，確認：
- `betWord` = 'play'（硬編碼）
- `payoutWord` = 'Reward'
- Buy Bonus 標題 = 'GET BONUS'
- Disclaimer 格式

### Step 3: 生成 PayTable 文字

對每個符號產出：
```
{symbol_label} ({symbol_id})
{count1}+: {payout1}x | {count2}+: {payout2}x | ...
```

加上：
- Wild 說明（替代規則 + FS 中乘數規則如有）
- Scatter 說明（觸發規則）

### Step 4A: 生成 GameRules 文字（Slot 類）

按以下區塊產出（全部使用統一禁用詞版本）：

1. **核心玩法**（PAY ANYWHERE / CLUSTER WIN / LINES / WAYS — 依 SPEC win_type）
2. **TUMBLE FEATURE**（如有）
3. **GLOBAL MULTIPLIER**（如有，含 base vs FS 行為差異）
4. **WILD SYMBOL**（替代規則 + 位置限制）
5. **FREE SPINS**（觸發表 + retrigger + hardcap）
6. **GET BONUS**（cost、旋轉次數分佈）— 注意不用 BUY BONUS
7. **WIN CAP**（最大贏分）
8. **DISCLAIMER**（法定 6 句）

### Step 4B: 生成 GameRules 文字（Non-Slot 類，2026-04-14 新增）

Slot 類的 Wild/Scatter/Tumble/FS/Buy Bonus/Multiplier Grid 全部**跳過**（non-slot 遊戲不適用）。改用以下區塊：

1. **Core Gameplay**（How to Play — 模式選擇、玩法選擇、結果決定）
2. **Game Modes**（如 Single / Double dice / 武器等級 / 下注選項）
3. **Guess Types / Play Types**（Exact / Big-Small / Odd-Even / 其他依遊戲類型）
4. **Near Miss 機制**（如有 — 線性不循環、賠率、適用範圍）
5. **Push / Consolation 機制**（如有 — 觸發條件、返還比例）
6. **Recent Results 面板**（如有 — 合規護欄：「Past results do not influence future outcomes.」）
7. **Auto Play**
8. **General**（RTP + Max Reward + Volatility + Play cost）
9. **DISCLAIMER**（法定 6 句，使用 "wins and plays" 非 "wins and bets"）

**Non-Slot 類 PayTable 結構建議：**
按 betMode 分組表格（而非符號分組），例如：
- Group 1: Mode A + Play Type 1（所有 betMode 的賠率表）
- Group 2: Mode A + Play Type 2
- Group 3: Mode B + Play Type 1 ... etc.
- 加上 Result Types 圖例（如 HIT / CLOSE / PUSH / MISS）

**參考範例：** `specs/05-dice-royale/GAME_TEXT.md`（Dice Royale 25 betMode 分 5 組 + 4 級 Result Types 圖例）

**Non-Slot 類還需要注意：**
- 參照 `specs/_shared/NON_SLOT_M_AUDIT_SOP.md` 確認 Near Miss / Push 機制符合 M-audit
- Disclaimer 第一句必須是 "Malfunction voids all wins and plays"（非 "wins and bets"）
- 若有 50/50 binary betMode（如 d_even/s_odd），送審時可能需要獨立申報 table game 慣例（參 SOP Ch 5）

### Step 5: 禁用詞處理

全文套用以下替換（不分 social/standard，統一版本）：

| 禁用 | 替換 |
|------|------|
| bet/bets | play/plays |
| total bet | total play |
| buy bonus | get bonus |
| wager | play |
| pay/pays/paid | win/wins/won |
| cash/money | coins |
| purchase | play |
| gamble | play |
| payout | reward |

### Step 6: 交叉驗證

- 賠率數值與 SPEC Chapter 3 一致
- 觸發表數值與 SPEC Chapter 9 一致
- wincap 數值與 SPEC Chapter 1 一致
- Disclaimer 6 句完整

### Step 7: 輸出

以 Markdown 格式輸出完整文字，標註哪些段落是 PayTable、哪些是 GameRules。

提醒 Client：
- PayTable 用 `payoutWord = 'Reward'`
- GameRules 用 `betWord = 'play'`（硬編碼，不用 isSocial 切換）

---

## References

- `stake-docs/04-approval-guidelines.md` §9 — 禁用術語完整列表
- `games/01-dragon-feast/src/components/PayTableContent.svelte` — 用詞基準
- `games/01-dragon-feast/src/components/GameRulesContent.svelte` — 結構基準
