---
name: init-game
description: 從遊戲企劃書初始化新遊戲專案。讀取 SPEC.md，選擇對應的 web-sdk 模板（cluster/lines/ways/scatter），複製模板到 games/ 目錄，初始化獨立 git repo 並添加為 submodule。使用方式：/init-game specs/01-dragon-feast
---

# init-game

從遊戲企劃書初始化新遊戲專案，建立獨立的 git repo 並作為 submodule 管理。

## 參數

- `$ARGUMENTS`: 企劃書路徑（例如：`specs/01-dragon-feast`）

## 模板檔案索引

所有模板位於 `.claude/files/game-templates/`：

| 檔案 | 類型 | 用途 | 使用步驟 |
|------|------|------|---------|
| `gitignore` | 直接複製 | .gitignore | Step 4.1 |
| `build_audio.bat` | 直接複製 | 音效打包啟動器 | Step 4.1 |
| `build_audio.template.mjs` | 變數替換 | 音效打包腳本 | Step 4.1 |
| `stories-CLAUDE.md` | 直接複製 | Storybook 指引 | Step 5.5 |
| `WORK_ITEMS.template.md` | 變數替換 | 上架工作清單 | Step 7.2 |
| `game-CLAUDE.template.md` | 變數替換 | 遊戲邏輯指引 | Step 7.3 |
| `components-CLAUDE.template.md` | 變數替換 | 元件架構指引 | Step 7.4 |

## 目錄結構

```
StakeProject/                    # 主 repo
├── sdks/web-sdk/                # SDK 和模板（apps/ + packages/）
├── games/                       # 遊戲目錄（各自獨立 repo / submodule）
└── specs/                       # 企劃書
```

## 執行流程

### Step 1: 讀取企劃書

讀取 `$ARGUMENTS/SPEC.md` 並提取關鍵資訊：

1. **遊戲 ID**（gameID）：從「遊戲 ID」欄位取得
2. **英文名稱**（gameName）：從「英文名稱」欄位取得
3. **SDK 計算類型**：從「SDK 計算類型」欄位決定模板
4. **版面大小**：從「版面大小」欄位取得 numReels x numRows
5. **符號列表與賠率表**：從「符號定義與賠率表」章節取得
6. **RTP**：從「目標 RTP」欄位取得
7. **最大獎金**：從「最大獎金」欄位取得（max_win）
8. **投注模式**：從「投注模式」章節取得（base 和 bonus 費用）
9. **波動性**（volatility）：從「波動性」欄位取得
10. **最低中獎門檻**（min_scatter_count）：如 8 個符號
11. **特殊符號定義**：wild/scatter/multiplier 列表（從「特殊符號」表取得）
12. **乘數封頂值**（multiplier_cap）：如 ×64
13. **遊戲特色機制**：掃描 SPEC 判斷 Tumble / Free Spins / Global Multiplier / Buy Bonus / Wild Multiplier / Position Multiplier Grid

### Step 2: 選擇模板

| SDK 計算類型 | 模板 |
|-------------|------|
| `evaluate_clusters_board()` | cluster |
| `evaluate_lines_board()` | lines |
| `evaluate_ways_board()` | ways |
| `evaluate_scatter_board()` | scatter |
| `evaluate_number_picker()` | number-picker |
| `evaluate_price_board()` | price |

### Step 3: 建立遊戲目錄

1. 確保 `games/` 目錄存在
2. 檢查 `games/{game_id}` 是否已存在，如果存在請詢問使用者是否覆蓋

```bash
# Windows
if not exist "games" mkdir games
# Unix/Mac
mkdir -p games
```

### Step 4: 複製模板

複製模板到 `games/{game_id}`，排除 node_modules。

