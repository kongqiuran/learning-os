# AGENTS.md

## 协作规则

1. 如果遇到可以通过用户简单操作就能解决的问题，要直接找用户处理。比如需要权限授权、需要确认某个账号权限、需要用户在界面点几下授权等，不要绕太久，直接说明需要用户做什么。

2. 完成项目文件修改后，自动执行 `git add` 和 `git commit`，并将提交结果告知用户；不要自动执行 `git push`，而是询问用户是否需要推送，并将可直接复制的 `git push` 命令放入代码块，由用户自行执行。

3. 语言使用规则：`.md` 文档以中文为主，方便用户阅读和销售交付；`.py` 代码以英文为主，包括变量名、函数名、界面文案、错误提示和注释。例外情况是 `prompts.py` 等需要明确要求模型生成中文内容的地方，可以保留必要中文指令或中文输出要求。

4. 向用户提供需要在项目中执行的命令代码块时，代码块第一行必须包含切换到项目目录的完整命令：`cd "D:\kongqiuran\ai\learning-os"`，后续再列出实际执行命令，确保代码块可以直接复制运行。

5. 提供本地 `git push` 命令后，必须继续提供“推送后服务器部署”复制区。每一步使用独立代码块，方便用户逐块复制执行，顺序如下：

   1. SSH 进入服务器：

      ```bash
      ssh learning@124.156.171.38
      ```

   2. 进入服务器项目目录并检查同步状态：

      ```bash
      cd ~/learning-os
      git status
      ```

      如果显示 `Your branch is up to date with 'origin/main'`，说明服务器代码已经同步；否则继续拉取：

      ```bash
      cd ~/learning-os
      git pull origin main
      ```

   3. 根据本次修改范围，只构建并重启对应服务，不要默认执行会同时重建全部服务的 `docker compose build`。

      前端改动：

      ```bash
      cd ~/learning-os
      docker compose build frontend
      docker compose up -d frontend
      ```

      后端改动：

      ```bash
      cd ~/learning-os
      docker compose build backend
      docker compose up -d backend
      ```

      如果前后端都有改动，分别构建并重启两个服务。

   4. 查看容器状态：

      ```bash
      cd ~/learning-os
      docker compose ps
      ```

      正常情况下应看到前端为 `Up`、后端为 `Up (healthy)`。

   5. 根据修改范围查看对应服务最近 50 行日志：

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

   6. 最后根据本次功能修改提供简短的浏览器验证步骤和预期结果。前端状态流转类修改应明确提醒用户测试“不刷新页面是否自动显示最新内容”。
