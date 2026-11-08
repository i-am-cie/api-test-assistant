#!/usr/bin/env python3
"""
api-test-assistant: Local AI API testing using Ollama.

Usage:
    python tester.py --desc "用户登录接口 POST /api/login"
    python tester.py --run --url "http://localhost:8000/api/login" --method POST
"""

import argparse
import json
import requests
import ollama

MODEL = "qwen2.5:7b"


def generate_test_cases(api_desc: str) -> list:
    """Generate API test cases from description."""
    prompt = f"""你是一个资深API测试工程师。请为以下API生成完整的测试用例。

API描述：
{api_desc}

请严格以JSON数组格式输出，每个测试用例包含以下字段：
- name: 用例名称
- method: HTTP方法 (GET/POST/PUT/DELETE)
- url: 请求路径（假设base URL是http://localhost:8000）
- headers: 请求头JSON对象
- body: 请求体JSON对象（如适用）
- expected_status: 预期HTTP状态码
- expected_contains: 预期响应中包含的关键字
- priority: 优先级 (P0/P1/P2)
- type: 用例类型 (正常/异常/边界/权限)
- description: 用例描述

请生成至少10个测试用例，覆盖：
1. 正常请求场景
2. 参数缺失/为空
3. 非法参数格式
4. 权限校验失败
5. 边界值（超长字符串、特殊字符）

只输出JSON数组，不要输出其他内容。
"""
    
    resp = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    content = resp["message"]["content"].strip()
    
    try:
        start = content.index("[")
        end = content.rindex("]") + 1
        return json.loads(content[start:end])
    except (ValueError, json.JSONDecodeError):
        return []


def run_single_case(case: dict, base_url: str = "") -> dict:
    """Run a single test case and return result."""
    url = case.get("url", "")
    if base_url and not url.startswith("http"):
        url = base_url.rstrip("/") + "/" + url.lstrip("/")
    
    method = case.get("method", "GET").upper()
    headers = case.get("headers") or {}
    body = case.get("body")
    
    result = {
        "name": case.get("name", ""),
        "type": case.get("type", ""),
        "priority": case.get("priority", ""),
        "url": url,
        "method": method,
        "status_code": None,
        "passed": False,
        "error": None,
        "response_preview": ""
    }
    
    try:
        kwargs = {"headers": headers, "timeout": 10}
        if body and method in ("POST", "PUT", "PATCH"):
            kwargs["json"] = body
        
        resp = requests.request(method, url, **kwargs)
        result["status_code"] = resp.status_code
        result["response_preview"] = resp.text[:500]
        
        expected_status = case.get("expected_status", 200)
        try:
            expected_status = int(expected_status)
        except (TypeError, ValueError):
            expected_status = 200
        expected_contains = case.get("expected_contains", "")
        
        status_ok = resp.status_code == expected_status
        content_ok = expected_contains in resp.text if expected_contains else True
        result["passed"] = status_ok and content_ok
        
    except requests.exceptions.ConnectionError:
        result["error"] = "连接失败"
    except requests.exceptions.Timeout:
        result["error"] = "请求超时"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def analyze_results(test_results: list) -> str:
    """Use AI to analyze test results."""
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    prompt = f"""你是一个API测试专家。请分析以下测试结果并给出总结。

测试结果：
- 总用例数：{total}
- 通过：{passed}
- 失败：{total - passed}

详细结果：
{json.dumps(test_results, ensure_ascii=False, indent=2)[:2000]}

请输出：
1. 总体评价
2. 失败用例的可能原因分析
3. 改进建议

用简洁的中文回答。
"""
    
    resp = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return resp["message"]["content"]


def main():
    parser = argparse.ArgumentParser(description="API Test Assistant")
    parser.add_argument("--desc", type=str, help="API描述，生成测试用例")
    parser.add_argument("--run", action="store_true", help="运行测试用例")
    parser.add_argument("--url", type=str, help="API base URL")
    parser.add_argument("--output", type=str, default="test_report.json", help="输出报告路径")
    
    args = parser.parse_args()
    
    if args.desc:
        print("生成测试用例中...\n")
        cases = generate_test_cases(args.desc)
        print(f"生成了 {len(cases)} 个测试用例\n")
        print(json.dumps(cases, ensure_ascii=False, indent=2))
    
    if args.run:
        # 这里简化演示，实际应该从文件读取用例
        print("请使用Web界面运行完整测试")


if __name__ == "__main__":
    main()
