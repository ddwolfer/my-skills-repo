# 輪帶設計通用指南

本指南適用於所有遊戲類型的輪帶（reel strip）設計。
每次生成或修改輪帶時，**務必遵守**本指南中對應遊戲類型的限制。

---

## 通用安全公式（Tumble 類遊戲）

Tumble 類遊戲（cluster、scatter）如果符號分佈不均，會導致**無限消除循環**。

### 公式

```
安全條件: total_positions × (symbol_count / reel_length) < min_win_threshold
```

- `total_positions`：版面總格數（如 7x7 = 49）
- `symbol_count`：單一符號在一條輪帶上的出現次數
- `reel_length`：輪帶總停止位數
- `min_win_threshold`：該遊戲類型的最小贏分門檻（cluster/scatter 通常為 5）

### 各版面的單一符號上限

| 版面 | 總格數 | 最小贏分門檻 | 理論上限 | 保守建議 |
|------|--------|-------------|---------|---------|
| 7x7 cluster | 49 | 5 | 10.2% | **13%** |
| 6x5 scatter | 30 | 5 | 16.7% | **15%** |
| 8x8 cluster | 64 | 5 | 7.8% | **8%** |
| 5x5 cluster | 25 | 5 | 20% | **18%** |
| 6x6 cluster | 36 | 5 | 13.9% | **12%** |
| 5x3 lines/ways | 15 | N/A（無 tumble） | N/A | **20%** |
| 6x4 ways | 24 | N/A（無 tumble） | N/A | **18%** |

> **注意**：保守建議值高於理論上限，因為理論上限假設完美均勻分佈。
> 實際上 RNG 會有波動，需要預留安全空間。

---

## 危險區域速查表（基於 Dragon Feast 實戰經驗）

以下是 RTP 優化過程中遇到的嚴重問題，整理為一眼可查的格式。
每次生成或修改輪帶時，先對照此表確認沒有踩入危險區域。

| 問題 | 症狀 | 原因 | 安全範圍 |
|------|------|------|---------|
| 模擬卡死 | CPU 100%, 10+ 分鐘無輸出 | FR0 Scatter > 6% → 無限 retrigger | Scatter **≤ 3%** |
| RTP 爆炸 (>200%) | 模擬完成但 RTP 異常高 | FR0 Wild > 6% + multiplier | Wild **≤ 3%**（帶乘數） |
| 無限 Tumble | 單轉耗時 > 10 秒 | 任何符號 > 13% on 7x7 | 所有符號 **≤ 13%** |
| Bonus RTP 太低 | bonus RTP < 50%（目標 96%） | mult_values 加權均值太低 | avg_mult **≥ 5x** |
| LUT 被覆蓋 | 優化後 RTP 回到原始值 | run.py analysis 覆蓋 publish_files/ | **先 optimize 再 analysis** |
| 缺少極端獎金 | LUT 沒有 5000x+ 條目 | 缺少 wincap distribution | 加入 **quota=0.05** wincap |
| Payout 格式錯誤 | 格式驗證 AssertionError | paytable 值非 0.1 的倍數 | 所有賠率 **% 0.1 == 0** |

> 使用 `/optimize-rtp` skill 可自動檢測並修復上述問題。

---

## 各遊戲類型對照表

| 限制 | Cluster | Lines | Ways | Scatter |
|------|---------|-------|------|---------|
| 推薦輪帶長度 | 100-150 | 200-220 | 150-200 | 120-180 |
| 單一符號上限 | **13%** | 20% | 18% | 15% |
| 最大連續同符號 | **2** | 3 | 3 | **2** |
| H1 每軸出現次數 | 5-10 | 3-4 | 3-5 | 3-4 |
| H2-H4 每軸 | 7-14 | 4-7 | 4-7 | 5-8 |
| L1-L5 每軸 | 12-20 | 8-18 | 10-18 | 10-16 |
| Wild 每軸 | 3-5 (2-3%) | 2-3 | 2-4 | 2-3 |
| Scatter 每軸 | 3-4 (2-3%) | 3-4 | 3-4 | 3-4 |

---

## 真實案例：為何 28.6% 導致無限 Tumble

### dragon-feast（7x7 cluster）原始輪帶問題

**問題**：L5 符號在 100 停止位的輪帶上出現 ~29 次 = **28.6%**

