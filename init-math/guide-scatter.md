# Scatter 類型指南

## SDK 來源

`sdks/math-sdk/games/0_0_scatter/`

## 核心特徵

- **Tumble 迴圈**：與 Cluster 類似（贏分 → 消除 → 掉落 → 重算）
- **Global Multiplier**：全域乘數，免費旋轉中每次 tumble 遞增
- **Scatter Pays**：不需要相鄰，只要版面上有足夠數量即算贏
- **乘數符號**：通常命名為 "M"（不是 "W"）
- **計算模組**：`src.calculations.scatter.Scatter`

---

## 複製後調整

### gamestate.py

有 Tumble 迴圈，但使用 `global_multiplier` 而非 position grid：

```python
# run_spin() 中的 tumble loop（與 cluster 類似）
while self.win_data["totalWin"] > 0 and not self.wincap_triggered:
    self.tumble_game_board()
    self.get_scatterpays_update_wins()
    self.emit_tumble_win_events()

# run_freespin() 中 tumble loop 的特殊點：
while self.win_data["totalWin"] > 0 and not self.wincap_triggered:
    self.tumble_game_board()
    self.update_global_mult()  # ← 每次 tumble 增加全域乘數
    self.get_scatterpays_update_wins()
    self.emit_tumble_win_events()
```

**必須加入 MAX_TUMBLES**：SDK 範例沒有，需手動加入（同 cluster）。

**注意與 Cluster 的差異**：
- Scatter 免費旋轉用 `update_global_mult()` 而非 `update_grid_mults()`
- 沒有位置乘數格（position_multipliers）
- `run_freespin()` 中先 `update_freespin()` 再 `draw_board()`（沒有 grid mult event）

### game_executables.py

**關鍵 import**：
```python
from src.calculations.scatter import Scatter
from game_events import send_mult_info_event
```

**關鍵方法**：
- `set_end_tumble_event()` — 在免費旋轉中，tumble 結束時將全域乘數套用到總贏分
  ```python
  board_mult, mult_info = self.get_board_multipliers()
  self.win_manager.set_spin_win(base_tumble_win * board_mult)
  ```
- `get_scatterpays_update_wins()` — 使用 `Scatter.get_scatterpay_wins()`
- `update_freespin_amount()` — 自訂的免費旋轉次數計算（如 scatter_count * 2）
- `update_freespin()` — 重置 global_multiplier 為 1

### game_calculations.py

包含 `get_board_multipliers()` — 遍歷版面收集所有乘數符號的值：

```python
def get_board_multipliers(self, multiplier_key="multiplier"):
    board_mult = 0
    mult_info = []
    for reel, _ in enumerate(self.board):
        for row, _ in enumerate(self.board[reel]):
            if self.board[reel][row].check_attribute(multiplier_key):
                board_mult += self.board[reel][row].get_attribute(multiplier_key)
                mult_info.append({"reel": reel, "row": row, "value": ...})
    return max(1, board_mult), mult_info
```

### game_override.py

**注意 Scatter 與其他類型的差異**：
- `reset_book()` 中重置 `self.tumble_win = 0`
- `reset_fs_spin()` 中重置 `self.global_multiplier = 1`（不是 grid mults）
- `assign_special_sym_function()` 使用 **"M"** 而非 "W"：
  ```python
  self.special_symbol_functions = {"M": [self.assign_mult_property]}
  ```
- `check_game_repeat()`（與 ways 類似，注意方法名稱）

### game_events.py

包含 `send_mult_info_event()` — 傳送版面乘數資訊事件

### game_config.py 特別注意

**乘數符號名稱**：
- Scatter SDK 使用 "M" 作為乘數符號（multiplier symbol）
- 確認 `special_symbols` 和輪帶 CSV 中一致
- 如果企劃書使用 "W" 作為乘數，需要統一修改

**freespin_triggers**：與 cluster 類似，大版面需覆蓋所有可能的 scatter 數量

---

## 輪帶限制

- 輪帶長度：120-180 停止位
- 單一符號上限：**15%**（有 tumble，比 lines/ways 嚴格）
- 最大連續同符號：2（與 cluster 相同）
- 高賠符號（H1-H4）：每軸 3-4 次
- 乘數符號（M）：每軸 2-3 次
- Scatter：每軸 3-4 次

**安全公式（假設 6x5 版面）**：
`30 格 × 15% = 4.5`，接近但低於最小贏分門檻 5

---

## 常見 Bug

### Bug 1: 模擬無限循環（同 Cluster Bug 1）

