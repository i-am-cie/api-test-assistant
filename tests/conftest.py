"""Pytest 共享配置：把项目根目录加入导入路径，并在未安装 ollama/requests 时注入占位模块。"""

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 未安装 ollama Python 包时注入占位模块；测试用例通过 unittest.mock 替换 ollama.chat。
if "ollama" not in sys.modules:
    fake_ollama = types.ModuleType("ollama")
    fake_ollama.chat = lambda **kwargs: {"message": {"content": ""}}
    sys.modules["ollama"] = fake_ollama

# 未安装 requests 时注入占位模块，并带上 exceptions 子模块供异常分类使用。
if "requests" not in sys.modules:
    fake_requests = types.ModuleType("requests")
    fake_exc = types.ModuleType("requests.exceptions")
    fake_exc.ConnectionError = type("ConnectionError", (Exception,), {})
    fake_exc.Timeout = type("Timeout", (Exception,), {})
    fake_exc.RequestException = type("RequestException", (Exception,), {})
    fake_requests.exceptions = fake_exc
    fake_requests.request = lambda *args, **kwargs: None
    sys.modules["requests"] = fake_requests
    sys.modules["requests.exceptions"] = fake_exc
