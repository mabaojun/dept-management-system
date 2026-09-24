#!/usr/bin/env bash
# 一键打包部署包：刷新种子库 → 前端构建校验 → 按规范命名压缩
# 用法：./scripts/package.sh
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=$(cat VERSION)
DATE=$(date +%Y%m%d)
NAME="bmms-v${VERSION}-${DATE}"

# 1. 刷新种子数据库（打包前必须执行，保证初始数据为最新本地库）
mkdir -p seed
cp backend/dev.db seed/dev.db

# 2. 前端构建校验（类型检查 + 产物生成，失败则中止打包）
(cd frontend && npm run build > /dev/null)
echo "前端构建通过"

# 3. 压缩（输出到项目上级目录，避免自包含）
tar --exclude node_modules --exclude .venv --exclude __pycache__ \
    --exclude 'frontend/dist' --exclude .git --exclude .env --exclude '*.pyc' \
    --exclude 'backend/dev.db' \
    -czf "../${NAME}.tar.gz" .

echo "打包完成：$(cd .. && pwd)/${NAME}.tar.gz"
echo "上传命令：scp ../${NAME}.tar.gz root@服务器IP:/bumenguanli/releases/"
