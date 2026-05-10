---
name: optimize-rtp
description: 自動化 RTP 優化流程。驗證輪帶分佈、執行模擬、LUT 權重優化、迭代至目標 RTP。當使用者提到 RTP 調整、模擬測試、輪帶優化、LUT 權重、數學模型驗證、回報率、命中率分析、獎金分佈檢查、或需要確認遊戲數值是否合規時都應使用。使用方式：/optimize-rtp models/dragon-feast 或 /optimize-rtp models/dragon-feast 96
---

# optimize-rtp

自動化老虎機數學模型的 RTP（Return To Player）優化流程。
讀取遊戲配置、驗證輪帶安全性、執行模擬、LUT 權重優化，迭代直到達成目標 RTP。

## 參數

- `$ARGUMENTS`: 遊戲目錄路徑 + 可選的目標 RTP
  - 例如：`models/dragon-feast`（使用 game_config.py 中的 rtp）
  - 例如：`models/dragon-feast 96`（指定 96%）

---

## 執行流程

### Step 1: 解析參數 + 讀取遊戲配置

從 `$ARGUMENTS` 提取：
- `GAME_DIR`: 遊戲目錄路徑（例如 `models/dragon-feast`）
- `TARGET_RTP`: 目標 RTP（如未指定，從 `game_config.py` 的 `self.rtp` 讀取）

讀取以下檔案：

| 檔案 | 提取內容 |
|------|---------|
| `{GAME_DIR}/game_config.py` | win_type, num_reels, num_rows, wincap, rtp, paytable, special_symbols, freespin_triggers, bet_modes（含 cost）, distributions, max_free_spins, mult_levels |
| `{GAME_DIR}/game_optimization.py` | opt_params（fence targets） |
| `{GAME_DIR}/reels/BR0.csv`, `FR0.csv` | 符號分佈 |
| `{GAME_DIR}/run.py` | 當前 run_conditions, num_sim_args |
| `{GAME_DIR}/optimize_lut.py` | 確認存在 |

計算衍生值：
```
board_size = num_reels × num_rows[0]       # 例如 7×7 = 49
game_type = win_type                        # cluster, lines, ways, scatter
has_tumble = game_type in ["cluster", "scatter"]
bonus_cost = bonus BetMode 的 cost          # 例如 80.0
```

---

### Step 2: 輪帶安全驗證（Pre-flight）

用 Python 腳本統計每個符號在每軸的出現次數和百分比。

#### 2a. 符號密度檢查

根據遊戲類型檢查上限：

| 遊戲類型 | 單一符號上限 | 最大連續同符號 |
|----------|------------|--------------|
| Cluster (7x7) | 13% | 2 |
| Cluster (6x6) | 12% | 2 |
| Scatter (6x5) | 15% | 2 |
| Lines (5x3) | 20% | 3 |
| Ways (5x3/6x4) | 18% | 3 |

#### 2b. Scatter/Wild 特殊限制

**Scatter retrigger 安全公式**（Tumble 類遊戲）：
```
board_size × scatter_pct < min_retrigger_count
```
- 7x7 cluster: `49 × scatter_pct < 3` → scatter_pct < 6.1%，**建議 ≤ 3%**
- 6x5 scatter: `30 × scatter_pct < 3` → scatter_pct < 10%，**建議 ≤ 3%**

**Wild 密度限制**（帶乘數時）：
- 如果 freegame 中 Wild 攜帶乘數（`mult_values` 中 freegame 有 >1 的值），Wild 密度 **≤ 3%**
- 不帶乘數的 Wild：**≤ 5%**

**期望出現數檢查**：
```
expected_on_board = board_size × (symbol_count / reel_length)
```
如果任何符號的 expected_on_board ≥ min_win_threshold（通常 5），表示每轉幾乎必定形成贏分 → 導致無限 tumble。

#### 2c. 連續符號檢查

確認沒有 3+ 連續相同符號（tumble 類遊戲）或 4+（非 tumble）。

#### 2d. 輸出驗證報告

```
=== 輪帶驗證報告 ===
BR0.csv:
  Reel 1 (150 stops): H1: 8 (5.3%) OK | L5: 18 (12.0%) OK | S: 4 (2.7%) OK | W: 0 (0.0%) OK
  ...
FR0.csv:
  ...

[PASS] 所有檢查通過
或
[DANGER] 發現以下問題：
  - FR0 Reel 2: W density 7.3% > 3% safe limit (multiplier wild)
  - FR0: Scatter expected on board = 3.4 >= retrigger threshold 3
```

**決策邏輯**：
- 全部 PASS → 跳到 Step 4
- 有 DANGER → 進入 Step 3

---

### Step 3: 自動修復輪帶（條件性）

只在 Step 2 發現 DANGER 時執行。

#### 3a. 備份原始輪帶
```bash
cp {GAME_DIR}/reels/BR0.csv {GAME_DIR}/reels/BR0.csv.bak
cp {GAME_DIR}/reels/FR0.csv {GAME_DIR}/reels/FR0.csv.bak
```

