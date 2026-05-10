# Cluster 類型指南

## SDK 來源

`sdks/math-sdk/games/0_0_cluster/`

## 核心特徵

- **Tumble 迴圈**：贏分 → 消除 → 掉落新符號 → 重新計算 → 重複直到無贏
- **Position Multiplier Grid**：位置乘數格，免費旋轉中贏過的位置累積乘數
- **大版面**：通常 7x7（49 格），符號分佈極度敏感
- **計算模組**：`src.calculations.cluster.Cluster`

---

## 複製後調整

### gamestate.py

SDK 範例的 tumble loop **沒有 MAX_TUMBLES 限制**。必須手動加入：

```python
MAX_TUMBLES = 20  # 防止大版面無限 cascade

# 在 run_spin() 的 tumble loop 中：
tumble_count = 0
while self.win_data["totalWin"] > 0 and not self.wincap_triggered and tumble_count < MAX_TUMBLES:
    self.tumble_game_board()
    self.get_clusters_update_wins()
    self.emit_tumble_win_events()
    tumble_count += 1
```

**必須確認的項目**：
- `run_spin()` 中有 `check_freespin_entry()` 呼叫（不是只有 `check_fs_condition()`）
  ```python
  if self.check_fs_condition() and self.check_freespin_entry():
      self.run_freespin_from_base()
  ```
- `run_freespin()` 中每次 tumble 後都有 `self.update_grid_mults()`
- `run_freespin()` 開頭有 `update_grid_mult_event(self)` 傳送初始 grid 狀態

### game_executables.py

**關鍵 import**：
```python
from src.calculations.cluster import Cluster
from game_events import update_grid_mult_event
```

**必須存在的方法**：
- `reset_grid_mults()` — 初始化 `self.position_multipliers` 為全 0 的 grid
- `update_grid_mults()` — 贏分位置的乘數遞增（首次 0→1，之後每次 +1）
- `get_clusters_update_wins()` — 呼叫 `Cluster.get_clusters(self.board, "wild")` 尋找群集
- `update_freespin()` — 免費旋轉計數器 +1，重置 spin win

### game_calculations.py

包含 `evaluate_clusters_with_grid()` — 自訂的 cluster 評估函式，支援位置乘數：
- 對每個 cluster 計算 `board_mult = sum(pos_mult_grid[pos])`
- 最終贏分 = `sym_win * board_mult * global_multiplier`
- 標記贏分符號 `board[pos].explode = True`

### game_override.py

**必須確認**：
- `reset_book()` 中重置 `self.tumble_win = 0`
- `reset_fs_spin()` 中呼叫 `self.reset_grid_mults()`（清空位置乘數格）
- `assign_special_sym_function()` — 如果有乘數 Wild，設定對應函式
- `check_repeat()` — 確認包含 `force_freegame` 和 `win_criteria` 檢查

### game_events.py

包含 `update_grid_mult_event()` — 傳送位置乘數格的更新事件

### game_config.py 特別注意

**freespin_triggers 必須覆蓋所有可能的 Scatter 數量**：
```python
# 7x7 版面最多 49 格，Scatter 可能出現很多
_base_fs = {4: 10, 5: 15, 6: 20, 7: 25}
_free_fs = {3: 5, 4: 10, 5: 15, 6: 20, 7: 25}
# 擴展到最大可能值
for n in range(8, 50):
    _base_fs[n] = 25
    _free_fs[n] = 25
```

**paytable 使用 cluster 格式**：
- Key 為 `(cluster_size, symbol)`
- 需要展開區間：5+ → (5,sym), (6,sym), (7,sym)；8+ → (8,sym)...(11,sym) 等

---

## 輪帶限制

**詳見 `guide-reel-design.md`，以下為摘要：**

- 🔴 **單一符號不超過 13%**（7x7 版面最嚴格的限制）
- 🔴 **不允許 3 連續同符號**（會在大版面形成必中 cluster）
- 推薦輪帶長度：100-150 停止位
- 高賠符號（H1-H4）：每軸 5-10 次
- 低賠符號（L1-L5）：每軸 12-20 次，均勻分散
- Wild：每軸 3-5 次（約 2-3%）
- Scatter：每軸 3-4 次（約 2-3%）

**為什麼 13%？**
安全公式：`49 格 × 13% = 6.37`，低於最小 cluster 贏分門檻 5，不會每轉必中。
如果是 28.6%：`49 × 28.6% = 14 個`，幾乎必定形成多個大型 cluster → 無限 tumble。

---

## 密度安全規則（7x7 Cluster + Multiplier Wild 專屬）

以下規則來自 Dragon Feast 優化的實戰經驗。
**FR0.csv（免費旋轉捲軸）比 BR0.csv 更敏感**，因為 freegame 有乘數加成，符號密度的影響被指數級放大。

### 1. Scatter 密度 ≤ 3%

```
49 格 × 3% = 1.47 期望出現 << retrigger 門檻 3 → 安全
49 格 × 6% = 2.94 期望出現 ≈ retrigger 門檻 3 → 危險
```

**實測結果**：FR0 Scatter 6.8%（28/410 每軸平均）→ 每轉期望 3.33 個 Scatter，retrigger 門檻只要 3 個 → 幾乎每轉都 retrigger → 模擬卡死 10+ 分鐘無法完成。