**計算**：
```
7x7 版面 = 49 格
每次轉動，L5 期望出現: 49 × 0.286 = 14 個
SDK cluster 演算法: 5 個相鄰即算贏
14 個 L5 散佈在 49 格上 → 幾乎必定形成多個大型 cluster
```

**結果**：
1. 14 個 L5 形成 2-3 個大型 cluster
2. 消除後，空位由輪帶上方掉落新符號填補
3. 新符號中 L5 仍佔 28.6%，又形成新 cluster
4. 重複步驟 2-3 → 永遠不停止

**修復後**：所有符號控制在 ≤ 13%
```
最大出現次數: 49 × 0.13 = 6.37 個
6 個 L5 散佈在 49 格上 → 不太可能形成 5 個相鄰的 cluster
偶爾形成也能正常消除完畢
```

---

## 輪帶生成注意事項

### 通用規則

1. **不要在同一軸上連續放置 3+ 個相同符號**（tumble 類遊戲限制為 2）
2. **Wild 和 Scatter 的位置要分散**，避免集中在特定軸或區域
3. **高賠符號比低賠符號稀少**，這是基本的賠率設計原則
4. **每個軸的分佈應獨立設計**，不要用完全相同的分佈

### Cluster 專屬

- 7 個軸的分佈要**略有差異**，避免相同位置總是出現相同符號
- Wild 通常限制在第 2-6 軸（不在最外側軸）
- Scatter 每軸 3-4 個，確保 basegame 中 4+ scatter 的觸發率合理

### Lines 專屬

- 第 1 軸和第 5 軸（頭尾）可以稍微不同
- Wild 通常限制在第 2-4 軸（中間軸）
- 高賠符號可以稍微集中在中間軸以增加線贏分機率

### Scatter 專屬

- 乘數符號（M）分佈要均勻，不要集中
- Scatter 的觸發率需考慮 tumble 後可能掉落新的 Scatter

---

## 驗證清單（每次生成輪帶後必做）

### 1. 符號佔比檢查

統計每個符號在每軸的出現次數和佔比：
```bash
python -c "
import csv
from collections import Counter
for reel_file in ['BR0.csv', 'FR0.csv']:
    print(f'=== {reel_file} ===')
    with open(f'reels/{reel_file}') as f:
        rows = list(csv.reader(f))
    num_reels = len(rows[0])
    for reel_idx in range(num_reels):
        syms = [row[reel_idx] for row in rows if row]
        total = len(syms)
        print(f'Reel {reel_idx+1} ({total} stops):')
        for sym, count in Counter(syms).most_common():
            pct = count/total*100
            flag = ' ⚠️' if pct > 13 else ''
            print(f'  {sym}: {count} ({pct:.1f}%){flag}')
"
```

### 2. 連續符號檢查

確認沒有 3+ 連續相同符號（tumble 類遊戲）：
```bash
python -c "
import csv
for reel_file in ['BR0.csv', 'FR0.csv']:
    with open(f'reels/{reel_file}') as f:
        rows = list(csv.reader(f))
    num_reels = len(rows[0])
    for reel_idx in range(num_reels):
        syms = [row[reel_idx] for row in rows if row]
        for i in range(len(syms)-2):
            if syms[i] == syms[i+1] == syms[i+2]:
                print(f'⚠️ {reel_file} Reel {reel_idx+1} row {i+1}: {syms[i]} x3')
"
```

### 3. 期望出現數計算

```bash
python -c "
board_positions = 49  # 修改為實際版面格數
min_threshold = 5     # cluster/scatter 的最小贏分門檻
import csv
from collections import Counter
with open('reels/BR0.csv') as f:
    rows = list(csv.reader(f))
reel_length = len(rows)
# 用第一軸估算
syms = [row[0] for row in rows if row]
for sym, count in Counter(syms).most_common():
    expected = board_positions * (count / reel_length)
    flag = ' ⚠️ DANGER' if expected >= min_threshold else ''
    print(f'{sym}: expected {expected:.1f} on board{flag}')
"
```

### 4. Wild/Scatter 位置限制

確認符合企劃書規定（如 Wild 僅在第 2-6 軸）

### 5. 快速模擬測試

跑 100 次模擬確認不會卡住：
```bash
# 在 run.py 中臨時設定 simulations = 100
python run.py
# 應在數秒內完成。如果超過 30 秒 → 輪帶有問題
```
