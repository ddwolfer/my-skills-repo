---
name: propagate-spec-change
description: 當 SPEC.md 修訂後，自動掃描下游受影響的檔案（math model / 前端 config / stateMeta / i18n / bookEvent handler / Art 素材清單），分類影響程度（Still Valid / Needs Review / Likely Broken），產出 impact report 給 Planner 與 Supervisor 分配工作。當使用者提到 SPEC 版本升級、SPEC 改版影響面、v2 → v3 哪些要改、Forge of Fortune SPEC 再改一版、SPEC diff 衝擊評估、改規格要動哪些檔、或 SPEC 升版後工作拆分時都應觸發。使用方式：/propagate-spec-change specs/06-forge-of-fortune 或 /propagate-spec-change specs/06-forge-of-fortune HEAD~2
---

# propagate-spec-change

When a `SPEC.md` is revised, scan downstream artifacts (math model, front-end config, stateMeta, i18n, bookEvent handlers, asset manifests) to identify what the change invalidates. Produce an **impact report** with per-file classification, then hand off to Planner + Supervisor for task allocation.

**對應鐵律**：`Spec Changes Must Go Through Planner First` — 本 skill **只報告 impact，不修改任何下游**。修改皆由 Planner 討論 → Supervisor 審核 → 派 Client / Server / Art 執行。

## 參數

- `$ARGUMENTS`: `<specPath> [<baseRef>]`
  - `specPath`: SPEC 檔案路徑或 spec 目錄（如 `specs/06-forge-of-fortune` 或 `specs/06-forge-of-fortune/SPEC.md`）
  - `baseRef` (可選): 要比對的 base commit（預設 `HEAD~1`，也可用 `v2.0..v3.1` range 或 commit sha）

## 執行流程

### Step 1: 解析參數 + 定位 SPEC

從 `$ARGUMENTS` 解析 `specPath` + `baseRef`：
- 若 `specPath` 是目錄 → 拼上 `/SPEC.md`
- 驗證檔案存在 + 在 git 控管下

從 SPEC 路徑推導 `gameId`（目錄末段，若 match `^\d+-(.+)$` 則剝前綴）→ 用 Glob 定位下游（注意 `games/` `models/` `Art/` 也有 `NN-` 前綴）：
- `mathPath`: Glob `models/*<gameId>/game_config.py`
- `mathLibDir`: 同目錄的 `gamestate/`、`library/`
- `gamePath`: Glob `games/*<gameId>`
- `configPath`: `<gamePath>/src/game/config.ts`
- `metaPath`: `<gamePath>/src/game/stateMeta.ts`
- `i18nDir`: `<gamePath>/src/game/i18n/`
- `eventHandlerDir`: `<gamePath>/src/game/eventHandlers/`、`<gamePath>/src/game/stateMachines/`
- `artDir`: Glob `Art/*<gameId>/`、以及 `specs/*<gameId>/ASSETS_MANIFEST.md`（若存在）

若某 Glob 無 match，標記 `missing`，照常跑其他 scan，在 report 中註記該目錄缺失。

---

### Step 2: 偵測 SPEC 變更

```bash
git diff <baseRef> -- <specPath>
```

若 diff 為空 → 早退：「No SPEC change detected between <baseRef> and HEAD.」

把 diff 分段解析，標記：
- **Added sections** — 新增的 `^##` 或 `^###` heading + 其內容
- **Removed sections** — 刪除的 heading
- **Modified tables** — `| ... |` 行的增刪改（常見於 paytable / betMode / symbol 表）
- **Modified rules** — 一般文字段落的變更

抽出具體變更項（entity 粒度）：
```
changes = [
  { kind: "paytable",   symbol: "H1", field: "mult_5", old: 20, new: 30 },
  { kind: "betMode",    name: "BONUS", field: "costMultiplier", old: 80, new: 100 },
  { kind: "rule_added", section: "§ 21 Ritual Narrative", summary: "新增三幕式敘事" },
  { kind: "rule_removed", section: "§ 5.9 Loss Juice Outro", summary: "移除 outro 動畫" },
  ...
]
```

---

### Step 3: 下游 impact 掃描

對每個 `change`，在下游檔案 grep 對應 reference，分類影響：

#### 影響分類
- ✅ **Still Valid** — 下游沒 reference 到這個 entity，不受影響
- ⚠️ **Needs Review** — 下游有 reference 但改動未必直接破壞（例如 paytable 改值，下游動態讀取可能自動生效）
- 🔴 **Likely Broken** — 下游 hard-code 對應值或與新 SPEC 衝突（例如 costMultiplier 改 80 → 100，stateMeta hard-code 80 就破了）

#### 掃描 targets（依 change 類型挑）

| change.kind | 要掃的 downstream files | grep pattern 範例 |
|-------------|--------------------------|-------------------|
| paytable    | mathPath, configPath, i18nDir | `<symbol>` + `payout|paytable|mult` |
| betMode     | mathPath, configPath, metaPath, i18nDir | `<betMode>` + `costMultiplier\|rtp\|maxWin\|displayName` |
| rule_added  | eventHandlerDir, gamePath/src/components, artDir | 新章節提到的關鍵詞 |
| rule_removed | eventHandlerDir, gamePath/src/components | 被刪除章節提過的 identifier |
| asset_added | artDir, `<gamePath>/static/assets/` | 新素材名 |

對每個 hit，用 `Read` 打開具體 section 確認是否真的受影響（避免假陽性）。

---

### Step 4: 檢查已存在的「decision log」

若專案有下列其中之一，視為 ADR（Architecture Decision Record）：
- `specs/<gameId>/DECISIONS.md`
- `specs/<gameId>/ADR/*.md`
- `specs/_shared/*_ANALYSIS.md`（跨遊戲共用原則）

