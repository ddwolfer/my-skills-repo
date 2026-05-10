---
name: investigate-rtp
description: 調查線上遊戲的 RTP 異常。分析樣本量是否足夠、比對模型設定、判斷統計波動 vs 真實 bug。當使用者提到 RTP 異常、回報率偏高偏低、Bonus mode 虧損、線上數據和模擬不符、玩家贏太多/太少、profit 異常時都應觸發。使用方式：/investigate-rtp models/dragon-feast "BASE: 56695 bets RTP 93.19%, BONUS: 882 bets RTP 122.23%"
---

# investigate-rtp

調查線上遊戲的 RTP 異常，區分「正常統計波動」和「數學模型 bug」。

## 參數

- `$ARGUMENTS`: 遊戲模型目錄 + 線上統計數據摘要
  - 例如：`models/dragon-feast "BASE: 56695 bets RTP 93.19%, BONUS: 882 bets RTP 122.23%"`

---

## 執行流程

### Step 1: 解析線上統計數據

從 `$ARGUMENTS` 提取每個 bet mode 的：
- **mode 名稱**（base / bonus）
- **bet 數量**（樣本量）
- **Effective RTP**
- **Normalized RTP**（如有）
- **Profit/Loss**（如有）

---

### Step 2: 樣本量充足性判斷（最重要的第一步）

**判斷標準：**

| 遊戲類型 | 最低樣本量 | 說明 |
|----------|-----------|------|
| 低波動 slot（base mode） | 10,000 spins | 收斂較快 |
| 高波動 slot（base mode） | 50,000 spins | 需要更多 |
| Buy Bonus（高波動 FS） | 100,000+ spins | 極端 payout 影響大 |

**快速判斷公式：**
```
若 N < 5,000 → 「樣本嚴重不足，任何 RTP 偏差都是正常波動」
若 N < 50,000 → 「樣本量偏低，RTP 可能有 ±10% 波動」
若 N > 100,000 → 「樣本量足夠，偏差 > 2% 需要調查」
```

**單個 big win 的影響計算：**
```python
# 假設一次 max_win (10000x) payout 的影響
impact = (max_win * base_bet * cost_multiplier) / (total_bets * base_bet * cost_multiplier) * 100
# = max_win / total_bets * 100 (% RTP)
```

如果樣本量不足，直接輸出結論：「正常統計波動，非 bug。建議繼續觀察到 N=X 後再評估。」

---

### Step 3: 對比 BASE mode 驗證模型正確性

如果 BASE mode 樣本量足夠（>10,000）且 RTP 接近目標（±1%），這強烈暗示模型本身是正確的。

- BASE RTP 正常 + BONUS RTP 異常 + BONUS 樣本少 → 幾乎確定是波動
- BASE RTP 也異常 + 大樣本 → 可能真的有 bug，進入 Step 4

---

### Step 4: 檢查數學模型設定（僅在 Step 2-3 無法排除 bug 時）

讀取以下檔案：

| 檔案 | 檢查項目 |
|------|---------|
| `game_config.py` | bet_modes 的 cost/rtp/max_win、distribution quotas、wincap 值 |
| `game_optimization.py` | fence targets 的 rtp 加總是否 = 目標 RTP |
| `gamestate.py` | run_freespin() 的 wincap_triggered 檢查 |
| `game_override.py` | reset_book() 是否清理所有持久狀態 |

**常見 bug 模式：**
1. reset_book() 漏清狀態 → FS 乘數洩漏到 basegame → RTP 虛高
2. scatter suppression 失效 → FS 無限 retrigger → 偶發超高 payout
3. wincap 未正確觸發 → 少數 round 的 payout 超過上限
4. distribution quota 設太高（如 wincap=0.05）→ 優化算法難以收斂

---

### Step 5: 檢查 LUT 權重（僅在本地有 library/ 時）

```bash
# 檢查 bonus mode LUT 的加權平均 payout（= 理論 RTP × cost）
awk -F', ' '{sw+=$2*$3; w+=$2} END{printf "Weighted avg payout: %.2f\n", sw/w}' \
  library/lookup_tables/lookUpTable_bonus_0.csv

# 檢查極端 payout 的權重是否合理
sort -t', ' -k3 -n -r library/lookup_tables/lookUpTable_bonus_0.csv | head -20
```

---

### Step 6: 輸出調查報告

格式：
```
🔍 RTP 異常調查報告 — {game_name}

## 結論：[正常波動 / 需要關注 / 確認 bug]

## 數據分析
- {mode}: {N} bets, RTP {X}%, 樣本充足性: [不足/偏低/足夠]
- 單次 max_win 影響: ±{Y}% RTP

## 模型檢查（如適用）
- game_config.py: [OK / 問題描述]
- game_optimization.py: [OK / 問題描述]
- reset_book(): [OK / 問題描述]

## 建議行動
- [繼續觀察到 N=X / 修改模型 / 重新模擬]

## 監控門檻
- {N1} rounds 且 RTP > {X1}%：關注
- {N2} rounds 且 RTP > {X2}%：調查
- {N3} rounds 且 RTP > {X3}%：bug
```
