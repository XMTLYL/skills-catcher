# 部署指南

本文档提供 GitHub Skill Indexer 的完整部署步骤。

## 环境要求

### 软件要求
- Python 3.11+
- MySQL 8.0+
- Git

### 硬件要求
- 最小：1 CPU, 2GB RAM, 10GB 磁盘
- 推荐：2 CPU, 4GB RAM, 20GB 磁盘

### 网络要求
- 稳定的互联网连接（访问 GitHub API）
- 建议使用固定 IP（用于定时任务）

---

## 部署步骤

### 1. 安装依赖

#### Ubuntu/Debian
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# 安装 MySQL
sudo apt install mysql-server -y

# 启动 MySQL
sudo systemctl start mysql
sudo systemctl enable mysql
```

#### CentOS/RHEL
```bash
# 安装 Python 3.11
sudo yum install python3.11 python3.11-pip -y

# 安装 MySQL
sudo yum install mysql-server -y

# 启动 MySQL
sudo systemctl start mysqld
sudo systemctl enable mysqld
```

---

### 2. 配置 MySQL

```bash
# 登录 MySQL
sudo mysql -u root -p

# 创建数据库
CREATE DATABASE skill_index CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户
CREATE USER 'skill_user'@'localhost' IDENTIFIED BY 'your_secure_password';

# 授权
GRANT ALL PRIVILEGES ON skill_index.* TO 'skill_user'@'localhost';
FLUSH PRIVILEGES;

# 退出
EXIT;
```

---

### 3. 获取 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 设置 Token 名称：`skill-indexer`
4. 勾选权限：
   - ✅ `public_repo` - 访问公开仓库
5. 点击 "Generate token"
6. **立即复制 Token**（只显示一次）

---

### 4. 部署项目

```bash
# 创建部署目录
sudo mkdir -p /opt/skill-catcher
cd /opt/skill-catcher

# 克隆项目（如果使用 Git）
git clone <your-repo-url> .

# 或者上传项目文件
# scp -r skill-catcher/* user@server:/opt/skill-catcher/

# 设置权限
sudo chown -R $USER:$USER /opt/skill-catcher

# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

### 5. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

填写以下内容：
```env
# GitHub API Token（必填）
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 数据库连接（必填）
DATABASE_URL=mysql+pymysql://skill_user:your_secure_password@localhost:3306/skill_index?charset=utf8mb4

# 日志级别（可选）
LOG_LEVEL=INFO
```

保存并退出（Ctrl+X, Y, Enter）

---

### 6. 初始化数据库

```bash
# 激活虚拟环境（如果未激活）
source venv/bin/activate

# 运行初始化脚本
python scripts/init_db.py
```

**预期输出：**
```
============================================================
Database initialization completed!
============================================================

Next steps:
1. Copy .env.example to .env
2. Fill in your GITHUB_TOKEN and DATABASE_URL
3. Run: python scripts/run_code_search.py
============================================================
```

---

### 7. 测试运行

```bash
# 测试 Code Search（会实际调用 GitHub API）
python main.py code_search

# 查看统计
python main.py stats

# 测试仓库扫描
python main.py repo_scan --repo anthropics/anthropic-quickstarts
```

---

### 8. 配置定时任务

#### 方式一：使用 Cron（推荐）

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（修改路径）
# 每天凌晨 3 点运行 Code Search
0 3 * * * cd /opt/skill-catcher && /opt/skill-catcher/venv/bin/python main.py code_search >> logs/code_search.log 2>&1

# 每天凌晨 4 点运行仓库扫描
0 4 * * * cd /opt/skill-catcher && /opt/skill-catcher/venv/bin/python main.py repo_scan >> logs/repo_scan.log 2>&1

# 每周日凌晨 2 点运行增量更新检查
0 2 * * 0 cd /opt/skill-catcher && /opt/skill-catcher/venv/bin/python main.py update_check --limit 200 >> logs/update_check.log 2>&1
```

保存并退出。

**验证 Cron 配置：**
```bash
# 查看已配置的定时任务
crontab -l

