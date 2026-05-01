# 部署指南

覆盖从本地开发到生产部署的完整流程。

---

## 环境要求

| 依赖 | 最低版本 |
|-----|---------|
| Python | 3.9+ |
| pip | 22.0+ |
| 操作系统 | macOS / Linux / Windows |

核心 Python 依赖：

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
```

---

## 方式一：本地运行（推荐用于开发和个人使用）

```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/data-cleaner-mvp.git
cd data-cleaner-mvp

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
streamlit run app.py
```

访问 [http://localhost:8501](http://localhost:8501)。

> **提示**：处理敏感数据时推荐本地运行，数据完全在你的电脑上处理。

---

## 方式二：Streamlit Cloud 部署（推荐用于公开演示）

Streamlit Cloud 是 Streamlit 官方提供的免费部署平台。

### 步骤

1. **推送代码到 GitHub 公开仓库**

   ```bash
   git init
   git add .
   git commit -m "v1.0 - Ready for Streamlit Cloud"
   git remote add origin https://github.com/YOUR_USERNAME/data-cleaner-mvp.git
   git branch -M main
   git push -u origin main
   ```

2. **登录 Streamlit Cloud**

   访问 [https://share.streamlit.io](https://share.streamlit.io)，使用 GitHub 账号登录。

3. **创建 App**

   - 点击右上角 "New app"
   - 选择仓库 `YOUR_USERNAME/data-cleaner-mvp`
   - 分支选择 `main`
   - 主文件路径：`app.py`
   - Python 版本选择 3.9 或更高
   - 点击 "Deploy"

4. **等待部署**

   部署过程中可以在 "Manage app" → "Logs" 查看日志。首次部署通常需要 3-5 分钟（安装依赖）。

5. **访问应用**

   部署成功后会获得类似 `https://your-app-name.streamlit.app` 的 URL。

### 更新应用

推送新的 commit 到 `main` 分支，Streamlit Cloud 会自动 re-deploy（或在控制台手动触发 "Reboot app"）。

### 注意事项

- 免费版内存限制约 1GB，处理 50MB 以内的文件通常没问题
- 超过 50MB 的文件会导致内存溢出或超时
- 如果需要处理更大的文件，建议使用私有部署方式

---

## 方式三：Docker 部署

创建 `Dockerfile`（放在项目根目录）：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.headless=true", "--server.port=8501", "--server.address=0.0.0.0"]
```

构建和运行：

```bash
# 构建镜像
docker build -t data-cleaner-mvp .

# 运行容器
docker run -p 8501:8501 data-cleaner-mvp

# 后台运行
docker run -d -p 8501:8501 --restart=unless-stopped --name data-cleaner data-cleaner-mvp
```

访问 [http://localhost:8501](http://localhost:8501)。

### Docker Compose（可选）

创建 `docker-compose.yml`：

```yaml
version: '3'
services:
  data-cleaner:
    build: .
    ports:
      - "8501:8501"
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

## 方式四：私有服务器部署

### 使用 Nginx 反向代理 + systemd 服务

**Step 1：部署应用**

```bash
# 服务器上创建目录
mkdir -p /opt/data-cleaner
cd /opt/data-cleaner

# 克隆代码
git clone https://github.com/YOUR_USERNAME/data-cleaner-mvp.git .

# 安装依赖
pip install -r requirements.txt

# 测试启动
streamlit run app.py --server.headless=true --server.port=8501
```

**Step 2：创建 systemd 服务**

```bash
sudo nano /etc/systemd/system/data-cleaner.service
```

```
[Unit]
Description=Data Cleaner MVP
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/data-cleaner
ExecStart=/usr/bin/streamlit run app.py --server.headless=true --server.port=8501 --server.address=127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable data-cleaner
sudo systemctl start data-cleaner
```

**Step 3：Nginx 反向代理**

```bash
sudo nano /etc/nginx/sites-available/data-cleaner
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/data-cleaner /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### HTTPS 配置（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 配置参数

`.streamlit/config.toml`：

```toml
[server]
maxUploadSize = 50       # 上传文件大小限制（MB）
headless = true          # 无头模式

[browser]
gatherUsageStats = false # 不收集使用数据

[theme]
primaryColor = "#0084FF"
backgroundColor = "#FFFFFF"
```

如需调整文件大小限制，同时修改此文件和 `src/file_handler.py` 中的 `MAX_FILE_SIZE_MB` 常量。

---

## 监控与日志

```bash
# Docker 日志
docker logs -f data-cleaner

# systemd 日志
sudo journalctl -u data-cleaner -f

# Streamlit Cloud 日志
# 在控制面板 "Manage app" → "Logs" 查看
```

---

*文档版本：v1.0 · 最后更新：2025-07*
