---
name: launch-team
description: Manager 啟動後執行的團隊協調流程。清理殘留狀態、確認團隊上線、建立初始任務、更新 dashboard。當 Manager 剛啟動完成、需要確認團隊狀態、或使用者說「啟動團隊」「開工」「check team」時觸發。使用方式：/launch-team 或 /launch-team Client Server（只等待特定角色）
---

# Launch Team — Manager 啟動後協調流程

此 skill 供 Manager 角色在完成自身啟動流程（register → claim_manager → get_briefing）後執行，負責：
1. 清理上次 session 殘留
2. 確認團隊成員上線
3. 建立初始任務分配
4. 更新 dashboard 狀態

## 前置條件

- 你已經是 Manager 角色且已 `claim_manager()`
- 其他 agent 已透過 `start_team.bat` 或手動方式啟動中

## 執行流程

### Phase 1 — 清理殘留狀態

1. `list_tasks()` — 查看上次未完成的任務
2. 將所有 stale 任務（前次 session 遺留、assignee 已離線的）標記為 `blocked` 或移除
3. `list_agents()` — 確認哪些 agent 已上線（status: alive）
4. `get_decisions()` — 回顧上次 session 的重要決策，確認是否仍有效

### Phase 2 — 等待團隊就位

使用輪詢迴圈等待所需角色上線：

```
預期角色 = 使用者指定的角色，或預設全部 5 個（Manager, Client, Server, Art, Planner）
最大等待 = 3 分鐘（6 次 × 30 秒）

迴圈：
  1. list_agents() 取得當前在線名單
  2. 比對預期角色 vs 實際在線
  3. 全部到齊 → 進入 Phase 3
  4. 未到齊 → 透過 Discord 回報「等待 [缺席角色] 上線...（已到齊: [在線角色]）」
  5. sleep 30 秒
  6. 超過最大等待 → 回報缺席名單，詢問使用者要繼續等還是先開工
```

### Phase 3 — 團隊狀態彙報

向使用者（透過 Discord）彙報：

```
團隊就位報告
━━━━━━━━━━━━━━━━━━
在線: Manager, Client, Server, Art, Planner
上次 session 決策: [列出關鍵決策]
未完成任務: [列出或標示「無」]
━━━━━━━━━━━━━━━━━━
今天要做什麼？
```

### Phase 4 — Dashboard 初始化

1. `workspace_write("status", ...)` — 更新 Manager 狀態頁
2. 為每個在線 agent 確認其 workspace 有 status key
3. `update_progress()` — 同步各功能的完成度（如果有上次紀錄）
4. 確保 dashboard 反映真實狀態（遵守 Dashboard Must Reflect Real Work 規則）

### Phase 5 — 等待指令

詢問使用者今天的工作方向，收到回覆後：
1. 拆解任務
2. `create_task()` 為每個子任務建檔（**口頭派工必須同步建 task**）
3. 視需要 `create_workflow()` 建立有依賴的流程
4. 開始 `yield_floor()` 派工

## 參數

- `/launch-team` — 等待全部 5 個角色
- `/launch-team Client Server` — 只等待指定角色（適合小型任務不需全員）
- `/launch-team --skip-cleanup` — 跳過 Phase 1（適合 session 剛結束立刻重開）

## 注意事項

- 這個 skill 只在 Manager 角色中使用，其他角色不適用
- 如果 agent-bridge 中有上次 session 的 managed mode 設定，Manager 啟動時會自動接管
- Phase 2 的等待不會超過 3 分鐘，避免 Manager 空轉
- 所有進度都透過 Discord 即時回報，使用者不需要盯 terminal