# 查看 Cron 日志
sudo tail -f /var/log/syslog | grep CRON
```

#### 方式二：使用 systemd timer

创建服务文件：
```bash
sudo nano /etc/systemd/system/skill-indexer-code-search.service
```

内容：
```ini
[Unit]
Description=GitHub Skill Indexer - Code Search
After=network.target mysql.service

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/opt/skill-catcher
Environment="PATH=/opt/skill-catcher/venv/bin"
ExecStart=/opt/skill-catcher/venv/bin/python main.py code_search
StandardOutput=append:/opt/skill-catcher/logs/code_search.log
StandardError=append:/opt/skill-catcher/logs/code_search.log

[Install]
WantedBy=multi-user.target
```

创建 timer 文件：
```bash
sudo nano /etc/systemd/system/skill-indexer-code-search.timer
```

内容：
```ini
[Unit]
Description=Run GitHub Skill Indexer Code Search daily

[Timer]
OnCalendar=daily
OnCalendar=03:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用 timer：
```bash
sudo systemctl daemon-reload
sudo systemctl enable skill-indexer-code-search.timer
sudo systemctl start skill-indexer-code-search.timer

# 查看状态
sudo systemctl status skill-indexer-code-search.timer
```

---

### 9. 配置日志轮转

```bash
# 创建 logrotate 配置
sudo nano /etc/logrotate.d/skill-catcher
```

内容：
```
/opt/skill-catcher/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 your_user your_user
}
```

测试配置：
```bash
sudo logrotate -d /etc/logrotate.d/skill-catcher
```

---

### 10. 配置监控（可选）

#### 邮件通知

安装 mailutils：
```bash
sudo apt install mailutils -y
```

修改 crontab，添加邮件通知：
```bash
MAILTO=your-email@example.com

0 3 * * * cd /opt/skill-catcher && /opt/skill-catcher/venv/bin/python main.py code_search >> logs/code_search.log 2>&1 || echo "Code Search failed" | mail -s "Skill Indexer Alert" $MAILTO
```

#### 健康检查脚本

创建健康检查脚本：
```bash
nano /opt/skill-catcher/scripts/health_check.sh
```

内容：
```bash
#!/bin/bash

# 检查最近一次任务是否成功
LAST_LOG=$(tail -1 /opt/skill-catcher/logs/code_search.log)

if [[ $LAST_LOG == *"Error"* ]]; then
    echo "Health check failed: Error detected in logs"
    exit 1
fi

echo "Health check passed"
exit 0
```

添加到 cron：
```bash
# 每小时检查一次
0 * * * * /opt/skill-catcher/scripts/health_check.sh
```

---

## 验证部署

### 1. 检查数据库连接
```bash
python -c "from src.database import engine; print('Database connection OK')"
```

### 2. 检查 GitHub API
```bash
python -c "from src.github.client import GitHubClient; client = GitHubClient(); print('GitHub API OK')"
```

### 3. 运行完整测试
```bash
# 运行单元测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest --cov=src tests/
```

### 4. 查看数据库
```bash
mysql -u skill_user -p skill_index

# 查看 Skills
SELECT COUNT(*) FROM github_skills;
SELECT name, repo_full_name, stars, status FROM github_skills LIMIT 10;

# 查看任务
SELECT task_type, status, total_found, total_saved FROM github_scan_tasks ORDER BY created_at DESC LIMIT 10;
```

---

## 故障排查

### 问题 1：数据库连接失败

