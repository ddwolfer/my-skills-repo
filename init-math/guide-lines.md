# Lines 類型指南

## SDK 來源

`sdks/math-sdk/games/0_0_lines/`

## 核心特徵

- **無 Tumble**：單次評估即完成，最簡單的遊戲類型
- **賠付線（Paylines）**：固定路徑，依序比對符號
- **標準版面**：通常 5x3（15 格）
- **計算模組**：`src.calculations.lines.Lines`

---

## 複製後調整

### gamestate.py

最簡單的遊戲迴圈，無需額外修改：

```python
# run_spin() 核心流程
self.draw_board()
self.evaluate_lines_board()
self.win_manager.update_gametype_wins(self.gametype)
if self.check_fs_condition():
    self.run_freespin_from_base()
self.evaluate_finalwin()
self.check_repeat()
```

**注意**：Lines 類型在 `check_fs_condition()` 後**不需要** `check_freespin_entry()`（與 cluster/scatter 不同）。
SDK Lines 範例直接呼叫 `self.run_freespin_from_base()`。

### game_executables.py

```python
from src.calculations.lines import Lines

def evaluate_lines_board(self):
    self.win_data = Lines.get_lines(self.board, self.config, global_multiplier=self.global_multiplier)
    Lines.record_lines_wins(self)
    self.win_manager.update_spinwin(self.win_data["totalWin"])
    Lines.emit_linewin_events(self)
```

### game_calculations.py

空的，直接 `pass`：
```python
class GameCalculations(Executables):
    pass
```

### game_override.py

**需確認的項目**：
- `assign_special_sym_function()` — 設定 Wild 乘數功能
  ```python
  self.special_symbol_functions = {"W": [self.assign_mult_property]}
  ```
- `assign_mult_property()` — 確認 `mult_values` 路徑與 game_config.py 的 distribution 一致
- `check_repeat()` — Lines SDK 有額外的零贏分重試邏輯：
  ```python
  if win_criteria is None and self.final_win == 0:
      self.repeat = True
  ```

### game_events.py

SDK Lines 範例**沒有**自訂 game_events.py。保留模板版本或使用空檔案。

### game_config.py 特別注意

**必須定義 paylines**：
```python
self.paylines = {
    1:  [1, 1, 1, 1, 1],  # 中間線
    2:  [0, 0, 0, 0, 0],  # 上方線
    3:  [2, 2, 2, 2, 2],  # 下方線
    # ... 通常 20-25 條
}
```

**paylines 的行索引必須 < num_rows**：
- num_rows = [3, 3, 3, 3, 3] → payline 值只能是 0, 1, 2
- 如果有 index = 3 會導致 IndexError

**paytable 使用 lines 格式**：
- Key 為 `(match_count, symbol)`
- 例如 `(5, "H1"): 50, (4, "H1"): 20, (3, "H1"): 10`

---

## 輪帶限制

- 輪帶長度：200-220 停止位
- 單一符號上限：**20%**（5x3 版面無 tumble，限制寬鬆）
- 最大連續同符號：3
- H1（最高賠付）：每軸約 3-4 次
- Wild：每軸約 2-3 次（通常限第 2-4 軸）
- Scatter：每軸約 3-4 次

---

## 常見 Bug

### Bug 1: IndexError in paylines

**症狀**：`IndexError: list index out of range`

**原因**：payline 定義中的行索引 ≥ num_rows

**解法**：確認所有 payline 值 < num_rows（例如 num_rows=3 時，值只能是 0, 1, 2）

### Bug 2: Wild 不參與線贏分

**症狀**：有 Wild 在贏分線上但沒有計算贏分

**原因**：`special_symbols` 中的 wild 名稱與輪帶/paytable 中的不一致

**解法**：確認 `self.special_symbols["wild"] = ["W"]` 中的 "W" 與輪帶 CSV 一致

### Bug 3: 免費旋轉中 Wild 乘數不生效

**症狀**：免費旋轉的贏分與基礎遊戲相同（沒有乘數加成）

**原因**：`assign_mult_property()` 中判斷 gametype 的邏輯有誤

**解法**：確認條件為 `if self.gametype == self.config.freegame_type`
