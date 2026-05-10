# SPEC.md 模板

生成 `specs/$ARGUMENTS/SPEC.md` 時使用此模板。將問答收集的資訊填入對應的 `{placeholder}`。

---

```markdown
# {中文名稱} {英文名稱} — 完整遊戲規格書

> **文件版本**：1.0
> **最後更新**：{today_date}
> **遊戲 ID**：`{game_id}`
> **平台**：Stake Engine
> **狀態**：規格定稿

---

## 目錄
[自動生成 20 個章節的目錄]

---

## 1. 遊戲概覽
[根據問答填入]

## 2. 美術風格與配色
[根據主題和色調生成]

## 3. 符號定義與賠率表
[根據機制類型生成賠率表結構]

## 4. 美術素材尺寸規格
[標準規格，必須包含以下素材類型：]
[符號素材：標準 200x200、靜態圖、旋轉模糊、贏分高亮]
[背景與 UI 素材：桌面版背景 1920x1080、直向背景 1080x1920、Logo 800x400、UI 按鈕 120x60、贏分彈窗背景 800x600、乘數格標記 100x100、盤面邊框 1024x1024（格子區域金色外框，中間透明）]
[Spine 動畫素材：符號動畫骨架、乘數格啟動、免費旋轉觸發、大獎慶祝]

## 5. 動畫規格
[6 種符號狀態 + 系統動畫]

## 6. 音效清單
[BGM + SFX 標準列表]

## 7. 核心玩法說明
[根據機制生成]

## 8. 遊玩流程圖
[Mermaid 流程圖]

## 9. 免費旋轉與特殊功能
[根據問答生成]

## 10. 後端數學模型規格
[game_config.py 結構]

### 10.x 模擬分佈條件（Distribution Conditions）

數學模型的模擬器需要以下分佈條件才能正確運行。**此章節必須填寫，否則 init-math 只能靠猜測。**

```python
distribution_conditions = {
    # 基礎遊戲條件
    "basegame": {
        "zero_win": {"target_ratio": 0.55},     # 零獎比例（約 50-60%）
        "small_win": {"max_multiplier": 10},      # 小獎上限（base bet 倍數）
    },
    # 免費遊戲條件
    "freegame": {
        "trigger_rate": {"target": 1/150},        # FS 觸發頻率（約 1/100 ~ 1/200）
        "avg_win": {"target_multiplier": 50},      # FS 平均獎金（base bet 倍數）
    },
    # Wincap 條件
    "wincap": {
        "max_win": {max_win}x,                    # 最大獎倍數
        "force_wincap_rate": {"target": 1/10000000},  # 強制封頂頻率
    },
    # 乘數分佈（若有乘數機制）
    "multiplier": {
        "mult_values": [{mult_values}],            # 可能的乘數值
        "mult_cap": {mult_cap},                    # 乘數封頂
        "wild_mult_values": [{wild_mult_values}],  # Wild 乘數值（若有）
    },
    # Scatter 觸發分佈（若為 Scatter 類型）
    "scatter_triggers": {
        "basegame": {{scatter_trigger_table}},     # {3: fs_count, 4: fs_count, ...}
        "freegame": {{scatter_retrigger_table}},   # re-trigger 表
    },
}
```

## 11. 捲軸設計指引
[符號分佈建議]

## 12. 投注模式
[base + bonus]

## 13. 事件定義
[事件 ID 和資料結構]

**重要**：每個後端事件必須明確對應前端 bookEvent 名稱，消除映射斷層。

| 後端事件 | 前端 bookEvent | 說明 |
|---------|---------------|------|
| spin_result | `reveal` | 開盤結果 |
| scatter_win / cluster_win | `winInfo` | 贏分資訊（符號、位置、金額） |
| tumble_start | `tumbleBoard` | 消除 + 掉落動畫 |
| tumble_win_update | `updateTumbleWin` | Tumble 累計贏分 |
| total_win_update | `setTotalWin` | 設定總贏分 |
| win_level | `setWin` | 大獎演出（Big/Mega/Epic/Max） |
| fs_trigger | `freeSpinTrigger` | 免費旋轉觸發 |
| fs_retrigger | `freeSpinRetrigger` | 免費旋轉重觸發 |
| fs_update | `updateFreeSpin` | FS 計數更新 |
| fs_end | `freeSpinEnd` | 免費旋轉結束 |
| grid_update | `updateGrid` | 乘數格更新 |
| global_mult_update | `updateGlobalMult` | 全域乘數更新 |
| win_cap | `wincap` | 最大獎封頂 |
| round_end | `finalWin` | 回合結束清理 |
| bonus_snapshot | `createBonusSnapshot` | 斷線恢復快照 |

## 14. 響應式佈局規格
[Desktop / Landscape / Portrait]

## 15. 多語系與在地化備註
[翻譯文字清單]

## 16. Game Tile 素材規格（送審必要）
[來源：approval-guidelines §7]

### 所需素材

| 素材 | 格式 | 命名規範 | 備註 |
|------|------|---------|------|
| 背景圖（BG） | 高解析度 PNG 或 JPG | `{GameTitle}-BG.png` 或 `.jpg` | 展示遊戲世界的環境背景 |
| 前景圖（FG） | 高解析度 PNG（透明背景） | `{GameTitle}-FG.png` | 代表遊戲的特色角色或關鍵物品 |
| 供應商 Logo | 高解析度 PNG（透明背景） | `{ProviderName}-Logo.png` | 必須在小尺寸下清晰可辨 |

### 重要限制

- **BG + FG 合計 ≤ 3MB**
- FG 和 Logo 必須是透明背景 PNG
- 視覺品質直接影響遊戲星級評定和玩家信任度

### 美術建議

- BG：建議以 {主題} 為背景，{色調} 色系，包含環境元素（如 {根據主題建議}）
- FG：建議使用遊戲中最具代表性的角色/物品，突出主題特色
- Logo：{providerName} 的官方 Logo

## 17. Stake.US 社群模式合規（Jurisdiction）
[來源：approval-guidelines §9]

### 概述

遊戲若通過審核，將自動考慮在 stake.us 上架。stake.us 受美國法規約束，**禁止使用賭博相關術語**。

### 技術實作

RGS 使用 URL query parameter `social=true/false` 指示社群模式。

```svelte
<script>
  import { stateUrlDerived } from 'state-shared';
  const isSocial = stateUrlDerived.social();
  const betWord = isSocial ? 'play' : 'bet';
  const buyBonusTitle = isSocial ? 'PLAY BONUS' : 'BUY BONUS';