**错误信息：**
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")
```

**解决方案：**
1. 检查 MySQL 是否运行：`sudo systemctl status mysql`
2. 检查 `.env` 中的 `DATABASE_URL` 是否正确
3. 检查用户权限：`SHOW GRANTS FOR 'skill_user'@'localhost';`

### 问题 2：GitHub API 限流

**错误信息：**
```
RateLimitError: API rate limit exceeded
```

**解决方案：**
1. 检查 Token 是否有效：`curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/rate_limit`
2. 等待限流重置（通常 1 小时）
3. 减少搜索关键词数量（修改 `config.py` 中的 `SEARCH_QUERIES`）

### 问题 3：Cron 任务未执行

**解决方案：**
1. 检查 cron 服务：`sudo systemctl status cron`
2. 查看 cron 日志：`sudo tail -f /var/log/syslog | grep CRON`
3. 确保路径正确（使用绝对路径）
4. 确保脚本有执行权限：`chmod +x scripts/*.py`

### 问题 4：日志文件过大

**解决方案：**
1. 配置 logrotate（见上文）
2. 手动清理：`find logs/ -name "*.log" -mtime +30 -delete`

---

## 性能优化

### 1. 数据库优化

```sql
-- 添加索引（如果未自动创建）
CREATE INDEX idx_repo_full_name ON github_skills(repo_full_name);
CREATE INDEX idx_status ON github_skills(status);
CREATE INDEX idx_stars ON github_skills(stars);

-- 定期优化表
OPTIMIZE TABLE github_skills;
OPTIMIZE TABLE github_scan_tasks;
```

### 2. 限流优化

修改 `config.py`：
```python
# 减少搜索关键词（降低 API 调用）
SEARCH_QUERIES = [
    'filename:SKILL.md "description:"',
    'filename:SKILL.md "name:"',
]

# 增加间隔时间（更保守的限流）
CODE_SEARCH_INTERVAL = 15  # 从 10 秒增加到 15 秒
```

### 3. 批量处理优化

修改采集脚本，增加批量提交：
```python
# 每 50 条记录提交一次（而不是每条）
if idx % 50 == 0:
    skill_repo.session.commit()
```

---

## 安全建议

1. **保护 .env 文件**
   ```bash
   chmod 600 .env
   ```

2. **使用强密码**
   - MySQL 密码至少 16 字符
   - 包含大小写字母、数字、特殊字符

3. **定期更新依赖**
   ```bash
   pip list --outdated
   pip install --upgrade <package>
   ```

4. **限制数据库访问**
   ```sql
   -- 只允许本地访问
   REVOKE ALL PRIVILEGES ON *.* FROM 'skill_user'@'%';
   GRANT ALL PRIVILEGES ON skill_index.* TO 'skill_user'@'localhost';
   ```

5. **配置防火墙**
   ```bash
   # 只允许必要的端口
   sudo ufw allow 22/tcp  # SSH
   sudo ufw enable
   ```

---

## 备份和恢复

### 备份数据库

```bash
# 创建备份目录
mkdir -p /opt/skill-catcher/backups

# 备份数据库
mysqldump -u skill_user -p skill_index > /opt/skill-catcher/backups/skill_index_$(date +%Y%m%d).sql

# 压缩备份
gzip /opt/skill-catcher/backups/skill_index_$(date +%Y%m%d).sql
```

### 自动备份（Cron）

```bash
# 每天凌晨 1 点备份
0 1 * * * mysqldump -u skill_user -p'your_password' skill_index | gzip > /opt/skill-catcher/backups/skill_index_$(date +\%Y\%m\%d).sql.gz

# 删除 30 天前的备份
0 2 * * * find /opt/skill-catcher/backups -name "*.sql.gz" -mtime +30 -delete
```

### 恢复数据库

```bash
# 解压备份
gunzip /opt/skill-catcher/backups/skill_index_20240101.sql.gz

# 恢复数据库
mysql -u skill_user -p skill_index < /opt/skill-catcher/backups/skill_index_20240101.sql
```

---

## 升级指南

### 升级步骤

```bash
# 1. 备份数据库
mysqldump -u skill_user -p skill_index > backup_before_upgrade.sql

# 2. 停止定时任务
crontab -e  # 注释掉所有任务

# 3. 拉取最新代码
cd /opt/skill-catcher
git pull origin main

# 4. 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. 运行数据库迁移（如果有）
python scripts/migrate_db.py

# 6. 测试
python main.py stats

# 7. 恢复定时任务
crontab -e  # 取消注释
```

---

## 联系支持

如有问题，请：
1. 查看日志：`tail -f logs/*.log`
2. 查看 GitHub Issues
3. 联系维护者

---

**部署完成！** 🎉
