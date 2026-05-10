---
name: init-math
description: 從遊戲企劃書初始化數學模型專案。讀取 SPEC.md，複製 _template-math 到 models/ 目錄，根據企劃書生成 game_config.py 和捲軸檔案，初始化獨立 git repo 並添加為 submodule。使用方式：/init-math specs/01-dragon-feast。⚠️ 僅適用 slot 類遊戲 — 非 slot（dice / table game / progression）請改讀 specs/_shared/NON_SLOT_M_AUDIT_SOP.md Ch 4 手動流程。
---

# init-math

從遊戲企劃書初始化數學模型專案，建立獨立的 git repo 並作為 submodule 管理。

## ⚠️ 非 Slot 遊戲請讀這裡（2026-04-14 新增）

**本 skill 僅適用 slot 類遊戲**（cluster / lines / ways / scatter）。如果 SPEC.md 的「SDK 計算類型」是以下任何一種，**不要用本 skill**：

- `win_type = "other"` — 非 reel-based 遊戲
- Table game（Dice Royale 這類骰子 / 牌桌）
- Progression game（Forge of Fortune 這類裝備強化）
- Binary / multi-level 機率判定遊戲

**判斷 flowchart：**
- 有 reels（轉軸）？→ slot（用本 skill）
- 有 paytable(kind, symbol) → payout map？→ slot
- 有 Free Spin trigger 機制？→ slot
- 純機率判定 / progression / table game？→ **non-slot，改讀下方文件**

**非 slot 遊戲請改讀：**

👉 `specs/_shared/NON_SLOT_M_AUDIT_SOP.md`

- **Ch 3** M-audit 9 項適用性判定（M6/M7/M8 天然違反 + Near Miss 解方）
- **Ch 4** 手動 init-math 替代流程（從 `sdks/math-sdk/games/fifty_fifty/` 複製，不是 `_template-math`）
- **Ch 5** Dice Royale case study（25 betMode binary + Near Miss + Push）
- **Ch 6** Forge of Fortune case study（6 betMode progression + Unbreakable）
- **Ch 9** M-audit FAIL 決策樹

**為什麼不能用本 skill 跑非 slot：** 本 skill 假設複製 `_template-math`（含 reels / symbols / paytable / freespin_triggers），但非 slot 遊戲這些欄位全部不需要。錯誤套用會導致 SDK 找不到 reels CSV 而 crash。

---

## 參數

- `$ARGUMENTS`: 企劃書路徑（例如：`specs/01-dragon-feast`）

## 目錄結構

```
StakeProject/                    # 主 repo
├── sdks/
│   ├── math-sdk/                # 官方 SDK（不修改）
│   └── web-sdk/                 # 前端 SDK
├── _template-math/              # 模板（保留）
├── models/                      # 數學模型目錄
│   ├── dragon-feast/          # submodule
│   ├── odins-reign/             # submodule
│   └── ...
├── games/                       # 前端遊戲
└── specs/                       # 企劃書
```

## 參考檔案

在執行 Step 5（game_config.py）和 Step 6（捲軸生成）時，請按需讀取以下參考檔案：

| 參考檔案 | 內容 | 何時讀取 |
|---------|------|---------|
| `references/game-config-examples.md` | Cluster/Lines 類型的完整 game_config.py 範例 | Step 5 生成 game_config.py 時 |
| `references/templates-and-distributions.md` | 賠率表格式、分佈條件、捲軸生成範例 | Step 5 設定賠率表/分佈條件、Step 6 生成捲軸時 |

---

## 執行流程

### Step 1: 讀取企劃書

讀取 `$ARGUMENTS/SPEC.md` 並提取關鍵資訊：

