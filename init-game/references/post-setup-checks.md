# 後置設定檢查

本文件包含 Step 7.6 至 7.9 的完整檢查細節。

## Step 7.6: 建立 Game Tile 素材目錄

根據 approval-guidelines §7，送審時需要 Game Tile 素材。在 Art 目錄預建結構：

```bash
mkdir -p Art/{spec_folder}/game-tile
```

在 `Art/{spec_folder}/game-tile/` 建立 `README.md` 說明所需素材：

```markdown
# Game Tile 素材（送審必要）

## 所需檔案

| 檔案 | 格式 | 說明 |
|------|------|------|
| `{GameTitle}-BG.png` 或 `.jpg` | 高解析度 | 遊戲背景圖 |
| `{GameTitle}-FG.png` | PNG 透明背景 | 特色角色/物品 |
| `{ProviderName}-Logo.png` | PNG 透明背景 | 供應商 Logo |

## 限制

- **BG + FG 合計 ≤ 3MB**
- FG 和 Logo 必須是透明背景
- 可使用 `/gen-assets` 生成

## 參考

- 來源：approval-guidelines §7 Game Tile Requirements
```

---

## Step 7.7: GameRulesContent 免責聲明驗證

確認 Step 5.4.2 生成的 `GameRulesContent.svelte` 包含**完整的免責聲明**（approval-guidelines §8 要求）：

必須包含以下所有短語：
1. `Malfunction voids all pays and plays`（社群模式：`wins and rounds`）
2. `consistent internet connection`
3. `reload the game`
4. `expected return is calculated`
5. `Animations are not representative`（或 `for illustrative purposes only`）
6. `Stake Engine`

如果遺漏任何短語，自動補全。

---

## Step 7.8: 社群模式合規檢查

確認所有生成的檔案都有 Social Mode 處理：

| 檔案 | 檢查項 |
|------|--------|
| `PayTableContent.svelte` | `import { stateUrlDerived } from 'state-shared'` + `betWord`/`payoutWord` 變數 |
| `GameRulesContent.svelte` | `betWord` + `buyBonusTitle` 變數，所有 "bet" 用 `{betWord}` 替代 |
| `Game.svelte` | `betModeMeta` 中 BONUS 的 text 使用 `isSocial` 判斷（`BUY BONUS` vs `PLAY BONUS`）|

如果遊戲有其他 UI 文字包含 approval-guidelines §9 禁用術語，一併替換。

---

## Step 7.9: Replay 就緒備註

在 `WORK_ITEMS.md` 或 `README.md` 中加入 Replay 實作提醒：

```markdown
## Replay（送審必要）

Bet Replay 是 Stake Engine 審核的強制要求。SDK 已在 `Authenticate.svelte` 中處理
`?replay=true` 偵測和 `requestReplay()` 呼叫，但 Replay UI 需在遊戲層實作。

### 待實作項目

- [ ] 建立 `BrandUIReplay.svelte`（若使用 BrandUI）或確認 `UIReplay.svelte` 可用
- [ ] Landing screen 顯示：Mode / Base Bet / Total Bet Cost / Payout Mult / Total Win
- [ ] SPIN 按鈕用 `eventMode="none"` 禁用但保留顯示
- [ ] MENU/TURBO 在 replay 中隱藏
- [ ] Play Again 按鈕（replay 結束後）
- [ ] Social mode 文字替換（replay UI 中的 "bet" → "play"）
- [ ] 準備各 mode 的 Event ID 供審查員測試

### 參考

- SDK 相關：`Authenticate.svelte`、`stateUrl.svelte.ts`、`stateUi.svelte.ts`
- 詳見：approval-guidelines §2 Game Replay Requirements
```