#### 3b. 修復策略

對每個輪帶檔案（BR0.csv, FR0.csv），每個軸（column）：

1. **減少過量符號**：如果符號 X 的 `count / reel_length > max_pct`：
   - 計算需移除數量：`excess = count - floor(reel_length × max_pct)`
   - 隨機選擇 excess 個 X 的位置來替換

2. **替換優先順序**：
   - 同階層中不足的符號（如 L5 過量 → 替換為 L3 或 L4）
   - 低階高賠符號（H3, H4）
   - **絕不**增加 Wild 或 Scatter

3. **位置約束**：替換時確保不造成 3 連續同符號

4. **Wild/Scatter 特殊處理**：
   - 過高時減少，替換為低賠符號
   - 最低保留：每軸 2 個 Scatter，帶乘數軸 2 個 Wild

#### 3c. 重新驗證

修復後重新執行 Step 2 驗證。如果仍有問題，報告並停止。

---

### Step 4: Distribution 配置檢查

#### 4a. Wincap Distribution 檢查

確認 `game_config.py` 中每個 bet_mode 的 distributions 包含 wincap：

```python
Distribution(
    criteria="wincap",
    quota=0.05,
    win_criteria=mode_maxwins["mode_name"],
    conditions=wincap_condition,
)
```

如果缺少 → **自動添加**，quota=0.05，並按比例調整其他 distribution 的 quota。

#### 4b. Bonus 數學驗證

計算 bonus 模式需要的平均 session payout：
```
avg_session_payout = bonus_cost × target_rtp
```

例如：cost=80, rtp=0.96 → 需要平均每次 bonus 回報 76.8x。

檢查 `freegame_condition` 中的 `mult_values` 加權平均值：
```python
avg_mult = sum(mult × weight for mult, weight in mult_values.items()) / sum(weights)
```

如果 `avg_mult < 3.0`：發出 WARNING，建議提高乘數配置。

#### 4c. game_optimization.py Fence Targets 檢查

確認 fence targets 的 RTP 加總 ≈ target_rtp：
```
sum(fence_rtp for all fences) ≈ target_rtp
```

#### 4d. Session 時長約束檢查（Stake Engine 審核要求）

**背景**：Stake Engine 審查員會測試 Max Win Replay。如果免費旋轉沒有硬上限或乘數成長太慢，
Max Win 可能需要數百輪才能達成 wincap（例如 790 輪 / 2+ 小時），會被退件。

**檢查項目：**

| 項目 | 檢查方式 | 標準 |
|------|---------|------|
| `max_free_spins` 存在 | 讀取 game_config.py | 必須定義，且 ≤ 50 |
| `mult_levels` 存在 | 讀取 game_config.py | 如有位置乘數，必須定義等級表 |
| Scatter 壓制邏輯 | 讀取 game_override.py | Tumble 類遊戲必須有 `_suppress_scatters()` |
| Wincap bypass | 讀取 gamestate.py | wincap 模擬必須繞過硬上限（`force_wincap` 條件） |
| 乘數封頂 | 檢查 mult_levels 最大值 | 建議 ≤ ×128，推薦 ×64 |
| Wincap 可達性 | 計算理論天花板（見下方公式） | `theoretical_max` 應 ≥ `wincap` |
| **FS 迴圈 wincap 中斷** | 讀取 gamestate.py | `run_freespin()` 外層 while 必須包含 `not self.wincap_triggered`（見 4e） |
| **Wincap FS 安全上限** | 讀取 gamestate.py | Wincap 模擬中 FS 必須有絕對上限（如 `MAX_WINCAP_FS = 200`）（見 4e） |

**Wincap 可達性計算**：
```
# 估算遊戲機制的理論最大贏分
mult_layers = 1（僅 global_mult）或 2（global_mult + wild_mult）
avg_tumbles_per_spin ≈ 3
max_base_win = max(paytable.values())  # 最高單次 scatter 賠付

if mult_layers == 1:
    theoretical_max ≈ max_free_spins × avg_tumbles_per_spin × mult_cap × max_base_win
elif mult_layers == 2:
    avg_wild_mult = weighted_avg(mult_values[freegame_type])
    theoretical_max ≈ max_free_spins × avg_tumbles × mult_cap × max_base_win × avg_wild_mult
```

**判定邏輯：**
- `max_free_spins` 未定義 → **[DANGER]** 停止模擬，提示使用者先設定
- `max_free_spins` > 50 → **[WARNING]** 提醒可能導致 replay 過長
- Scatter 壓制缺失（Tumble 類遊戲）→ **[DANGER]** 即使有硬上限，retrigger 仍可能累積過多輪次
- Wincap bypass 缺失 → **[WARNING]** wincap 模擬可能無法達成 10,000x（被硬上限截斷）
- `theoretical_max < wincap` → **[DANGER]** 遊戲機制無法自然達到 wincap，需加 Wild 乘數（見 `guide-scatter.md` Bug 8）或降低 wincap
- `theoretical_max < wincap × 2` → **[WARNING]** wincap 可達但極端稀有，模擬會非常慢，建議使用 wincap fallback 流程（見 Step 5c）