1. **遊戲 ID**（game_id）：從「遊戲 ID」欄位取得（例如：`dragon-feast`）
2. **英文名稱**（working_name）：從「英文名稱」欄位取得
3. **SDK 計算類型**：從「SDK 計算類型」欄位決定 win_type
4. **版面大小**：從「版面大小」欄位取得 num_reels x num_rows
5. **符號列表與賠率表**：從「符號定義與賠率表」章節取得
6. **RTP**：從「目標 RTP」欄位取得
7. **最大獎金**：從「最大獎金」欄位取得（wincap）
8. **免費旋轉觸發**：從「免費旋轉觸發」章節取得
9. **投注模式**：從「投注模式」章節取得（base 和 bonus 費用）

### Step 2: 選擇 win_type

根據 SDK 計算類型選擇對應的 win_type：

| SDK 計算類型 | win_type |
|-------------|----------|
| `evaluate_clusters_board()` | cluster |
| `evaluate_lines_board()` | lines |
| `evaluate_ways_board()` | ways |
| `evaluate_scatter_board()` | scatter |

### Step 3: 建立遊戲目錄

1. 確保 `models/` 目錄存在
2. 檢查 `models/{game_id}` 是否已存在，如果存在請詢問使用者是否覆蓋

```bash
mkdir -p models
```

### Step 4: 複製模板

複製 `_template-math` 到 `models/{game_id}`，排除不需要的目錄。

```bash
cp -r _template-math models/{game_id}
rm -rf models/{game_id}/__pycache__
rm -rf models/{game_id}/library
rm -rf models/{game_id}/games
rm -rf models/{game_id}/.git
```

#### 4.1 重建 library/ 子目錄結構

複製時排除了 `library/`（避免帶入舊的模擬結果），但 run.py 需要這些子目錄：

```bash
mkdir -p models/{game_id}/library/{books,configs,forces,lookup_tables,optimization_files,publish_files}
```

#### 4.2 修正相對路徑（SDK + 前端）

模板設計給根目錄（`_template-math/`），但遊戲在 `models/{game_id}/`（兩層深）。
所有相對路徑的 `".."` 都需要改成 `"..", ".."`，否則指向 `models/` 而非專案根目錄。

需要修正的 3 個路徑變數：

**run.py — MATH_SDK_PATH**：
```python
# 修改前（模板預設，指向 models/sdks/math-sdk — 不存在）
MATH_SDK_PATH = os.path.abspath(os.path.join(GAME_DIR, "..", "sdks", "math-sdk"))

# 修改後（指向 StakeProject/sdks/math-sdk）
MATH_SDK_PATH = os.path.abspath(os.path.join(GAME_DIR, "..", "..", "sdks", "math-sdk"))
```

**validate_sync.py — MATH_SDK_PATH**（同上修法）

**validate_sync.py — FRONTEND_CONFIG_PATH**：
```python
# 修改前（模板預設）
FRONTEND_CONFIG_PATH = os.path.join(GAME_DIR, "..", "stake-slot-template", "src", "game", "config.ts")

# 修改後
FRONTEND_CONFIG_PATH = os.path.join(GAME_DIR, "..", "..", "games", "{game_id}", "src", "game", "config.ts")
```

#### 4.3 更新 SYNC_GUIDE.md 引用

將 `SYNC_GUIDE.md` 中的模板名稱替換為實際路徑：
- `_template-math` -> `models/{game_id}`
- `stake-slot-template` -> `games/{game_id}`

### Step 5: 修改 game_config.py

根據企劃書內容修改 `models/{game_id}/game_config.py`。

> **完成 Step 5 後，務必繼續執行 Step 5.5**（複製遊戲類型專屬程式碼）。
> 跳過 Step 5.5 會導致遊戲類型不符的無限循環 bug。

使用 Edit 工具修改以下配置項：

**基本資訊**：
```python
self.working_name = "{英文名稱}"
self.wincap = {最大獎金倍數}
self.win_type = "{win_type}"  # "lines" | "cluster" | "scatter" | "ways"
self.rtp = {RTP 數值，例如 0.96}
```

**遊戲版面**：
```python
self.num_reels = {軸數}
self.num_rows = [{每軸行數}]  # 例如 [7] * 7 或 [3, 3, 3, 3, 3]
```

**賠率表**：根據 win_type 使用不同格式。

