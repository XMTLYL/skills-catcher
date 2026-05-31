# GitHub Skills 获取方案设计文档

## 1. 方案目标

本文档只解决一个问题：

> 如何从 GitHub 上发现、获取、解析并保存公开 Skills 的索引信息。

这里的“获取”不是把别人的 Skill 文件完整镜像到自己的服务器，而是获取用于展示和检索的元数据，例如：

- Skill 名称
- Skill 描述
- GitHub 仓库地址
- SKILL.md 地址
- 作者
- License
- Stars
- Forks
- 更新时间
- 是否包含 scripts / assets / references
- 风险标签
- 原始仓库跳转地址

最终效果是：

```text
GitHub 公开仓库
    ↓
搜索 SKILL.md
    ↓
读取 SKILL.md 内容
    ↓
解析元数据
    ↓
获取仓库信息
    ↓
保存到自己的数据库
    ↓
前端展示
    ↓
用户点击跳转原 GitHub 仓库
```

---

## 2. 核心原则

### 2.1 不做镜像

不把完整 Skill 包保存到自己的服务器。

不保存：

```text
完整 scripts/
完整 assets/
完整 references/
完整 zip 包
完整仓库副本
```

只保存：

```text
名称
描述
来源
仓库链接
SKILL.md 链接
License
Stars
风险标签
更新时间
```

### 2.2 不爬 SkillsMP 等第三方网站

数据来源优先使用：

```text
GitHub REST API
GitHub Search API
GitHub Contents API
GitHub Trees API
官方开源仓库
用户主动提交的 GitHub 地址
```

不建议：

```text
爬 SkillsMP 页面
爬其他 marketplace 页面
批量复制别人整理好的数据
```

### 2.3 所有采集结果先进入待审核

采集到的数据不要直接上线展示。

推荐状态流转：

```text
found       已发现
parsed      已解析
pending     待审核
approved    审核通过
rejected    拒绝收录
risky       高风险
offline     链接失效
```

---

## 3. GitHub Skills 识别标准

### 3.1 基础识别条件

一个目录只要存在：

```text
SKILL.md
```

就可以作为候选 Skill。

### 3.2 推荐有效 Skill 条件

优先收录满足以下条件的 Skill：

```text
包含 SKILL.md
SKILL.md 中有 name
SKILL.md 中有 description
仓库是 public
仓库未 archived
仓库有明确 License
SKILL.md 可正常读取
仓库近期有维护或有一定 star
```

### 3.3 常见目录结构

```text
some-skill/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

也可能是：

```text
repo-root/
├── skills/
│   ├── pdf/
│   │   └── SKILL.md
│   ├── browser/
│   │   └── SKILL.md
│   └── data-analysis/
│       └── SKILL.md
```

或者：

```text
repo-root/
├── pdf-processing/
│   └── SKILL.md
├── image-generation/
│   └── SKILL.md
└── code-review/
    └── SKILL.md