#### 4e. Gamestate 無限迴圈防護檢查（**關鍵 — 必檢**）

**背景**：pharaohs-cascade 曾因此問題導致模擬無限迴圈、進程卡死、電腦當機。
SDK 的 scatter 模板 `run_freespin()` 外層 while 迴圈**不檢查 `wincap_triggered`**，
加上 wincap 模擬繞過 scatter 壓制和 FS 硬上限 → WCAP 輪帶高 S 密度不斷 retrigger →
`tot_fs` 無限成長 → 單個 session 永遠跑不完。

**檢查 1：FS 外層迴圈必須包含 `wincap_triggered` 檢查**

讀取 `{GAME_DIR}/gamestate.py`，確認 `run_freespin()` 的外層 while 條件：

```python
# 正確 ✅
while self.fs < self.tot_fs and not self.wincap_triggered:

# 錯誤 ❌ — wincap 達成後仍繼續跑剩餘 FS 輪次
while self.fs < self.tot_fs:
```

如果缺少 → **自動修復**：用 Edit 工具在 while 條件中加入 `and not self.wincap_triggered`。

**檢查 2：Wincap 模擬 FS 絕對安全上限**

讀取 `{GAME_DIR}/gamestate.py`，確認 wincap 模擬中的 retrigger 有上限。
在 `run_freespin()` 的 retrigger 處理段落中：

```python
# 正確 ✅ — wincap 模擬也有 FS 上限
if not is_wincap_sim:
    self.tot_fs = min(self.tot_fs, self.config.max_free_spins)
else:
    self.tot_fs = min(self.tot_fs, self.MAX_WINCAP_FS)  # 200

# 錯誤 ❌ — wincap 模擬沒有任何 FS 上限
if not is_wincap_sim:
    self.tot_fs = min(self.tot_fs, self.config.max_free_spins)
# else: 無限制 → 無限 retrigger
```

如果缺少：
1. 確認 class 中有 `MAX_WINCAP_FS = 200`（或在 game_override.py 中）
2. 在 retrigger 的 else 分支加入 `self.tot_fs = min(self.tot_fs, self.MAX_WINCAP_FS)`

**判定邏輯：**
- 兩項都存在 → **[PASS]** 繼續 Step 5
- 任一缺失 → **[DANGER]** 自動修復後繼續（如果不修復，模擬必定卡住）

---

### Step 5: 執行模擬

#### 5a. 清理環境

```bash
# 清除舊的 publish_files 中的 LUT（防止與新模擬衝突）
rm -f {GAME_DIR}/library/publish_files/lookUpTable_*.csv

# 清除可能的舊 lookup_tables
rm -f {GAME_DIR}/library/lookup_tables/lookUpTable_*.csv
```

#### 5b. 配置 run.py

用 Edit 工具修改 `run.py`：
```python
run_conditions = {
    "run_sims": True,
    "run_optimization": False,
    "run_analysis": False,
    "run_format_checks": False,
}
num_sim_args = {
    "base": int(1e4),
    "bonus": int(1e4),
}
```

#### 5c. 執行模擬

```bash
cd {GAME_DIR}
python run.py
```

**超時保護**：設定 10 分鐘超時。如果超時：
1. 終止進程（`taskkill /F /IM python.exe` on Windows）
2. 清理殘留的 worker 進程
3. 診斷原因（**按優先順序檢查**）：
   - **[最常見] FS 迴圈缺少 wincap_triggered 檢查**（Step 4e 遺漏）→ 回到 Step 4e 修復
   - **[最常見] Wincap 模擬 FS 無上限** → WCAP 輪帶高 S 密度 + scatter 壓制繞過 → 無限 retrigger → 回到 Step 4e 加 MAX_WINCAP_FS
   - **Scatter 密度太高** → 回到 Step 3 降低密度
   - **缺少 MAX_TUMBLES** → 確認 gamestate.py 中有 tumble 上限
   - **Wincap 模擬卡住**（`>5,000 repeats per wincap event`）→ 檢查 Session 約束：
     - `max_free_spins` 是否太高或未設定 → 導致 wincap 需要數百輪 free spin
     - 乘數成長是否太慢（如 +1 線性 vs ×2 等級制）→ 需要更多輪才能累積到 wincap
     - Wild 乘數是否在 win formula 中 → 沒有 wild mult 可能無法在合理輪次達到 wincap
     - Wincap bypass 是否生效 → `force_wincap` 條件必須同時繞過硬上限和 scatter 壓制
