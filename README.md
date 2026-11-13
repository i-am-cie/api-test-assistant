# API Test Assistant

A local web tool that generates API test cases from a plain-language endpoint description with an [Ollama](https://ollama.com/)-served LLM, then sends the requests and reports pass/fail — fully offline, no API key.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![LLM](https://img.shields.io/badge/LLM-Ollama-black)
![Offline](https://img.shields.io/badge/Offline-100%25-success)
![Tests](https://img.shields.io/badge/tests-16%20passed-success)

## What it does

- **Description → cases**: describe an endpoint (method, path, parameters, success and error responses) and the LLM returns a JSON array of test cases covering normal, missing-parameter, invalid-format, permission and boundary scenarios.
- **Executes the cases**: the web UI sends each generated case with `requests` (10 s timeout) against the base URL you enter and records status code, pass/fail and a 500-character response preview.
- **Pass/fail summary**: counts total, passed and failed cases, with the method, URL and status code for each result.
- **AI analysis**: sends the aggregated results back to the model for a short written summary of likely causes and suggestions.
- **Local only**: your API descriptions and test results stay on your machine; only the target API you point at receives traffic.

## Requirements

- [Ollama](https://ollama.com/) installed and running locally.
- A chat model, default `qwen2.5:7b` (see [Configuration](#configuration)). Any instruction-following model should work, e.g. `qwen2.5:3b` on small machines.
- Python 3.9 or newer.
- An API you are allowed to test, reachable from your machine (any framework, not just Python).

## Install

```bash
git clone https://github.com/i-am-cie/api-test-assistant.git
cd api-test-assistant
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open <http://localhost:5002> in your browser. The Flask development server listens on port `5002`.

## Run tests

The repository ships with a pytest suite under `tests/` that covers case JSON parsing, URL joining, request construction, pass/fail judgment, error classification and result counting. Both the Ollama call and the HTTP request are mocked, so the suite does **not** require Ollama, a live API, or the `ollama`/`requests` packages to be installed.

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

## Usage

1. Make sure Ollama is running and the model is pulled: `ollama pull qwen2.5:7b`. Start the API you want to test and note its base URL, e.g. `http://localhost:8000`.
2. Open <http://localhost:5002>.
3. **Step 1** — describe the API in the text area (method, path, parameters, success/error responses) and click **生成测试用例 / Generate cases**. The page reports how many cases were generated.
4. **Step 2** — set the **Base URL** field to your API root. Relative paths returned by the model are appended to it.
5. **Step 3** — click **运行所有测试 / Run all tests**. Results appear as green (pass) or red (fail) cards, followed by the AI's written analysis.
6. Command-line generation only (no execution):

```bash
python tester.py --desc "用户登录接口 POST /api/login，参数 username 和 password，成功 200，失败 401"
```

The generated JSON array is printed to stdout. Running the cases is done from the web UI; `tester.py --run` currently just prints a reminder.

## Configuration

There is no configuration file; settings live in the source or are entered in the UI:

| Setting | Where | Default | Meaning |
| --- | --- | --- | --- |
| Model | `MODEL` in `tester.py` | `qwen2.5:7b` | Ollama model used for case generation and analysis. |
| Ollama endpoint | `OLLAMA_HOST` environment variable | `http://127.0.0.1:11434` | Read automatically by the `ollama` Python client; set it if Ollama runs elsewhere. |
| Web port | `app.run(..., port=5002)` in `app.py` | `5002` | Port of the Flask development server. |
| Base URL | **Base URL** input in the web UI | `http://localhost:8000` | Target API root; can be changed per run without restarting. |
| Request timeout | `"timeout": 10` in `run_single_case` (`tester.py`) | 10 s | Per-request timeout. |

## How it works

1. The page posts the API description to `POST /api/generate`.
2. `tester.py::generate_test_cases` builds a prompt that demands a strict JSON array (name, method, url, headers, body, expected_status, expected_contains, priority, type, description), then extracts the first `[ ... ]` block and parses it.
3. The page keeps the cases in memory and posts them with the base URL to `POST /api/run`.
4. For each case, `run_single_case` joins the URL with the base URL, sends the request with `requests` (JSON body for POST/PUT/PATCH), and marks the case passed when the status code equals `expected_status` and `expected_contains` appears in the response text.
5. `analyze_results` sends the result list to the model and returns a short Chinese summary.

The repository's own pytest suite covers only this parsing/execution/analysis code; it does **not** hit a real API or validate the model's generated cases.

## Limitations

- **Generation quality depends on the model.** Cases may use wrong paths, wrong methods or unrealistic payloads; expect to edit or regenerate them.
- **Shallow assertions.** A case passes only on status-code equality plus an optional substring match; response schema, headers and timing are not checked.
- **No authentication helpers.** Tokens and cookies must be supplied manually in the generated `headers`; there is no login flow or secret storage.
- **Runs whatever it is told.** The server sends arbitrary HTTP requests from the case data to the base URL — only run it locally, and never expose this Flask app (`debug=True`) to a network.
- **No test report export.** Results are shown in the page and are lost on refresh; the README no longer claims an HTML/Markdown report.
- **No persistence/history.** Cases and results are not stored, and `reports/` (ignored by git) is not written by the current code.
- **Chinese prompts.** Prompts are in Chinese, so generated cases and analysis are usually in Chinese.

## License

MIT © 2026 i-am-cie — see [LICENSE](LICENSE).

## 中文说明

这是一个本地 AI API 测试助手：用自然语言描述接口后，通过本机 Ollama 大模型生成 JSON 格式的测试用例（覆盖正常、缺失参数、非法格式、权限、边界等场景），再在网页里设置 Base URL 一键批量发送请求，得到通过/失败统计和 AI 分析总结。所有数据都在本机，无需 API Key。使用前先安装 Ollama 并拉取 `qwen2.5:7b`，然后 `pip install -r requirements.txt`、`python app.py`，浏览器打开 http://localhost:5002。仓库自带 pytest 单元测试（`tests/` 目录），覆盖用例解析、URL 拼接、请求构造、通过/失败判定、异常分类和结果统计，模型调用与 HTTP 请求均已打桩，运行测试无需启动 Ollama 或真实接口：`pip install -r requirements-dev.txt` 后 `python -m pytest tests/ -v`。注意：生成用例可能不准确，断言只比较状态码和关键字，且只会执行你指定的目标接口，请勿对未授权系统发起测试。