```

---

## 4. 获取 GitHub Skills 的三种方式

建议同时使用三种方式。

---

# 方式一：GitHub Code Search 搜索 SKILL.md

## 4.1 适用场景

用于发现全网公开仓库里的 `SKILL.md` 文件。

适合：

```text
发现新仓库
发现未知作者的 Skill
扩大索引范围
每日增量采集
```

## 4.2 API

```http
GET https://api.github.com/search/code
```

请求参数：

```text
q        搜索语句
page     页码
per_page 每页数量，最大一般设置 100
```

## 4.3 推荐搜索语句

第一批搜索语句：

```text
filename:SKILL.md "description:"
filename:SKILL.md "name:"
filename:SKILL.md "allowed-tools"
filename:SKILL.md "Agent Skills"
filename:SKILL.md "scripts/"
```

第二批搜索语句：

```text
path:skills filename:SKILL.md
path:skill filename:SKILL.md
filename:SKILL.md "compatibility"
filename:SKILL.md "license"
filename:SKILL.md "Claude"
filename:SKILL.md "Codex"
```

第三批搜索语句：

```text
filename:SKILL.md "SKILL.md"
filename:SKILL.md "This skill"
filename:SKILL.md "When to use"
filename:SKILL.md "Overview"
```

## 4.4 请求示例

```bash
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/search/code?q=filename:SKILL.md+description:&per_page=30&page=1"
```

## 4.5 返回数据中需要的字段

每个搜索结果中重点使用：

```text
item.name
item.path
item.sha
item.url
item.html_url
item.repository.full_name
item.repository.html_url
item.repository.default_branch
item.repository.owner.login
```

示例：

```json
{
  "name": "SKILL.md",
  "path": "skills/pdf-processing/SKILL.md",
  "html_url": "https://github.com/openai/skills/blob/main/skills/pdf-processing/SKILL.md",
  "url": "https://api.github.com/repos/openai/skills/contents/skills/pdf-processing/SKILL.md",
  "repository": {
    "full_name": "openai/skills",
    "html_url": "https://github.com/openai/skills",
    "default_branch": "main",
    "owner": {
      "login": "openai"
    }
  }
}
```

## 4.6 优点

```text
覆盖范围大
能发现未知仓库
不需要提前知道仓库地址
适合每日自动发现新 Skill
```

## 4.7 缺点

```text
Code Search 有单独限流
结果不一定完整
只搜索默认分支
部分仓库不会被索引
搜索结果可能有误报
分页最多只能获取有限结果
```

---

# 方式二：指定高可信仓库扫描

## 5.1 适用场景

用于扫描你已经知道的高质量 Skill 仓库。

例如：

```text
openai/skills
anthropics/skills
vercel-labs/agent-skills
browserbase/skills
readthedocs/skills
其他用户提交的仓库
```

## 5.2 推荐方式

对指定仓库不要用 Code Search，而是直接扫描仓库目录树。

流程：

```text
获取仓库信息
    ↓
获取默认分支
    ↓
获取默认分支对应 commit
    ↓
获取 tree sha
    ↓
递归读取 Git Tree
    ↓
找出所有路径以 SKILL.md 结尾的文件
    ↓
逐个读取 SKILL.md 内容
```

## 5.3 可以使用的 API

### 获取仓库信息

```http
GET /repos/{owner}/{repo}
```

### 获取仓库内容

```http
GET /repos/{owner}/{repo}/contents/{path}
```

### 获取 Git Tree

```http
GET /repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1
```

## 5.4 为什么指定仓库要用 Trees API

如果一个仓库里面有很多 Skill，使用 Trees API 可以一次性列出仓库中的文件路径，然后筛选：

```text
path.endswith("SKILL.md")
```

这样比对每个目录调用 Contents API 更高效。

## 5.5 扫描逻辑

```text
输入：openai/skills

1. 调用 GET /repos/openai/skills
2. 获得 default_branch
3. 获得 default_branch 对应的 commit sha
4. 获得 tree sha
5. 调用 GET /repos/openai/skills/git/trees/{tree_sha}?recursive=1
6. 遍历 tree
7. 找到所有 SKILL.md
8. 读取每个 SKILL.md
9. 解析元数据
10. 保存到数据库
```

---

# 方式三：用户提交 GitHub 仓库地址

## 6.1 适用场景

用户或作者主动提交 Skill。

提交字段：

```text
GitHub 仓库地址
Skill 所在路径
推荐分类
提交说明
提交人邮箱，可选
```

## 6.2 处理流程

```text
用户提交 repo_url
    ↓
后端解析 owner/repo
    ↓
检查仓库是否存在
    ↓
如果用户填写了 skill_path，则直接读取
    ↓
如果没有填写 skill_path，则扫描仓库 Tree
    ↓
查找所有 SKILL.md
    ↓
解析并入库
    ↓
进入 pending
    ↓
人工审核
```

## 6.3 仓库地址解析

支持输入：

```text
https://github.com/owner/repo
https://github.com/owner/repo/tree/main/skills/pdf
https://github.com/owner/repo/blob/main/skills/pdf/SKILL.md
owner/repo
```

解析后统一得到：

```text
owner
repo
branch
skill_path
```

---

## 7. 推荐采集总流程

### 7.1 每日自动采集流程

```text
开始任务
  ↓
读取搜索关键词列表
  ↓
调用 GitHub Code Search
  ↓
获得候选 SKILL.md
  ↓
根据 repo_full_name + skill_path 去重
  ↓
读取 SKILL.md 内容
  ↓
解析 frontmatter
  ↓
读取仓库信息
  ↓
检测目录结构
  ↓
风险扫描
  ↓
写入数据库
  ↓
状态设为 pending
  ↓