```bash
# Windows（robocopy 遞迴排除比 Copy-Item -Exclude 更可靠）
robocopy "sdks\web-sdk\apps\{template}" "games\{game_id}" /E /XD node_modules .cache .svelte-kit dist build .turbo
# robocopy 退出碼 < 8 為正常；若在 Git Bash 下 robocopy 不可用，改用：
# cp -r sdks/web-sdk/apps/{template}/* games/{game_id}/ && rm -rf games/{game_id}/node_modules games/{game_id}/.turbo
# Unix/Mac
cp -r sdks/web-sdk/apps/{template} games/{game_id}
rm -rf games/{game_id}/node_modules games/{game_id}/.cache games/{game_id}/.svelte-kit games/{game_id}/dist games/{game_id}/build
```


#### 4.1 補充基礎檔案

複製以下模板檔案到遊戲目錄：

1. `.claude/files/game-templates/gitignore` → `games/{game_id}/.gitignore`
2. `.claude/files/game-templates/build_audio.bat` → `games/{game_id}/build_audio.bat`
3. `.claude/files/game-templates/build_audio.template.mjs` → `games/{game_id}/build_audio.mjs`（替換變數）

**build_audio.mjs 變數替換：**

| 變數 | 來源 |
|------|------|
| `{{gameName}}` | SPEC §1 英文名稱 |
| `{{templateType}}` | Step 2 選擇的模板類型（cluster/lines/ways/scatter） |
| `{{loopSounds}}` | 從 `sound.ts` 的 `MusicName` union 提取所有 bgm_* 名稱，加上 `sfx_bigwin_coinloop` |

### Step 5: 修改配置

#### 5.1 修改 package.json

更新 `games/{game_id}/package.json`：name 改為 `{game_id}`，version 改為 `0.0.1`。

**加入 `ui-brand` 依賴** — 模板預設用 `components-ui-pixi`（SDK 預設 UI），但我們所有遊戲統一使用 `ui-brand`（BrandUI）。在 `dependencies` 中加入：

```json
"ui-brand": "workspace:*"
```

#### 5.2 生成 config.ts

根據企劃書內容生成 `games/{game_id}/src/game/config.ts`：

```typescript
export default {
	providerName: 'stake_engine',
	gameName: '{英文名稱}',
	gameID: '{遊戲ID}',
	rtp: {RTP數值},
	numReels: {軸數},
	numRows: [{每軸行數陣列}],
	betModes: {
		base: { cost: 1.0, feature: true, buyBonus: false, rtp: {RTP}, max_win: {max_win} },
		bonus: { cost: {費用倍數}, feature: true, buyBonus: true, rtp: {RTP}, max_win: {max_win} },
	},
	symbols: { /* 根據企劃書賠率表生成 */ },
	SPECIAL_SYMBOLS: {
		wild: ['{Wild符號ID}'],      // 從 SPEC 特殊符號表取得
		scatter: ['{Scatter符號ID}'], // 從 SPEC 特殊符號表取得
		// multiplier: ['{ID}'],     // 若 Wild 在 FS 中帶乘數
	},
	paddingReels: { basegame: '', freegame: '' },
};
```

**符號賠率表格式**：

- **Cluster 類型**：賠率區間展開為連續數值（`5+` → 5,6,7、`8+` → 8-11、`12+` → 12-14、`15+` → 15-19、`20+` → 20-36）
- **Lines 類型**：按連線數（3/4/5），需包含 paylines 配置
- **Ways 類型**：與 Lines 類似，不需 paylines
- **Scatter 類型**：與 Cluster 類似，使用 scatter 計算邏輯

> **注意**：Scatter/Cluster 的 paytable 刻意將每個 count（如 8~30）逐一展開為獨立物件，以匹配 SDK `evaluate_scatter_board()` 的 exact-count 查表邏輯。不要壓縮為 range 格式。

#### 5.3 生成 constants.ts 的符號映射

更新 `games/{game_id}/src/game/constants.ts`：

1. **HIGH_SYMBOLS**：只包含 config.ts 中 H 系列符號，不要留模板的 H5
2. **INITIAL_BOARD**：確認所有引用的符號名稱都存在於 config.symbols 中
3. **SYMBOL_INFO_MAP**：為每個符號生成條目，使用 placeholder assetKey（`H1_static` 等）

