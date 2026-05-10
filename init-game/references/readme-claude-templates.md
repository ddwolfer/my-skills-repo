# README.md 和 CLAUDE.md 生成模板

本文件包含 Step 7 和 Step 7.5 的完整模板內容。

## Step 7: 生成 README.md

在 `games/{game_id}/` 根目錄生成 `README.md`，內容包含：

```markdown
# {gameName}

{遊戲簡述，一行描述}

## Game Info

| Item | Value |
|------|-------|
| Game ID | `{game_id}` |
| Template | {template} |
| Board Size | {numReels} x {numRows} |
| RTP | {rtp}% |
| Max Win | {max_win}x |
| Volatility | {volatility} |

## Symbols

列出所有符號的 ID、名稱、類型（High Pay / Low Pay / Wild / Scatter）

## Bet Modes

列出所有投注模式的 ID、費用、說明

## Features

列出遊戲的核心特色功能（Cluster/Lines/Ways、Tumble、Free Spins、特殊機制等）

## Project Structure

顯示專案目錄結構樹

## Development

包含安裝依賴、啟動 Storybook、開發伺服器、建置的指令

## Spec

指向企劃書路徑
```

## Step 7.5: 生成 game-level CLAUDE.md

在 `games/{game_id}/` 根目錄生成 `CLAUDE.md`，提供 Claude Code 進入遊戲目錄時的上下文：

```markdown
# {gameName} — Claude Code 工作規則

## 優先事項

開始工作前，先讀取 `WORK_ITEMS.md` 確認目前的上架工作進度。
優先完成 P0 項目，再處理 P1、P2。
每完成一個工作項目，立即更新 `WORK_ITEMS.md` 的狀態欄位。

## 專案結構

```
games/{game_id}/
├── src/
│   ├── components/    — Svelte + Pixi.js 元件
│   ├── game/          — 遊戲邏輯（狀態、常數、事件處理）
│   ├── stories/       — Storybook 測試故事
│   └── i18n/          — 多語系
├── static/assets/     — 靜態素材（sprites, spines, audio, fonts）
└── .storybook/        — Storybook 配置
```

## 技術棧

- SvelteKit + Pixi.js（pixi-svelte）
- Spine 動畫（@esotericsoftware/spine-pixi-v8）
- Storybook 9 + @storybook/addon-svelte-csf
- 工作區套件來自 `sdks/web-sdk/packages/`

## 開發驗證

使用 Storybook 驗證遊戲功能：
```bash
pnpm run storybook
```

## 關鍵檔案

| 檔案 | 用途 |
|------|------|
| `src/game/constants.ts` | 符號尺寸、Spine 比例、動畫速度 |
| `src/game/bookEventHandlerMap.ts` | 所有 bookEvent 的演出邏輯 |
| `src/components/Game.svelte` | 主遊戲元件 |
| `src/game/sound.ts` | 音效名稱定義 |
| `src/game/assets.ts` | 素材載入清單 |
```