> 賠率表格式模板、特殊符號、免費旋轉觸發、投注模式、分佈條件的詳細設定，
> 請參閱 `references/templates-and-distributions.md`。

要點提醒：
- **RGS Payout 約束**：所有賠率值必須是 **0.1 的整數倍**（如 0.2, 0.5, 1.5）。不合法值如 `0.25` 會導致格式驗證失敗。
- **Cluster 類型**需要將賠率區間展開為連續數值（5+, 8+, 12+ 等），用 `for n in range()` 簡化
- **Wincap Distribution**：Base 和 Bonus 模式都必須包含。quota 建議 **0.1%（0.001）**，搭配 WCAP 專用輪帶。過高的 quota（如 5%）會使 wincap 事件數量過多（1e5 × 5% = 5,000 個），每個都需大量重試，導致模擬耗時不切實際。詳見 `/optimize-rtp` Step 5c wincap fallback
- **mult_values 加權均值**建議 >= 5x

**Session 時長限制**（Stake Engine 審核要求）：

```python
# 免費旋轉硬上限（從 SPEC.md 讀取，預設 30）
self.max_free_spins = 30
```

此值用於：
- `gamestate.py`：retrigger 後 `tot_fs = min(tot_fs, max_free_spins)`
- `game_override.py`：達到上限時 scatter 壓制（替換為一般符號）
- wincap 模擬 bypass：`force_wincap=True` 時跳過上述兩項限制

乘數封頂（如有位置乘數網格）：
```python
# 乘數等級表（從 SPEC.md 讀取，預設 ×2 倍增至 ×64）
self.mult_levels = [0, 2, 4, 8, 16, 32, 64]
```

> 完整的 Cluster/Lines 範例請參閱 `references/game-config-examples.md`。

### Step 5.5: 複製遊戲類型專屬程式碼

**這一步至關重要** -- 模板預設的 5 個遊戲邏輯檔案是 Lines 類型。
如果遊戲不是 Lines 類型，必須用 SDK 範例覆蓋，否則會導致無限循環。

#### 5.5a 閱讀對應的類型指南

根據 win_type 選擇對應的指南文件（位於本 skill 同目錄下）：

| win_type | 閱讀指南 | SDK 範例來源 |
|----------|---------|-------------|
| cluster | `guide-cluster.md` | `sdks/math-sdk/games/0_0_cluster/` |
| lines | `guide-lines.md` | `sdks/math-sdk/games/0_0_lines/` |
| ways | `guide-ways.md` | `sdks/math-sdk/games/0_0_ways/` |
| scatter | `guide-scatter.md` | `sdks/math-sdk/games/0_0_scatter/` |

**務必先閱讀指南**，了解該類型的注意事項和常見 bug。

#### 5.5b 從 SDK 範例複製 5 個遊戲邏輯檔案

```bash
SDK_DIR=sdks/math-sdk/games/0_0_{win_type}
TARGET=models/{game_id}
for f in gamestate.py game_executables.py game_calculations.py game_override.py game_events.py; do
    cp "$SDK_DIR/$f" "$TARGET/$f"
done
```

**注意**：
- `game_config.py` **不要**從 SDK 複製（Step 5 已根據企劃書生成）
- `run.py`、`validate_sync.py`、`game_optimization.py` 保留模板版本
- `optimize_lut.py` 不在模板中 -- 由 `/optimize-rtp` skill 在首次 RTP 優化時自動生成
- 如果 SDK 範例中某個檔案不存在（如 0_0_lines 沒有 game_events.py），保留模板版本

#### 5.5c 按照類型指南調整複製的檔案

根據指南中的「複製後調整」章節：
- 確認特殊符號名稱與 game_config.py 一致
- Cluster/Scatter 類型：確認 `MAX_TUMBLES` 安全限制存在
- 補充中文行內註釋（SDK 版本為英文）

#### 5.5d Session 時長保護（必做）

如果 `game_config.py` 定義了 `max_free_spins`，必須在以下檔案加入保護邏輯：

