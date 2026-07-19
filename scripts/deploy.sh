#!/bin/bash

set -e

DEPLOY_TIME="$(date '+%Y-%m-%d %H:%M:%S %Z')"
COMMIT_HASH=""
BUILD_TARGET=""
CONTAINER_STATUS=""
CHANGED_FILES=()

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "错误：$*"
  exit 1
}

check_project_directory() {
  if [[ ! -d .git || ! -f docker-compose.yml || ! -d frontend || ! -d src ]]; then
    fail "当前目录不是完整的 Learning OS 项目，请在项目根目录执行 scripts/deploy.sh。"
  fi

  local project_name
  project_name="$(basename "$(git rev-parse --show-toplevel)")"
  if [[ "$project_name" != "learning-os" ]]; then
    fail "当前 Git 仓库是 ${project_name}，不是 learning-os。"
  fi
}

collect_changed_files() {
  mapfile -t CHANGED_FILES < <(
    git diff-tree --no-commit-id --name-only -r -m HEAD | sort -u
  )
}

detect_build_target() {
  local frontend_changed=false
  local backend_changed=false
  local unknown_changed=false
  local changed_file

  if ((${#CHANGED_FILES[@]} == 0)); then
    unknown_changed=true
  fi

  for changed_file in "${CHANGED_FILES[@]}"; do
    case "$changed_file" in
      frontend/*|nginx.conf)
        frontend_changed=true
        ;;
      src/*|api_server.py|Dockerfile|requirements.txt|requirements-*.txt)
        backend_changed=true
        ;;
      *)
        unknown_changed=true
        ;;
    esac
  done

  if $unknown_changed; then
    BUILD_TARGET="all"
  elif $frontend_changed && $backend_changed; then
    BUILD_TARGET="frontend backend"
  elif $frontend_changed; then
    BUILD_TARGET="frontend"
  elif $backend_changed; then
    BUILD_TARGET="backend"
  else
    BUILD_TARGET="all"
  fi
}

build_services() {
  case "$BUILD_TARGET" in
    frontend)
      log "最近 commit 只影响前端，构建 frontend。"
      docker compose build frontend
      ;;
    backend)
      log "最近 commit 只影响后端，构建 backend。"
      docker compose build backend
      ;;
    "frontend backend")
      log "最近 commit 同时影响前端和后端，构建两个服务。"
      docker compose build frontend backend
      ;;
    *)
      log "无法安全判断修改范围，构建全部服务。"
      docker compose build
      ;;
  esac
}

wait_for_backend_health() {
  local container_id
  local health_status
  local attempts=30

  container_id="$(docker compose ps -q backend)"
  if [[ -z "$container_id" ]]; then
    fail "没有找到 backend 容器。"
  fi

  health_status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}not-configured{{end}}' "$container_id")"
  if [[ "$health_status" == "not-configured" ]]; then
    log "backend 未配置 Docker health check，跳过健康等待。"
    return
  fi

  while ((attempts > 0)); do
    health_status="$(docker inspect --format '{{.State.Health.Status}}' "$container_id")"
    if [[ "$health_status" == "healthy" ]]; then
      log "backend 健康检查通过。"
      return
    fi
    if [[ "$health_status" == "unhealthy" ]]; then
      fail "backend 健康检查失败，容器状态为 unhealthy。"
    fi

    log "等待 backend 健康检查：${health_status}"
    sleep 3
    attempts=$((attempts - 1))
  done

  fail "等待 backend 健康检查超时。"
}

print_report() {
  printf '\n========== Learning OS 部署报告 ==========\n'
  printf '部署时间：%s\n' "$DEPLOY_TIME"
  printf 'Commit：%s\n' "$COMMIT_HASH"
  printf '修改文件：\n'
  if ((${#CHANGED_FILES[@]} == 0)); then
    printf '  - 未检测到文件\n'
  else
    printf '  - %s\n' "${CHANGED_FILES[@]}"
  fi
  if [[ "$BUILD_TARGET" == "all" ]]; then
    printf '构建服务：全部服务\n'
  else
    printf '构建服务：%s\n' "$BUILD_TARGET"
  fi
  printf '容器状态：\n%s\n' "$CONTAINER_STATUS"
  printf '==========================================\n'
}

main() {
  check_project_directory

  log "拉取 GitHub main 分支最新代码。"
  git pull origin main

  COMMIT_HASH="$(git rev-parse --short HEAD)"
  log "当前部署 commit：${COMMIT_HASH}"

  collect_changed_files
  detect_build_target
  log "最近 commit 修改文件数：${#CHANGED_FILES[@]}"

  build_services

  log "启动 Docker Compose 服务。"
  docker compose up -d

  log "等待服务启动。"
  sleep 5
  wait_for_backend_health

  log "检查容器状态。"
  CONTAINER_STATUS="$(docker compose ps)"
  print_report
}

main "$@"