记录日志
  ↓
结束
```

### 7.2 指定仓库扫描流程

```text
开始任务
  ↓
读取 trusted_repositories 表
  ↓
逐个扫描仓库 Tree
  ↓
找出所有 SKILL.md
  ↓
读取文件内容
  ↓
解析元数据
  ↓
保存或更新数据库
  ↓
结束
```

### 7.3 用户提交处理流程

```text
用户提交 GitHub 地址
  ↓
解析 owner/repo/path
  ↓
检查仓库存在性
  ↓
读取或扫描 SKILL.md
  ↓
解析元数据
  ↓
保存为 pending
  ↓
通知后台审核
```

---

## 8. 需要保存的数据字段

### 8.1 skills 表

```sql
CREATE TABLE github_skills (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',

    name VARCHAR(255) DEFAULT NULL COMMENT 'Skill名称',
    description TEXT COMMENT 'Skill描述',
    slug VARCHAR(255) DEFAULT NULL COMMENT 'URL slug',

    repo_full_name VARCHAR(255) NOT NULL COMMENT '仓库全名，例如 openai/skills',
    repo_owner VARCHAR(255) DEFAULT NULL COMMENT '仓库所有者',
    repo_name VARCHAR(255) DEFAULT NULL COMMENT '仓库名称',
    repo_url VARCHAR(500) NOT NULL COMMENT '仓库地址',
    repo_default_branch VARCHAR(100) DEFAULT NULL COMMENT '默认分支',

    skill_path VARCHAR(500) NOT NULL COMMENT 'SKILL.md路径',
    skill_dir VARCHAR(500) DEFAULT NULL COMMENT 'Skill目录',
    skill_html_url VARCHAR(500) DEFAULT NULL COMMENT 'GitHub页面地址',
    skill_raw_url VARCHAR(500) DEFAULT NULL COMMENT 'Raw文件地址',
    skill_api_url VARCHAR(500) DEFAULT NULL COMMENT 'GitHub Contents API地址',

    skill_sha VARCHAR(100) DEFAULT NULL COMMENT '文件sha',
    skill_size INT DEFAULT NULL COMMENT '文件大小',
    skill_etag VARCHAR(255) DEFAULT NULL COMMENT 'ETag，用于增量更新',
    skill_last_modified VARCHAR(255) DEFAULT NULL COMMENT 'Last-Modified',

    frontmatter_json JSON DEFAULT NULL COMMENT 'SKILL.md frontmatter原始解析结果',
    license VARCHAR(100) DEFAULT NULL COMMENT 'Skill声明License',
    compatibility VARCHAR(255) DEFAULT NULL COMMENT '适配平台',
    allowed_tools TEXT COMMENT '允许工具',

    stars INT DEFAULT 0 COMMENT '仓库Stars',
    forks INT DEFAULT 0 COMMENT '仓库Forks',
    watchers INT DEFAULT 0 COMMENT '仓库Watchers',
    open_issues INT DEFAULT 0 COMMENT 'Open Issues',
    repo_license VARCHAR(100) DEFAULT NULL COMMENT '仓库License',
    repo_archived TINYINT DEFAULT 0 COMMENT '仓库是否归档',
    repo_disabled TINYINT DEFAULT 0 COMMENT '仓库是否禁用',
    repo_private TINYINT DEFAULT 0 COMMENT '是否私有，正常应为0',
    repo_updated_at DATETIME DEFAULT NULL COMMENT '仓库更新时间',
    repo_pushed_at DATETIME DEFAULT NULL COMMENT '仓库最近push时间',

    has_scripts TINYINT DEFAULT 0 COMMENT '是否包含scripts目录',
    has_assets TINYINT DEFAULT 0 COMMENT '是否包含assets目录',
    has_references TINYINT DEFAULT 0 COMMENT '是否包含references目录',
    has_tests TINYINT DEFAULT 0 COMMENT '是否包含tests目录',

    risk_level VARCHAR(50) DEFAULT 'unknown' COMMENT '风险等级 low/medium/high/unknown',
    risk_flags JSON DEFAULT NULL COMMENT '风险标签',
    license_status VARCHAR(50) DEFAULT 'unknown' COMMENT 'license状态 clear/missing/conflict/unknown',

    source_type VARCHAR(50) DEFAULT 'github_search' COMMENT '来源 github_search/trusted_repo/user_submit',
    status VARCHAR(50) DEFAULT 'pending' COMMENT '状态 found/parsed/pending/approved/rejected/risky/offline',

    first_found_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '首次发现时间',
    last_checked_at DATETIME DEFAULT NULL COMMENT '最后检查时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_repo_skill_path (repo_full_name, skill_path),
    INDEX idx_name (name),
    INDEX idx_repo_full_name (repo_full_name),
    INDEX idx_status (status),
    INDEX idx_source_type (source_type),
    INDEX idx_stars (stars),
    INDEX idx_repo_updated_at (repo_updated_at)
) COMMENT='GitHub Skills索引表';
```

### 8.2 github_scan_tasks 表

```sql
CREATE TABLE github_scan_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    task_type VARCHAR(50) NOT NULL COMMENT '任务类型 code_search/repo_tree/user_submit/update_check',
    query_text VARCHAR(500) DEFAULT NULL COMMENT '搜索语句或仓库地址',

    status VARCHAR(50) DEFAULT 'pending' COMMENT 'pending/running/success/failed',
    total_found INT DEFAULT 0 COMMENT '发现数量',
    total_saved INT DEFAULT 0 COMMENT '保存数量',
    total_skipped INT DEFAULT 0 COMMENT '跳过数量',
    error_message TEXT COMMENT '错误信息',

    started_at DATETIME DEFAULT NULL,
    finished_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT='GitHub采集任务表';
