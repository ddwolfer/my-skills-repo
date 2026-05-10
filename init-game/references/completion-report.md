# Step 12: 完成報告模板

完成後顯示以下資訊：

```
遊戲專案已創建

遊戲資訊：
- 遊戲 ID: {game_id}
- 遊戲名稱: {gameName}
- 模板類型: {template}
- 版面大小: {numReels} x {numRows}
- RTP: {rtp}%
- 最大獎金: {max_win}x

專案位置：games/{game_id}
Git Repo: 已初始化（獨立 repo）
Git Clone: 獨立 repo（不受主 repo 版控）

下一步：
1. 設定 remote（如果尚未設定）：
   cd games/{game_id}
   git remote add origin git@github.com:your-org/{game_id}.git
   git push -u origin main

2. 安裝依賴（⚠️ 修改 SDK 後務必 clean build）：
   cd sdks/web-sdk && pnpm install
   # 如果之前 build 過，先刪除 cache：
   # rm -rf games/{game_id}/dist games/{game_id}/.svelte-kit

3. PayTable 和 Game Rules 已自動生成，可從 menu 開啟確認：
   - PayTableContent.svelte（符號賠率表）
   - GameRulesContent.svelte（遊戲規則）

4. 製作美術素材並放入 games/{game_id}/static/assets/ 目錄：
   - 符號圖片（200x200 PNG）→ static/assets/sprites/
   - 背景圖（bg_desktop.png）→ static/assets/sprites/
   - 邊框圖（frame.png）→ static/assets/sprites/
   - Spine 動畫（.skel/.json + .atlas）→ static/assets/spines/symbols/

5. 音效（模板音效已保留作為 placeholder）：
   - 自訂音效 → 替換 static/assets/audio/ 中的檔案
   - sounds.json 是 PixiJS audio loader 必需的，不可刪除

6. 素材就位後，執行 /preview-game games/{game_id} 看到第一個畫面

7. Game Tile 素材（送審必要）：
   - 準備 BG / FG / Logo 三張圖 → Art/{spec_folder}/game-tile/
   - BG + FG 合計 ≤ 3MB
   - 可用 /gen-assets 生成

8. Replay 實作（送審必要）：
   - 參見 README.md 中的 Replay 待實作項目
   - SDK 已處理 replay 偵測，需實作 Replay UI

9. 社群模式（stake.us 合規）：
   - PayTable / GameRules 已處理 social mode 文字替換
   - 確認 Game.svelte 的 betModeMeta 也有 isSocial 判斷

10. 已生成文檔：
   - WORK_ITEMS.md（上架工作追蹤）
   - src/game/CLAUDE.md（遊戲邏輯架構指引）
   - src/components/CLAUDE.md（元件架構指引）
   - src/stories/CLAUDE.md（Storybook 使用指引）
```