**原因**：gamestate.py 仍呼叫 `evaluate_lines_board()`

**驗證**：
```bash
grep "evaluate_lines\|get_scatterpays" models/{game_id}/gamestate.py
# 應看到 get_scatterpays_update_wins，不是 evaluate_lines_board
```

### Bug 2: 無限 Tumble（同 Cluster Bug 2）

**原因**：符號分佈太集中 + 沒有 MAX_TUMBLES 限制

**解法**：加入 MAX_TUMBLES + 重新設計輪帶

### Bug 3: 乘數符號名稱不符

**症狀**：免費旋轉中沒有乘數效果，贏分正常但沒有倍增

**原因**：`game_override.py` 中的 `assign_special_sym_function` 使用 "M"，但輪帶/config 使用 "W"

**解法**：統一所有地方的乘數符號名稱

### Bug 4: global_multiplier 未正確重置

**症狀**：免費旋轉的贏分異常偏高

**原因**：`update_freespin()` 中沒有重置 `self.global_multiplier = 1`

**解法**：確認 `update_freespin()` 方法中包含重置邏輯

### Bug 5: set_end_tumble_event 乘數計算錯誤

**症狀**：最終贏分與預期不符

**原因**：`set_end_tumble_event()` 只在 freegame 才套用版面乘數，basegame 中不應套用

**解法**：確認 `if self.gametype == self.config.freegame_type:` 條件正確

### Bug 6: draw_board trigger_symbol 覆寫為 None

**症狀**：`KeyError: None` 在 `count_special_symbols()`，模擬立即 crash

**原因**：覆寫 `draw_board()` 時把預設參數改成 `trigger_symbol=None`，但 SDK 基類 `board.py` 的預設是 `trigger_symbol="scatter"`。傳入 `None` 後 `count_special_symbols(None)` 在 `special_syms_on_board` dict 中找不到 key

**解法**：覆寫 `draw_board()` 時保持預設值 `trigger_symbol="scatter"`：
```python
# 錯誤
def draw_board(self, emit_event=True, trigger_symbol=None):

# 正確
def draw_board(self, emit_event=True, trigger_symbol="scatter"):
```

### Bug 7: freespin_triggers 不覆蓋高 scatter 數量

**症狀**：`KeyError: 7`（或 8、9）在 `update_fs_retrigger_amt()`

**原因**：6×5 版面在 tumble 後新符號掉落或使用 WCAP 輪帶時，可出現 7+ 個 scatter。但 `freespin_triggers[freegame_type]` 只定義到 5 或 6，SDK 的 `update_fs_retrigger_amt()` 直接用 `scatter_count` 查表會 KeyError

**解法**：覆寫 `update_fs_retrigger_amt` 和 `update_freespin_amount`，用 clamp 處理超出範圍的 scatter 數量：
```python
def update_fs_retrigger_amt(self, scatter_key="scatter"):
    scatter_count = self.count_special_symbols(scatter_key)
    triggers = self.config.freespin_triggers[self.gametype]
    clamped = min(scatter_count, max(triggers.keys()))
    self.tot_fs += triggers[clamped]
    fs_trigger_event(self, freegame_trigger=True, basegame_trigger=False)
```

### Bug 8: 單層乘數無法達到高 wincap

**症狀**：wincap 模擬卡住（>10,000 repeats per event），永遠無法完成

**原因**：遊戲只有 global_multiplier 一層乘數（如 ×64 封頂），沒有 Wild 乘數或板面乘數符號。wincap 10,000x 需要 `10000 / 64 ≈ 156x` 的累積 base win，在 30 輪內幾乎不可能自然達到

**判斷公式**：
```
theoretical_max ≈ max_free_spins × avg_tumbles × mult_cap × avg_base_win
如果 theoretical_max < wincap × 2 → 需要額外乘數層
```

**解法**：加 Wild 乘數作為第二層乘數（免費旋轉限定）：
- `special_symbols` 加 `"multiplier": ["W"]`
- `padding_symbol_values` 設定 `"W": {"multiplier": {2: 50, 3: 30, 5: 15, 10: 5}}`
- `assign_special_sym_function` 中註冊 `"W": [self.assign_mult_property]`
- 基礎遊戲 `mult_values: {1: 1}`（固定 ×1），免費旋轉給隨機值
- 贏分公式變為：`paytable_win × global_mult × symbol_mult`（SDK 的 `get_scatterpay_wins` 已內建 `symbol_mult` 邏輯）