**gamestate.py** — retrigger 後限制總免費旋轉數：
```python
if self.check_fs_condition():
    self.update_fs_retrigger_amt()
    # 防禦性硬上限（wincap 模擬時不限制）
    is_wincap_sim = self.get_current_distribution_conditions().get("force_wincap", False)
    if not is_wincap_sim:
        self.tot_fs = min(self.tot_fs, self.config.max_free_spins)
```

**game_override.py** — 達到上限時壓制 Scatter：
```python
def draw_board(self, emit_event=True, trigger_symbol="scatter"):
    is_wincap_sim = self.get_current_distribution_conditions().get("force_wincap", False)
    if (self.gametype == self.config.freegame_type
            and self.tot_fs >= self.config.max_free_spins
            and not is_wincap_sim):
        super().draw_board(emit_event=False, trigger_symbol=trigger_symbol)
        self._suppress_scatters()  # 將 S 替換為隨機一般符號
        if emit_event:
            reveal_event(self)
    else:
        super().draw_board(emit_event=emit_event, trigger_symbol=trigger_symbol)
```

**背景**：沒有這些保護，Max Win Replay 可能跑數百輪（曾發生 790 輪 / 2+ 小時），
會被 Stake Engine 審查員退件。`force_wincap` bypass 確保 wincap 模擬不受限制。

#### 5.5d 混合機制處理

如果遊戲有額外機制（如 Cluster + Hold & Win）：
1. 先複製最接近的基礎類型（如 cluster）
2. 在複製的檔案中手動加入額外機制的程式碼
3. 參考 `sdks/math-sdk/games/` 下的其他範例（如 `0_0_expwilds`）

---

### Step 6: 生成捲軸檔案

**生成前必須先閱讀 `guide-reel-design.md`** 中該遊戲類型的輪帶限制。
不遵守限制會導致 Tumble 類遊戲無限消除循環。

根據版面大小和符號列表生成初始捲軸 `reels/BR0.csv` 和 `reels/FR0.csv`。

> **⚠️ FR0 獨立性警告**：初始化時 FR0 是 BR0 的副本，但有 Free Spin 的遊戲**必須在 `/optimize-rtp` 前獨立調整 FR0**。
> 否則 bonus mode 的贏率無法獨立控制，會導致 `/optimize-rtp` 的 B5 檢查 FAIL。
> 調整方向：降低 H1/H2 高賠符號密度 30-50%，補充 L3/L4 低賠符號。

**Lines/Ways 類型（5x3）**：每行 5 符號，約 220 行。
**Scatter 類型（6x5）**：每行 6 符號，約 120-140 行。
**Cluster 類型（7x7）**：每行 7 符號，約 100-150 行。

CSV 格式，每行用逗號分隔：
```csv
L1,H3,L5,L4,L3,L2,H1
H1,H3,H4,L2,L5,L3,L4
```

> 各類型的符號分佈原則和完整範例請參閱 `references/templates-and-distributions.md` 的「捲軸檔案生成」章節。

**FR0.csv 頂部加入提醒註釋**（生成時自動寫入）：
```csv
# WARNING: 這是 BR0 的副本。有 Free Spin 的遊戲必須獨立調整 FR0（降低 H1/H2 密度，補充 L3/L4）。
# /optimize-rtp B5 檢查會比對 FR0 vs BR0，完全相同會 FAIL。
L1,H3,L5,L4,L3,L2,H1
...
```

**game_optimization.py fence targets 提醒**：模板中的 `game_optimization.py` 預設 fence targets 是佔位值。在 `/optimize-rtp` 前，確認：
- FR0 已獨立調整（不再是 BR0 副本）
- Fence targets 的 RTP 加總 ≈ target RTP

### Step 7: 初始化 Git Repo

在遊戲目錄中初始化獨立的 git repo：

```bash
cd models/{game_id}
git init
git add .
git commit -m "Initial commit: {game_id} math model"
```

### Step 8: 詢問 Remote URL

詢問使用者是否要設定 remote repository URL：

