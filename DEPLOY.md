# 青青草原牛马管理系统 — 部署与升级规范

> 本文档是**强制规范**。每次打包、上传、升级都必须按本文执行，避免再次出现双系统并存、端口冲突、数据未载入等问题。

---

## 1. 环境约定（不得随意更改）

| 项目 | 约定值 | 说明 |
|---|---|---|
| 服务器部署目录 | `/bumenguanli/bmms` | 固定唯一目录，所有版本都解压覆盖到这里 |
| 部署包存档目录 | `/bumenguanli/releases/` | 保留历史包，用于回滚 |
| Compose 项目名 | `bmms`（=目录名） | 决定容器名 `bmms-backend-1` / `bmms-frontend-1` |
| 数据卷 | `bmms_backend-data` | 数据库持久化位置，**升级默认保留** |
| 对外端口 | `8080`（前端网页） | 浏览器访问 `http://服务器IP:8080` |
| 后端端口 | `9000`（容器内部对外） | 与服务器上 8000 端口的 opt-backend 无关，勿混淆 |
| 种子库 | 包内 `seed/dev.db` | 仅 volume 为空时自动载入，**已有数据不会覆盖** |

**核心原则：一个系统只允许存在一个 compose 项目目录。** 禁止把新版本解压到新目录后两套同时跑（历史事故：`dept-console` 与新目录并存，争抢 8080/9000 端口导致启动失败）。

---

## 2. 部署包命名规范（强制）

```
bmms-v{主}.{次}.{修订}-{日期}.tar.gz
示例：bmms-v0.3.0-20260924.tar.gz
```

- 版本号写在项目根目录 `VERSION` 文件里，打包脚本自动读取，**不得手工在文件名里自由发挥**
- 版本号规则（语义化）：
  - **修订位 +1**（0.3.0 → 0.3.1）：修 Bug、样式微调、文案修改
  - **次位 +1**（0.3.0 → 0.4.0）：新增功能（如新的页面、接口、定时任务）
  - **主位 +1**（0.9.0 → 1.0.0）：数据库结构破坏性变更、大版本重构
- **每次升级必须 +1 版本**，包名里带当天日期；同名包禁止覆盖已上传到服务器的历史包

## 3. 本机打包流程

**一键打包（必须用脚本，禁止手工 tar）：**

```bash
cd /Users/goofy/项目/联通部门管理系统
# 若本次有功能升级，先改 VERSION 文件，再打包
./scripts/package.sh
```

脚本自动完成三件事：
1. 把本地 `backend/dev.db`（含全部账号、任务、改动记录）复制为 `seed/dev.db`
2. 执行前端构建校验（类型检查不过则中止打包）
3. 按规范命名压缩到 `/Users/goofy/项目/bmms-vX.Y.Z-日期.tar.gz`

包内**包含**：全部源码、`docker-compose.yml`、`seed/dev.db`、`VERSION`、`.env`（LLM 密钥随包分发，走 scp 加密传输；服务器解压后 compose 自动读取，**不要在公网网页端提交密钥**）。
包内**不包含**：`node_modules`、`.venv`、构建产物、`.git`、`backend/dev.db`（开发库本体）。

> 注意：`.env` 中**禁止**配置 `DATABASE_URL`，否则会覆盖 compose 默认值 `sqlite:////data/dev.db`，导致数据不落数据卷。LLM 配置优先级：网页设置（DB）> `.env`；只要从未在网页保存过 API Key，`.env` 即为生效配置。

## 4. 服务器升级流程（标准 7 步）

```bash
# ── 本机 ──
# 1. 上传到存档目录（不要散放在 /bumenguanli 根目录）
scp /Users/goofy/项目/bmms-vX.Y.Z-日期.tar.gz root@服务器IP:/bumenguanli/releases/

# ── 服务器 ──
# 2. 备份当前线上数据库（防手滑）
docker run --rm -v bmms_backend-data:/data -v /bumenguanli:/backup \
  python:3.12-slim cp /data/dev.db /backup/db-backup-$(date +%Y%m%d-%H%M).db

# 3. 解压覆盖到固定部署目录（统一目录 = compose 自动替换旧容器）
mkdir -p /bumenguanli/bmms
tar -xzf /bumenguanli/releases/bmms-vX.Y.Z-日期.tar.gz -C /bumenguanli/bmms
cd /bumenguanli/bmms

# 4. 重建并启动（同目录执行会自动停旧容器、换新镜像，中断约半分钟）
docker compose up -d --build

# 5. 清理悬空旧镜像（可选，保持整洁）
docker image prune -f

# 6. 验证（见第 5 节清单）

# 7. 确认无误后，删除上一个版本的旧包？不删——releases 目录保留最近 3 个包用于回滚
```

## 5. 验证清单（每项必查）

```bash
docker compose ps                     # bmms-backend / bmms-frontend 均为 Up
docker compose logs backend --tail 30 # 出现「scheduler:下次阶段总结生成：…」
curl -s -X POST http://localhost:9000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"你的密码"}' | head -c 100   # 返回 token
```

- 浏览器打开 `http://服务器IP:8080` → 能看到任务数据
- 手机浏览器打开 → 侧边栏为抽屉式（汉堡按钮）
- 「工作日志」页 → 有「阶段总结」标签页

## 6. 数据库规则（何时保留、何时重置）

- **正常升级：什么都不做。** volume 里的库原样保留，seed 不会覆盖线上数据
- **想以本地最新数据重置线上**（如本地录入了一批任务要带上服务器）：
  ```bash
  docker compose down
  docker volume rm bmms_backend-data     # 删旧卷
  docker compose up -d --build           # 首次启动自动从 seed 载入完整数据
  ```
- **升级后账号密码忘记**：无法找回（bcrypt 加密），按上一步重置为本地库中的密码

## 7. 回滚流程

```bash
# 用 releases 里上一个可用版本覆盖回固定目录即可
tar -xzf /bumenguanli/releases/bmms-v0.2.9-日期.tar.gz -C /bumenguanli/bmms
cd /bumenguanli/bmms && docker compose up -d --build
# 若新版本改过数据库结构导致旧代码不兼容，再按第 6 节删卷重置，并用第 4 步的 db-backup 文件还原：
# docker compose down && docker run --rm -v bmms_backend-data:/data -v /bumenguanli:/backup \
#   python:3.12-slim sh -c "cp /backup/db-backup-*.db /data/dev.db" && docker compose up -d
```

## 8. 历史问题记录（升级前先读）

| 日期 | 事故 | 教训 |
|---|---|---|
| 2026-09-24 | 旧系统 `dept-console`（目录 /bumenguanli/dept-console）未停止，与新目录新系统并存，争抢 8080/9000 端口；且旧卷为空库导致"部署好的系统没有任务数据" | 必须使用唯一固定目录 `/bumenguanli/bmms`；升级前 `docker ps` 确认无其他项目占用端口；数据靠 seed 机制随包分发 |

## 9. 服务器上其他系统（严禁误伤）

- `opt-backend`（8000 端口）与 `opt-db`（5432 TimescaleDB）是**另一套无关系统**，升级本系统时**不得**对其执行任何 down/stop/rm 操作
