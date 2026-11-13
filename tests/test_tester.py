"""
tester.py 的单元测试。

ollama 与 requests 调用均通过 unittest.mock 打桩，测试不发起真实模型请求或真实 HTTP 请求，
也不依赖 ollama / requests Python 包是否安装（见 conftest.py）。
"""

from unittest.mock import MagicMock, patch

import tester as t


class FakeResp:
    """模拟 requests.Response。"""

    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text


def _fake_ollama(content: str) -> MagicMock:
    return MagicMock(return_value={"message": {"content": content}})


# ---------- generate_test_cases ----------

def test_generate_parses_plain_json_array():
    payload = '[{"name": "登录成功", "method": "POST", "url": "/api/login"}]'
    with patch.object(t.ollama, "chat", _fake_ollama(payload)):
        cases = t.generate_test_cases("用户登录接口")
    assert cases == [{"name": "登录成功", "method": "POST", "url": "/api/login"}]


def test_generate_strips_markdown_fence_and_text():
    payload = '用例如下：\n```json\n[{"name": "密码错误"}]\n```\n以上。'
    with patch.object(t.ollama, "chat", _fake_ollama(payload)):
        cases = t.generate_test_cases("用户登录接口")
    assert cases == [{"name": "密码错误"}]


def test_generate_returns_empty_on_invalid_json():
    with patch.object(t.ollama, "chat", _fake_ollama("不是 JSON，没有数组")):
        cases = t.generate_test_cases("接口描述")
    assert cases == []


def test_generate_returns_empty_on_empty_content():
    with patch.object(t.ollama, "chat", _fake_ollama("")):
        cases = t.generate_test_cases("接口描述")
    assert cases == []


# ---------- run_single_case ----------

def test_run_joins_relative_url_with_base():
    case = {"url": "/api/login", "method": "GET"}
    with patch.object(t.requests, "request", return_value=FakeResp(200, "ok")) as mock_req:
        result = t.run_single_case(case, base_url="http://localhost:8000/")
    assert result["url"] == "http://localhost:8000/api/login"
    assert result["passed"] is True
    mock_req.assert_called_once()


def test_run_keeps_absolute_url():
    case = {"url": "http://other-host/x", "method": "GET"}
    with patch.object(t.requests, "request", return_value=FakeResp(200, "ok")):
        result = t.run_single_case(case, base_url="http://localhost:8000")
    assert result["url"] == "http://other-host/x"


def test_run_uppercases_method():
    case = {"url": "/x", "method": "post"}
    with patch.object(t.requests, "request", return_value=FakeResp(200, "ok")):
        result = t.run_single_case(case)
    assert result["method"] == "POST"


def test_run_passes_when_status_and_keyword_match():
    case = {"url": "/x", "method": "GET", "expected_status": 200, "expected_contains": "welcome"}
    with patch.object(t.requests, "request", return_value=FakeResp(200, "welcome back")):
        result = t.run_single_case(case)
    assert result["passed"] is True
    assert result["status_code"] == 200


def test_run_fails_on_status_mismatch():
    case = {"url": "/x", "method": "GET", "expected_status": 200}
    with patch.object(t.requests, "request", return_value=FakeResp(401, "unauthorized")):
        result = t.run_single_case(case)
    assert result["passed"] is False


def test_run_fails_when_keyword_missing():
    case = {"url": "/x", "method": "GET", "expected_status": 200, "expected_contains": "welcome"}
    with patch.object(t.requests, "request", return_value=FakeResp(200, "hello")):
        result = t.run_single_case(case)
    assert result["passed"] is False


def test_run_post_sends_json_body():
    case = {"url": "/x", "method": "POST", "body": {"username": "a"}}
    with patch.object(t.requests, "request", return_value=FakeResp(200, "ok")) as mock_req:
        t.run_single_case(case)
    assert mock_req.call_args.kwargs["json"] == {"username": "a"}


def test_run_get_does_not_send_json_body():
    case = {"url": "/x", "method": "GET", "body": {"username": "a"}}
    with patch.object(t.requests, "request", return_value=FakeResp(200, "ok")) as mock_req:
        t.run_single_case(case)
    assert "json" not in mock_req.call_args.kwargs


def test_run_connection_error_marks_failed():
    case = {"url": "/x", "method": "GET"}
    with patch.object(t.requests, "request", side_effect=t.requests.exceptions.ConnectionError()):
        result = t.run_single_case(case)
    assert result["passed"] is False
    assert result["error"] == "连接失败"


def test_run_timeout_marks_failed():
    case = {"url": "/x", "method": "GET"}
    with patch.object(t.requests, "request", side_effect=t.requests.exceptions.Timeout()):
        result = t.run_single_case(case)
    assert result["passed"] is False
    assert result["error"] == "请求超时"


def test_run_non_numeric_expected_status_defaults_to_200():
    case = {"url": "/x", "method": "GET", "expected_status": "abc"}
    with patch.object(t.requests, "request", return_value=FakeResp(200, "ok")):
        result = t.run_single_case(case)
    assert result["passed"] is True


# ---------- analyze_results ----------

def test_analyze_counts_and_returns_summary():
    results = [
        {"passed": True},
        {"passed": True},
        {"passed": False},
    ]
    mock_chat = _fake_ollama("总体通过 2/3")
    with patch.object(t.ollama, "chat", mock_chat):
        summary = t.analyze_results(results)

    assert summary == "总体通过 2/3"
    prompt = mock_chat.call_args.kwargs["messages"][0]["content"]
    assert "总用例数：3" in prompt
    assert "通过：2" in prompt
    assert "失败：1" in prompt