- 如果使用者提供 URL（例如：`git@github.com:user/{game_id}-math.git`）：
  ```bash
  cd models/{game_id}
  git remote add origin {remote_url}
  ```

- 如果使用者選擇稍後設定，跳過此步驟。

### Step 9: 添加為 Submodule

回到主 repo，將遊戲目錄添加為 submodule：

```bash
cd {project_root}
git submodule add ./models/{game_id} models/{game_id}
git add .gitmodules models/{game_id}
git commit -m "Add {game_id} math model as submodule"
```

### Step 10: 輸出報告

完成後顯示以下資訊：

```
數學模型專案已創建

遊戲資訊：
- 遊戲 ID: {game_id}
- 遊戲名稱: {working_name}
- 計算類型: {win_type}
- 版面大小: {num_reels} x {num_rows}
- RTP: {rtp}%
- 最大獎金: {wincap}x
- 購買獎勵費用: {bonus_cost}x

專案位置：models/{game_id}
Git Repo: 已初始化（獨立 repo）
Git Clone: 獨立 repo（不受主 repo 版控）

下一步：
1. 設定 remote（如果尚未設定）：
   cd models/{game_id}
   git remote add origin git@github.com:your-org/{game_id}-math.git
   git push -u origin main

2. 使用 /optimize-rtp 自動優化 RTP（會自動生成 optimize_lut.py）：
   /optimize-rtp models/{game_id}

3. 前端專案同步（如果已執行 /init-game）：
   python validate_sync.py   # 驗證前後端配置一致

4. 優化順序：模擬 -> LUT優化 -> 分析（不可顛倒，詳見下方說明）
```

---

## 重要：模擬後的優化順序

完成 init-math 後，執行 RTP 優化時必須遵循以下順序：

```
1. 輪帶驗證 (validate reels)
2. 模擬 (run_sims)
3. LUT 生成 (自動)
4. LUT 權重優化 (optimize_lut.py)     <- 必須在分析之前！
5. 統計分析 (run_analysis)
6. 格式驗證 (run_format_checks)
```

**第 5 步（統計分析）絕對不能在第 4 步（LUT 優化）之前執行。**
分析模組從 `publish_files/` 讀取 LUT。如果在優化前就執行分析，
`run.py` 的 analysis 步驟可能會將原始 LUT 複製到 `publish_files/`，
覆蓋掉優化後的 LUT。

> 建議使用 `/optimize-rtp` skill 自動化此流程，避免順序錯誤。

---

## 與 init-game 的整合

完整工作流程：

```
/write-spec 06-dragon-fortune
        |
/init-game specs/06-dragon-fortune    # 前端專案
        |
/init-math specs/06-dragon-fortune    # 數學模型
        |
   前後端同步驗證（validate_sync.py）
        |
   開發完成
```

---

## 驗證方式

1. 執行 `/init-math specs/01-dragon-feast`
2. 確認 `models/dragon-feast/` 已創建
3. 執行模擬測試：
   ```bash
   cd models/dragon-feast
   python run.py
   ```
4. 檢查輸出檔案是否正確生成
5. 使用 `validate_sync.py` 驗證前後端同步

---

## 注意事項

1. **Cluster 類型**需要將賠率區間展開為連續數值（5+, 8+, 12+ 等）
2. **捲軸檔案**需要後續用 RTP 優化工具調整符號分佈
3. **前後端配置**需要用 `validate_sync.py` 驗證同步
4. **Wild 符號位置限制**需要在捲軸生成時考慮（如僅出現在第 2-6 軸）
5. **game_id** 會自動從資料夾名稱取得，不需要在 game_config.py 中手動設定

## 連動修改提醒

<!-- 以下由 /project-insights 第一輪分析萃取 (2026-02-21) -->

- **`guide-cluster.md` <-> `game_config.py`**：這兩個檔案在歷史 session 中有 3 次共同修改。修改 cluster 指南時，確認 game_config.py 的範例是否需要同步更新，反之亦然。
- **`SKILL.md` <-> `guide-*.md`**：修改 init-math 主流程時，檢查對應的類型指南是否需要更新。
