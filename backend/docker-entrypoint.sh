#!/bin/sh
# 容器启动入口：volume 中无数据库时，用随部署包分发的种子库初始化
set -e

if [ ! -f /data/dev.db ] && [ -f /seed/dev.db ]; then
  echo "初始化：从种子数据库 /seed/dev.db 载入初始数据..."
  cp /seed/dev.db /data/dev.db
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 9000
