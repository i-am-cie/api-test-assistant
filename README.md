# API Test Assistant

> 本地AI API测试助手，基于 Ollama 大模型，完全离线运行，无需 API Key。

## ✨ 功能特性

- **AI生成测试用例**：输入API文档或描述，自动生成完整测试用例
- **自动发送请求**：一键执行所有测试用例，收集响应
- **响应分析**：AI自动分析响应是否符合预期，识别异常
- **多场景覆盖**：正常请求、参数缺失、权限校验、边界值、异常输入
- **测试报告**：生成HTML/Markdown格式的测试报告
- **完全本地**：所有数据都在你的电脑上

## 🚀 快速开始

### 前置要求

1. 安装 [Ollama](https://ollama.com/)
2. 拉取模型：
   ```bash
   ollama pull qwen2.5:7b
   ```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动 Web 界面

```bash
python app.py
```

打开浏览器访问 http://localhost:5002

### 命令行模式

```bash
# 从API描述生成测试用例
python tester.py --desc "用户登录接口 POST /api/login，参数username和password"

# 运行测试
python tester.py --run --url "http://localhost:8000/api/login" --method POST
```

## 📦 项目结构

```
api-test-assistant/
├── app.py              # Flask Web 界面
├── tester.py           # 核心测试逻辑
├── requirements.txt    # Python 依赖
└── README.md
```

## 🛠️ 技术栈

- **后端**：Python + Flask + requests
- **LLM**：Ollama (Qwen2.5)
- **前端**：HTML + 原生 JS

## 📝 License

MIT