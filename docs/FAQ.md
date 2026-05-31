# GitHub Skill Indexer - 常见问题解答

## 安装和配置

### Q1: 如何获取 GitHub Token？

**A:**
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 设置名称：`skill-indexer`
4. 勾选权限：`public_repo`
5. 点击 "Generate token"
6. 立即复制 Token（只显示一次）

### Q2: 数据库连接失败怎么办？

**A:** 检查以下几点：
1. MySQL 是否运行：`sudo systemctl status mysql`
2. 数据库是否创建：`mysql -u root -p -e "SHOW DATABASES;"`
3. 用户权限是否正确：`SHOW GRANTS FOR 'skill_user'@'localhost';`
4. `.env` 中的 `DATABASE_URL` 格式是否正确

**正确格式：**
```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/database_name?charset=utf8mb4
```

### Q3: 如何验证配置是否正确？

**A:** 运行健康检查脚本：
```bash
bash scripts/health_check.sh
```

---

## 使用问题

### Q4: Code Search 没有找到任何结果？

**A:** 可能的原因：
1. **搜索关键词不准确**：修改 `config.py` 中的 `SEARCH_QUERIES`
2. **GitHub 索引延迟**：新创建的文件可能需要几小时才能被索引
3. **API 限流**：检查 `x-ratelimit-remaining`

**解决方案：**
```python
# 在 config.py 中添加更多关键词
SEARCH_QUERIES = [
    'filename:SKILL.md "name:"',
    'filename:SKILL.md "description:"',
    'filename:SKILL.md "license:"',
    'filename:SKILL.md "compatibility:"',
]
```

### Q5: 为什么有些 Skills 被标记为 risky？

**A:** 风险扫描检测到以下内容：
- 危险命令：`rm -rf`, `curl | bash`, `eval()`
- 敏感信息：`PRIVATE_KEY`, `SECRET`, `TOKEN`
- 包含 scripts 目录

**这是正常的安全机制**，可以手动审核后修改状态：
```sql
UPDATE github_skills SET status='approved' WHERE id=123;
```

### Q6: 如何手动添加一个 Skill？

**A:** 使用 user_submit 命令：
```bash
# 方式一：提交整个仓库（自动扫描）
python main.py user_submit --repo anthropics/anthropic-quickstarts

# 方式二：提交特定文件
python main.py user_submit --repo openai/skills --path skills/pdf/SKILL.md
```

---

## 性能问题

### Q7: 采集速度太慢怎么办？

**A:** 主要受 GitHub API 限流影响：
- **Code Search**：30 次/小时（认证）
- **Contents API**：5000 次/小时（认证）

**优化建议：**
1. 减少搜索关键词数量
2. 增加 `CODE_SEARCH_INTERVAL`（降低频率）
3. 使用多个 GitHub Token 轮换（需修改代码）

### Q8: 数据库查询慢怎么办？

**A:**
1. **检查索引**：
```sql
SHOW INDEX FROM github_skills;
```

2. **添加缺失的索引**：
```sql
CREATE INDEX idx_repo_full_name ON github_skills(repo_full_name);
CREATE INDEX idx_status ON github_skills(status);
CREATE INDEX idx_stars ON github_skills(stars);
```

3. **定期优化表**：
```sql
OPTIMIZE TABLE github_skills;
```

### Q9: 日志文件太大怎么办？

**A:** 配置日志轮转：
```bash
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
}
```

---

## API 限流问题

### Q10: 遇到 "API rate limit exceeded" 错误？

**A:**
1. **检查剩余配额**：
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/rate_limit
```

2. **等待限流重置**（通常 1 小时）

3. **减少搜索频率**：
```python
# 在 config.py 中
CODE_SEARCH_INTERVAL = 15  # 从 10 秒增加到 15 秒
```

### Q11: 如何避免触发限流？

**A:**
1. **使用认证 Token**（已实现）
2. **监控 `x-ratelimit-remaining`**（已实现）
3. **主动等待**（已实现）
4. **减少搜索关键词**
5. **增加间隔时间**

---

## 定时任务问题

### Q12: Cron 任务没有执行？

**A:** 检查以下几点：
1. **Cron 服务是否运行**：
```bash
sudo systemctl status cron
```

2. **查看 Cron 日志**：
```bash
sudo tail -f /var/log/syslog | grep CRON
```

3. **确保路径正确**（使用绝对路径）：
```bash
0 3 * * * cd /opt/skill-catcher && /opt/skill-catcher/venv/bin/python main.py code_search
```

4. **检查权限**：
```bash
chmod +x /opt/skill-catcher/main.py
```

### Q13: 如何测试 Cron 任务？

**A:**
1. **手动运行命令**：
```bash
cd /opt/skill-catcher && /opt/skill-catcher/venv/bin/python main.py code_search
```

2. **设置临时 Cron（5 分钟后执行）**：
```bash
# 获取当前时间 + 5 分钟
date -d "+5 minutes" "+%M %H %d %m *"

