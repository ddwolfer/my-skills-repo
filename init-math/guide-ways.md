# Ways 類型指南

## SDK 來源

`sdks/math-sdk/games/0_0_ways/`

## 核心特徵

- **無 Tumble**：單次評估即完成
- **無賠付線**：自動計算所有可能路徑（如 5x3 = 243 ways，6x4 = 4096 ways）
- **版面大小**：通常 5x3 或 6x4
- **計算模組**：`src.calculations.ways.Ways`

---

## 複製後調整

### gamestate.py

與 Lines 類似，但使用 `evaluate_ways_board()`：

```python
# run_spin() 核心流程
self.draw_board(emit_event=True)  # 注意：Ways 有 emit_event=True
self.evaluate_ways_board()
self.win_manager.update_gametype_wins(self.gametype)
if self.check_fs_condition() and self.check_freespin_entry():
    self.run_freespin_from_base()
```

**注意**：
- Ways SDK 使用 `self.draw_board(emit_event=True)`（自動發送 reveal 事件）
- Ways SDK 在 freespin 觸發時使用 `check_freespin_entry()`（與 cluster 相同）

### game_executables.py

```python
from src.calculations.ways import Ways

def evaluate_ways_board(self):
    self.win_data = Ways.get_ways_data(self.config, self.board)
    if self.win_data["totalWin"] > 0:
        Ways.record_ways_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
    Ways.emit_wayswin_events(self)
```

**注意**：Ways 的 `record_ways_wins` 和 `update_spinwin` 只在有贏分時呼叫。

### game_calculations.py

空的，直接 `pass`：
```python
class GameCalculations(Executables):
    pass
```

### game_override.py

**需確認的項目**：
- `assign_special_sym_function()` 和 `assign_mult_property()` — 確認乘數符號設定
- Ways SDK 使用 `check_game_repeat()`（不是 `check_repeat()`）：
  ```python
  def check_game_repeat(self):
      if self.repeat is False:
          win_criteria = self.get_current_betmode_distributions().get_win_criteria()
          if win_criteria is not None and self.final_win != win_criteria:
              self.repeat = True
  ```
  **注意**：方法名稱為 `check_game_repeat`，會被 SDK 的 `check_repeat()` 自動呼叫。

### game_events.py

SDK Ways 範例使用標準事件：
```python
from src.events.events import *
```

### game_config.py 特別注意

**不需要定義 paylines**！Ways 自動計算所有路徑。
如果從 Lines 模板複製，**務必刪除 `self.paylines` 定義**。

**paytable 使用 ways 格式**：
- Key 為 `(match_count, symbol)`
- 與 Lines 相同格式，但計算方式不同（每個 reel 的每個 matching symbol 都獨立計路徑）

---

## 輪帶限制

- 輪帶長度：150-200 停止位
- 單一符號上限：**18%**
- 最大連續同符號：3
- H1：每軸約 3-5 次
- Wild：每軸約 2-4 次
- Scatter：每軸約 3-4 次

---

## 常見 Bug

### Bug 1: 意外保留了 paylines 定義

**症狀**：模擬可能正常運行，但贏分計算不正確

**原因**：從 Lines 模板複製後，`game_config.py` 中仍有 `self.paylines` 定義

**解法**：確認 `game_config.py` 中**沒有** `self.paylines`

### Bug 2: check_repeat vs check_game_repeat

**症狀**：模擬不符合分佈條件，或某些 criteria 永遠重試

**原因**：Ways SDK 使用 `check_game_repeat()` 而非直接覆蓋 `check_repeat()`

**解法**：確認 `game_override.py` 中的方法名稱正確

### Bug 3: Wild 沒有正確替代

**症狀**：Ways 計算找不到應有的贏分組合

**原因**：`special_symbols["wild"]` 設定不正確

**解法**：確認 wild 符號名稱與輪帶 CSV 中的一致