**注意**：此時用 placeholder key，等素材就位後由 `/gen-placeholder-assets` 連接實際素材。

#### 5.3b 修正 utils.ts 的 Wild multiplier guard

模板的 `getSymbolKey()` 會把帶 multiplier 的符號拼成 `W_2`、`W_3` 等 key，但 Wild 不管 multiplier 值都使用同一組動畫（乘數由疊層元件顯示）。若不加 guard，RGS 回傳帶 multiplier 的 Wild 時會在 `SYMBOL_INFO_MAP` 找不到 key 而崩潰。

修改 `games/{game_id}/src/game/utils.ts` 的 `getSymbolKey` 函數，在 multiplier 判斷前加入 Wild 短路：

```diff
 export const getSymbolKey = ({ rawSymbol }: { rawSymbol: RawSymbol }) => {
+	// W (wild) 不管 multiplier 值都使用同一組 Spine 動畫，
+	// multiplier 數字由疊層元件顯示，不影響符號外觀。
+	if (rawSymbol.name === 'W') {
+		return 'W' as keyof typeof SYMBOL_INFO_MAP;
+	}
 	if (rawSymbol.multiplier !== undefined) {
 		return `${rawSymbol.name}_${rawSymbol.multiplier}` as keyof typeof SYMBOL_INFO_MAP;
 	}
 	return rawSymbol.name as keyof typeof SYMBOL_INFO_MAP;
 };
```

> **適用條件**：SPEC 的特殊符號有 `multiplier: ['W']` 時必加。即使沒有，加了也無害（Wild 沒 multiplier 就不會走到下面的分支）。

#### 5.4 生成 PayTable 和 Game Rules 頁面

根據 SPEC.md 的符號賠率表和遊戲規則，生成兩個 Svelte 元件：
- `games/{game_id}/src/components/PayTableContent.svelte` — 符號賠率表
- `games/{game_id}/src/components/GameRulesContent.svelte` — 遊戲規則
- 修改 `Game.svelte` 加入 import 和 Modals snippet 接線
- 更新 `Game.svelte` 中 `<UiGameName name="..." />` 為遊戲英文名稱大寫（如 `"PHARAOHS CASCADE"`）

> 完整的 Svelte 模板生成規範、Social Mode 處理、免責聲明文字、樣式要求請參閱 `references/paytable-gamerules-template.md`

#### 5.6 切換為 BrandUI

模板預設使用 SDK 的 `UI`（from `components-ui-pixi`），但我們統一使用 `BrandUI`（from `ui-brand`）作為底部 UI 列。需修改 4 個檔案：

**1. `src/components/Game.svelte`** — 替換 import 和元件：

```diff
- import { UI, UiGameName } from 'components-ui-pixi';
+ import { BrandUI } from 'ui-brand';
```

將模板中的 `<UI>...</UI>` 區塊替換為：

```svelte
<BrandUI>
  {#snippet gameName()}{/snippet}
  {#snippet logo()}{/snippet}
</BrandUI>
```

**2. `src/game/eventEmitter.ts`** — 替換 type import：

```diff
- import type { EmitterEventUi } from 'components-ui-pixi';
+ import type { EmitterEventUi } from 'ui-brand';
```

**3. `src/i18n/messagesMap/index.ts`** — 替換翻譯來源：

```diff
- import { messagesMap as messagesMapUiPixi } from 'components-ui-pixi';
+ import { messagesMap as messagesMapUiPixi } from 'ui-brand';
```

**4. `src/i18n/i18nDerived.ts`** — 替換 i18n 衍生值：

```diff
- import { i18nDerived as i18nDerivedUiPixi } from 'components-ui-pixi';
+ import { i18nDerived as i18nDerivedUiPixi } from 'ui-brand';
```

> **為什麼不直接從模板改？** 因為模板由 SDK 團隊維護，我們不應該修改 `sdks/web-sdk/apps/` 下的檔案。改在 init-game 流程中自動替換更安全。