# 添加到 crontab
crontab -e
# 例如：35 14 * * * cd /opt/skill-catcher && ...
```

3. **查看执行结果**：
```bash
tail -f logs/code_search.log
```

---

## 数据问题

### Q14: 如何清空数据库重新开始？

**A:**
```bash
# 方式一：删除所有数据（保留表结构）
mysql -u skill_user -p skill_index -e "TRUNCATE TABLE github_skills; TRUNCATE TABLE github_scan_tasks;"

# 方式二：重新初始化数据库
python scripts/init_db.py
```

### Q15: 如何导出数据？

**A:**
```bash
# 导出为 SQL
mysqldump -u skill_user -p skill_index > backup.sql

# 导出为 CSV
mysql -u skill_user -p skill_index -e "SELECT * FROM github_skills" | sed 's/\t/,/g' > skills.csv

# 使用 Python 导出为 JSON
python -c "
from src.storage.skill_repository import SkillRepository
import json

with SkillRepository() as repo:
    skills = repo.find_all()
    data = [s.to_dict() for s in skills]
    with open('skills.json', 'w') as f:
        json.dump(data, f, indent=2)
"
```

### Q16: 如何批量修改 Skill 状态？

**A:**
```sql
-- 批量审核通过（stars > 100 且 risk_level = 'low'）
UPDATE github_skills
SET status='approved'
WHERE stars > 100 AND risk_level='low' AND status='pending';

-- 批量标记为 risky（risk_level = 'high'）
UPDATE github_skills
SET status='risky'
WHERE risk_level='high' AND status='pending';
```

---

## 开发问题

### Q17: 如何添加新的搜索关键词？

**A:** 编辑 `config.py`：
```python
SEARCH_QUERIES = [
    'filename:SKILL.md "name:"',
    'filename:SKILL.md "description:"',
    # 添加新关键词
    'filename:SKILL.md "author:"',
    'filename:SKILL.md "version:"',
]
```

### Q18: 如何添加新的风险检测规则？

**A:** 编辑 `src/scanner/risk_scanner.py`：
```python
# 在 DANGER_KEYWORDS 中添加
DANGER_KEYWORDS = [
    'rm -rf',
    'curl | bash',
    # 添加新规则
    'sudo rm',
    'dd if=',
]
```

### Q19: 如何运行单元测试？

**A:**
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_github_client.py -v

# 生成覆盖率报告
pytest --cov=src tests/
pytest --cov=src --cov-report=html tests/
```

---

## 部署问题

### Q20: 如何在生产环境部署？

**A:** 参考 [部署指南](deployment.md)，关键步骤：
1. 使用独立的数据库服务器
2. 配置日志轮转
3. 设置监控和告警
4. 配置自动备份
5. 使用 systemd 管理服务

### Q21: 如何升级到新版本？

**A:**
```bash
# 1. 备份数据库
mysqldump -u skill_user -p skill_index > backup_before_upgrade.sql

# 2. 停止定时任务
crontab -e  # 注释掉所有任务

# 3. 拉取最新代码
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

## 其他问题

### Q22: 项目支持哪些操作系统？

**A:**
- ✅ Linux (Ubuntu, Debian, CentOS, RHEL)
- ✅ macOS
- ✅ Windows (需要 WSL 或修改脚本)

### Q23: 可以使用其他数据库吗？

**A:** 理论上可以，但需要修改：
1. `requirements.txt` 中的数据库驱动
2. `.env` 中的 `DATABASE_URL`
3. 可能需要调整 SQL 语法

**支持的数据库：**
- MySQL 8.0+ (推荐)
- PostgreSQL 12+
- SQLite (仅用于开发测试)

### Q24: 如何贡献代码？

**A:**
1. Fork 项目
2. 创建功能分支：`git checkout -b feature/my-feature`
3. 编写代码和测试
4. 提交：`git commit -m "Add my feature"`
5. 推送：`git push origin feature/my-feature`
6. 创建 Pull Request

### Q25: 在哪里报告 Bug？

**A:**
- GitHub Issues: [项目地址]/issues
- 提供详细信息：
  - 错误信息和日志
  - 复现步骤
  - 系统环境（OS, Python 版本）

---

## 联系支持

如果以上 FAQ 没有解决你的问题：
1. 查看 [部署指南](deployment.md)
2. 查看 [项目总结](PROJECT_SUMMARY.md)
3. 提交 GitHub Issue
4. 联系维护者

---

**最后更新：** 2026-05-31
