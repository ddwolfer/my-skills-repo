# game_config.py 完整生成範例

> 此檔案包含各遊戲類型的 game_config.py 完整範例，供 init-math Step 5 參考。

## 目錄

- [Cluster 類型（Dragon Feast）](#cluster-類型dragon-feast)
- [Scatter 類型（Pharaohs Cascade）](#scatter-類型pharaohs-cascade)
- [Lines 類型（Odin's Reign）](#lines-類型odins-reign)

---

## Cluster 類型（Dragon Feast）

根據 dragon-feast 企劃書：

```python
# ========================================
# 第一部分：遊戲基本資訊
# ========================================

self.working_name = "Dragon Feast"
self.wincap = 10000.0
self.win_type = "cluster"
self.rtp = 0.9600

# ========================================
# 第二部分：遊戲版面尺寸
# ========================================

self.num_reels = 7
self.num_rows = [7] * self.num_reels  # 7x7 grid

# ========================================
# 第三部分：賠率表（Cluster 格式）
# ========================================

# 展開區間：5+ → 5,6,7 | 8+ → 8-11 | 12+ → 12-14 | 15+ → 15-19 | 20+ → 20-49
self.paytable = {}

# H1 龍 Dragon
for n in range(5, 8):   self.paytable[(n, "H1")] = 2
for n in range(8, 12):  self.paytable[(n, "H1")] = 5
for n in range(12, 15): self.paytable[(n, "H1")] = 15
for n in range(15, 20): self.paytable[(n, "H1")] = 50
for n in range(20, 50): self.paytable[(n, "H1")] = 200

# H2 鳳 Phoenix
for n in range(5, 8):   self.paytable[(n, "H2")] = 1.5
for n in range(8, 12):  self.paytable[(n, "H2")] = 4
for n in range(12, 15): self.paytable[(n, "H2")] = 12
for n in range(15, 20): self.paytable[(n, "H2")] = 40
for n in range(20, 50): self.paytable[(n, "H2")] = 150

# H3 金魚 Goldfish
for n in range(5, 8):   self.paytable[(n, "H3")] = 1
for n in range(8, 12):  self.paytable[(n, "H3")] = 3
for n in range(12, 15): self.paytable[(n, "H3")] = 10
for n in range(15, 20): self.paytable[(n, "H3")] = 30
for n in range(20, 50): self.paytable[(n, "H3")] = 100

# H4 元寶 Gold Ingot
for n in range(5, 8):   self.paytable[(n, "H4")] = 0.8
for n in range(8, 12):  self.paytable[(n, "H4")] = 2.5
for n in range(12, 15): self.paytable[(n, "H4")] = 8
for n in range(15, 20): self.paytable[(n, "H4")] = 25
for n in range(20, 50): self.paytable[(n, "H4")] = 80

# L1 桃 Peach
for n in range(5, 8):   self.paytable[(n, "L1")] = 0.5
for n in range(8, 12):  self.paytable[(n, "L1")] = 1.5
for n in range(12, 15): self.paytable[(n, "L1")] = 5
for n in range(15, 20): self.paytable[(n, "L1")] = 15
for n in range(20, 50): self.paytable[(n, "L1")] = 50

# L2 李 Plum
for n in range(5, 8):   self.paytable[(n, "L2")] = 0.4
for n in range(8, 12):  self.paytable[(n, "L2")] = 1.2
for n in range(12, 15): self.paytable[(n, "L2")] = 4
for n in range(15, 20): self.paytable[(n, "L2")] = 12
for n in range(20, 50): self.paytable[(n, "L2")] = 40

# L3 梅 Plum Blossom
for n in range(5, 8):   self.paytable[(n, "L3")] = 0.3
for n in range(8, 12):  self.paytable[(n, "L3")] = 1
for n in range(12, 15): self.paytable[(n, "L3")] = 3
for n in range(15, 20): self.paytable[(n, "L3")] = 10
for n in range(20, 50): self.paytable[(n, "L3")] = 30

# L4 竹 Bamboo（注意：0.25 不合法，需用 0.3）
for n in range(5, 8):   self.paytable[(n, "L4")] = 0.3
for n in range(8, 12):  self.paytable[(n, "L4")] = 0.8
for n in range(12, 15): self.paytable[(n, "L4")] = 2.5
for n in range(15, 20): self.paytable[(n, "L4")] = 8
for n in range(20, 50): self.paytable[(n, "L4")] = 25

# L5 菊 Chrysanthemum
for n in range(5, 8):   self.paytable[(n, "L5")] = 0.2
for n in range(8, 12):  self.paytable[(n, "L5")] = 0.6
for n in range(12, 15): self.paytable[(n, "L5")] = 2
for n in range(15, 20): self.paytable[(n, "L5")] = 6
for n in range(20, 50): self.paytable[(n, "L5")] = 20

# ========================================
# 第五部分：特殊符號
# ========================================

self.special_symbols = {
    "wild": ["W"],
    "scatter": ["S"],
    "multiplier": ["W"],
}

# ========================================
# 第六部分：免費旋轉觸發條件
# ========================================

self.freespin_triggers = {
    self.basegame_type: {4: 10, 5: 15, 6: 20, 7: 25},
    self.freegame_type: {3: 5, 4: 10, 5: 15},
}

# ========================================
# 第九部分：投注模式
# ========================================

# bonus 模式的 cost 改為 80.0
BetMode(
    name="bonus",
    cost=80.0,
    # ... 其他參數保持不變
)
```

---

## Scatter 類型（Pharaohs Cascade）

根據 pharaohs-cascade 企劃書（6×5 Pay Anywhere + Tumble + 全域乘數 + Wild 乘數）：

```python
# ========================================
# 第一部分：遊戲基本資訊
# ========================================

self.working_name = "Pharaohs Cascade"
self.wincap = 10000.0
self.win_type = "scatter"
self.rtp = 0.9600

# ========================================
# 第二部分：遊戲版面尺寸
# ========================================

self.num_reels = 6
self.num_rows = [5] * self.num_reels  # 6x5

# ========================================
# 第三部分：賠率表（Scatter — tuple range 格式）
# ========================================

# 使用 convert_range_table() 將 (min, max) 區間展開為逐一 count
t1 = (8, 9)      # 8-9 個
t2 = (10, 11)    # 10-11 個
t3 = (12, 14)    # 12-14 個
t4 = (15, 19)    # 15-19 個
t5 = (20, 24)    # 20-24 個
t6 = (25, 29)    # 25-29 個
t7 = (30, 30)    # 30 個（全滿）

pay_group = {
    (t1, "H1"): 2.0,    (t2, "H1"): 5.0,    (t3, "H1"): 10.0,
    (t4, "H1"): 25.0,   (t5, "H1"): 50.0,   (t6, "H1"): 100.0,   (t7, "H1"): 500.0,
    (t1, "H2"): 1.5,    (t2, "H2"): 3.0,    (t3, "H2"): 8.0,
    (t4, "H2"): 20.0,   (t5, "H2"): 40.0,   (t6, "H2"): 80.0,    (t7, "H2"): 400.0,
    # H3, H4, L1-L4 同理...
}
self.paytable = self.convert_range_table(pay_group)

# ========================================
# 第四部分：特殊符號（含 Wild 乘數）
# ========================================

self.special_symbols = {
    "wild": ["W"],
    "scatter": ["S"],
    "multiplier": ["W"],  # 免費旋轉中 W 攜帶隨機乘數
}

# Wild 乘數權重（免費旋轉時賦值）
self.padding_symbol_values = {
    "W": {"multiplier": {2: 50, 3: 30, 5: 15, 10: 5}}
}

# ========================================
# 第五部分：全域乘數與 Session 保護
# ========================================

self.mult_cap = 64          # 全域乘數封頂
self.max_free_spins = 30    # 免費旋轉硬上限

# ========================================
# 第六部分：免費旋轉觸發
# ========================================

self.freespin_triggers = {
    self.basegame_type: {3: 8, 4: 12, 5: 15, 6: 20},
    self.freegame_type: {3: 5, 4: 8, 5: 12, 6: 15},
}

# ========================================
# 第八部分：分佈條件（含 mult_values）
# ========================================

freegame_condition = {
    "reel_weights": {
        self.basegame_type: {"BR0": 1},
        self.freegame_type: {"FR0": 1},
    },
    "scatter_triggers": {3: 50, 4: 20, 5: 5, 6: 1},
    "mult_values": {
        self.basegame_type: {1: 1},                      # 基礎遊戲 W 固定 ×1
        self.freegame_type: {2: 50, 3: 30, 5: 15, 10: 5},  # 免費旋轉隨機乘數
    },
    "force_wincap": False,
    "force_freegame": True,
}

wincap_condition = {
    "reel_weights": {
        self.basegame_type: {"BR0": 1},
        self.freegame_type: {"FR0": 1, "WCAP": 5},  # WCAP 輪帶加速 wincap
    },
    "mult_values": {
        self.basegame_type: {1: 1},
        self.freegame_type: {2: 10, 3: 20, 5: 50, 10: 100},  # 偏重高乘數
    },
    "scatter_triggers": {5: 1, 6: 2},
    "force_wincap": True,
    "force_freegame": True,
}

# ========================================
# 第九部分：投注模式
# ========================================

# base: cost=1.0, bonus: cost=80.0
# wincap quota=0.001（不要用 0.05，會導致模擬耗時過長）
```

---

## Lines 類型（Odin's Reign）

根據 odin's-reign 企劃書：

```python
# 第一部分
self.working_name = "Odin's Reign"
self.wincap = 5000.0
self.win_type = "lines"
self.rtp = 0.9600

# 第二部分
self.num_reels = 5
self.num_rows = [3] * self.num_reels  # 5x3

# 第三部分：Lines 格式賠率表
self.paytable = {
    (5, "W"): 50,

    (5, "H1"): 50,   (4, "H1"): 20,   (3, "H1"): 10,
    (5, "H2"): 30,   (4, "H2"): 15,   (3, "H2"): 5,
    (5, "H3"): 20,   (4, "H3"): 10,   (3, "H3"): 3,
    (5, "H4"): 15,   (4, "H4"): 5,    (3, "H4"): 2,

    (5, "L1"): 5,    (4, "L1"): 1,    (3, "L1"): 0.5,
    (5, "L2"): 3,    (4, "L2"): 0.7,  (3, "L2"): 0.3,
    (5, "L3"): 3,    (4, "L3"): 0.7,  (3, "L3"): 0.3,
    (5, "L4"): 2,    (4, "L4"): 0.5,  (3, "L4"): 0.2,
    (5, "L5"): 1,    (4, "L5"): 0.3,  (3, "L5"): 0.1,
}

# 第四部分：25 條賠付線（如需調整）
self.paylines = {
    1:  [1, 1, 1, 1, 1],
    2:  [0, 0, 0, 0, 0],
    # ... 根據企劃書設定
}

# 第六部分
self.freespin_triggers = {
    self.basegame_type: {3: 10, 4: 15, 5: 20},
    self.freegame_type: {3: 5, 4: 10, 5: 15},
}
```
