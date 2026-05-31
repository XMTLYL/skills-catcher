# GitHub Skill Catcher

[English](README.md) | 简体中文

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/XMTLYL/skills-catcher/workflows/Tests/badge.svg)](https://github.com/XMTLYL/skills-catcher/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

一个用于从 GitHub 自动发现、获取、解析并索引公开 Skills 的元数据索引服务。

## 项目简介

GitHub skills-catcher 不是爬虫或镜像系统，而是一个元数据索引服务，只保存 Skill 的名称、描述、仓库链接、Stars 等信息，不下载完整的 scripts 或 assets。

### 核心功能

- 🔍 **自动发现**：通过 GitHub Code Search API 搜索 SKILL.md 文件
- 📊 **元数据提取**：解析 SKILL.md 的 frontmatter 和仓库信息
- 🛡️ **风险扫描**：检测危险命令、API Key、敏感信息
- 🔄 **增量更新**：使用 ETag 机制避免重复请求
- 📈 **统计分析**：Stars、Forks、License、更新时间等

### 三种采集方式

1. **GitHub Code Search**：搜索全网公开仓库中的 SKILL.md
2. **指定仓库扫描**：扫描已知的高质量 Skill 仓库
3. **用户提交**：用户主动提交 GitHub 仓库地址

## 快速开始

### 环境要求

- Python 3.11+
- MySQL 8.0+
- GitHub Personal Access Token

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/XMTLYL/skills-catcher.git
cd skill-catcher
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
nano .env  # 填写 GITHUB_TOKEN 和 DATABASE_URL
```

4. **初始化数据库**
```bash
python scripts/init_db.py
```

5. **运行采集任务**
```bash
# 使用统一入口
python main.py code_search          # Code Search 采集
python main.py repo_scan            # 仓库扫描
python main.py update_check         # 增量更新检查
python main.py stats                # 显示统计

# 或使用独立脚本
python scripts/run_code_search.py
python scripts/run_repo_scan.py
python scripts/update_check.py
```

### 完整部署指南

详细的部署步骤请参考：[部署指南](docs/deployment.md)

## 项目结构

```
skill-catcher/
├── config.py                     # 配置管理
├── main.py                       # 主入口
├── requirements.txt              # Python 依赖
│
├── src/                          # 源代码
│   ├── models.py                 # 数据库模型
│   ├── database.py               # 数据库连接
│   ├── github/                   # GitHub API 交互层
│   ├── parser/                   # 解析层
│   ├── scanner/                  # 扫描层
│   ├── acquisition/              # 采集策略层
│   ├── storage/                  # 存储层
│   └── utils/                    # 工具层
│
├── scripts/                      # 独立运行脚本
│   ├── init_db.py                # 数据库初始化
│   ├── run_code_search.py        # Code Search 采集
│   ├── run_repo_scan.py          # 仓库扫描
│   └── update_check.py           # 增量更新
│
├── tests/                        # 测试
└── logs/                         # 日志
```

## 配置说明

### 环境变量 (.env)

```env
# GitHub API Token (必填)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# 数据库连接 (必填)
DATABASE_URL=mysql+pymysql://user:password@host:port/database?charset=utf8mb4

# 日志级别 (可选)
LOG_LEVEL=INFO
```

### 获取 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `public_repo` 权限
4. 生成并复制 Token

## 数据库表结构

### github_skills（核心表）

存储 Skill 的元数据和索引信息。

**主要字段：**
- `name`, `description` - Skill 名称和描述
- `repo_full_name`, `repo_url` - 仓库信息
- `skill_path`, `skill_html_url` - SKILL.md 路径和链接
- `stars`, `forks`, `license` - 仓库统计
- `risk_level`, `risk_flags` - 风险评估
- `status` - 状态（pending/approved/rejected/risky/offline）

### github_scan_tasks（任务表）

记录每次采集任务的执行情况。

### github_known_repositories（已知仓库表）

存储已知的高质量 Skill 仓库列表。

## 使用示例

### 手动运行 Code Search

```bash
python scripts/run_code_search.py
```

输出示例：
```
[1/30] 正在处理: openai/skills/pdf-processing/SKILL.md
[2/30] 正在处理: anthropics/skills/browser/SKILL.md
...
✅ 任务完成 - 发现: 30, 保存: 25, 跳过: 5, 失败: 0
```

### 定时任务配置

使用 cron 定时运行：

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 3 点运行 Code Search
0 3 * * * cd /path/to/skill-catcher && python3 scripts/run_code_search.py >> logs/code_search.log 2>&1

# 每天凌晨 4 点扫描指定仓库
0 4 * * * cd /path/to/skill-catcher && python3 scripts/run_repo_scan.py >> logs/repo_scan.log 2>&1

# 每周日凌晨 2 点增量更新
0 2 * * 0 cd /path/to/skill-catcher && python3 scripts/update_check.py >> logs/update_check.log 2>&1
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=src tests/

# 运行特定测试文件
pytest tests/test_parser.py
```

### 添加新的搜索关键词

编辑 `config.py`：

```python
SEARCH_QUERIES = [
    'filename:SKILL.md "description:"',
    'filename:SKILL.md "your-new-keyword"',
    # 添加更多关键词...
]
```

### 添加已知仓库

```sql
INSERT INTO github_known_repositories
(repo_full_name, repo_url, source_level, scan_enabled)
VALUES
('owner/repo', 'https://github.com/owner/repo', 'trusted', 1);
```

## 风险扫描规则

### 风险等级

- **低风险**：仅 SKILL.md，无 scripts，无危险关键词
- **中风险**：包含 scripts，需要 API Key，需要网络访问
- **高风险**：出现 `rm -rf`, `curl | bash`, `eval()`, `PRIVATE_KEY`

### 关键词列表

**高风险关键词：**
- `rm -rf`, `curl | bash`, `wget`, `eval(`, `exec(`
- `PRIVATE_KEY`, `id_rsa`, `ssh`

**中风险关键词：**
- `subprocess`, `os.system`, `API_KEY`, `SECRET`, `TOKEN`
- `.env`, `process.env`

## 限流策略

- **Code Search API**：6次/分钟，每次间隔 10 秒
- **Contents API**：每次间隔 0.5-1 秒
- **自动等待**：`x-ratelimit-remaining` < 10 时主动等待
- **错误处理**：403/429 触发 60 秒等待 + 指数退避

## 增量更新机制

使用 ETag 和 Last-Modified 实现增量更新：

1. 首次请求保存 ETag 和 Last-Modified
2. 后续请求带上 `If-None-Match` 和 `If-Modified-Since`
3. 304 响应时只更新 `last_checked_at`，不重新解析

## 故障排查

### 数据库连接失败

检查 `.env` 中的 `DATABASE_URL` 是否正确：
```bash
mysql -u user -p -h host -P port database
```

### GitHub API 限流

检查 Token 是否有效：
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/rate_limit
```

### 日志查看

```bash
# 查看最新日志
tail -f logs/code_search.log

# 搜索错误
grep "ERROR" logs/*.log
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！详细信息请参考 [贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用 [Apache-2.0 License](LICENSE) 开源许可证。

## 联系方式

- 提交 Issue: [GitHub Issues](https://github.com/XMTLYL/skills-catcher/issues)
- 讨论: [GitHub Discussions](https://github.com/XMTLYL/skills-catcher/discussions)

## 参考资料

- [GitHub REST API 文档](https://docs.github.com/en/rest)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [设计文档](docs/github_skills_acquisition_plan.md)