#### 5.5 複製 stories CLAUDE.md

將 `.claude/files/game-templates/stories-CLAUDE.md` 直接複製到 `games/{game_id}/src/stories/CLAUDE.md`，不需任何修改。

### Step 6: 清理素材

清空 spines 和 sprites 目錄（保留目錄結構和 fonts/）。

**保留 audio 目錄** — `sounds.json` + 音效檔是 PixiJS audio loader 必需的。刪除會導致部署後 404 → `Cannot read 'src'` → 遊戲卡住。

> 模板 audio 僅為佔位（音效名稱與新遊戲不同），後續用 `build_audio.mjs` 重新打包生成正確的 sounds.json。

```bash
# Windows
rmdir /S /Q "games\{game_id}\static\assets\spines" 2>nul
mkdir "games\{game_id}\static\assets\spines"
rmdir /S /Q "games\{game_id}\static\assets\sprites" 2>nul
mkdir "games\{game_id}\static\assets\sprites"
```

```bash
# Unix/Mac
rm -rf games/{game_id}/static/assets/spines/*
rm -rf games/{game_id}/static/assets/sprites/*
```

清理 `games/{game_id}/src/game/assets.ts`，替換為只保留 sound entry 的最小版本：

```ts
// 素材清單 — 等素材就位後由 /gen-placeholder-assets 自動填充
export default {
	// 音效（模板自帶，不可刪除）
	sound: {
		type: 'audio',
		src: new URL('../../assets/audio/sounds.json', import.meta.url).href,
		preload: true,
	},
} as const;
```

> **為什麼保留 sound？** `EnableSound.svelte` 在 `onMount` 時會存取 `loadedAssets['sound']`。如果 assets.ts 沒有 `sound` entry，載入後 `loadedAssets['sound']` 為 undefined → `Cannot read 'src'` → 遊戲崩潰黑屏。

### Step 7: 生成 README.md

在 `games/{game_id}/` 根目錄生成 `README.md`，包含 Game Info 表格、符號列表、Bet Modes、Features、Project Structure、Development 指令。

**語言**：README 使用中文撰寫（中英對照格式，如「龍宴盛典 Dragon Feast」「高賠 High Pay」）。

> 完整 README 模板請參閱 `references/readme-claude-templates.md`

### Step 7.1: 生成 game-level CLAUDE.md

在 `games/{game_id}/` 根目錄生成 `CLAUDE.md`，提供 Claude Code 進入遊戲目錄時的上下文（優先事項、專案結構、技術棧、關鍵檔案）。

> 完整 CLAUDE.md 模板請參閱 `references/readme-claude-templates.md`

### Step 7.2: 生成 WORK_ITEMS.md

讀取 `.claude/files/game-templates/WORK_ITEMS.template.md`，根據 SPEC 填入變數：

| 變數 | 來源 |
|------|------|
| `{{gameName}}` | SPEC §1 英文名稱 |
| `{{gameId}}` | SPEC §1 遊戲 ID |
| `{{symbolCount}}` | SPEC §3 符號總數 |
| `{{rtp}}` | SPEC §1 目標 RTP |
| `{{featureItems}}` | 根據 SPEC 機制動態生成 P1 項目（見下方） |
| `{{p2Start}}` | P1 最後一項的編號 + 1 |

**P1 功能項目動態生成規則**：掃描 SPEC，有對應機制就加入：

| SPEC 機制 | P1 項目 |
|-----------|--------|
| Free Spins / 免費旋轉 | Free Spins UI（FreeSpinIntro/Outro/Counter） |
| Tumble / 連鎖消除 | Tumble 動畫調校 |
| Global Multiplier / 全域乘數 | Global Multiplier UI 元件 |
| Buy Bonus / 購買獎勵 | Buy Bonus 確認彈窗 |
| Wild Multiplier | Wild 乘數顯示（FS 限定） |
| Position Multiplier Grid | 位置乘數格 UI |