</script>
```

### 禁用術語對照表（完整列表）

| 禁用詞彙 | 替換詞彙 |
|---------|---------|
| bet/bets | play/plays |
| total bet | total play |
| stake | play amount |
| wager | play |
| betting | playing |
| buy | play |
| buy bonus | get bonus / bonus |
| purchase | play |
| bought | instantly triggered |
| cash | coins |
| money | coins |
| pay/pays/paid | win/wins/won |
| pay out/paid out | win/won |
| payer | winner |
| gamble | play |
| credit | balance |
| currency | token |
| fund | balance |
| deposit | get coins |
| withdraw | redeem |
| at the cost of | for |
| cost of | can be played for |
| rebet | respin |

### 適用範圍

- 遊戲規則（GameRulesContent.svelte）
- 派彩表（PayTableContent.svelte）
- UI 文字（按鈕標籤、彈窗）
- 圖片中的文字（如有）

## 18. Replay（Bet Replay）規格
[來源：approval-guidelines §2]

### 概述

Bet Replay 是**所有新遊戲送審的強制要求**。玩家可在回合結束後查看並分享結果。

### Query Parameters

| 參數 | 必填 | 說明 |
|------|------|------|
| `replay` | 是 | `true` 表示回放模式 |
| `game` | 是 | 遊戲 ID |
| `version` | 是 | 數學版本 |
| `mode` | 是 | 下注模式 |
| `event` | 是 | 唯一模擬 ID（= LUT bookIndex）|
| `rgs_url` | 是 | RGS 伺服器 URL |
| `currency` | 否 | 幣種 |
| `amount` | 否 | 下注金額 |
| `social` | 否 | 社群模式 |

### RGS 端點

```
GET {rgs_url}/bet/replay/{game}/{version}/{mode}/{event}
```

### UX 要求

| 階段 | 行為 |
|------|------|
| 載入 | 自動載入事件資料，顯示 Play 按鈕 |
| 回放中 | 播放完整動畫/音效，停用下注控制 |
| 回放後 | 顯示 Play Again 按鈕，保持結果可見 |

### UI 精簡

| 隱藏 | 保留 |
|------|------|
| 餘額顯示 | 獲勝金額 |
| 下注按鈕 | 回放控制 |
| 下注選擇器 | 回放下注金額 |
| 自動遊玩 | 幣種顯示 |

### 送審時需提供的 Event IDs

審查員會要求各 bet mode 的 Event ID（= LUT bookIndex），涵蓋：
- 一般獲勝、大獎、最大獎、未獲獎、獎勵回合

## 19. 免責聲明（General Disclaimer）
[來源：approval-guidelines §8]

遊戲規則/資訊頁面**必須**包含以下免責聲明：

> Malfunction voids all pays and plays. A consistent internet connection is required. In the event of a disconnection, reload the game to finish any uncompleted rounds. The expected return is calculated over many plays. Animations are not representative of any physical device, and are for illustrative purposes only. Winnings are settled according to the amount received from the Remote Game Server and not from events within the web browser.
>
> TM and &copy; {year} Stake Engine.

**注意**：社群模式下 "pays" → "wins"，"plays" → "rounds"

## 20. RGS 通訊注意事項
[來源：approval-guidelines §4、§5]

### XSS 政策

遊戲建置**只能包含靜態檔案**，不可存取外部資源。常見問題：
- 從外部 CDN 下載字型（typekit、jsdelivr）→ 會被 CSP 擋住
- 所有圖片和字型必須從 Stake Engine CDN 載入

### RGS URL

必須使用 `rgs_url` query parameter，**不可硬編碼**。

### 幣種與語言

- 英語為唯一必要語言
- 傳入不支援的語言時文字不得損壞
- 所有 RGS 支援的幣種都需正確顯示符號和小數位

---

> **文件結束**
```

