# API 参考文档

本文档提供 GitHub Skill Indexer 的核心 API 参考。

---

## 目录

1. [GitHub Client API](#github-client-api)
2. [Parser API](#parser-api)
3. [Scanner API](#scanner-api)
4. [Storage API](#storage-api)
5. [Acquisition API](#acquisition-api)

---

## GitHub Client API

### GitHubClient

GitHub API 客户端，提供对 GitHub REST API 的封装。

#### 初始化

```python
from src.github.client import GitHubClient

client = GitHubClient(token="ghp_xxxxxxxxxxxx")
```

**参数：**
- `token` (str, optional): GitHub Personal Access Token。如果不提供，从环境变量 `GITHUB_TOKEN` 读取。

#### 方法

##### search_code()

搜索代码文件。

```python
results = client.search_code(
    query='filename:SKILL.md "name:"',
    per_page=30,
    page=1
)
```

**参数：**
- `query` (str): 搜索查询字符串
- `per_page` (int): 每页结果数（默认 30，最大 100）
- `page` (int): 页码（默认 1）

**返回：**
```python
{
    'total_count': 150,
    'items': [
        {
            'name': 'SKILL.md',
            'path': 'skills/pdf/SKILL.md',
            'html_url': 'https://github.com/...',
            'repository': {
                'full_name': 'owner/repo',
                'html_url': 'https://github.com/owner/repo',
                'stargazers_count': 100,
                'forks_count': 20,
                'license': {'spdx_id': 'MIT'}
            }
        }
    ]
}
```

##### get_file_content()

获取文件内容。

```python
content = client.get_file_content(
    owner='anthropics',
    repo='anthropic-quickstarts',
    path='skills/pdf/SKILL.md'
)
```

**参数：**
- `owner` (str): 仓库所有者
- `repo` (str): 仓库名称
- `path` (str): 文件路径

**返回：**
```python
{
    'content': 'base64_encoded_content',
    'encoding': 'base64',
    'sha': 'abc123...',
    'size': 1234,
    'html_url': 'https://github.com/...'
}
```

##### get_repository()

获取仓库信息。

```python
repo_info = client.get_repository(
    owner='anthropics',
    repo='anthropic-quickstarts'
)
```

**返回：**
```python
{
    'full_name': 'anthropics/anthropic-quickstarts',
    'html_url': 'https://github.com/anthropics/anthropic-quickstarts',
    'description': 'Repository description',
    'stargazers_count': 500,
    'forks_count': 100,
    'license': {'spdx_id': 'MIT'},
    'default_branch': 'main'
}
```

##### get_git_tree()

获取 Git 树（递归获取所有文件）。

```python
tree = client.get_git_tree(
    owner='anthropics',
    repo='anthropic-quickstarts',
    tree_sha='main',
    recursive=True
)
```

**返回：**
```python
{
    'sha': 'abc123...',
    'tree': [
        {
            'path': 'skills/pdf/SKILL.md',
            'type': 'blob',
            'sha': 'def456...',
            'size': 1234,
            'url': 'https://api.github.com/...'
        }
    ],
    'truncated': False
}
```

##### get_rate_limit()

获取 API 限流状态。

```python
rate_limit = client.get_rate_limit()
```

**返回：**
```python
{
    'resources': {
        'core': {
            'limit': 5000,
            'remaining': 4999,
            'reset': 1234567890
        },
        'search': {
            'limit': 30,
            'remaining': 29,
            'reset': 1234567890
        }
    }
}
```

---

## Parser API

### SkillParser

SKILL.md 文件解析器。

#### 初始化

```python
from src.parser.skill_parser import SkillParser

parser = SkillParser()
```

#### 方法

##### parse()

解析 SKILL.md 内容。

```python
skill_data = parser.parse(content)
```

**参数：**
- `content` (str): SKILL.md 文件内容

**返回：**
```python
{
    'name': 'PDF Skill',
    'description': 'Convert PDF to text',
    'license': 'MIT',
    'compatibility': 'claude-3-5-sonnet-20241022',
    'allowed_tools': ['Read', 'Write'],
    'frontmatter': {
        'name': 'PDF Skill',
        'description': 'Convert PDF to text',
        # ... 完整的 frontmatter
    }
}
```

**解析策略：**
1. 优先解析 YAML frontmatter（`---` 包围的部分）
2. 如果没有 frontmatter，使用 fallback 解析（从标题和正文提取）

---

## Scanner API

### RiskScanner

风险扫描器，检测 SKILL.md 中的潜在风险。

#### 初始化

```python
from src.scanner.risk_scanner import RiskScanner

scanner = RiskScanner()
```

#### 方法

##### scan()

扫描内容并返回风险评估。

```python
risk_result = scanner.scan(content)
```

**参数：**
- `content` (str): SKILL.md 文件内容

**返回：**
```python
{
    'risk_level': 'medium',  # 'low', 'medium', 'high'
    'risk_flags': [
        'has_scripts',
        'requires_api_key',
        'network_access'
    ]
}
```

**风险等级：**
- **low**: 仅 SKILL.md，无 scripts，无危险关键词
- **medium**: 包含 scripts，需要 API Key，需要网络访问
- **high**: 出现危险命令、密钥、敏感信息

**风险标签：**
- `has_scripts`: 包含 scripts 目录
- `has_assets`: 包含 assets 目录
- `requires_api_key`: 需要 API Key
- `network_access`: 需要网络访问
- `dangerous_commands`: 包含危险命令
- `sensitive_info`: 包含敏感信息

### DirectoryDetector

目录结构检测器。

#### 初始化

```python
from src.scanner.directory_detector import DirectoryDetector

detector = DirectoryDetector()
```

#### 方法

##### detect_from_tree()

从 Git 树检测目录结构。

```python
structure = detector.detect_from_tree(tree_data, skill_path)
```

**参数：**
- `tree_data` (dict): Git 树数据（来自 `get_git_tree()`）
- `skill_path` (str): SKILL.md 文件路径

**返回：**
```python
{
    'has_scripts': True,
    'has_assets': False,
    'has_references': True,
    'scripts_count': 3,
    'assets_count': 0,
    'references_count': 2
}
```

---

## Storage API

### SkillRepository

Skill 数据仓库，提供数据库操作。

#### 初始化

```python
from src.storage.skill_repository import SkillRepository

# 方式一：使用上下文管理器（推荐）
with SkillRepository() as repo:
    skill = repo.find_by_id(1)

# 方式二：手动管理
repo = SkillRepository()
skill = repo.find_by_id(1)
repo.close()
```

#### 方法

##### upsert()

插入或更新 Skill。

```python
skill = repo.upsert(
    repo_full_name='anthropics/anthropic-quickstarts',
    skill_path='skills/pdf/SKILL.md',
    skill_data={
        'name': 'PDF Skill',
        'description': 'Convert PDF to text',
        'license': 'MIT',
        # ...
    },
    repo_data={
        'html_url': 'https://github.com/anthropics/anthropic-quickstarts',
        'stargazers_count': 500,
        'forks_count': 100,
        # ...
    }
)
```

**返回：** `GitHubSkill` 对象

##### find_by_id()

根据 ID 查找 Skill。

```python
skill = repo.find_by_id(1)
```

**返回：** `GitHubSkill` 对象或 `None`

##### find_by_repo_and_path()

根据仓库和路径查找 Skill。

```python
skill = repo.find_by_repo_and_path(
    repo_full_name='anthropics/anthropic-quickstarts',
    skill_path='skills/pdf/SKILL.md'
)
```

**返回：** `GitHubSkill` 对象或 `None`

##### find_all()

查找所有 Skills。

```python
skills = repo.find_all(
    status='approved',
    limit=100,
    offset=0
)
```

**参数：**
- `status` (str, optional): 状态过滤（pending/approved/rejected/risky/offline）
- `limit` (int): 返回数量限制
- `offset` (int): 偏移量

**返回：** `List[GitHubSkill]`

##### count_by_status()

统计各状态的 Skill 数量。

```python
stats = repo.count_by_status()
# {'pending': 50, 'approved': 100, 'rejected': 10, 'risky': 5, 'offline': 2}
```

### TaskRepository

任务数据仓库。

#### 初始化

```python
from src.storage.task_repository import TaskRepository

with TaskRepository() as repo:
    task = repo.create_task(...)
```

#### 方法

##### create_task()

创建新任务。

```python
task = repo.create_task(
    task_type='code_search',
    query='filename:SKILL.md'
)
```

**返回：** `GitHubScanTask` 对象

##### update_task()

更新任务状态。

```python
repo.update_task(
    task_id=1,
    status='success',
    total_found=100,
    total_saved=95,
    total_skipped=3,
    total_failed=2,
    error_message=None
)
```

##### get_task_stats()

获取任务统计。

```python
stats = repo.get_task_stats()
# {
#     'total': 10,
#     'pending': 1,
#     'running': 0,
#     'success': 8,
#     'failed': 1
# }
```

---

## Acquisition API

### BaseAcquirer

采集器基类，定义通用接口。

```python
from src.acquisition.base import BaseAcquirer

class MyAcquirer(BaseAcquirer):
    def acquire(self):
        # 实现采集逻辑
        pass
```

### CodeSearchAcquirer

Code Search 采集器。

#### 初始化

```python
from src.acquisition.code_search import CodeSearchAcquirer

acquirer = CodeSearchAcquirer()
```

#### 方法

##### acquire()

执行 Code Search 采集。

```python
task = acquirer.acquire()
```

**返回：** `GitHubScanTask` 对象

**流程：**
1. 创建任务记录
2. 遍历搜索关键词
3. 分页获取搜索结果
4. URL 去重
5. 获取文件内容
6. 解析 SKILL.md
7. 风险扫描
8. 保存到数据库
9. 更新任务状态

### RepoScanAcquirer

仓库扫描采集器。

#### 初始化

```python
from src.acquisition.repo_scan import RepoScanAcquirer

# 扫描特定仓库
acquirer = RepoScanAcquirer(
    repo_full_name='anthropics/anthropic-quickstarts'
)

# 扫描所有已知仓库
acquirer = RepoScanAcquirer()
```

#### 方法

##### acquire()

执行仓库扫描。

```python
task = acquirer.acquire()
```

**流程：**
1. 获取仓库列表（指定仓库或从数据库加载）
2. 获取 Git 树（递归）
3. 查找所有 SKILL.md 文件
4. 获取文件内容
5. 解析和扫描
6. 检测目录结构
7. 保存到数据库

### UserSubmitAcquirer

用户提交处理器。

#### 初始化

```python
from src.acquisition.user_submit import UserSubmitAcquirer

# 提交整个仓库
acquirer = UserSubmitAcquirer(
    repo_full_name='anthropics/anthropic-quickstarts'
)

# 提交特定文件
acquirer = UserSubmitAcquirer(
    repo_full_name='anthropics/anthropic-quickstarts',
    skill_path='skills/pdf/SKILL.md'
)
```

#### 方法

##### acquire()

处理用户提交。

```python
task = acquirer.acquire()
```

**流程：**
1. 如果指定了 `skill_path`，直接获取该文件
2. 否则，扫描整个仓库
3. 解析和扫描
4. 保存到数据库

---

## 数据模型

### GitHubSkill

Skill 数据模型。

```python
from src.models import GitHubSkill

skill = GitHubSkill(
    name='PDF Skill',
    description='Convert PDF to text',
    repo_full_name='anthropics/anthropic-quickstarts',
    skill_path='skills/pdf/SKILL.md',
    # ...
)
```

**字段：**
- `id` (int): 主键
- `name` (str): Skill 名称
- `description` (str): 描述
- `repo_full_name` (str): 仓库全名（owner/repo）
- `repo_url` (str): 仓库 URL
- `skill_path` (str): SKILL.md 路径
- `skill_html_url` (str): SKILL.md 网页 URL
- `stars` (int): 仓库星标数
- `forks` (int): 仓库 Fork 数
- `license` (str): 许可证
- `risk_level` (str): 风险等级（low/medium/high）
- `risk_flags` (JSON): 风险标签列表
- `status` (str): 状态（pending/approved/rejected/risky/offline）
- `frontmatter` (JSON): 完整的 frontmatter
- `etag` (str): ETag（用于增量更新）
- `last_modified` (str): Last-Modified（用于增量更新）
- `last_checked_at` (datetime): 最后检查时间
- `created_at` (datetime): 创建时间
- `updated_at` (datetime): 更新时间

### GitHubScanTask

任务数据模型。

```python
from src.models import GitHubScanTask

task = GitHubScanTask(
    task_type='code_search',
    query='filename:SKILL.md',
    status='running',
    # ...
)
```

**字段：**
- `id` (int): 主键
- `task_type` (str): 任务类型（code_search/repo_scan/user_submit）
- `query` (str): 搜索查询（仅 code_search）
- `repo_full_name` (str): 仓库全名（仅 repo_scan/user_submit）
- `status` (str): 状态（pending/running/success/failed）
- `total_found` (int): 找到的总数
- `total_saved` (int): 保存的总数
- `total_skipped` (int): 跳过的总数
- `total_failed` (int): 失败的总数
- `error_message` (str): 错误信息
- `created_at` (datetime): 创建时间
- `updated_at` (datetime): 更新时间

---

## 错误处理

### 异常类型

```python
from src.github.exceptions import (
    GitHubAPIError,
    RateLimitError,
    NotFoundError,
    AuthenticationError
)
```

**异常层次：**
```
GitHubAPIError (基类)
├── RateLimitError (限流错误)
├── NotFoundError (404 错误)
└── AuthenticationError (认证错误)
```

### 使用示例

```python
from src.github.client import GitHubClient
from src.github.exceptions import RateLimitError, NotFoundError

client = GitHubClient()

try:
    content = client.get_file_content('owner', 'repo', 'path/to/file')
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # 等待限流重置
except NotFoundError as e:
    print(f"File not found: {e}")
except GitHubAPIError as e:
    print(f"GitHub API error: {e}")
```

---

## 配置

### 环境变量

```bash
# GitHub API Token（必填）
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 数据库连接（必填）
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/skill_index?charset=utf8mb4

# 日志级别（可选，默认 INFO）
LOG_LEVEL=INFO
```

### 配置文件

`config.py` 包含所有可配置项：

```python
# GitHub API 配置
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 搜索配置
SEARCH_QUERIES = [
    'filename:SKILL.md "name:"',
    'filename:SKILL.md "description:"',
    # ...
]

# 限流配置
CODE_SEARCH_INTERVAL = 10  # 秒
CONTENTS_API_INTERVAL = 0.5  # 秒
RATE_LIMIT_THRESHOLD = 10  # 剩余次数阈值

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

---

## 命令行接口

### main.py

统一主入口。

```bash
# 查看帮助
python main.py --help

# Code Search
python main.py code_search

# 仓库扫描
python main.py repo_scan [--repo REPO]

# 增量更新检查
python main.py update_check [--limit LIMIT]

# 用户提交
python main.py user_submit --repo REPO [--path PATH]

# 显示统计
python main.py stats
```

---

## 最佳实践

### 1. 使用上下文管理器

```python
# 推荐
with SkillRepository() as repo:
    skill = repo.find_by_id(1)
    # 自动提交和关闭

# 不推荐
repo = SkillRepository()
skill = repo.find_by_id(1)
repo.close()  # 容易忘记
```

### 2. 错误处理

```python
from src.github.exceptions import GitHubAPIError

try:
    acquirer = CodeSearchAcquirer()
    task = acquirer.acquire()
except GitHubAPIError as e:
    logger.error(f"Acquisition failed: {e}")
    # 处理错误
```

### 3. 批量操作

```python
# 批量提交（提高性能）
with SkillRepository() as repo:
    for skill_data in skill_list:
        repo.upsert(...)
        if idx % 50 == 0:
            repo.session.commit()  # 每 50 条提交一次
```

### 4. 限流保护

```python
# 已内置限流保护，无需手动处理
client = GitHubClient()
for query in queries:
    results = client.search_code(query)  # 自动限流
```

---

## 更新日志

### v1.0.0 (2026-05-31)
- 初始版本发布
- 实现 Code Search、仓库扫描、用户提交三种采集方式
- 实现 SKILL.md 解析和风险扫描
- 实现增量更新机制
- 提供统一命令行接口

---

**最后更新：** 2026-05-31