掃這些檔找提到 SPEC 變更對象的 ADR，加入 impact report：
- ADR 假設跟 SPEC 新版相符 → ✅ Still Valid
- ADR 假設與 SPEC 改動有交集 → ⚠️ Needs Review
- ADR 結論明顯被 SPEC 新版推翻 → 🔴 **Likely Superseded**（建議附 "Superseded by SPEC v<new>" note）

---

### Step 5: 產出 impact report

輸出路徑：`specs/<gameId>/impact/<YYYY-MM-DD>-<baseRef>-to-HEAD.md`

報告結構：

```markdown
# SPEC Change Impact Report — <gameId>
Base: <baseRef> (<sha_short>) 
Head: HEAD (<sha_short>)
Generated: YYYY-MM-DD HH:MM

---

## SPEC Changes Summary

N changes detected:
- 📝 Added: N sections / N rules
- 🗑️ Removed: N sections / N rules
- ✏️ Modified: N table rows / N values

### Changes list
1. [paytable] H1 mult_5: 20 → 30
2. [betMode] BONUS costMultiplier: 80 → 100
3. [rule_added] § 21 Ritual Narrative — 新增三幕式敘事
...

---

## Downstream Impact

### 🔴 Likely Broken (N)

#### models/<gameId>/game_config.py:L145
```python
PAYTABLE["H1"] = {3: 2, 4: 5, 5: 20}  # ← 20, SPEC 已改 30
```
Related change: #1
**Owner suggestion**: Server（math），須同步改 PAYTABLE 值 → 重跑 `/optimize-rtp`

#### games/<gameId>/src/game/stateMeta.ts:L22
```typescript
BONUS: { costMultiplier: 80 }  // ← 80, SPEC 已改 100
```
Related change: #2
**Owner suggestion**: Client

---

### ⚠️ Needs Review (N)

#### games/<gameId>/src/game/i18n/en.ts
```
paytable.h1.desc: "Up to 20× your play"
```
Related change: #1
**Review note**: 文案可能提到 20 倍數；需 Planner 決定是否同步改 30 倍文案，或維持象徵性描述。

#### specs/_shared/STAR_RATING_ANALYSIS.md
Mentions Ritual Narrative as star-rating factor. § 21 新增可能影響星級評估 — Planner 請 review。

---

### ✅ Still Valid (N)

Files referencing affected entities but unaffected by this change:
- `games/<gameId>/src/components/ReelsLayout.svelte` — 只引用 H1 asset key，不涉 multiplier
- ...

---

### ADR / Decision Impact

#### 🔴 Likely Superseded
- `specs/<gameId>/DECISIONS.md#adr-003-bonus-pricing`
  - ADR assumed `BONUS.costMultiplier = 80`; 新 SPEC 已改 100
  - Suggested: append "Superseded by SPEC change on YYYY-MM-DD; see new pricing rationale"

---

## Recommended Task Allocation

| Task | Owner | Artifacts | Blocker for |
|------|-------|-----------|-------------|
| Update PAYTABLE H1 × 5 to 30 | Server | models/<gameId>/game_config.py | RTP re-run |
| Rerun `/optimize-rtp` to verify RTP 96.00% | Server | models/<gameId>/ | Launch |
| Update stateMeta BONUS costMultiplier to 100 | Client | stateMeta.ts | Launch |
| Review i18n paytable.h1.desc wording | Planner | i18n/*.ts | Client update |
| Implement § 21 Ritual Narrative 3-act | Client + Art | components/ + Art/<gameId>/spine/ | Playtest |
| Append "Superseded" note on ADR-003 | Planner | DECISIONS.md | — |

---

## Suggested Next Actions

1. **Planner**: 確認本報告分類 + 回答 Still Valid / Needs Review 的模糊項
2. **Supervisor**: 依上表派工給 Client / Server / Art
3. **完工後**: 跑 `/spec-consistency-check <gamePath>` 驗證 drift 清零
4. **非 trivial 改動**: 跑 `/audit-launch <gamePath>` 重新評估送審 readiness

---

Verdict: N impact items (🔴 X / ⚠️ Y / ✅ Z)
```

---

### Step 6: 禁止行為

- **不自動修改** SPEC / math config / stateMeta / i18n / handler / Art manifest
- **不自動追加** "Superseded" 到 ADR — 只在 report 中建議，由 Planner 手動確認
- **不派工** — 只產 recommended allocation table，實際派工走 Supervisor

---

## 可與其他 skill 串接

- 上游：SPEC 修版本後立刻跑（通常在 Planner commit SPEC.md 後）
- 下游：impact report 指引 Supervisor 派工 → 完工後跑 `/spec-consistency-check` 驗證 → `/audit-launch` 評估送審
- 姊妹：`/spec-consistency-check`（檢查 drift）、`/reverse-spec`（code → SPEC 補齊）

---

## 特殊案例

### SPEC 是新檔（無 git history）
若 `git log -- <specPath>` 無 commit 則 abort：
「SPEC file has no prior git history. Use `/write-spec` for initial authoring, not propagate-spec-change.」

### baseRef 不存在
若 `git rev-parse <baseRef>` 失敗 → 列出最近 5 個 SPEC 變更 commit 給使用者挑：
```
git log --oneline -- <specPath> | head -5
```

### 跨遊戲共用規範變更
若 `<specPath>` 指向 `specs/_shared/*.md`，則：
1. 用 Grep 找所有 `specs/NN-*/SPEC.md` reference 到此共用檔的遊戲
2. 對每個遊戲執行一輪 Step 3 掃描
3. Impact report 改名 `specs/_shared/impact/<date>-<filename>.md`