```

### 8.3 github_known_repositories 表

```sql
CREATE TABLE github_known_repositories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    repo_full_name VARCHAR(255) NOT NULL COMMENT 'owner/repo',
    repo_url VARCHAR(500) NOT NULL COMMENT 'GitHub仓库地址',
    source_level VARCHAR(50) DEFAULT 'normal' COMMENT 'official/trusted/normal/user',
    scan_enabled TINYINT DEFAULT 1 COMMENT '是否启用扫描',

    last_scanned_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_repo_full_name (repo_full_name)
) COMMENT='已知Skill仓库表';
```

---

## 9. SKILL.md 解析规则

### 9.1 优先解析 YAML Frontmatter

推荐格式：

```markdown
---
name: pdf-processing
description: Read and process PDF files.
license: Apache-2.0
compatibility: codex
allowed-tools:
  - python
  - file-system
---

# PDF Processing
```

解析步骤：

```text
1. 判断文件开头是否为 ---
2. 提取两个 --- 之间内容
3. 使用 YAML parser 解析
4. 读取 name / description / license / compatibility / allowed-tools
5. 保存 frontmatter_json
```

### 9.2 没有 Frontmatter 的处理方式

如果没有 frontmatter：

```text
1. 从一级标题提取 name
2. 从前 300 字提取 description 候选
3. 标记 parse_quality = weak
4. status = pending
5. 不自动审核通过
```

### 9.3 必填字段

自动认可的最低条件：

```text
name 非空
description 非空
repo_full_name 非空
skill_path 非空
skill_html_url 非空
```

---

## 10. 目录结构检测

拿到 `skill_path` 后，例如：

```text
skills/pdf-processing/SKILL.md
```

得到 `skill_dir`：

```text
skills/pdf-processing
```

然后调用：

```http
GET /repos/{owner}/{repo}/contents/{skill_dir}
```

检测目录下是否存在：

```text
scripts/
assets/
references/
tests/
README.md
LICENSE
LICENSE.txt
```

保存为：

```text
has_scripts
has_assets
has_references
has_tests
```

---

## 11. 风险扫描规则

### 11.1 基础风险判断

低风险：

```text
只有 SKILL.md
没有 scripts
没有外部下载
没有要求 API Key
没有危险命令
```

中风险：

```text
包含 scripts
需要 API Key
需要访问本地文件
需要网络访问
包含安装依赖说明
```

高风险：

```text
出现 rm -rf
出现 curl | bash
出现 wget + 执行
出现 eval / exec
出现上传 token
出现读取 .env
出现读取 SSH key
出现删除文件
出现远程执行命令
```

### 11.2 关键词扫描

建议扫描 `SKILL.md` 内容和 scripts 文件名，不下载完整 scripts 内容也可以先做初筛。

关键词：

```text
rm -rf
curl | bash
wget
eval(
exec(
subprocess
os.system
child_process
process.env
.env
API_KEY
SECRET
TOKEN
PRIVATE_KEY
id_rsa
ssh
upload
webhook
```

### 11.3 风险标签

```text
contains_scripts
needs_api_key
needs_network
needs_file_access
dangerous_command
secret_related
license_missing
repo_archived
unknown_format
```

---

## 12. 增量更新策略

### 12.1 为什么需要增量更新

不能每天全量重复读取所有文件，否则很容易触发 GitHub API 限流。

### 12.2 使用 ETag

每次读取 `SKILL.md` 时保存响应头：

```text
ETag
Last-Modified
```

下次请求时带上：

```http
If-None-Match: 上次保存的 ETag
If-Modified-Since: 上次保存的 Last-Modified
```

如果 GitHub 返回：

```text
304 Not Modified
```

说明文件没变，可以跳过解析和更新。

### 12.3 更新检查流程

```text
读取数据库中已收录的 Skill
    ↓
按 last_checked_at 排序
    ↓
每天检查一部分
    ↓
带 ETag 请求 SKILL.md
    ↓
304：只更新 last_checked_at
    ↓
200：重新解析并更新
    ↓
404：标记 offline
```

### 12.4 检查频率

推荐：

```text
新发现 pending：每天检查
approved：每 7 天检查一次
risky：每 14 天检查一次
offline：每 30 天复查一次
rejected：不自动检查
```

---

## 13. 限流策略

### 13.1 必须使用 GitHub Token

Code Search API 建议使用认证请求。

环境变量：

```env
GITHUB_TOKEN=ghp_xxx
```

请求头：

```http
Authorization: Bearer YOUR_GITHUB_TOKEN
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

### 13.2 控制 Code Search 调用频率

建议第一版保守处理：

```text
每分钟最多 6 次 Code Search
每次搜索 per_page = 30
每个关键词最多跑 2 页
每个搜索关键词之间 sleep 10 秒
```

### 13.3 Contents API 调用频率

建议：

```text
每次请求间隔 0.5 - 1 秒
遇到 403 / 429 立即停止
根据 x-ratelimit-reset 等待
使用指数退避
```

### 13.4 读取限流响应头

保存并监控：

```text
x-ratelimit-limit
x-ratelimit-remaining
x-ratelimit-reset
x-ratelimit-resource
```

### 13.5 错误处理

```text
403 且 remaining = 0：等待 reset 时间
403 且提示 secondary rate limit：暂停至少 1 分钟，之后指数退避
429：暂停并指数退避
404：标记文件失效
422：搜索语句非法，记录日志
5xx：重试 3 次
```

---

## 14. Python 采集器 MVP 设计

### 14.1 目录结构

```text
github-skill-indexer/
├── main.py
├── config.py
├── github_client.py
├── parser.py
├── scanner.py
├── storage.py
├── models.py
├── requirements.txt
└── .env
```

### 14.2 requirements.txt

```text
requests
PyYAML
python-dotenv
SQLAlchemy
pymysql
```

### 14.3 .env

```env
GITHUB_TOKEN=your_token
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/skill_index?charset=utf8mb4
```

### 14.4 MVP 代码示例

```python
import os
import re
import time
import base64
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


SEARCH_QUERIES = [
    'filename:SKILL.md "description:"',
    'filename:SKILL.md "name:"',
    'filename:SKILL.md "allowed-tools"',
    'path:skills filename:SKILL.md',
]


def github_get(url, params=None, extra_headers=None):
    headers = dict(HEADERS)
    if extra_headers:
        headers.update(extra_headers)

    resp = requests.get(url, headers=headers, params=params, timeout=30)

    remaining = resp.headers.get("x-ratelimit-remaining")
    reset = resp.headers.get("x-ratelimit-reset")
    resource = resp.headers.get("x-ratelimit-resource")

    print("rate:", resource, remaining, reset)

    if resp.status_code == 304:
        return {
            "not_modified": True,
            "etag": resp.headers.get("etag"),
            "last_modified": resp.headers.get("last-modified"),
        }

    if resp.status_code in [403, 429]:
        print("rate limited:", resp.text)
        time.sleep(60)
        return None

    if resp.status_code == 404:
        return None

    resp.raise_for_status()

    return {
        "data": resp.json(),
        "etag": resp.headers.get("etag"),
        "last_modified": resp.headers.get("last-modified"),
    }


def search_code(query, page=1, per_page=30):
    result = github_get(
        "https://api.github.com/search/code",
        params={
            "q": query,
            "page": page,
            "per_page": per_page,
        },
    )

    if not result or "data" not in result:
        return []

    return result["data"].get("items", [])


def fetch_content(file_api_url, etag=None):
    headers = {}
    if etag:
        headers["If-None-Match"] = etag

    result = github_get(file_api_url, extra_headers=headers)

    if not result:
        return None

    if result.get("not_modified"):
        return {
            "not_modified": True,
            "etag": result.get("etag"),
            "last_modified": result.get("last_modified"),
        }

    data = result.get("data")
    if not data:
        return None

    content = data.get("content")
    encoding = data.get("encoding")

    if encoding == "base64" and content:
        text = base64.b64decode(content).decode("utf-8", errors="ignore")
    else:
        text = ""

    return {
        "content": text,
        "sha": data.get("sha"),
        "size": data.get("size"),
        "download_url": data.get("download_url"),
        "etag": result.get("etag"),
        "last_modified": result.get("last_modified"),
    }


def parse_skill_md(content):
    meta = {}

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

    if match:
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            meta = {}

    name = meta.get("name")
    description = meta.get("description")

    if not name:
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            name = title_match.group(1).strip()

    if not description:
        body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
        description = body.strip().replace("\n", " ")[:300]

    if not name or not description:
        return None

    return {
        "name": str(name).strip(),
        "description": str(description).strip(),
        "license": str(meta.get("license", "")).strip() if meta.get("license") else "",
        "compatibility": str(meta.get("compatibility", "")).strip() if meta.get("compatibility") else "",
        "allowed_tools": meta.get("allowed-tools", ""),
        "frontmatter": meta,
    }


def fetch_repo_info(repo_full_name):
    result = github_get(f"https://api.github.com/repos/{repo_full_name}")

    if not result or "data" not in result:
        return {}

    data = result["data"]
    license_info = data.get("license") or {}

    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("watchers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "repo_license": license_info.get("spdx_id") or "",
        "default_branch": data.get("default_branch") or "main",
        "archived": data.get("archived", False),
        "disabled": data.get("disabled", False),
        "private": data.get("private", False),
        "updated_at": data.get("updated_at"),
        "pushed_at": data.get("pushed_at"),
    }


def get_skill_dir(skill_path):
    if "/" not in skill_path:
        return ""
    return skill_path.rsplit("/", 1)[0]


def detect_dirs(repo_full_name, skill_path):
    skill_dir = get_skill_dir(skill_path)

    if not skill_dir:
        return {
            "has_scripts": False,
            "has_assets": False,
            "has_references": False,
            "has_tests": False,
        }

    url = f"https://api.github.com/repos/{repo_full_name}/contents/{skill_dir}"
    result = github_get(url)

    if not result or "data" not in result:
        return {
            "has_scripts": False,
            "has_assets": False,
            "has_references": False,
            "has_tests": False,
        }

    data = result["data"]

    if not isinstance(data, list):
        return {
            "has_scripts": False,
            "has_assets": False,
            "has_references": False,
            "has_tests": False,
        }

    dir_names = {
        item.get("name")
        for item in data
        if item.get("type") == "dir"
    }

    return {
        "has_scripts": "scripts" in dir_names,
        "has_assets": "assets" in dir_names,
        "has_references": "references" in dir_names,
        "has_tests": "tests" in dir_names,
    }


def scan_risk(content, dir_info):
    flags = []

    keyword_map = {
        "rm -rf": "dangerous_delete",
        "curl | bash": "remote_shell",
        "wget": "network_download",
        "eval(": "dynamic_eval",
        "exec(": "dynamic_exec",
        "subprocess": "command_execute",
        "os.system": "command_execute",
        "process.env": "env_access",
        ".env": "env_file_access",
        "API_KEY": "api_key",
        "SECRET": "secret",
        "TOKEN": "token",
        "PRIVATE_KEY": "private_key",
        "id_rsa": "ssh_key",
    }

    lower_content = content.lower()

    for keyword, flag in keyword_map.items():
        if keyword.lower() in lower_content:
            flags.append(flag)

    if dir_info.get("has_scripts"):
        flags.append("contains_scripts")

    if "api key" in lower_content or "apikey" in lower_content:
        flags.append("needs_api_key")

    high_flags = {
        "dangerous_delete",
        "remote_shell",
        "env_file_access",
        "private_key",
        "ssh_key",
    }

    if any(flag in high_flags for flag in flags):
        risk_level = "high"
    elif flags:
        risk_level = "medium"
    else:
        risk_level = "low"

    return risk_level, sorted(set(flags))


def build_raw_url(repo_full_name, branch, path):
    return f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/{path}"


def process_search_item(item):
    repo = item.get("repository", {})
    repo_full_name = repo.get("full_name")
    repo_url = repo.get("html_url")
    owner = repo.get("owner", {}).get("login")
    skill_path = item.get("path")
    skill_html_url = item.get("html_url")
    file_api_url = item.get("url")

    if not repo_full_name or not skill_path or not file_api_url:
        return None

    file_data = fetch_content(file_api_url)

    if not file_data or file_data.get("not_modified"):
        return None

    content = file_data.get("content", "")

    skill_meta = parse_skill_md(content)

    if not skill_meta:
        return None

    repo_info = fetch_repo_info(repo_full_name)
    dir_info = detect_dirs(repo_full_name, skill_path)
    risk_level, risk_flags = scan_risk(content, dir_info)

    default_branch = repo_info.get("default_branch") or repo.get("default_branch") or "main"

    record = {
        "name": skill_meta["name"],
        "description": skill_meta["description"],
        "license": skill_meta["license"],
        "compatibility": skill_meta["compatibility"],
        "allowed_tools": skill_meta["allowed_tools"],
        "frontmatter": skill_meta["frontmatter"],

        "repo_full_name": repo_full_name,
        "repo_owner": owner,
        "repo_url": repo_url,
        "repo_default_branch": default_branch,

        "skill_path": skill_path,
        "skill_dir": get_skill_dir(skill_path),
        "skill_html_url": skill_html_url,
        "skill_raw_url": build_raw_url(repo_full_name, default_branch, skill_path),
        "skill_api_url": file_api_url,
        "skill_sha": file_data.get("sha"),
        "skill_size": file_data.get("size"),
        "skill_etag": file_data.get("etag"),
        "skill_last_modified": file_data.get("last_modified"),

        **repo_info,
        **dir_info,

        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "source_type": "github_search",
        "status": "pending",
    }

    return record


def save_record(record):
    # TODO: 换成你的数据库保存逻辑
    print("SAVE:", record["name"], record["repo_full_name"], record["skill_path"])


def main():
    seen = set()

    for query in SEARCH_QUERIES:
        print("Search:", query)

        for page in range(1, 3):
            items = search_code(query, page=page, per_page=30)

            if not items:
                break

            for item in items:
                key = item.get("html_url")

                if not key or key in seen:
                    continue

                seen.add(key)

                try:
                    record = process_search_item(item)
                    if record:
                        save_record(record)
                except Exception as e:
                    print("ERROR:", e)

                time.sleep(1)

            time.sleep(10)


if __name__ == "__main__":
    main()
```

---

## 15. Java / Spring Boot 实现方式

如果你后端使用 Java，可以这样拆。

### 15.1 模块

```text
GitHubClient
SkillDiscoveryService
SkillParserService
SkillRiskScanner
SkillRepository
GitHubScanTaskService
```

### 15.2 定时任务

```java
@Scheduled(cron = "0 0 3 * * ?")
public void scanGithubSkills() {
    skillDiscoveryService.scanByCodeSearch();
}
```

### 15.3 核心调用流程

```text
SkillDiscoveryService.scanByCodeSearch()
    ↓
GitHubClient.searchCode()
    ↓
GitHubClient.getContent()
    ↓
SkillParserService.parse()
    ↓
GitHubClient.getRepoInfo()
    ↓
SkillRiskScanner.scan()
    ↓
SkillRepository.upsert()
```

### 15.4 Java 版建议

如果项目初期只是为了快速验证，建议先用 Python 采集器。

原因：

```text
GitHub采集、YAML解析、字符串清洗，Python开发更快
后续稳定后，可以迁移为Java定时任务
也可以长期保持 Python 采集器 + Java 后端服务
```

---

## 16. 采集任务调度建议

### 16.1 第一阶段

```text
每天凌晨 3 点跑 GitHub Code Search
每天凌晨 4 点跑指定仓库扫描
每周跑一次已收录 Skill 更新检查
```

### 16.2 Linux cron

```bash
0 3 * * * cd /www/github-skill-indexer && /usr/bin/python3 main.py >> logs/indexer.log 2>&1
```

### 16.3 任务分批

不要一次性扫描太多。

建议：

```text
每次最多搜索 5 个关键词
每个关键词最多 2 页
每页 30 条
单次最多处理 300 个候选结果
```

后续再逐步扩大。

---

## 17. 去重规则

### 17.1 主去重键

```text
repo_full_name + skill_path
```

示例：

```text
openai/skills + skills/pdf-processing/SKILL.md
```

### 17.2 辅助去重

```text
skill_sha
skill_raw_url
skill_html_url
name + repo_full_name
```

### 17.3 Fork 处理

如果发现仓库是 fork：

```text
fork = true
```

可以做：

```text
默认不收录低 star fork
如果 fork stars 高于原仓库，可进入 pending
如果 fork 修改明显，可进入 pending
```

---

## 18. License 处理

### 18.1 读取来源

License 来源有两个：

```text
SKILL.md frontmatter 中的 license
GitHub repo API 返回的 license.spdx_id
```

### 18.2 判断逻辑

```text
如果 Skill license 存在，优先展示 Skill license
如果 Skill license 不存在，展示 repo license
如果两者都没有，标记 license_missing
如果两者冲突，标记 license_conflict
```

### 18.3 License 状态

```text
clear
missing
conflict
unknown
```

### 18.4 前端提示

对于 `license_missing` 的 Skill：

```text
该仓库未检测到明确 License，建议仅查看，不建议复制、修改、分发或商用。
```

---

## 19. 采集日志设计

每一次请求和处理都应记录日志，便于排查。

日志字段：

```text
task_id
query
repo_full_name
skill_path
api_url
status
message
rate_limit_remaining
rate_limit_reset
created_at
```

常见日志状态：

```text
search_success
search_failed
content_success
content_404
parse_failed
saved
skipped_duplicate
rate_limited
repo_archived
license_missing
```

---

## 20. 上线前最小验收标准

满足以下条件，就可以认为 GitHub Skills 获取方案 MVP 可用：

```text
可以通过 GitHub Code Search 找到 SKILL.md
可以读取 SKILL.md 内容
可以解析 name 和 description
可以获取 repo stars / forks / license / updated_at
可以检测 scripts / assets / references
可以保存到数据库
可以去重
可以限流
可以记录失败日志
可以标记 pending
不会下载完整仓库
不会保存完整 scripts/assets/references
```

---

## 21. 推荐实施顺序

### 第一步：写 Python MVP

目标：

```text
跑通 GitHub Code Search
找到 SKILL.md
打印解析结果
```

### 第二步：接入数据库

目标：

```text
保存 github_skills 表
实现 upsert
实现去重
```

### 第三步：扫描指定仓库

目标：

```text
支持 openai/skills 这种指定仓库扫描
用 Trees API 找出全部 SKILL.md
```

### 第四步：增加风险扫描

目标：

```text
识别 scripts
识别 API Key
识别危险命令
生成 risk_flags
```

### 第五步：做定时任务

目标：

```text
每天自动搜索
每周自动更新
失败自动记录
```

### 第六步：接后台审核

目标：

```text
pending -> approved / rejected / risky
```

---

## 22. 最终结论

你要写的不是“爬虫”，而是一个：

```text
GitHub Skill Indexer
```

它的核心功能是：

```text
用 GitHub API 搜索 SKILL.md
读取 SKILL.md
解析元数据
补充仓库信息
判断风险
保存索引
等待审核
前端跳转原仓库
```

第一版最推荐的组合是：

```text
Python 采集器
GitHub REST API
MySQL 数据库
定时任务 cron
后台人工审核
前端只展示索引和原仓库链接
```

这样可以快速实现，也能避开直接镜像、托管、执行带来的版权和安全风险。

---

## 23. 参考资料

- GitHub REST API：Repository Contents
- GitHub REST API：Code Search
- GitHub REST API：Git Trees
- GitHub REST API：Rate Limits
- GitHub REST API：Best Practices
- GitHub Code Search legacy syntax


## 24.GitHub REST API Token
-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