4. 根據診斷結果修復後重試
5. **Wincap 標準 fallback**（wincap 重試 >5,000 且其他 thread 已完成時）：
   a. 停止模擬，從 `game_config.py` 移除 wincap Distribution（將 quota 分配給其他 distribution）
   b. 重新跑完整模擬（不含 wincap），此時應能在合理時間內完成
   c. 手動注入合成事件到 LUT 檔案：
      - `lookUpTable_{mode}.csv`：追加 `{max_id+i},1,{wincap×100}` 共 10 條
      - `lookUpTableSegmented_{mode}.csv`：追加 `{max_id+i},wincap,0.0,{wincap}` 共 10 條
      - 可選：追加中間層級事件（wincap×30%、50%、70%）填補分佈空洞
   d. 繼續 Step 6 LUT 優化（優化器會自動分配極低權重）
   e. 完成後恢復 `game_config.py` 的 wincap Distribution（確保程式碼完整性）

#### 5d. 驗證輸出

確認以下檔案存在：
- `library/lookup_tables/lookUpTable_base.csv`
- `library/lookup_tables/lookUpTable_bonus.csv`
- `library/lookup_tables/lookUpTableSegmented_base.csv`
- `library/lookup_tables/lookUpTableSegmented_bonus.csv`

#### 5e. B3 Early Gate — Raw Simulation RTP 檢查（**阻擋型**）

**在 LUT 優化前攔截源頭問題。** Raw sim RTP 過高表示模型本身過肥，優化器壓縮比越大分佈越失真。

```bash
# 計算 bonus LUT equal-weight 平均 payout
cd {GAME_DIR}
awk -F', ' '{s+=$3; n++} END{printf "Raw avg payout: %.1f (RTP vs cost: %.1f%%)\n", s/n, s/n/{bonus_cost*100}*100}' library/lookup_tables/lookUpTable_bonus.csv
```

**判定邏輯（三級）：**
- Raw sim RTP ≤ 150% → **[PASS]** 繼續 Step 6
- Raw sim RTP 150-200% → **[WARNING]** 可繼續但建議微調 FR0（降低高賠符號密度或 wild mult）
- Raw sim RTP > 200% → **[FAIL — 阻擋]** 不得進入 Step 6。必須回到 Step 3 調整：
  1. 降低 FR0 高賠符號（H1/H2）密度
  2. 降低 mult_cap 或 wild mult_values
  3. 重新執行 Step 2-5

---

### Step 6: LUT 權重優化

#### 6a. 執行 Python LUT 優化器

```bash
cd {GAME_DIR}
python optimize_lut.py
```

#### 6b. 驗證結果

讀取優化器輸出，提取：
- 各 mode 的最終 RTP 和偏差
- PASS/FAIL 狀態
- 獎金分佈表

確認以下檔案存在：
- `library/publish_files/lookUpTable_base_0.csv`
- `library/publish_files/lookUpTable_bonus_0.csv`

---

### Step 7: 統計分析 + 結果評估

#### 7a. 執行分析

用 Edit 工具修改 `run.py`：
```python
run_conditions = {
    "run_sims": False,
    "run_optimization": False,
    "run_analysis": True,
    "run_format_checks": False,
}
```

⚠️ 確認 `run.py` 的 LUT 同步邏輯不會覆蓋已優化的 LUT：
```python
# 只在 publish_files 不存在 LUT 時才複製
if not os.path.exists(_dst_lut) and os.path.exists(_src_lut):
    shutil.copy2(_src_lut, _dst_lut)
```

執行：
```bash
cd {GAME_DIR}
python run.py
```

#### 7b. 評估 Pass Criteria

**基礎 RTP 與分佈檢查：**

| 指標 | 目標 | 容忍範圍 |
|------|------|---------|
| Base RTP | TARGET_RTP | ± 0.5% |
| Bonus RTP | TARGET_RTP | ± 0.5% |
| Payout 格式 | 所有 cents % 10 == 0 | 零違規 |
| 獎金分佈 | 各層級有覆蓋 | 不能有連續空層 |

**Stake Engine 審核標準驗證（來自 approval-guidelines §6 Math Verification）：**

以下檢查項來自 Stake Engine 官方審核標準，**必須全部通過**才能送審：

