# 賠率表格式、捲軸範例、分佈條件

> 此檔案包含 init-math Step 5（賠率表格式）、Step 6（捲軸生成）、及分佈條件的詳細模板。

## 目錄

- [賠率表格式](#賠率表格式)
  - [Lines/Ways 類型](#lineswaysscatter-類型)
  - [Cluster 類型](#cluster-類型)
  - [賠付線定義（Lines 專用）](#賠付線定義lines-專用)
  - [特殊符號設定](#特殊符號設定)
  - [免費旋轉觸發](#免費旋轉觸發)
  - [投注模式](#投注模式)
- [分佈條件（Distribution Conditions）](#分佈條件distribution-conditions)
  - [Wincap Distribution](#wincap-distribution必要)
  - [Bonus RTP 數學驗證](#bonus-rtp-數學驗證)
  - [乘數值配置](#乘數值配置mult_values)
  - [scatter_triggers 權重](#scatter_triggers-權重)
- [捲軸檔案生成](#捲軸檔案生成)
  - [7x7 Cluster 類型](#7x7-cluster-類型br0csv)
  - [6x5 Scatter 類型](#6x5-scatter-類型br0csv)
  - [5x3 Lines 類型](#5x3-lines-類型br0csv)

---

## 賠率表格式

> RGS Payout 約束：所有賠率值必須是 **0.1 的整數倍**（例如 0.2, 0.3, 0.5, 0.8, 1.5）。
> SDK 會將賠率 x 100 轉成 LUT 的「cents」格式，RGS 要求 cents 值必須是 10 的整數倍。
> 不合法的值如 `0.25`（-> 25 cents）、`0.15`（-> 15 cents）會導致格式驗證失敗。

### Lines/Ways/Scatter 類型

```python
self.paytable = {
    # Wild
    (5, "W"): {5連線賠率},

    # 高賠符號
    (5, "H1"): {5連}, (4, "H1"): {4連}, (3, "H1"): {3連},
    (5, "H2"): {5連}, (4, "H2"): {4連}, (3, "H2"): {3連},
    # ...

    # 低賠符號
    (5, "L1"): {5連}, (4, "L1"): {4連}, (3, "L1"): {3連},
    # ...
}
```

### Cluster 類型

Cluster 需要將賠率區間展開為連續數值：

```python
self.paytable = {
    # 高賠符號 - 展開區間
    # 5+ 對應 5,6,7
    (5, "H1"): {5+賠率}, (6, "H1"): {5+賠率}, (7, "H1"): {5+賠率},
    # 8+ 對應 8,9,10,11
    (8, "H1"): {8+賠率}, (9, "H1"): {8+賠率}, (10, "H1"): {8+賠率}, (11, "H1"): {8+賠率},
    # 12+ 對應 12,13,14
    (12, "H1"): {12+賠率}, (13, "H1"): {12+賠率}, (14, "H1"): {12+賠率},
    # 15+ 對應 15,16,17,18,19
    (15, "H1"): {15+賠率}, (16, "H1"): {15+賠率}, (17, "H1"): {15+賠率},
    (18, "H1"): {15+賠率}, (19, "H1"): {15+賠率},
    # 20+ 對應 20-49
    (20, "H1"): {20+賠率}, (21, "H1"): {20+賠率}, # ... 到 (49, "H1")
    # ... 其他符號
}
```

使用 for-range 簡化寫法（推薦）：
```python
for n in range(5, 8):   self.paytable[(n, "H1")] = 2
for n in range(8, 12):  self.paytable[(n, "H1")] = 5
for n in range(12, 15): self.paytable[(n, "H1")] = 15
for n in range(15, 20): self.paytable[(n, "H1")] = 50
for n in range(20, 50): self.paytable[(n, "H1")] = 200
```

### 賠付線定義（Lines 專用）

Lines 類型需要定義 paylines，保留模板中的 20 線定義，或根據企劃書調整。

### 特殊符號設定

```python
self.special_symbols = {
    "wild": ["W"],
    "scatter": ["S"],
    "multiplier": ["W"],  # 如果 Wild 有乘數功能
}
```

### 免費旋轉觸發

```python
self.freespin_triggers = {
    self.basegame_type: {Scatter數量: 免費旋轉次數, ...},
    self.freegame_type: {重觸發Scatter數量: 追加次數, ...},
}
```

Cluster 7x7 版面範例：
```python
self.freespin_triggers = {
    self.basegame_type: {4: 10, 5: 15, 6: 20, 7: 25},
    self.freegame_type: {3: 5, 4: 10, 5: 15},
}
```

### 投注模式

修改 BetMode 中的 cost 參數：
```python
BetMode(
    name="bonus",
    cost={購買獎勵費用倍數},  # 例如 80.0
    # ...
)
```

---

## 分佈條件（Distribution Conditions）

> 以下設定直接影響模擬能否正常運行和 RTP 是否合理。

### Wincap Distribution（必要）

Base 和 Bonus 模式**都必須包含 wincap distribution**。
缺少 wincap 會導致 LUT 無法覆蓋極端贏分，優化結果不完整。

**quota 建議 0.1%（0.001）**，搭配 WCAP 專用輪帶。
過高的 quota（如 5%）會產生過多 wincap 事件（1e5 × 5% = 5,000 個），
每個都需大量重試才能自然達到 wincap，導致模擬耗時不切實際。
詳見 `/optimize-rtp` Step 5c wincap fallback。

```python
Distribution(
    criteria="wincap",
    quota=0.001,  # 0.1% — 不要用 0.05（5%），會導致模擬耗時過長
    win_criteria=mode_maxwins["base"],  # 或 "bonus"
    conditions=wincap_condition,
),
```

### Bonus RTP 數學驗證

設定前，先計算 bonus 模式需要的平均 session payout：
```
avg_session_payout = bonus_cost x target_rtp
```
例如：cost=80, rtp=0.96 -> avg_session_payout = 76.8x

### 乘數值配置（mult_values）

freegame 的 `mult_values` 加權均值建議 >= 5x：
```python
# 加權均值 = (2x40 + 3x30 + 5x15 + 10x10 + 25x4 + 50x1) / (40+30+15+10+4+1) = 5.0x
"mult_values": {
    self.freegame_type: {2: 40, 3: 30, 5: 15, 10: 10, 25: 4, 50: 1},
}
```

### scatter_triggers 權重

權重需與輪帶中的 scatter 密度匹配。
如果輪帶 scatter 密度很低（2%），高 scatter 數量（6, 7）的權重應更低：
```python
"scatter_triggers": {4: 40, 5: 25, 6: 10, 7: 3},
```

---

## 捲軸檔案生成

### 7x7 Cluster 類型（BR0.csv）

```csv
L5,L3,L4,L2,H3,L1,L5
H1,L4,L5,L3,L2,H2,L4
L3,L5,L1,H4,L4,L3,L2
S,L2,L4,L1,H3,L5,S
L4,H3,L2,L5,L1,L4,H4
L2,L1,H2,L3,W,L2,L5
H4,L5,L3,L4,L2,H1,L3
...
```

符號分佈原則（每軸約 100 個符號）：

| 符號 | 每軸次數 | 備註 |
|------|---------|------|
| H1 | 3-4 | 最高賠付 |
| H2 | 4-5 | |
| H3 | 5-6 | |
| H4 | 6-7 | |
| L1 | 8-10 | |
| L2 | 10-12 | |
| L3 | 12-14 | |
| L4 | 13-15 | |
| L5 | 15-18 | 最低賠付，最多 |
| W | 2-3 | 僅第 2-6 軸 |
| S | 3-4 | |

### 6x5 Scatter 類型（BR0.csv）

```csv
H3,L1,L4,H4,L2,L3
L2,H2,L1,L3,H4,L4
L4,L3,H1,L2,L1,H3
S,L4,L2,H3,L3,L1
L1,H4,L3,L4,L2,H2
L3,L2,H3,L1,W,L4
...
```

符號分佈原則（每軸約 128 個停止位，低賠符號有梯度）：

| 符號 | 每軸次數 | 佔比 | 備註 |
|------|---------|------|------|
| H1 | 6 | 4.3% | 最高賠付 |
| H2 | 10 | 7.1% | |
| H3 | 14 | 10.0% | |
| H4 | 17 | 12.1% | |
| L1 | 20 | 14.3% | 低賠符號需有梯度 |
| L2 | 19 | 13.6% | 不要全部頂到 15% 上限 |
| L3 | 18 | 12.9% | |
| L4 | 17 | 12.1% | |
| W | 3 | 2.1% | 各軸均勻分佈 |
| S | 4 | 2.9% | 各軸均勻分佈 |

**WCAP 輪帶**（wincap 模擬專用，可選）：
- 用於 wincap distribution 的 `reel_weights`（如 `"WCAP": 5`）
- 高密度 H1（~14%）、W（~10%）、S（~10%）
- 不受 15% 上限約束（僅用於模擬，不影響正式遊戲）

### 5x3 Lines 類型（BR0.csv）

```csv
L1,H3,L5,L4,L3
H1,H3,H4,L2,L5
S,S,S,S,S
L5,L4,L2,L1,H2
...
```

符號分佈原則（每軸約 220 個停止位置）：

| 符號 | 每軸次數 | 備註 |
|------|---------|------|
| H1 | 3-4 | 最高賠付 |
| H2-H4 | 4-7 | |
| L1-L5 | 8-18 | L5 最多 |
| W | 2-3 | 僅中間軸 |
| S | 3-4 | |
