# 遊戲後續管理

### 更新 Submodule Remote

當遊戲 repo 已推送到 remote 後，更新 .gitmodules：

```bash
git config -f .gitmodules submodule.games/{game_id}.url git@github.com:your-org/{game_id}.git
git submodule sync
```

### Clone 專案（包含所有遊戲）

```bash
git clone --recurse-submodules {main_repo_url}
```

### 更新所有遊戲 Submodule

```bash
git submodule update --remote --merge
```

## 注意事項

1. 每個遊戲有獨立的 git 歷史，方便追溯和回滾
2. 共享組件透過 pnpm workspace 連結，不需重複安裝
3. 可以獨立開發、測試、部署各個遊戲
4. 主 repo 的 .gitmodules 記錄所有遊戲的 submodule 資訊