### 2. Wild 密度 ≤ 3%（帶乘數時）

```
49 格 × 3% = 1.47 個 Wild/spin，每個帶 avg 5x 乘數 → 可控
49 格 × 14% = 6.86 個 Wild/spin，每個帶 avg 8.8x 乘數 → RTP 爆炸
```

**實測結果**：
- FR0 Wild 14% → Base RTP 1150%（目標 96%）
- FR0 Wild 5.3% → Base RTP 396%（仍偏高但 LUT 優化可修正）
- FR0 Wild 3% → 正常範圍

**原理**：Cluster 贏分 = base_win × sum(wild_multipliers) × grid_multiplier。多個 Wild 的乘數效果是**乘法疊加**，不是加法，所以密度增加會導致指數級 RTP 增長。

### 3. FR0 vs BR0 限制差異

| 符號 | BR0（基礎遊戲） | FR0（免費旋轉） | 原因 |
|------|----------------|----------------|------|
| Wild | ≤ 5%（無乘數） | **≤ 3%**（有乘數） | 乘數效果放大 |
| Scatter | ≤ 3% | **≤ 2.5%** | retrigger 風險更高 |
| 其他符號 | ≤ 13% | ≤ 13% | 相同（tumble 限制） |

---

## 常見 Bug

### Bug 1: 模擬無限循環（run.py 完全卡住）

**症狀**：`python run.py` 執行後 CPU 100%，無任何輸出

**原因**：`gamestate.py` 仍然呼叫 `evaluate_lines_board()` 而非 cluster 方法。
Lines 計算在 cluster paytable（key 格式為 `(cluster_size, symbol)`）上找不到任何贏分，
`final_win` 永遠為 0，`check_repeat()` 永遠重試。

**快速驗證**：
```bash
grep "evaluate_lines" models/{game_id}/gamestate.py
# 如果有結果 → 就是這個 bug，Step 5.5 沒有正確執行
```

**解法**：重新執行 Step 5.5，從 SDK cluster 範例複製 5 個檔案

### Bug 2: 無限 Tumble（單次 spin 極慢）

**症狀**：模擬雖然沒有完全卡住，但每一局耗時極長

**原因**：符號分佈太集中，消除後掉落的新符號又形成新 cluster，永無止境

**快速驗證**：
```bash
# 統計輪帶中每個符號的出現次數
python -c "
import csv
from collections import Counter
with open('models/{game_id}/reels/BR0.csv') as f:
    reader = csv.reader(f)
    all_syms = [sym for row in reader for sym in row]
total = len(all_syms)
for sym, count in Counter(all_syms).most_common():
    print(f'{sym}: {count}/{total} = {count/total*100:.1f}%')
"
# 如果任何符號 > 13% → 需要重新設計輪帶
```

**解法**：
1. 加入 `MAX_TUMBLES = 20`（立即止血）
2. 重新設計輪帶，參考 `guide-reel-design.md`

### Bug 3: KeyError in freespin_triggers

**症狀**：`KeyError: 6`（或 7, 8...）

**原因**：7x7 版面可出現 6+ 個 Scatter，但 `freespin_triggers` 只定義到 5

**解法**：擴充 triggers 覆蓋到最大可能的 Scatter 數量（見上方 game_config.py 章節）

### Bug 4: Distribution wincap 無法達成

**症狀**：模擬卡住（類似 Bug 1），但 grep 確認不是類型不符

**原因**：`wincap` distribution 要求 `final_win == 10000`，但初始輪帶分佈不可能達到

**解法**：先移除 wincap distribution（將 quota 設為 0 或刪除），確認模擬能跑通後再加回

### Bug 5: Payout values must be in increments of 10

**症狀**：模擬完成但格式驗證失敗，`AssertionError: Payout values must be in increments of 10.`

**原因**：SDK 將 paytable 賠率值 × 100 轉換為 LUT 的「cents」格式（`books.py: int(round(self.payout_multiplier * 100, 0))`）。RGS 要求 LUT 中的 payout 必須是 10 的整數倍。因此 **paytable 中所有賠率值必須是 0.1 的整數倍**。

例如 `0.25 × 100 = 25`（不是 10 的倍數 ❌），而 `0.3 × 100 = 30` ✅。

此外，一次 spin/tumble 中多個 cluster 的贏分會加總寫入 LUT，如果其中任何一個 cluster 的 payout 不是 10 的倍數，加總結果也可能不是。

**合法值範例**：`0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0, 2.5, ...`
**不合法值範例**：`0.25, 0.15, 0.35, 0.45, 0.75, ...`（× 100 後不是 10 的倍數）

**快速驗證**：
```bash
# 檢查 paytable 中是否有不合法的值
python -c "
vals = [0.25, 0.8, 2.5]  # 替換成實際的 paytable 值
for v in vals:
    cents = round(v * 100)
    if cents % 10 != 0:
        print(f'{v}x -> {cents} cents ❌ (not multiple of 10)')
    else:
        print(f'{v}x -> {cents} cents ✅')
"
```

**解法**：將不合法的賠率值改為最接近的 0.1 的整數倍（例如 `0.25` → `0.3`）
