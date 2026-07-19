# AGENTS.md

## 协作规则

1. 如果遇到可以通过用户简单操作就能解决的问题，要直接找用户处理。比如需要权限授权、需要确认某个账号权限、需要用户在界面点几下授权等，不要绕太久，直接说明需要用户做什么。

2. 完成项目文件修改后，默认自动执行 `git add`、`git commit` 和 `git push`，不需要先询问用户是否推送，并将提交与推送结果告知用户。推送成功后继续按第 5 条自动完成服务器更新和部署，不再默认让用户复制执行。如果 GitHub 连接、认证、权限或其他外部原因导致推送失败，应停止在失败步骤，直接说明需要用户处理的问题，并提供可从该步骤继续执行的命令。

3. 语言使用规则：`.md` 文档以中文为主，方便用户阅读和销售交付；`.py` 代码以英文为主，包括变量名、函数名、界面文案、错误提示和注释。例外情况是 `prompts.py` 等需要明确要求模型生成中文内容的地方，可以保留必要中文指令或中文输出要求。

4. 向用户提供需要在项目中执行的命令代码块时，代码块第一行必须包含切换到项目目录的完整命令：`cd "D:\kongqiuran\ai\learning-os"`，后续再列出实际执行命令，确保代码块可以直接复制运行。

5. 本地 `git push` 成功后，默认由 Codex 按以下 1—8 的顺序直接完成服务器更新、构建、重启和验证，不再要求用户逐块复制命令。服务器项目目录只在第 2 步进入一次，第 3—7 步不要重复执行 `cd ~/learning-os`。如果 SSH、网络、认证、权限、Docker 或其他外部原因导致某一步失败，应停止后续操作，直接说明失败原因和需要用户处理的事项，并提供从失败步骤继续执行的可复制命令。向用户报告执行结果时仍严格保留 1—8 的编号；不需要执行的步骤也要保留编号并明确说明。

   1. SSH 进入服务器：

      ```bash
      ssh learning@124.156.171.38
      ```

      如果确认服务器仍在运行，但 SSH 无法连接，要明确提醒用户这是“情况 4：服务器 SSH 服务挂了”。此时需要用户登录云服务商控制台，使用 VNC 或网页终端执行：

      ```bash
      systemctl status ssh
      ```

      如果 SSH 服务异常，执行：

      ```bash
      systemctl restart ssh
      ```

      如果当前控制台用户权限不足，在命令前添加 `sudo`。

   2. 进入服务器项目目录：

      ```bash
      cd ~/learning-os
      ```

   3. 拉取最新代码：

      ```bash
      git pull origin main
      ```

   4. 根据本次修改范围选择构建命令：确定只改前端时只构建前端，确定只改后端时只构建后端。不要在影响范围明确时默认重新构建全部服务。

      前端改动：

      ```bash
      docker compose build frontend
      ```

      后端改动：

      ```bash
      docker compose build backend
      ```

      如果前后端都有改动，构建两个服务：

      ```bash
      docker compose build frontend backend
      ```

      如果无法确定本次改动影响前端还是后端，为避免遗漏，应重新构建全部服务：

      ```bash
      docker compose build
      ```

      如果只是文档等不影响运行服务的改动，保留本步骤并明确说明无需重新构建容器。

   5. 根据第 4 步确定的修改范围，重启对应服务。

      前端改动：

      ```bash
      docker compose up -d frontend
      ```

      后端改动：

      ```bash
      docker compose up -d backend
      ```

      前后端都有改动：

      ```bash
      docker compose up -d frontend backend
      ```

      无法确定影响范围：

      ```bash
      docker compose up -d
      ```

      如果无需重新构建容器，本步骤也明确说明无需重启。

   6. 查看容器状态：

      ```bash
      docker compose ps
      ```

      正常情况下应看到前端为 `Up`、后端为 `Up (healthy)`。

   7. 根据修改范围查看对应服务最近 50 行日志：

      前端：

      ```bash
      docker compose logs frontend --tail=50
      ```

      后端：

      ```bash
      docker compose logs backend --tail=50
      ```

      日志中不应出现 `error` 或 `failed`；前端正常启动通常会显示 `Configuration complete; ready for start up`。

      如果无法确定影响范围，查看全部服务日志：

      ```bash
      docker compose logs --tail=50
      ```

   8. 最后根据本次功能修改提供简短的浏览器验证步骤和预期结果。前端状态流转类修改应明确提醒用户测试“不刷新页面是否自动显示最新内容”。如果本次改动不影响运行功能，也要保留本步骤并说明无需浏览器验证。
