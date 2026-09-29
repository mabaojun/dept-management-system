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
# 注意：.env（含 LLM 密钥）随包分发，走 scp 加密传输，避免在公网网页端明文提交密钥
tar --exclude node_modules --exclude .venv --exclude __pycache__ \
    --exclude 'frontend/dist' --exclude .git --exclude '*.pyc' \
    --exclude 'backend/dev.db' \
    -czf "../${NAME}.tar.gz" .

if grep -q '^LLM_API_KEY=..*' .env 2>/dev/null; then
  echo "提示：.env 已随包分发（LLM_API_KEY 已配置）"
else
  echo "警告：.env 中 LLM_API_KEY 为空，AI 功能将以演示模式运行"
fi

echo "打包完成：$(cd .. && pwd)/${NAME}.tar.gz"
echo "上传命令：scp ../${NAME}.tar.gz root@服务器IP:/bumenguanli/releases/"