| # | 檢查項 | 標準 | 驗證方法 |
|---|--------|------|---------|
| M1 | RTP 合規範圍 | 90.0% ≤ RTP ≤ 98.0% | 讀取分析報告的 base/bonus RTP |
| M2 | 多模式 RTP 偏差 | 所有模式 RTP 差異 ≤ 0.5% | `abs(base_rtp - bonus_rtp) ≤ 0.5` |
| M3 | Max Win 可達性 | 命中率 > 1/10,000,000 | 從 LUT 統計 wincap payout 的加權頻率：`sum(weight for payout==wincap) / sum(all weights)` |
| M4 | Max Win 與規則一致 | LUT 中的 max payout == config.wincap | 比對 LUT 最大 payout vs game_config.py 的 wincap |
| M5 | 模擬多樣性 | 100,000+ 模擬，結果充分多樣 | 確認 num_sim_args ≥ 1e5（送審標準），檢查唯一 payout 值數量 |
| M6 | 非零獲勝命中率 | ≥ 1/20（每 20 注至少 1 次非零獲勝） | 從 LUT 計算：`sum(weight for payout>0) / sum(all weights) ≥ 0.05` |
| M7 | 零獲勝不過多 | 100,000 次中不應有 90,000+ 次零獲勝 | 從 LUT 計算零獲勝佔比 ≤ 90% |
| M8 | 獎金分佈無間隙 | 可達範圍內有中間獲勝 | 檢查 `payout_ratio ≤ wincap/cost` 範圍內的各層級，不能有連續 2 層以上命中率為 0。超過 `wincap/cost` 的區間物理上不可能存在，自動排除（例：bonus cost=80x, wincap=10000x → max_ratio=125x → 500x+ 區間排除） |
| M9 | 單一結果不壓倒 | 最高頻率單一 payout 命中率合理 | 最高頻率非零 payout 的 HR ≤ 1/3（不能佔總命中 33% 以上） |

**Bonus Mode 體驗品質驗證（B1-B5）：**

以下檢查針對有 Buy Bonus（is_buybonus=True）的模式，**必須全部通過**。
這些 gate 是 Pharaohs Cascade 送審被退後新增的 — M1-M9 只覆蓋數值合規，B1-B5 覆蓋玩家體驗品質。

| # | 檢查項 | 標準 | 驗證方法 | 背景 |
|---|--------|------|---------|------|
| B1 | Bonus Zero Win Rate | **= 0%** | 從 bonus LUT 計算：`sum(weight for payout==0) / sum(all weights) == 0` | 玩家花 80x 買入，每次都必須有回報。Dragon Feast 已做到 0% |
| B2 | Bonus Below-Cost Rate | ≤ 75%（WARNING ≤ 65%） | `sum(weight for payout < cost*100) / sum(all weights)` | 低於成本比例太高 = 體驗惡劣 |
| B3 | Raw Simulation RTP | ≤ 200% | 模擬完成後（LUT 優化前），計算 bonus LUT equal-weight 平均 payout / cost | 超過 200% = 優化器壓縮比 >2x，分佈必然失真 |
| B4 | Optimizer Zero Weight | ≤ 35% | LUT 優化後，計算 bonus 零贏 entries 的權重佔比 | 優化器分配 >35% 給零贏 = 模型源頭有問題 |
| B5 | FR0 vs BR0 獨立性 | FR0 ≠ BR0 | 比對 reels/FR0.csv 和 reels/BR0.csv 的符號分佈 | 有 FS 的遊戲 FR0 必須獨立調整，否則 FS 贏率無法獨立控制 |

**B1 是硬性 gate — 任何值 > 0% 都必須停下來修復模型，不能靠調 LUT 權重解決。**
修復方式：在 game_override.py 中 override `check_repeat()`（注意：不是 `check_game_repeat()`，SDK 不呼叫後者），
bonus mode freegame distribution 的 `final_win < 0.01` 時設 `self.repeat = True`。

**B1 自動修復模板**（直接貼入 `game_override.py`）：
```python
def check_repeat(self):
    """Override SDK check_repeat(): bonus mode 零贏強制重試。"""
    super().check_repeat()
    if (self.gametype == self.config.freegame_type
            and self.final_win < 0.01):
        self.repeat = True
```

**B2 分級標準：** ≤ 65% PASS、65-75% WARNING（可送審但建議優化）、> 75% FAIL。

**B3 檢查時機：** 已提前到 Step 5e（Early Gate）。如果 B3 FAIL，不會進入 Step 6。

**驗證腳本模板**（用 Bash + awk 分析 LUT）：

```bash
# M1: RTP 範圍（從分析報告讀取，或從 LUT 計算）
awk -F', ' '{sw+=$2*$3; w+=$2} END{rtp=sw/w/100; if(rtp<90||rtp>98) print "[FAIL] M1: RTP="rtp"% 超出 90-98% 範圍"; else print "[PASS] M1: RTP="rtp"%"}' lookUpTable_base_0.csv

# M3: Max Win 命中率
awk -F', ' -v wc={wincap*100} '{w+=$2; if($3==wc) ww+=$2} END{hr=w/ww; if(hr>10000000) print "[FAIL] M3: Max Win HR=1/"hr" > 1/10M"; else print "[PASS] M3: Max Win HR=1/"hr}' lookUpTable_base_0.csv

# M6: 非零獲勝命中率
awk -F', ' '{w+=$2; if($3>0) nz+=$2} END{hr=nz/w; if(hr<0.05) print "[FAIL] M6: 非零HR="hr" < 5%"; else print "[PASS] M6: 非零HR="hr}' lookUpTable_base_0.csv

# M7: 零獲勝佔比
awk -F', ' '{w+=$2; if($3==0) z+=$2} END{r=z/w; if(r>0.9) print "[FAIL] M7: 零獲勝="r*100"% > 90%"; else print "[PASS] M7: 零獲勝="r*100"%"}' lookUpTable_base_0.csv
```