---

## 各機制類型的預設值

### Cluster 類型
- 版面：7x7
- 最小群集：5 個
- 賠率區間：5+, 8+, 12+, 15+, 20+
- 附加機制：Tumble, Multiplier Grid

### Lines 類型
- 版面：5x3 或 5x5
- 賠付線：20 或 25 條
- 賠率區間：3, 4, 5 連線
- 附加機制：Expanding Wild

### Ways 類型
- 版面：5x3（243 ways）或 6x4（4096 ways）
- 賠率區間：3, 4, 5, 6 連線
- 附加機制：Cascading Multiplier

### Scatter 類型
- 版面：6x5
- 最小配對：8 個（由問卷 Step 3.1 決定）
- 賠率區間：根據版面大小自動生成（從 min_scatter_count 到 cols×rows 的合理範圍）
  - 6x5 預設：8+, 10+, 12+, 15+, 20+, 25+, 30
  - 5x4 預設：6+, 8+, 10+, 12+, 15+, 20
- 附加機制：Tumble

## 賠率表生成規則

### Cluster 賠率表模板
```
| 符號 | 5+ 個 | 8+ 個 | 12+ 個 | 15+ 個 | 20+ 個 |
|------|-------|-------|--------|--------|--------|
| H1   | 2x    | 5x    | 15x    | 50x    | 200x   |
| H2   | 1.5x  | 4x    | 12x    | 40x    | 150x   |
| H3   | 1x    | 3x    | 10x    | 30x    | 100x   |
| H4   | 0.8x  | 2.5x  | 8x     | 25x    | 80x    |
| L1   | 0.5x  | 1.5x  | 5x     | 15x    | 50x    |
| L2   | 0.4x  | 1.2x  | 4x     | 12x    | 40x    |
| L3   | 0.3x  | 1x    | 3x     | 10x    | 30x    |
| L4   | 0.25x | 0.8x  | 2.5x   | 8x     | 25x    |
| L5   | 0.2x  | 0.6x  | 2x     | 6x     | 20x    |
```

### Lines/Ways 賠率表模板
```
| 符號 | 3 連線 | 4 連線 | 5 連線 |
|------|--------|--------|--------|
| H1   | 3x     | 10x    | 25x    |
| H2   | 2x     | 8x     | 20x    |
| H3   | 1.5x   | 6x     | 15x    |
| H4   | 1x     | 5x     | 10x    |
| L1   | 0.5x   | 2x     | 5x     |
| L2   | 0.4x   | 1.5x   | 4x     |
| L3   | 0.3x   | 1x     | 3x     |
| L4   | 0.2x   | 0.8x   | 2x     |
| L5   | 0.1x   | 0.5x   | 1.5x   |
```

## 注意事項

1. 所有數值都是建議值，可根據數學模型調整
2. 符號名稱需要在生成後手動填入具體內容
3. 賠率表需要經過數學驗證確保 RTP 正確
4. 美術風格描述可根據實際需求調整
