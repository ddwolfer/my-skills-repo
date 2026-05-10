---
name: audit-spines
description: 掃描遊戲專案的 Spine 動畫資源，解析動畫名稱與秒數，判斷 placeholder 狀態，產出 SPINE_ASSETS.md。當使用者提到 Spine 盤點、動畫素材狀態、placeholder 檢查、動畫秒數確認、想了解哪些 Spine 還沒做完、想看目前美術進度、或需要產出動畫規格清單給美術團隊時都應觸發。使用方式：/audit-spines games/dragon-feast
---

# audit-spines

掃描遊戲專案的 Spine 動畫資源目錄，解析每組動畫的名稱與秒數，判斷 placeholder 狀態，
產出結構化的 `SPINE_ASSETS.md` 作為美術製作的規格參考文件。

## 參數

- `$ARGUMENTS`: 遊戲專案路徑（例如：`games/dragon-feast`）

---

## 建議秒數參考表

符號 Spine 動畫的建議秒數。

> **重要**：`win` 和 `explosion` 秒數必須全符號統一。程式用 `Promise.all` 等所有中獎符號動畫播完才繼續（`Board.svelte` 的 `boardWithAnimateSymbols`），秒數不同會導致短的呆站等長的。各符號的差異化靠動畫內容（動態豐富度、特效層次）而非秒數。`land` 可以各自不同（各符號獨立落地）。

| 動畫 | 建議秒數 | 是否必須統一 | 說明 |
|------|----------|-------------|------|
| explosion | **0.80s** | 全符號統一 | Tumble 消除同步播放 |
| win | **1.00s** | 全符號統一 | 中獎同步播放（Promise.all） |
| land | 0.33–0.50s | 可各自不同 | H 系 0.50s、L 系 0.33s、S 0.67s |

Feature Spine：沿用 SDK 模板目前的秒數作為建議值（已在合理範圍內）。

---

## 執行流程

### Step 1: 解析參數

從 `$ARGUMENTS` 提取：

- `gamePath`: 遊戲專案路徑（例如 `games/dragon-feast`）
- `gameId`: 從路徑推導遊戲 ID（例如 `dragon-feast`）

驗證目錄存在：

```bash
ls {gamePath}/static/assets/spines/
```

如果目錄不存在，報告錯誤並停止。

---

### Step 2: 執行掃描腳本

執行 `audit_spines.js` 掃描 Spine 資源：

```bash
node .claude/scripts/audit_spines.js {gamePath}
```

- 將 stdout 捕獲為 JSON
- 如果腳本執行失敗（exit code !== 0），報告錯誤訊息並停止

JSON 輸出結構：

```json
{
  "gameId": "dragon-feast",
  "spineVersion": "4.2.xx",
  "symbols": [
    {
      "name": "H1",
      "path": "static/assets/spines/symbols/H1.skel",
      "format": "binary",
      "fileSize": 456,
      "isPlaceholder": true,
      "animations": [
        { "name": "explosion", "duration": 0.5 },
        { "name": "land", "duration": 0.3333 },
        { "name": "win", "duration": 0.5 }
      ]
    }
  ],
  "features": [
    {
      "name": "bigwin",
      "directory": "static/assets/spines/bigwin/",
      "format": "binary",
      "isPlaceholder": true,
      "skeletons": [...]
    }
  ],
  // 備註：format 可為 "binary"（包含 .skel 檔案）或 "json"（包含 .json 檔案）
  "summary": {
    "totalSymbols": 11,
    "totalFeatures": 4,
    "placeholderSymbols": 11,
    "placeholderFeatures": 4
  }
}
```

---

### Step 3: 補充程式碼資訊

使用 `Read` 工具從遊戲原始碼補充 JSON 未包含的資訊：

#### 3a. 讀取 assets.ts

讀取 `{gamePath}/src/game/assets.ts`，提取：

- 每組 Spine 資源的 `scale` 值
- 使用該 Spine 的 component 名稱

#### 3b. 讀取 winLevelMap.ts

讀取 `{gamePath}/src/game/winLevelMap.ts`，提取：

- 每個贏分等級的 `presentDuration`（Big Win / Mega Win / Epic Win 等）
- 此資訊用於 bigwin feature Spine 的建議秒數

---

### Step 4: 組裝 SPINE_ASSETS.md

使用 `Write` 工具生成 Markdown 檔案，包含以下章節：

#### Section 1: Header

```markdown
# {gameId} — Spine 動畫資源清單

> 最後更新：{today's date}
> 用途：逐項確認每組 Spine 動畫的製作狀態，作為美術製作的規格參考
> 產生方式：`/audit-spines {gamePath}`
```

#### Section 2: 總覽

概覽表格，一目了然掌握全局狀態：

```markdown
## 總覽

| 分類 | 數量 | 狀態 | 格式 |
|------|------|------|------|
| 符號 Spine | {N} 組 | {placeholder: M 組 / 已完成: K 組} | {binary/json} |
| Feature Spine | {N} 組 | {SDK 模板: M 組 / 已完成: K 組} | {binary/json} |
```

#### Section 3: 一、符號 Spine

符號 Spine 的完整盤點：

