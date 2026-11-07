#!/usr/bin/env python3
"""
api-test-assistant Web UI (Flask)
"""

from flask import Flask, render_template_string, request, jsonify
from tester import generate_test_cases, run_single_case, analyze_results
import json

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Test Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 30px; font-size: 2.5rem; }
        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .step { margin-bottom: 25px; }
        .step-title { font-size: 1.2rem; font-weight: bold; color: #333; margin-bottom: 10px; }
        textarea {
            width: 100%;
            min-height: 100px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            font-family: 'Courier New', monospace;
            resize: vertical;
        }
        textarea:focus { outline: none; border-color: #11998e; }
        input[type=text] {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 10px;
        }
        input[type=text]:focus { outline: none; border-color: #11998e; }
        button {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .results { margin-top: 20px; }
        .case-item {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 4px solid #ccc;
        }
        .case-pass { background: #d4edda; border-color: #28a745; }
        .case-fail { background: #f8d7da; border-color: #dc3545; }
        .case-name { font-weight: bold; }
        .case-meta { font-size: 0.9rem; color: #666; margin-top: 4px; }
        .stats { display: flex; gap: 15px; margin: 20px 0; }
        .stat-box {
            flex: 1;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-total { background: #e9ecef; }
        .stat-pass { background: #d4edda; }
        .stat-fail { background: #f8d7da; }
        .stat-num { font-size: 2rem; font-weight: bold; }
        .loading { text-align: center; padding: 20px; display: none; }
        .loading.show { display: block; }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #11998e;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .analysis-box {
            margin-top: 20px;
            padding: 20px;
            background: #f0f9ff;
            border-radius: 8px;
            display: none;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        .analysis-box.show { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 API Test Assistant</h1>
        
        <div class="card">
            <div class="step">
                <div class="step-title">1. 描述你的API</div>
                <textarea id="api-desc" placeholder="例如：用户登录接口 POST /api/login，需要username和password参数，返回token和用户信息。错误时返回401。">用户登录接口 POST /api/login
参数：username (string, 必填), password (string, 必填)
成功返回：200 + token
失败返回：401 + 错误信息</textarea>
                <button onclick="generateCases()" style="margin-top:10px">生成测试用例</button>
            </div>

            <div class="step">
                <div class="step-title">2. 设置测试环境</div>
                <input type="text" id="base-url" placeholder="Base URL，例如 http://localhost:8000" value="http://localhost:8000">
            </div>

            <div class="step">
                <div class="step-title">3. 运行测试</div>
                <button onclick="runTests()" id="run-btn" disabled>运行所有测试</button>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p id="loading-text">处理中...</p>
            </div>

            <div class="stats" id="stats" style="display:none">
                <div class="stat-box stat-total">
                    <div class="stat-num" id="stat-total">0</div>
                    <div>总用例</div>
                </div>
                <div class="stat-box stat-pass">
                    <div class="stat-num" id="stat-pass">0</div>
                    <div>通过</div>
                </div>
                <div class="stat-box stat-fail">
                    <div class="stat-num" id="stat-fail">0</div>
                    <div>失败</div>
                </div>
            </div>

            <div class="results" id="results"></div>

            <div class="analysis-box" id="analysis"></div>
        </div>
    </div>

    <script>
        let testCases = [];

        async function generateCases() {
            const desc = document.getElementById('api-desc').value;
            if (!desc.trim()) { alert('请输入API描述'); return; }
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('loading-text').textContent = 'AI 正在生成测试用例...';
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({desc: desc})
            });
            
            const data = await response.json();
            testCases = data.cases || [];
            
            document.getElementById('loading').classList.remove('show');
            document.getElementById('run-btn').disabled = testCases.length === 0;
            
            alert(`生成了 ${testCases.length} 个测试用例`);
        }

        async function runTests() {
            if (testCases.length === 0) { alert('请先生成测试用例'); return; }
            
            const baseUrl = document.getElementById('base-url').value;
            document.getElementById('loading').classList.add('show');
            document.getElementById('loading-text').textContent = '正在运行测试...';
            
            const response = await fetch('/api/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cases: testCases, base_url: baseUrl})
            });
            
            const data = await response.json();
            const results = data.results || [];
            
            document.getElementById('loading').classList.remove('show');
            
            // 显示统计
            document.getElementById('stats').style.display = 'flex';
            document.getElementById('stat-total').textContent = results.length;
            document.getElementById('stat-pass').textContent = results.filter(r => r.passed).length;
            document.getElementById('stat-fail').textContent = results.filter(r => !r.passed).length;
            
            // 显示结果
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            results.forEach(r => {
                const div = document.createElement('div');
                div.className = 'case-item ' + (r.passed ? 'case-pass' : 'case-fail');
                div.innerHTML = `
                    <div class="case-name">${r.name} [${r.priority}]</div>
                    <div class="case-meta">${r.method} ${r.url} → ${r.status_code || 'ERROR'}</div>
                    ${r.error ? `<div class="case-meta">错误: ${r.error}</div>` : ''}
                `;
                resultsDiv.appendChild(div);
            });
            
            // AI分析
            if (data.analysis) {
                const analysisDiv = document.getElementById('analysis');
                analysisDiv.textContent = data.analysis;
                analysisDiv.classList.add('show');
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json
    desc = data.get('desc', '')
    cases = generate_test_cases(desc)
    return jsonify({"cases": cases})


@app.route('/api/run', methods=['POST'])
def api_run():
    data = request.json
    cases = data.get('cases', [])
    base_url = data.get('base_url', '')
    
    results = []
    for case in cases:
        result = run_single_case(case, base_url)
        results.append(result)
    
    analysis = analyze_results(results)
    
    return jsonify({"results": results, "analysis": analysis})


if __name__ == '__main__':
    print("🚀 API Test Assistant 启动中...")
    print("📖 访问 http://localhost:5002")
    app.run(debug=True, port=5002)
