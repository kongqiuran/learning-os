# AGENTS.md

## 协作规则

1. 如果遇到可以通过用户简单操作就能解决的问题，要直接找用户处理。比如需要权限授权、需要确认某个账号权限、需要用户在界面点几下授权等，不要绕太久，直接说明需要用户做什么。

2. 完成项目文件修改后，自动执行 `git add` 和 `git commit`，并将提交结果告知用户；不要自动执行 `git push`，而是询问用户是否需要推送，并将可直接复制的 `git push` 命令放入代码块，由用户自行执行。

3. 语言使用规则：`.md` 文档以中文为主，方便用户阅读和销售交付；`.py` 代码以英文为主，包括变量名、函数名、界面文案、错误提示和注释。例外情况是 `prompts.py` 等需要明确要求模型生成中文内容的地方，可以保留必要中文指令或中文输出要求。

4. 向用户提供需要在项目中执行的命令代码块时，代码块第一行必须包含切换到项目目录的完整命令：`cd "D:\kongqiuran\ai\learning-os"`，后续再列出实际执行命令，确保代码块可以直接复制运行。

5. 提供本地 `git push` 命令后，必须继续提供完整的“推送后服务器部署”复制区。严格保留以下 1—8 的编号和顺序，不得合并或省略步骤；某一步不需要执行时，也要保留编号并明确说明无需执行。每条命令使用独立代码块，方便用户逐块复制。

   1. SSH 进入服务器：

      ```bash
      ssh learning@124.156.171.38
      ```

   2. 进入服务器项目目录：

      ```bash
      cd ~/learning-os
      ```

   3. 检查并拉取最新代码：

      ```bash
      cd ~/learning-os
      git status
      ```

      如果显示 `Your branch is up to date with 'origin/main'`，说明服务器代码已经同步；否则继续拉取：

      ```bash
      cd ~/learning-os
      git pull origin main
      ```

   4. 根据本次修改范围选择构建命令：确定只改前端时只构建前端，确定只改后端时只构建后端。不要在影响范围明确时默认重新构建全部服务。

      前端改动：

      ```bash
      cd ~/learning-os
      docker compose build frontend
      ```

      后端改动：

      ```bash
      cd ~/learning-os
      docker compose build backend
      ```

      如果前后端都有改动，构建两个服务：

      ```bash
      cd ~/learning-os
      docker compose build frontend backend
      ```

      如果无法确定本次改动影响前端还是后端，为避免遗漏，应重新构建全部服务：

      ```bash
      cd ~/learning-os
      docker compose build
      ```

      如果只是文档等不影响运行服务的改动，保留本步骤并明确说明无需重新构建容器。

   5. 根据第 4 步确定的修改范围，重启对应服务。

      前端改动：

      ```bash
      cd ~/learning-os
      docker compose up -d frontend
      ```

      后端改动：

      ```bash
      cd ~/learning-os
      docker compose up -d backend
      ```

      前后端都有改动：

      ```bash
      cd ~/learning-os
      docker compose up -d frontend backend
      ```

      无法确定影响范围：

      ```bash
      cd ~/learning-os
      docker compose up -d
      ```

      如果无需重新构建容器，本步骤也明确说明无需重启。

   6. 查看容器状态：

      ```bash
      cd ~/learning-os
      docker compose ps
      ```

      正常情况下应看到前端为 `Up`、后端为 `Up (healthy)`。

   7. 根据修改范围查看对应服务最近 50 行日志：

      前端：

      ```bash
      cd ~/learning-os
      docker compose logs frontend --tail=50
      ```

      后端：

      ```bash
      cd ~/learning-os
      docker compose logs backend --tail=50
      ```

      日志中不应出现 `error` 或 `failed`；前端正常启动通常会显示 `Configuration complete; ready for start up`。

      如果无法确定影响范围，查看全部服务日志：

      ```bash
      cd ~/learning-os
      docker compose logs --tail=50
      ```

   8. 最后根据本次功能修改提供简短的浏览器验证步骤和预期结果。前端状态流转类修改应明确提醒用户测试“不刷新页面是否自动显示最新内容”。如果本次改动不影响运行功能，也要保留本步骤并说明无需浏览器验证。