```markdown
## 一、符號 Spine

- 路徑：`static/assets/spines/symbols/`
- 共用貼圖：{是否使用共用 atlas/texture}
- 目前狀態：{placeholder / 部分完成 / 已完成}

### 動畫現況

| 符號 | explosion | land | win | 狀態 |
|------|-----------|------|-----|------|
| H1 | {current}s → {suggested}s | {current}s → {suggested}s | {current}s → {suggested}s | placeholder |
| H2 | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |

### 製作清單

#### 高價值符號（H 系列）

- [ ] H1 — explosion ({suggested}s) / land ({suggested}s) / win ({suggested}s)
- [ ] H2 — explosion ({suggested}s) / land ({suggested}s) / win ({suggested}s)
- [ ] ...

#### 低價值符號（L 系列）

- [ ] L1 — explosion ({suggested}s) / land ({suggested}s) / win ({suggested}s)
- [ ] L2 — ...

#### 特殊符號（W / S）

- [ ] W — explosion ({suggested}s) / land ({suggested}s) / win ({suggested}s)
- [ ] S — explosion ({suggested}s) / land ({suggested}s) / win ({suggested}s)
```

**建議秒數查表邏輯**：根據符號名稱前綴與編號，對照上方「建議秒數參考表」填入。

#### Section 4: 二、Feature Spine（SDK 官方模板）

每個 Feature 作為獨立小節：

```markdown
## 二、Feature Spine（SDK 官方模板）

### {featureName}（例如 bigwin）

- 路徑：`{directory}`
- 檔案：{skeleton files list}
- 使用元件：{component name from assets.ts}
- Scale：{scale value from assets.ts}

| 動畫名稱 | 目前秒數 | 建議秒數 | 用途 |
|----------|---------|---------|------|
| {animName} | {current}s | {suggested}s | {purpose} |
| ... | ... | ... | ... |

- [ ] 重製 {featureName} 動畫
  - [ ] {animName1}（{suggested}s）
  - [ ] {animName2}（{suggested}s）
```

**Feature 動畫用途推斷規則**：

| 動畫名稱模式 | 用途說明 |
|-------------|---------|
| idle | 待機循環 |
| show / intro | 出場動畫 |
| loop | 持續播放循環 |
| end / outro | 結束退場 |
| bigwin / megawin / epicwin | 對應贏分等級 |
| anticipation | 預告/期待效果 |
| freespin_start | Free Spin 開始 |
| freespin_end | Free Spin 結束 |

#### Section 5: 三、製作優先級建議

```markdown
## 三、製作優先級建議

| 優先級 | 項目 | 說明 |
|--------|------|------|
| P0（必須） | 符號 Spine — H1, H2, W, S | 高價值 + 特殊符號，影響核心視覺 |
| P1（重要） | 符號 Spine — H3, H4 | 中高價值符號 |
| P2（建議） | 符號 Spine — L1–L5 | 低價值符號，可簡化動畫 |
| P3（可選） | Feature Spine | SDK 模板已可運作，替換可提升質感 |
```

#### Section 6: 四、美術交付規格

```markdown
## 四、美術交付規格

| 項目 | 規格 |
|------|------|
| Spine 版本 | {spineVersion}（必須與專案一致） |
| 骨架格式 | Binary (.skel)（正式）/ JSON (.json)（開發測試） |
| 貼圖格式 | PNG，使用 Spine Texture Packer 匯出 |
| 貼圖尺寸 | 符號：建議單張 atlas ≤ 2048x2048；Feature：依需求 |
| 動畫命名 | 嚴格遵循上表的動畫名稱（explosion / land / win 等） |
| 匯出設定 | Premultiplied Alpha: ON |
```

---

### Step 5: 寫入檔案

使用 `Write` 工具將組裝完成的 Markdown 寫入：

```
{gamePath}/SPINE_ASSETS.md
```

---

### Step 6: 輸出報告

在終端顯示摘要報告：

```
=== Spine 動畫資源盤點完成 ===

遊戲：{gameId}
Spine 版本：{spineVersion}
符號 Spine：{N} 組（placeholder: {M} 組）
Feature Spine：{N} 組（SDK 模板: {M} 組）

檔案位置：{gamePath}/SPINE_ASSETS.md

下一步：
1. 檢視 SPINE_ASSETS.md 確認各項規格
2. 將文件交給美術團隊作為製作依據
3. 美術交付後重新執行 /audit-spines 更新狀態
```

---

### Step 7: 提議 Commit

提議 commit 並 push：

```bash
git add {gamePath}/SPINE_ASSETS.md
git commit -m "docs: 更新 Spine 動畫資源清單 — {gameId}"
```

如果使用者同意，執行 push。

---

## 注意事項

1. **掃描腳本需要 node_modules** — 遊戲專案必須已執行過 `pnpm install`，否則 `spine-core` 無法載入
2. **placeholder 判定邏輯** — 所有符號 `.skel` 檔案 ≤ 700 bytes 且動畫秒數完全相同 = placeholder
3. **Feature 預設為 SDK 模板** — `isPlaceholder: true` 表示尚未被遊戲專屬動畫替換
4. **建議秒數僅供參考** — 實際秒數應由動畫師依遊戲節奏微調
5. **重複執行安全** — 每次執行會完整覆寫 `SPINE_ASSETS.md`，可在任何階段重新盤點
