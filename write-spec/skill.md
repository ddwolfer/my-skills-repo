---
name: write-spec
description: 互動式創建遊戲企劃書。透過一系列問答收集遊戲參數，生成符合標準格式的 SPEC.md。使用方式：/write-spec 06-dragon-fortune
---

# write-spec

互動式創建遊戲企劃書，透過問答收集參數並生成標準格式的 SPEC.md。

## 參數

- `$ARGUMENTS`: 企劃書資料夾名稱（例如：`06-dragon-fortune`）

## 執行流程

### Step 1: 建立目錄

創建 `specs/$ARGUMENTS/` 目錄。

```bash
mkdir -p "specs/$ARGUMENTS"
```

### Step 2: 基本資訊問答

使用 AskUserQuestion 工具依序詢問以下資訊：

#### 2.1 遊戲名稱
```
問題：遊戲的中文名稱是什麼？
範例：金玉滿堂、奧丁之治、霓虹連鎖
```

#### 2.2 英文名稱
```
問題：遊戲的英文名稱是什麼？
範例：Dragon Feast、Odin's Reign、Neon Chain
```

#### 2.3 遊戲 ID
```
問題：遊戲 ID 是什麼？（小寫英文、連字符）
預設：從英文名稱轉換（例如：Dragon Feast → dragon-feast）
```

#### 2.4 主題
```
問題：遊戲的主題是什麼？
選項：
- 亞洲傳統（農曆新年、財神、龍鳳）
- 古埃及（法老、金字塔、神話）
- 北歐神話（維京、奧丁、雷神）
- 賽博龐克（霓虹、未來、科技）
- 海洋探險（深海、寶藏、亞特蘭提斯）
- 其他（自訂）
```

### Step 3: 遊戲機制問答

#### 3.1 核心機制
```
問題：選擇核心計算機制
選項：
- Cluster（群集消除）→ evaluate_clusters_board()
- Lines（賠付線）→ evaluate_lines_board()
- Ways（全盤路）→ evaluate_ways_board()
- Scatter（散佈計算）→ evaluate_scatter_board()
```

**若選了 Scatter**，立即追問 Pay Anywhere 最低中獎數：
```
問題：Pay Anywhere 最低中獎數是多少個相同符號？
（注意：這跟「觸發免費旋轉的 Scatter 數量」是兩個獨立概念）
選項：
- 6 個
- 8 個（推薦）
- 10 個
- 自訂
預設：8
```

#### 3.2 版面大小
```
問題：版面大小是多少？
選項（根據機制建議）：
- Cluster: 7x7、6x6、8x8
- Lines: 5x3、5x4、5x5
- Ways: 5x3（243 ways）、6x4（4096 ways）
- Scatter: 6x5、5x4
```

#### 3.3 附加機制
```
問題：選擇附加機制（可多選）
選項：
- Tumble（連鎖消除）
- Expanding Wild（展開百搭）
- Sticky Wild（黏性百搭）
- Global Multiplier（全域乘數 — 每次 Tumble/Win 累加，適用所有贏分）
- Position Multiplier Grid（位置乘數格 — 特定格子帶固定或隨機乘數）
- Cascading Multiplier（連鎖乘數 — 每次連鎖消除後乘數遞增）
- Hold & Win / Hold & Spin
- 無附加機制
```

#### 3.4 乘數細節追問（若 3.3 選了任何乘數類型）

**此步驟必須詢問，否則數學模型和前端都會卡住。**

```
問題 A：乘數封頂值是多少？
選項：
- ×32
- ×64（推薦）
- ×128
- 無封頂（不建議 — 可能導致遊戲時長失控）
- 自訂
預設：×64

問題 B：乘數在 Base Game 和 Free Spins 中的行為？
選項：
- Base 每輪重置、FS 中持續累積（推薦，如 dragon-feast）
- Base 和 FS 都每輪重置
- Base 和 FS 都持續累積
- 自訂

問題 C：Wild 是否帶乘數？
選項：
- 否
- 是 — 僅 Free Spins 中（推薦）
- 是 — Base 和 FS 都有
若選「是」，追問：
  可能的乘數值有哪些？（例如：×2, ×3, ×5, ×10）
```

### Step 4: 數值設定問答

#### 4.1 RTP
```
問題：目標 RTP 是多少？
選項：
- 96.0%（標準）
- 95.0%（較低）
- 97.0%（較高）
- 自訂
```