**報告格式（加入 Step 8 最終報告）：**

```
------------------------------------------------------------
Stake Engine 審核標準驗證
------------------------------------------------------------
[PASS/FAIL] M1: RTP 合規範圍 — Base={base_rtp}%, Bonus={bonus_rtp}% (90-98%)
[PASS/FAIL] M2: 多模式偏差 — |{base_rtp}-{bonus_rtp}| = {diff}% (≤0.5%)
[PASS/FAIL] M3: Max Win 可達性 — HR=1/{hr} (≤1/10M)
[PASS/FAIL] M4: Max Win 一致性 — LUT max={lut_max}, config={wincap}
[PASS/FAIL] M5: 模擬多樣性 — {unique_payouts} 種唯一 payout, {total_sims} 次模擬
[PASS/FAIL] M6: 非零獲勝命中率 — {nz_hr}% (≥5%)
[PASS/FAIL] M7: 零獲勝佔比 — {zero_pct}% (≤90%)
[PASS/FAIL] M8: 獎金分佈連續性 — {gap_info}
[PASS/FAIL] M9: 單一結果集中度 — 最高頻 payout HR={top_hr}% (≤33%)
```

**B 系列驗證腳本模板**（用 Python 分析 bonus LUT）：

```python
# B1: Bonus Zero Win Rate（必須 = 0%）
import csv
with open('lookUpTable_bonus_0.csv') as f:
    rows = list(csv.reader(f))
tw = sum(int(r[1]) for r in rows)
zw = sum(int(r[1]) for r in rows if float(r[2]) == 0)
print(f"[{'PASS' if zw == 0 else 'FAIL'}] B1: Bonus Zero Win = {zw/tw*100:.2f}%")

# B2: Below-Cost Rate（≤ 75%，WARNING ≤ 65%）
cost = 8000  # bonus_cost * 100
bcw = sum(int(r[1]) for r in rows if 0 < float(r[2]) < cost)
bcr = bcw/tw
if bcr <= 0.65: print(f"[PASS] B2: Below-Cost = {bcr*100:.1f}%")
elif bcr <= 0.75: print(f"[WARNING] B2: Below-Cost = {bcr*100:.1f}% (65-75% 邊界)")
else: print(f"[FAIL] B2: Below-Cost = {bcr*100:.1f}% > 75%")

# B3: Raw Simulation RTP（≤ 200%，LUT 優化前用 lookup_tables/ 目錄的檔案）
avg = sum(float(r[2]) for r in rows) / len(rows)
raw_rtp = avg / cost * 100
print(f"[{'PASS' if raw_rtp <= 200 else 'FAIL'}] B3: Raw Sim RTP = {raw_rtp:.1f}%")

# B4: Optimizer Zero Weight（≤ 35%，LUT 優化後）
print(f"[{'PASS' if zw/tw <= 0.35 else 'FAIL'}] B4: Zero Weight = {zw/tw*100:.2f}%")

# B5: FR0 vs BR0 獨立性（檢查符號分佈差異）
# 用 Python 比對兩個 CSV 的符號計數，任一軸有差異即 PASS
```

**決策邏輯：**
- M1-M9 + B1-B5 全部 PASS → 可送審
- M1/M2 FAIL → 調整 fence targets 重新優化
- M3 FAIL → 增加 wincap distribution quota 或加專用 reel
- M5 FAIL + 即將送審 → 提高 num_sim_args 到 1e5+，提醒使用者重新模擬
- M6/M7 FAIL → 輪帶問題，回到 Step 3 調整符號密度
- M8/M9 FAIL → 調整 distribution quota 或 fence targets
- **B1 FAIL → [阻擋] 必須修復模型：override check_repeat() 加零贏拒絕（見 B1 自動修復模板），不能靠 LUT 調整**
- **B2 > 75% FAIL → 調整 FR0 輪帶降低 FS 贏率，或降低 mult_cap / wild mult**
- **B2 65-75% WARNING → 可繼續但建議優化 FR0**
- **B3 FAIL → 已在 Step 5e Early Gate 攔截，不會到這裡**
- **B4 FAIL → B1/B3 的下游症狀，先修 B1/B3**
- **B5 FAIL → 為 FS 設計獨立 FR0 輪帶（降低 H1/H2 密度，補 L3/L4）**

**B 系列失敗決策樹（按此順序處理）：**

