---
name: lesson
description: 回顧當前對話，萃取經驗教訓並寫入對應層級的 CLAUDE.md。在完成複雜任務、修復棘手 bug、發現架構模式、或對話中反覆犯錯後應主動使用。使用方式：/lesson 或 /lesson games/dragon-feast
---

# lesson

回顧當前對話中的錯誤嘗試、偵錯過程和解決方案，萃取可複用的經驗教訓，寫入對應層級的 CLAUDE.md。

## 參數

- `$ARGUMENTS`: 可選的目標專案路徑（例如：`games/dragon-feast`）
  - 如未指定，自動判斷當前對話涉及的主要目錄

## 執行流程

### Step 1: 回顧對話

掃描當前對話，識別以下模式：

**錯誤嘗試（Missteps）：**
- 嘗試了錯誤的方法後才找到正確解法
- 修改了錯誤的檔案
- 誤解了架構或資料流
- 遺漏了必要的連動修改

**偵錯洞察（Debug Insights）：**
- 問題的根本原因（root cause）
- 有效的偵錯路徑
- 誤導性的錯誤訊息

**架構發現（Architecture Discoveries）：**
- 元件之間的隱含依賴
- 未記錄的約定或慣例
- 常踩到的邊界條件

### Step 2: 萃取教訓

將識別出的模式轉化為具體、可執行的規則。

**好的教訓：**
```
- Spine 動畫的 assetKey 必須與 assets.ts 的 key 完全一致，大小寫敏感
- tumbleBoard 的 adding 陣列在 combined 中排列在 base 前面（上方）
```

**不好的教訓（太模糊）：**
```
- 要小心素材檔案
- 注意動畫順序
```

### Step 3: 判斷寫入層級

根據教訓的適用範圍，決定寫入哪一層的 CLAUDE.md：

| 範圍 | 寫入位置 | 範例 |
|------|---------|------|
| 跨專案通用 | 主 repo `CLAUDE.md` | commit 規範、submodule 操作注意事項 |
| 遊戲專案通用 | `games/{id}/CLAUDE.md` | Storybook 驗證流程、SDK 使用規則 |
| 遊戲邏輯相關 | `games/{id}/src/game/CLAUDE.md` | bookEvent 處理規則、state 管理注意事項 |
| 元件相關 | `games/{id}/src/components/CLAUDE.md` | Pixi/Spine 元件開發規則 |
| 測試相關 | `games/{id}/src/stories/CLAUDE.md` | Story 資料格式、常見測試問題 |
| 數學模型相關 | `models/{id}/CLAUDE.md` | 輪帶設計、RTP 優化注意事項 |

### Step 4: 寫入 CLAUDE.md

**寫入規則：**

1. **讀取目標 CLAUDE.md** — 先讀取完整內容
2. **檢查是否重複** — 如果已有類似規則，更新而非重複添加
3. **追加到「常見陷阱」區段** — 如果有此區段，追加到其中；如果沒有，在檔案末尾新增此區段
4. **保持簡潔** — 每條規則 1-2 行，避免過度描述
5. **標注來源** — 用 HTML 註解標記更新時間

**追加格式：**
```markdown
## 常見陷阱

<!-- 以下由 /lesson 自動萃取 -->
- **[分類]** 具體規則描述
```

### Step 5: 也寫入自動記憶

如果教訓具有跨 session 價值，同時更新 Claude 的自動記憶目錄：

路徑：當前專案的 memory 目錄（通常位於 `~/.claude/projects/` 下對應專案路徑的 `memory/` 子目錄）

- 如果 `MEMORY.md` 中還沒有相關項目，加入簡要提示
- 如果是詳細的技術模式，建立專門的 topic file（例如 `spine-debugging.md`）

### Step 6: 輸出摘要

```
============================================================
/lesson 萃取報告
============================================================

本次對話萃取了 {N} 條教訓：

1. [game/CLAUDE.md] 新增：Spine assetKey 大小寫敏感規則
2. [components/CLAUDE.md] 更新：Board vs TumbleBoard 切換時機
3. [stories/CLAUDE.md] 新增：bonus book 測試需要 createBonusSnapshot

已更新檔案：
- games/dragon-feast/src/game/CLAUDE.md
- games/dragon-feast/src/components/CLAUDE.md

記憶更新：
- memory/MEMORY.md — 新增 Spine 偵錯提示
============================================================
```

## 注意事項

1. **只記錄已驗證的教訓** — 不記錄猜測或未確認的結論
2. **避免記錄一次性的操作細節** — 只記錄可複用的模式
3. **不刪除現有規則** — 只追加或更新，除非明確發現現有規則有誤
4. **保持 CLAUDE.md 精簡** — 每個檔案的「常見陷阱」區段建議不超過 15 條
