# Learning OS Alpha 部署说明

本文档适用于当前 SQLite Alpha 版本。部署结构保持为单台服务器、Docker Compose、FastAPI、Nginx、SQLite 与本地持久化卷，不包含 PostgreSQL、Kubernetes 或多机任务队列。

## 1. 服务器要求

- Linux x86_64 服务器，建议 Ubuntu 24.04 LTS。
- 最低 2 核 CPU、4 GB 内存、20 GB 可用磁盘；课件较多时应预留更多磁盘。
- 已开放 HTTP 80 端口；接入域名后还需开放 HTTPS 443 端口。
- Docker Engine 29 或兼容版本，Docker Compose v2 或更高版本。
- 一个可用的 DeepSeek API Key。

安装 Docker 时应优先按照 Docker 官方 Ubuntu 安装文档配置软件源。安装完成后，用 `docker --version` 和 `docker compose version` 确认服务可用。

## 2. 上传代码

建议把项目放在 `/opt/learning-os`。可以使用 Git 拉取仓库，也可以通过发布包上传。进入项目目录后确认存在 `Dockerfile`、`frontend/Dockerfile`、`docker-compose.yml` 和 `nginx.conf`。

如果使用 Git，依次执行 `git clone <repository-url> /opt/learning-os` 与 `cd /opt/learning-os`。

## 3. 配置生产环境

在项目目录执行 `cp .env.production.example .env.production`，然后编辑 `.env.production`。

必须设置以下内容：

- `LLM_API_KEY`：真实 DeepSeek Key，不得提交到 Git。
- `LLM_MODEL`：当前已验证的模型名称。
- `API_SESSION_SECRET`：至少 32 个随机字符，不能使用示例值或 `secret`。
- `API_COOKIE_SECURE=true`：域名启用 HTTPS 后必须保持为 true。
- `API_ALLOWED_ORIGINS=https://app.learning-os.cn`。

可以使用 `openssl rand -hex 32` 生成会话密钥。生产模式会在启动时检查密钥长度和默认值，不安全时后端会拒绝启动。

SQLite 与上传文件在容器中固定存放于：

- `/data/database/learning_os.db`
- `/data/uploads`

不要把生产数据库复制进镜像，也不要把真实 Key 写入 Dockerfile 或 Compose 文件。

## 4. 启动与检查

在 `/opt/learning-os` 中执行 `docker compose up -d --build`。

使用 `docker compose ps` 检查 `backend` 和 `frontend` 均为 healthy。使用 `curl http://127.0.0.1/api/health` 检查 API，预期返回 `status=ok`。使用 `curl -I http://127.0.0.1/` 检查前端。

常用运维命令：

- 查看后端日志：`docker compose logs -f backend`
- 查看前端日志：`docker compose logs -f frontend`
- 重启服务：`docker compose restart`
- 停止服务但保留数据：`docker compose down`
- 查看容器健康状态：`docker compose ps`

Compose 使用 `restart: unless-stopped`，进程异常退出或服务器重启后会自动恢复。Docker healthcheck 会把探测失败的容器标记为 unhealthy，便于日志、监控与人工处理。

## 5. 域名与 HTTPS

把 `app.learning-os.cn` 的 DNS A/AAAA 记录指向服务器。在开放真实用户访问前，应在服务器或 Cloudflare 配置 HTTPS，并确认浏览器访问地址为 `https://app.learning-os.cn`。

当前容器中的 Nginx 提供：

- `/`：React 静态文件与 React Router fallback。
- `/api/*`：反向代理到 FastAPI `backend:8000`。
- `/healthz`：前端容器健康检查。

如果服务器外层还有 Nginx 或 Cloudflare，应把流量转发到本项目的 80 端口，并保留 `Host`、`X-Forwarded-For` 和 `X-Forwarded-Proto` 请求头。

## 6. 更新版本

更新前先备份数据库和上传文件。然后在项目目录执行 `git pull`，再执行 `docker compose up -d --build`。最后使用 `docker compose ps`、`docker compose logs --tail=100 backend` 和 `/api/health` 完成检查。

若新版本启动失败，可切回上一 Git 提交并再次执行 `docker compose up -d --build`。不要删除数据卷。

## 7. SQLite 与上传文件备份

命名卷固定为：

- `learning-os-database`
- `learning-os-uploads`

建议每天备份，并把备份复制到服务器以外的位置。备份前应短暂停止后端写入：先执行 `docker compose stop backend`，分别归档两个命名卷，随后执行 `docker compose start backend`。

可以用临时 Alpine 容器读取命名卷并生成压缩包。例如数据库卷可挂载为只读 `/source`，服务器备份目录挂载到 `/backup`，然后从 `/source` 创建带日期的 tar.gz。上传卷使用相同方法处理。

恢复前必须先停止后端，并先备份当前卷。恢复完成后启动后端，检查 `/api/health`、用户登录、课程数量和上传文件是否一致。

注意：`docker compose down` 不会删除命名卷；不要执行 `docker compose down -v`，除非明确要永久删除全部生产数据。

## 8. 安全检查清单

- `.env` 与 `.env.production` 未进入 Git。
- 数据库、上传文件和用户课件未进入 Git 或 Docker 镜像。
- `API_SESSION_SECRET` 为至少 32 个随机字符。
- `API_COOKIE_SECURE=true`，网站通过 HTTPS 访问。
- `API_ALLOWED_ORIGINS` 只包含正式域名。
- 只对外开放 Nginx 端口，不直接公开 FastAPI 8000 端口。
- 定期检查 `docker compose logs`、磁盘空间和卷备份。
