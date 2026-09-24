# 云服务器部署文档

本文档面向将系统部署到云服务器（Ubuntu/Debian）的场景，采用 SQLite + Docker Compose 的最简方案，通过 `http://服务器IP:8080` 直接访问。部署包已位于服务器 `/bumenguanli/dept-console.tar.gz`。

## 1. 部署架构

```
浏览器 ──http──> 服务器 8080 端口
                    │
              frontend 容器（Nginx）
              ├── 静态资源（Vue3 打包产物）
              └── /api/* 反代 ──> backend 容器（FastAPI, 9000）
                                        │
                                  Docker 卷 backend-data
                                  （SQLite 数据库 /data/dev.db）
```

| 端口 | 用途 | 是否对外开放 |
|---|---|---|
| 22 | SSH 远程登录 | 是 |
| 8080 | 系统访问入口（前端 + API 反代） | 是 |
| 9000 | 后端 API 直连 | 否（已发布到宿主机，靠云安全组拦截；VPC 内其他主机可直连，如需收紧见 FAQ） |

## 2. 服务器要求

- 操作系统：Ubuntu 20.04 / 22.04 / 24.04 或 Debian 11+
- 配置：最低 1 核 2G，磁盘 20G 以上（镜像构建需要临时空间；1 核 2G 建议先加 2G swap，见 FAQ）
- 网络：能访问外网（拉取 Docker 镜像与基础依赖）
- 云厂商安全组已放行 22、8080 端口（9000 不放行）

## 3. 安装 Docker

SSH 登录服务器后执行：

```bash
# 一键安装 Docker（官方脚本，已包含 compose 插件）
curl -fsSL https://get.docker.com | sudo sh

# 国内服务器如脚本下载慢，改用阿里云镜像安装：
curl -fsSL https://get.docker.com | sudo sh -s -- --mirror Aliyun

# 设置开机自启并启动
sudo systemctl enable --now docker

# 验证（两个命令都有版本输出即为成功）
sudo docker --version
sudo docker compose version
```

将当前用户加入 docker 组，避免每次都要 sudo（加完后需重新登录 SSH 生效）：

```bash
sudo usermod -aG docker $USER
```

### 3.1 国内服务器：配置镜像加速（可选）

如果拉取镜像超时，配置镜像加速地址：

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run"
  ]
}
EOF
sudo systemctl restart docker
```

> 加速地址失效时请自行更换可用的镜像源；海外服务器跳过此步。

## 4. 解压部署包

部署包已位于服务器 `/bumenguanli/dept-console.tar.gz`。若还未上传，先在本地开发机项目目录内执行：

```bash
scp dept-console.tar.gz user@服务器IP:/bumenguanli/
```

在服务器上解压并就位（应用目录为 `/bumenguanli/dept-console`，下文所有命令均在此目录执行）：

```bash
cd /bumenguanli
tar -xzf dept-console.tar.gz
mv 联通部门管理系统 dept-console
ls dept-console   # 应能看到 docker-compose.yml、backend、frontend、.env.example 等
```

## 5. 配置环境变量

```bash
cd /bumenguanli/dept-console
cp .env.example .env
```

编辑 `.env`，**必须修改**以下四项：

```bash
# 生成随机密钥，把输出填到 SECRET_KEY
openssl rand -hex 32

# ── 必改 ──
SECRET_KEY=<上面命令生成的随机字符串>
ADMIN_PASSWORD=<自定义管理员初始密码>
CORS_ORIGINS=http://<服务器IP>:8080
# 数据库必须落到 Docker 卷（/data 目录），否则数据存在容器内，重建容器会丢失！
DATABASE_URL=sqlite:////data/dev.db

# ── 按需修改 ──
# AI 功能（OpenAI 兼容协议，默认 DeepSeek）：
# 填入 LLM_API_KEY 启用 AI 绩效分析；留空则自动降级为演示数据（Mock 模式）
LLM_API_KEY=
```

> 注意两点：
> 1. `.env.example` 里默认的 `DATABASE_URL=sqlite:///./dev.db` 是**本地开发**路径（存在容器内 `/app/dev.db`），Docker 部署务必按上面改成 `sqlite:////data/dev.db`（四个斜杠）。
> 2. `ACCESS_TOKEN_EXPIRE_DAYS` 未在 docker-compose.yml 中透传，Docker 部署下修改不生效；如需调整登录有效期，需在 `docker-compose.yml` 的 backend `environment` 中补充该变量映射。

## 6. 构建并启动

```bash
cd /bumenguanli/dept-console
docker compose up -d --build
```