輸出至 `games/{game_id}/WORK_ITEMS.md`。

### Step 7.3: 生成 src/game/CLAUDE.md

讀取 `.claude/files/game-templates/game-CLAUDE.template.md`，根據遊戲實際內容填入：

| 變數 | 來源 |
|------|------|
| `{{bookEventList}}` | 讀取 `games/{game_id}/src/game/typesBookEvent.ts`，提取所有 event type 名稱，生成 bullet list |
| `{{gameSpecificTips}}` | 根據 SPEC 機制生成對應的常見陷阱提示（例如：Global Multiplier 跨 FS 不重置） |

輸出至 `games/{game_id}/src/game/CLAUDE.md`。

### Step 7.4: 生成 src/components/CLAUDE.md

讀取 `.claude/files/game-templates/components-CLAUDE.template.md`，根據遊戲實際內容填入：

| 變數 | 來源 |
|------|------|
| `{{componentTree}}` | 讀取 `games/{game_id}/src/components/Game.svelte`，提取元件 import 和渲染順序，生成縮排樹狀結構 |
| `{{featureComponents}}` | 掃描 `games/{game_id}/src/components/` 目錄，將 Feature 演出類元件（FreeSpinIntro、GlobalMultiplier 等）列出並加說明 |

輸出至 `games/{game_id}/src/components/CLAUDE.md`。

### Step 7.5: 後置檢查

依序執行以下檢查，確保送審就緒：

1. **Step 7.5a: Game Tile 目錄** — 建立 `Art/{spec_folder}/game-tile/` 和 README
2. **Step 7.5b: 免責聲明驗證** — 確認 GameRulesContent 包含完整的 6 項免責短語
3. **Step 7.5c: 社群模式合規** — 確認 PayTable/GameRules/Game.svelte 的 Social Mode 處理
4. **Step 7.5d: Replay 備註** — 在 README 中加入 Replay 待實作項目清單

> 各項檢查的完整細節請參閱 `references/post-setup-checks.md`

### Step 8: 初始化 Git Repo

**判斷**：若 `games/{game_id}/.git` 已存在（submodule 已建立），跳過 Step 8–10，直接在現有 repo 中 `git add . && git commit`。

在遊戲目錄中初始化獨立的 git repo：

```bash
cd games/{game_id}
git init
git add .
git commit -m "Initial commit: {game_id} from {template} template"
```

### Step 9: 設定 Remote 並添加為 Submodule

詢問使用者 remote repository URL：

**有 URL 的情況**（推薦）：
```bash
cd games/{game_id}
git remote add origin {remote_url}
git push -u origin main
cd {project_root}
git submodule add {remote_url} games/{game_id}
git add .gitmodules games/{game_id}
git commit -m "Add {game_id} as submodule"
```

**無 URL（稍後設定）**：
```bash
cd {project_root}
git submodule add ./games/{game_id} games/{game_id}
git add .gitmodules games/{game_id}
git commit -m "Add {game_id} as submodule"
```
之後設定 remote 時需更新 `.gitmodules`。

### Step 10: 更新 pnpm-workspace.yaml

檢查 `sdks/web-sdk/pnpm-workspace.yaml` 是否包含 `"../games/*"`，如果沒有則添加：

```yaml
packages:
  - "apps/*"
  - "packages/*"
  - "../games/*"
```

### Step 11: 輸出報告

顯示遊戲資訊摘要（ID、名稱、模板、版面、RTP、Max Win）和下一步指引。

> 完整報告模板請參閱 `references/completion-report.md`

## 參考資料

- 遊戲後續管理（Clone、目錄命名） → `references/game-types-and-management.md`
- PayTable / GameRules 模板細節 → `references/paytable-gamerules-template.md`
- README / CLAUDE.md 模板 → `references/readme-claude-templates.md`
- 後置檢查（Game Tile / 免責聲明 / Social / Replay） → `references/post-setup-checks.md`
- 完成報告模板 → `references/completion-report.md`