```
B1 FAIL (零贏 > 0%)?
  └─ YES → 停止。貼入 check_repeat() 修復模板到 game_override.py → 重跑 Step 5-7
       └─ 仍然 FAIL? → 檢查 gametype 判斷是否正確（freegame_type 名稱）
B5 FAIL (FR0 = BR0)?
  └─ YES → 停止。設計獨立 FR0（降 H1/H2 密度 30-50%，補 L3/L4）→ 重跑 Step 2-7
B2 FAIL (below-cost > 75%)?
  └─ YES → 降低 FR0 高賠符號密度 或 降 mult_cap → 重跑 Step 5-7
B4 WARNING (零權重 > 35%)?
  └─ YES → 通常是 B1/B3 的下游症狀。如果 B1 已 PASS，檢查 raw sim RTP 是否邊界（150-200%）
全部 PASS → 可送審
```

#### 7c. FAIL 時的診斷與重試

**最多 3 次完整迭代**（Step 2 → Step 7）。

| 失敗原因 | 診斷方式 | 修復策略 |
|---------|---------|---------|
| RTP 偏差 > 0.5% | 檢查 optimize_lut.py 是否收斂 | 調整 game_optimization.py fence targets |
| RTP 超出 90-98% | M1 檢查結果 | 調整 paytable 或符號密度，重新模擬 |
| 原始 RTP 異常高 (>500%) | Wild/高賠符號密度太高 | 回到 Step 3 降低密度 |
| 原始 RTP 異常低 (<20%) | 符號密度太低或乘數太低 | 增加 Wild/高賠密度，提高 mult_values |
| 模擬超時 | Scatter 密度太高 / 缺少 MAX_TUMBLES | 回到 Step 3 降低 Scatter，確認 MAX_TUMBLES |
| Wincap 模擬卡住 | wincap event 重複 >5,000 次仍未達標 | 檢查 session 約束：max_free_spins、乘數成長速度、wild mult 是否在公式中、wincap bypass |
| 獎金分佈空洞 | 模擬量不足 | 提高 num_sim_args 到 5e4 |
| Max Win 不可達 | M3 檢查結果 | 增加 wincap distribution quota，或增加專用 reel (WCAP) |
| 非零命中率過低 | M6/M7 檢查結果 | 調整輪帶符號密度，增加低賠符號 |
| 單一結果過集中 | M9 檢查結果 | 增加模擬數量或調整 distribution quota |
| **Bonus 零贏 > 0%** | **B1 FAIL** | **override check_repeat() 加零贏拒絕（not check_game_repeat）** |
| **Bonus below-cost > 60%** | **B2 FAIL** | **調整 FR0 降 FS 贏率，或降 mult_cap / wild mult** |
| **Raw sim RTP > 200%** | **B3 FAIL（阻擋）** | **回到 Step 3：降 FR0 高賠密度、mult_cap、wild mult** |
| **Optimizer 零權重 > 35%** | **B4 FAIL** | **先修 B1/B3，B4 是下游症狀** |
| **FR0 = BR0** | **B5 FAIL** | **為 FS 設計獨立 FR0（降 H1/H2，補 L3/L4）** |

---

### Step 8: 最終報告

#### 8a. 恢復 run.py 設定

```python
run_conditions = {
    "run_sims": False,
    "run_optimization": False,
    "run_analysis": True,
    "run_format_checks": False,
}
```

#### 8b. 輸出報告