首次构建约需几分钟。查看运行状态：

```bash
docker compose ps        # 两个服务状态应为 Up（本系统未配置健康检查，无 healthy 状态）
docker compose logs -f   # Ctrl+C 退出，看到 "Uvicorn running" 即后端就绪
```

> 修改过 `.env` 后需执行 `docker compose up -d` 使新配置生效（会自动重建相关容器）。

## 7. 验证部署

```bash
# 服务器本机自测（返回 JSON 即正常）
curl http://localhost:8080/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"你设置的ADMIN_PASSWORD"}'
```

浏览器访问 `http://<服务器IP>:8080`：

1. 用 `admin` / `ADMIN_PASSWORD` 登录
2. **立即到成员管理页修改 admin 密码**
3. 检查看板、任务页正常加载；如需 AI 功能，到「系统设置」填入 LLM Key（DB 配置优先于 .env）

## 8. 日常运维

### 常用命令（均在 `/bumenguanli/dept-console` 下执行）

```bash
docker compose ps                    # 查看服务状态
docker compose logs -f backend       # 跟踪后端日志
docker compose logs -n 100 frontend  # 前端最近 100 行日志
docker compose restart backend       # 重启后端
docker compose down                  # 停止全部服务（数据卷保留，不丢数据）
docker compose up -d                 # 启动服务
```

### 版本更新

```bash
cd /bumenguanli/dept-console
git pull                             # 或重新上传打包并解压覆盖（目录结构保持一致）
docker compose up -d --build
```

### 数据备份（建议每周一次）

SQLite 数据库位于 Docker 卷中，备份方式：

```bash
cd /bumenguanli/dept-console
mkdir -p backups
docker compose stop backend   # 先停后端，保证快照完整一致
docker cp $(docker compose ps -aq backend):/data/dev.db ./backups/dept-$(date +%F).db
docker compose start backend  # 停机约几秒，建议低峰期执行
```

### 数据恢复

```bash
cd /bumenguanli/dept-console
docker compose stop backend
docker cp ./backups/dept-2026-09-24.db $(docker compose ps -aq backend):/data/dev.db
docker compose start backend
```

## 9. 常见问题

**Q：浏览器打不开 8080？**
依次排查：云厂商安全组是否放行 8080 → 服务器防火墙 `sudo ufw status`（如开启需 `sudo ufw allow 8080`）→ `docker compose ps` 确认 frontend 在运行。

**Q：页面能打开但接口报错 / 502？**
后端未就绪或启动失败：`docker compose logs -n 200 backend` 查看报错；刚启动时等 10 秒再刷新。

**Q：登录提示网络错误 / CORS 报错？**
检查 `.env` 中 `CORS_ORIGINS` 是否为 `http://<服务器IP>:8080`（与浏览器地址完全一致），改后执行 `docker compose up -d`。

**Q：构建时拉取镜像或 pip install 很慢/失败？**
镜像拉取慢按 3.1 节配置加速；pip 慢可在 `backend/Dockerfile` 的 pip 命令后追加 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。

**Q：忘记 admin 密码？**
在服务器上进入容器重置（把 `新密码` 替换掉）：

```bash
cd /bumenguanli/dept-console
docker compose exec backend python -c "from app.db.base import SessionLocal; from app.models import User; from app.core.security import hash_password; db=SessionLocal(); u=db.query(User).filter(User.username=='admin').first(); u.password_hash=hash_password('新密码'); db.commit(); print('ok')"
```

**Q：构建过程失败（npm install 报错、卡住或进程被杀）？**
常见原因是内存不足（1 核 2G 构建前端易被 OOM 杀掉），先加 2G swap 再重新构建：

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
docker compose up -d --build
```

磁盘不足用 `docker system df` 检查，`docker system prune -f` 清理无用镜像；npm 拉包慢可在 `frontend/Dockerfile` 的 `npm install` 后追加 `--registry=https://registry.npmmirror.com`。

**Q：想进一步收紧 9000 端口？**
compose 默认把后端发布到了宿主机所有网卡（`9000:9000`），VPC 内其他主机可绕过 Nginx 直连后端。公网访问已被安全组拦截；如需更严，把 `docker-compose.yml` 中 backend 的 `"9000:9000"` 改为 `"127.0.0.1:9000:9000"`（仅本机可访问），再 `docker compose up -d`。

**Q：8080 端口被占用想换端口？**
修改 `docker-compose.yml` 中 frontend 的 `"8080:80"` 为其他端口（如 `"8081:80"`），同时同步更新 `.env` 的 `CORS_ORIGINS`，再 `docker compose up -d`。