#### 4.2 波動性
```
問題：波動性等級？
選項：
- 低（Low）
- 中（Medium）
- 中高（Medium-High）
- 高（High）
- 極高（Very High）
```

#### 4.3 最大獎金
```
問題：最大獎金倍數是多少？
選項：
- 5,000x
- 8,000x
- 10,000x
- 15,000x
- 自訂
```

#### 4.4 贏分等級門檻
```
問題：各贏分等級的倍數門檻是多少？（以 base bet 為單位）
預設建議（可自訂）：

| 等級 | 門檻 | 動畫 |
|------|------|------|
| Small Win | < 10x | 數字跳動 |
| Nice Win | 10x+ | 短慶祝 |
| Big Win | 15x+ | 大慶祝 |
| Super Win | 25x+ | 加強慶祝 |
| Mega Win | 50x+ | 全螢幕慶祝 |
| Epic Win | 100x+ | 全螢幕 + 粒子效果 |
| Max Win | {wincap}x | 最大獎專屬動畫 |

（直接按 Enter 使用預設值，或輸入自訂門檻）
```

#### 4.5 購買獎勵費用
```
問題：購買獎勵（Buy Bonus）費用是多少倍投注額？
選項：
- 50x
- 75x
- 80x
- 100x
- 無購買獎勵功能
```

### Step 5: 符號設定問答

#### 5.1 高付費符號數量
```
問題：高付費符號（H1-H4）數量？
選項：3、4、5
預設：4
```

#### 5.2 低付費符號數量
```
問題：低付費符號（L1-L5）數量？
選項：4、5、6
預設：5
```

#### 5.3 特殊符號
```
問題：需要哪些特殊符號？（可多選）
選項：
- Wild（百搭）
- Scatter（散佈/免費旋轉觸發）
- Bonus（獎勵遊戲觸發）
- Multiplier Wild（乘數百搭）— 細節已在 Step 3.4 收集
```

#### 5.4 符號描述（改善 AI 圖片生成品質）
```
問題：請簡單描述各符號的具體形象（可跳過，之後手動補）

高付費符號：
- H1: （例如：金龍、法老面具、雷神之鎚）
- H2: （例如：鳳凰、阿努比斯、奧丁之眼）
- H3: （例如：錦鯉、荷魯斯之眼、北歐符文）
- H4: （例如：金元寶、聖甲蟲、維京盾牌）

低付費符號：
- L1-L5: （例如：撲克牌 A/K/Q/J/10、寶石、花朵）

提示：這些描述會直接影響 /gen-symbols 的 ComfyUI prompt 品質
```

### Step 6: 免費旋轉設定

#### 6.1 觸發條件
```
問題：免費旋轉觸發需要幾個 Scatter？
選項（根據版面大小）：
- 7x7 Cluster: 4/5/6/7 個
- 5x3 Lines: 3/4/5 個
- 6x5 Scatter: 4/5/6 個
```

#### 6.2 免費旋轉次數（自動補全所有 scatter 數量）
```
問題：基礎免費旋轉次數？
輸入最小觸發數對應的旋轉次數，其餘自動推算。
範例：{4: 10, 5: 15, 6: 20, 7: 25}
```

**自動補全邏輯**：根據版面大小（cols × rows），自動覆蓋從最小觸發數到版面總格數的所有可能 scatter 數量。
例如 7×7 版面，使用者輸入 `{4: 10, 5: 15, 6: 20, 7: 25}`，自動補全 8+ 的值（遞增規則或 clamp 到最大值）。
這樣數學模型不會因為出現超出表格的 scatter 數量而 crash（KeyError）。

#### 6.3 重觸發規則（Re-trigger）
```
問題：免費旋轉中再次出現 Scatter 時，追加多少次？
預設：與初始觸發相同（例如 {3: 5, 4: 8, 5: 12}）
```

**自動補全邏輯**：同 6.2，覆蓋所有可能的 scatter 數量，避免邊界 crash。

#### 6.4 Session 時長限制（Stake Engine 審核要求）
```
問題：免費旋轉的硬上限是多少輪？
選項：
- 20 輪（低波動）
- 30 輪（標準，推薦）
- 50 輪（高波動）
- 自訂
預設：30
```

**背景**：Stake Engine 審查員會測試 Max Win Replay。如果免費旋轉沒有硬上限，
Max Win 可能需要數百輪才能達成 wincap（例如 790 輪 / 2+ 小時），會被退件。