```
============================================================
RTP 優化報告
============================================================

遊戲: {game_id} ({working_name})
類型: {win_type} ({num_reels}x{num_rows[0]})
目標 RTP: {TARGET_RTP}%
最大獎金: {wincap}x
購買獎勵費用: {bonus_cost}x
免費旋轉硬上限: {max_free_spins} 輪
乘數封頂: ×{max(mult_levels)}

------------------------------------------------------------
輪帶驗證
------------------------------------------------------------
BR0.csv: {PASS/FIXED} (最大單一符號 {max_pct}%)
FR0.csv: {PASS/FIXED} (最大單一符號 {max_pct}%)
自動修復: {是/否} ({N}個問題)

------------------------------------------------------------
RTP 結果
------------------------------------------------------------
[PASS] Base:  RTP={base_rtp}% (目標={TARGET_RTP}%, 偏差={diff}%)
[PASS] Bonus: RTP={bonus_rtp}% (目標={TARGET_RTP}%, 偏差={diff}%)

------------------------------------------------------------
Base 獎金分佈
------------------------------------------------------------
      零獎 (    0x~    0x): HR=1/X, RTP=X%
      微獎 (    0x~    1x): HR=1/X, RTP=X%
      小獎 (    1x~    2x): HR=1/X, RTP=X%
      中獎 (    2x~    5x): HR=1/X, RTP=X%
     中大獎 (    5x~   10x): HR=1/X, RTP=X%
      大獎 (   10x~   20x): HR=1/X, RTP=X%
     超大獎 (   20x~   50x): HR=1/X, RTP=X%
      巨獎 (   50x~  100x): HR=1/X, RTP=X%
      極獎 (  100x~  500x): HR=1/X, RTP=X%
      神獎 (  500x~ 1000x): HR=1/X, RTP=X%
      傳說 ( 1000x~ 5000x): HR=1/X, RTP=X%
  MAX WIN ( 5000x~{wincap}x): HR=1/X, RTP=X%

------------------------------------------------------------
Bonus 獎金分佈
------------------------------------------------------------
（同上格式）

------------------------------------------------------------
模擬統計
------------------------------------------------------------
模擬次數: base={base_sims}, bonus={bonus_sims}
迭代次數: {iterations}

------------------------------------------------------------
輸出檔案
------------------------------------------------------------
- library/publish_files/lookUpTable_base_0.csv
- library/publish_files/lookUpTable_bonus_0.csv
- library/statistics_summary.json
- library/{game_id}_full_statistics.xlsx

------------------------------------------------------------
Stake Engine 審核標準驗證
------------------------------------------------------------
[PASS/FAIL] M1: RTP 合規範圍 — Base={base_rtp}%, Bonus={bonus_rtp}% (90-98%)
[PASS/FAIL] M2: 多模式偏差 — |base-bonus| = {diff}% (≤0.5%)
[PASS/FAIL] M3: Max Win 可達性 — HR=1/{hr} (≤1/10M)
[PASS/FAIL] M4: Max Win 一致性 — LUT max={lut_max}, config={wincap}
[PASS/FAIL] M5: 模擬多樣性 — {unique_payouts} 種唯一 payout
[PASS/FAIL] M6: 非零獲勝命中率 — {nz_hr}% (≥5%)
[PASS/FAIL] M7: 零獲勝佔比 — {zero_pct}% (≤90%)
[PASS/FAIL] M8: 獎金分佈連續性 — {gap_info}
[PASS/FAIL] M9: 單一結果集中度 — 最高頻HR={top_hr}% (≤33%)

------------------------------------------------------------
Bonus Mode 體驗品質驗證（僅 Buy Bonus 模式）
------------------------------------------------------------
[PASS/FAIL] B1: Bonus Zero Win Rate — {bonus_zero_pct}% (= 0%)
[PASS/FAIL] B2: Below-Cost Rate — {below_cost_pct}% (≤60%)
[PASS/FAIL] B3: Raw Simulation RTP — {raw_rtp}% (≤200%)
[PASS/FAIL] B4: Optimizer Zero Weight — {zero_weight_pct}% (≤35%)
[PASS/FAIL] B5: FR0 vs BR0 獨立性 — {independent_or_identical}

------------------------------------------------------------
Session 時長估算（Stake Engine Replay）
------------------------------------------------------------
Max Win Event 免費旋轉輪數: ~{wincap_fs_rounds} 輪
預估 Replay 播放時間: ~{estimated_minutes} 分鐘
判定: {PASS: ≤3分鐘 / WARNING: 3-5分鐘 / DANGER: >5分鐘}

說明：從 wincap LUT 事件的 book 檔案讀取實際 free spin 輪數。
每輪 tumble 動畫約 3-5 秒，加上開場/結算，估算總播放時長。
審查員標準：Max Win Replay 應在 2-3 分鐘內完成。

------------------------------------------------------------
下一步
------------------------------------------------------------
1. 如需更精確的 RTP，提高模擬次數到 1e5+，重新執行 /optimize-rtp
2. 開啟 run_format_checks 驗證格式：修改 run.py 後執行 python run.py
3. 使用 validate_sync.py 驗證前後端同步
4. M1-M9 全部 PASS 後，執行 /audit-launch 進行前端審核
```

---

## 安全機制

| 機制 | 說明 |
|------|------|
| 輪帶備份 | 修改前自動備份為 `.bak` |
| 迭代上限 | 最多 3 次完整迭代，防止無限循環 |
| 模擬超時 | 10 分鐘超時保護 |
| LUT 保護 | 不覆蓋已優化的 LUT |
| run.py 恢復 | 完成後恢復 run_conditions 到中性狀態 |
| Worker 清理 | 模擬前後清理殘留的 Python worker 進程 |
| **FS wincap 中斷** | `run_freespin()` 外層 while 必須包含 `not self.wincap_triggered`（Step 4e 自動檢查/修復） |
| **Wincap FS 上限** | Wincap 模擬中 FS 上限 200 輪，防止 WCAP 輪帶高 S 密度導致無限 retrigger（Step 4e 自動檢查/修復） |

---

## Idempotency（冪等性）

此 skill 可安全重複執行：
- 如果 `publish_files/lookUpTable_*_0.csv` 已存在，會詢問是否重新優化
- 輪帶 `.bak` 檔案只在首次修改時建立
- 每次執行完成後 `run.py` 恢復到中性狀態

---

## 依賴

- Python 3.12+
- math-sdk 已安裝（`pip install -e sdks/math-sdk`）
- `optimize_lut.py` 存在於遊戲目錄中（由 init-math 或手動建立）
