# 贡献指南

感谢你对 GitHub Skill Catcher 项目的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请：

1. 检查 [Issues](https://github.com/XMTLYL/skill-catcher/issues) 确认问题是否已被报告
2. 如果没有，创建一个新的 Issue，使用 Bug Report 模板
3. 提供详细的复现步骤和环境信息

### 提出新功能

如果你有新功能的想法：

1. 创建一个 Issue，使用 Feature Request 模板
2. 描述功能的使用场景和预期效果
3. 等待维护者的反馈

### 提交代码

1. **Fork 项目**
   ```bash
   # 在 GitHub 上 Fork 项目
   git clone https://github.com/YOUR_USERNAME/skill-catcher.git
   cd skill-catcher
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **开发和测试**
   ```bash
   # 安装依赖
   pip install -r requirements.txt

   # 运行测试
   pytest tests/

   # 检查代码风格
   flake8 src/
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   # 或
   git commit -m "fix: fix bug description"
   ```

5. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   # 然后在 GitHub 上创建 Pull Request
   ```

## 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用 4 个空格缩进
- 最大行长度 100 字符
- 使用类型提示（Type Hints）
- 添加文档字符串（Docstrings）

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: add user submission API
fix: resolve rate limit issue
docs: update deployment guide
```

### 测试要求

- 新功能必须包含单元测试
- Bug 修复应包含回归测试
- 测试覆盖率应保持在 80% 以上
- 所有测试必须通过

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/XMTLYL/skill-catcher.git
cd skill-catcher
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install pytest pytest-cov flake8  # 开发依赖
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的配置
```

### 5. 初始化数据库

```bash
python scripts/init_db.py
```

### 6. 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
skill-catcher/
├── src/                    # 源代码
│   ├── github/            # GitHub API 客户端
│   ├── parser/            # SKILL.md 解析器
│   ├── scanner/           # 风险扫描器
│   ├── acquisition/       # 采集策略
│   ├── storage/           # 数据存储
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
├── scripts/               # 运行脚本
├── docs/                  # 文档
└── main.py               # 主入口
```

## 发布流程

项目维护者会定期发布新版本：

1. 更新 `CHANGELOG.md`
2. 创建版本标签
3. 发布到 GitHub Releases

## 行为准则

- 尊重所有贡献者
- 保持友好和专业的沟通
- 接受建设性的批评
- 关注项目的最佳利益

## 许可证

通过贡献代码，你同意你的贡献将在 [Apache-2.0 License](LICENSE) 下发布。

## 联系方式

如有问题，可以：

- 创建 [Issue](https://github.com/XMTLYL/skill-catcher/issues)
- 发起 [Discussion](https://github.com/XMTLYL/skill-catcher/discussions)

---

再次感谢你的贡献！🎉