以下項目會自動帶入企劃書：
- **max_free_spins**: 硬上限值
- **Scatter 壓制機制**: 達到上限後，新抽出的 Scatter 替換為一般符號，防止無限重觸發
- **Wincap 模擬 bypass**: 數學模擬中 wincap 事件不受硬上限限制（確保 10,000x 可達）

### Step 7: 美術風格問答

#### 7.1 主色調
```
問題：選擇主色調
選項（根據主題建議）：
- 亞洲傳統：紅金、玉綠金
- 古埃及：金藍、沙金
- 北歐神話：冰藍金、暗灰金
- 賽博龐克：霓虹紫粉、電子藍綠
- 海洋探險：深海藍、翡翠綠
```

#### 7.2 符號風格
```
問題：符號美術風格？
選項：
- 半寫實（Semi-realistic）
- 卡通風格（Cartoon）
- 像素風格（Pixel Art）
- 3D 渲染（3D Rendered）
```

### Step 8: Wincap 可達性驗算（自動）

在生成企劃書前，自動計算 theoretical_max 並與 wincap 比較：

```
# 單層乘數（無 Wild 乘數）
theoretical_max = max_fs_spins × avg_tumbles_per_spin × mult_cap × max_symbol_pay

# 雙層乘數（有 Wild 乘數）
theoretical_max = max_fs_spins × avg_tumbles_per_spin × mult_cap × max_symbol_pay × avg_wild_mult
```

**判斷邏輯**：
- `theoretical_max >= wincap × 1.5` → ✅ PASS，設計可行
- `theoretical_max >= wincap` → ⚠️ 勉強可達，建議加寬裕度
- `theoretical_max < wincap` → ❌ FAIL，**必須提示使用者**：
  「目前乘數設計（封頂 ×{mult_cap}）的理論天花板約 {theoretical_max}x，低於 wincap {wincap}x。
   建議方案：(1) 加入 Wild 乘數 (2) 提高乘數封頂 (3) 降低 wincap」

**注意**：avg_tumbles_per_spin 預設值根據版面和機制估算：
- 7×7 Cluster + Tumble: 3-5
- 6×5 Scatter + Tumble: 2-4
- 5×3 Lines: 1（無 tumble）

### Step 9: 生成企劃書

根據收集的資訊，讀取 `references/spec-template.md` 的模板結構，生成 `specs/$ARGUMENTS/SPEC.md`。
模板包含 20 個章節（遊戲概覽、美術、符號賠率、動畫、音效、核心玩法、流程圖、免費旋轉、數學模型、捲軸設計、投注模式、事件定義、響應式佈局、多語系、Game Tile、社群合規、Replay、免責聲明、RGS 通訊），需將問答收集的資訊填入對應章節。

**音效清單注意**：§6 音效除了標準清單外，根據遊戲機制自動加入特有音效提示：
- 有乘數系統 → `sfx_multiplier_up`, `sfx_multiplier_cap`, `sfx_multiplier_reset`
- 有 Tumble → `tumble_win_1~5`, `sfx_symbols_landing`
- 有 Scatter → `sfx_scatter_reveal`, `sfx_scatter_stop_1~N`

### Step 10: 輸出報告

```
企劃書已創建

檔案位置：specs/$ARGUMENTS/SPEC.md

遊戲資訊：
- 遊戲 ID: {game_id}
- 遊戲名稱: {中文名稱} ({英文名稱})
- 機制類型: {mechanism}
- 版面大小: {cols} x {rows}
- RTP: {rtp}%
- 最大獎金: {max_win}x

下一步：
1. 審核並調整企劃書內容
2. 補充符號的具體名稱和描述
3. 調整賠率表數值
4. 執行 /init-math specs/$ARGUMENTS 初始化數學模型
5. 執行 /init-game specs/$ARGUMENTS 初始化前端專案
6. 執行 /gen-symbols specs/$ARGUMENTS 生成符號圖片腳本
7. 執行 /gen-assets specs/$ARGUMENTS 生成其他素材腳本（背景/Logo/贏分彈窗/盤面邊框等）
```

## 參考資料

機制預設值、賠率表模板、注意事項等參考資料位於 `references/spec-template.md`。
生成 SPEC.md 時須讀取該檔案取得完整模板和數值。
