# PayTable 和 GameRules Svelte 模板生成指南

本文件包含 Step 5.4 的完整模板生成細節。

## 5.4.1 生成 `PayTableContent.svelte`

建立 `games/{game_id}/src/components/PayTableContent.svelte`，參考現有遊戲的結構：
- Cluster 類型：`games/dragon-feast/src/components/PayTableContent.svelte`
- Scatter 類型：`games/pharaohs-cascade/src/components/PayTableContent.svelte`

- **從 config.ts 讀取賠率數據**（不要寫死數字）
- **Stake.US Social Mode 必要處理**：script 區塊必須加入 social 模式變數：
```svelte
<script lang="ts">
    import config from '../game/config';
    import { stateUrlDerived } from 'state-shared';
    const isSocial = stateUrlDerived.social();
    const betWord = isSocial ? 'play' : 'bet';
    const payoutWord = isSocial ? 'Reward' : 'Payout';
</script>
```
- 所有 "bet" → `{betWord}`、"Payout" → `{payoutWord}`、"pay" → `{isSocial ? 'reward' : 'pay'}`
- **Special Symbols 區塊**：Wild 和 Scatter（或其他特殊符號），顯示圖片 + 說明
- **Symbol Payouts 區塊**：每個一般符號的圖片 + 各階賠率
- 賠率階的門檻值根據遊戲類型調整：
  - Cluster：依企劃書的 cluster size 門檻（例如 5+/8+/12+/15+/20+）
  - Lines/Ways：依連線數（例如 3/4/5）
- 樣式：金色標題（`#ffd700`）、白色文字、深色半透明背景卡片
- **必須加上** `max-height: 80vh; overflow-y: auto;` 以確保內容在 modal 內捲動

`getPayTiers` 函式需根據 config.ts 的 paytable 結構動態擷取門檻值（不要硬寫門檻）。

## 5.4.2 生成 `GameRulesContent.svelte`

建立 `games/{game_id}/src/components/GameRulesContent.svelte`，參考現有遊戲的結構：
- Cluster 類型：`games/dragon-feast/src/components/GameRulesContent.svelte`
- Scatter 類型：`games/pharaohs-cascade/src/components/GameRulesContent.svelte`

**Stake.US Social Mode 必要處理**：script 區塊必須加入 social 模式變數，所有 "bet" 用 `{betWord}` 替代：
```svelte
<script lang="ts">
    import { stateUrlDerived } from 'state-shared';
    const betWord = $derived(stateUrlDerived.social() ? 'play' : 'bet');
    const buyBonusTitle = $derived(stateUrlDerived.social() ? 'PLAY BONUS' : 'BUY BONUS');
</script>
```
- `80× bet` → `80× {betWord}`
- `Maximum win: 10,000× bet` → `Maximum win: 10,000× {betWord}`
- `BUY BONUS` → `{buyBonusTitle}`

根據 SPEC.md 的規則章節，生成對應的英文規則段落。常見章節：

1. **核心機制**（Cluster Pay / Lines / Ways / Scatter）— 盤面大小、最低中獎條件
2. **Tumble/Cascade 機制**（如果有）
3. **Wild 符號**（替代規則、出現位置限制）
4. **特殊機制**（Multiplier Grid、Hold & Win、堆疊符號等 — 依企劃書）
5. **Scatter & Free Spins**（觸發條件表格、re-trigger 表格）
6. **Buy Bonus**（費用、效果）
7. **General + Disclaimer**（RTP、Volatility、Max Win、**完整免責聲明**）

**完整免責聲明（必須）**：
```svelte
<p class="disclaimer">
    Malfunction voids all pays and plays. A consistent internet connection is required.
    In the event of a disconnection, reload the game to finish any uncompleted {betWord}s.
    The expected return is calculated over many spins. Animations are not representative
    of any physical device, and are for illustrative purposes only.
    TM and &copy; {new Date().getFullYear()} Stake Engine.
</p>
```

```scss
.disclaimer {
    font-size: 0.75rem;
    opacity: 0.5;
    line-height: 1.6;
    margin: 0.5rem 0 0;
    font-style: italic;
}
```

每個章節使用 `<section>` + `<h3 class="section-title">` + `<ul class="rules-list">`，表格使用 `<table class="rules-table">`。

樣式同 PayTableContent — 金色標題、白字、`max-height: 80vh; overflow-y: auto;`。

## 5.4.3 修改 Game.svelte 接線

在 `games/{game_id}/src/components/Game.svelte` 中：

1. 加入 import：
```typescript
import PayTableContent from './PayTableContent.svelte';
import GameRulesContent from './GameRulesContent.svelte';
```

2. 在 `<Modals>` 區塊加入 snippet：
```svelte
<Modals>
	{#snippet version()}
		<GameVersion version="0.0.1" />
	{/snippet}
	{#snippet payTableContent()}
		<PayTableContent />
	{/snippet}
	{#snippet gameRulesContent()}
		<GameRulesContent />
	{/snippet}
</Modals>
```

**前提**：SDK 的 `Modals.svelte` 已支援 `payTableContent` / `gameRulesContent` optional snippets（已在 web-sdk commit `9c936cc` 中完成）。
