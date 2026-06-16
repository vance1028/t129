from __future__ import annotations

import json
import os
from typing import Dict, List, Any
from datetime import datetime

from .models import ScanResult, Severity


class ReportGenerator:
    def __init__(self, result: ScanResult):
        self.result = result

    def generate_json(self, pretty: bool = True) -> str:
        data = self.result.to_dict()
        data["generated_at"] = datetime.now().isoformat()
        if pretty:
            return json.dumps(data, ensure_ascii=False, indent=2)
        return json.dumps(data, ensure_ascii=False)

    def generate_html(self) -> str:
        template = self._html_template()
        data = self._prepare_template_data()
        return template.format(**data)

    def _prepare_template_data(self) -> Dict[str, Any]:
        result = self.result

        by_rule: Dict[str, List[Any]] = {}
        for issue in result.all_issues:
            rule_id = issue.rule_id
            if rule_id not in by_rule:
                by_rule[rule_id] = []
            by_rule[rule_id].append(issue)

        by_rule_sorted = sorted(
            by_rule.items(),
            key=lambda x: (-len(x[1]), x[0]),
        )

        by_page_sorted = sorted(
            result.pages,
            key=lambda p: (-p.error_count, -p.warning_count, p.file_path),
        )

        rule_sections = ""
        for rule_id, issues in by_rule_sorted:
            if not issues:
                continue
            first = issues[0]
            severity = first.severity.value
            issues_html = self._render_issues_list(issues)
            rule_sections += f"""
            <div class="rule-section severity-{severity}">
                <h3>{first.rule_name} <span class="rule-id">[{rule_id}]</span> <span class="count">{len(issues)} 个问题</span></h3>
                <div class="issues-list">
                    {issues_html}
                </div>
            </div>
            """

        page_sections = ""
        for page in by_page_sorted:
            rel_path = os.path.relpath(page.file_path, result.root_dir).replace("\\", "/")
            page_issues_html = self._render_issues_list(page.issues) if page.issues else "<p class='no-issues'>未发现无障碍问题</p>"
            page_sections += f"""
            <div class="page-section">
                <h3>{rel_path}
                    <span class="counts">
                        {f'<span class="error-count">{page.error_count} 错误</span>' if page.error_count else ''}
                        {f'<span class="warning-count">{page.warning_count} 警告</span>' if page.warning_count else ''}
                        {f'<span class="info-count">{page.info_count} 提示</span>' if page.info_count else ''}
                    </span>
                </h3>
                <div class="page-issues">
                    {page_issues_html}
                </div>
            </div>
            """

        return {
            "title": "信息无障碍检测报告",
            "root_dir": result.root_dir,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_pages": result.total_pages,
            "total_errors": result.total_errors,
            "total_warnings": result.total_warnings,
            "total_info": result.total_info,
            "rule_sections": rule_sections,
            "page_sections": page_sections,
        }

    def _render_issues_list(self, issues: List) -> str:
        html = ""
        for issue in issues:
            severity = issue.severity.value
            location = ""
            if issue.file_path:
                location += f"<span class='file'>{os.path.basename(issue.file_path)}</span>"
                if issue.line:
                    location += f"<span class='line'>第 {issue.line} 行</span>"
            if issue.element:
                location += f"<span class='element'>{issue.element}</span>"

            snippet_html = ""
            if issue.snippet:
                snippet_html = f"<pre class='snippet'>{self._escape_html(issue.snippet[:200])}</pre>"

            html += f"""
            <div class="issue severity-{severity}">
                <div class="issue-header">
                    <span class="severity-badge">{severity}</span>
                    <span class="message">{self._escape_html(issue.message)}</span>
                </div>
                <div class="issue-location">{location}</div>
                {snippet_html}
            </div>
            """
        return html

    def _escape_html(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _html_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 28px; margin-bottom: 10px; color: #1a1a2e; }}
        h2 {{ font-size: 22px; margin: 30px 0 15px; color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }}
        h3 {{ font-size: 18px; margin: 20px 0 12px; color: #333; }}
        .summary {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .summary-stats {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 16px;
        }}
        .stat-card {{
            flex: 1;
            min-width: 140px;
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card .number {{ font-size: 32px; font-weight: bold; }}
        .stat-card .label {{ font-size: 14px; opacity: 0.85; }}
        .stat-pages {{ background: #e3f2fd; color: #1565c0; }}
        .stat-errors {{ background: #ffebee; color: #c62828; }}
        .stat-warnings {{ background: #fff3e0; color: #e65100; }}
        .stat-info {{ background: #e8f5e9; color: #2e7d32; }}
        .meta {{
            color: #666;
            font-size: 14px;
            margin-top: 12px;
        }}
        .nav-tabs {{
            display: flex;
            gap: 4px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .nav-tab {{
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            color: #666;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
        }}
        .nav-tab.active {{
            color: #1976d2;
            border-bottom-color: #1976d2;
            font-weight: 600;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .rule-section, .page-section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }}
        .rule-section h3, .page-section h3 {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .rule-id {{
            font-size: 12px;
            color: #999;
            font-family: monospace;
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .count {{
            font-size: 13px;
            background: #f0f0f0;
            padding: 2px 10px;
            border-radius: 12px;
            color: #666;
        }}
        .counts {{ display: flex; gap: 8px; margin-left: auto; }}
        .counts span {{ font-size: 12px; padding: 2px 8px; border-radius: 4px; }}
        .error-count {{ background: #ffebee; color: #c62828; }}
        .warning-count {{ background: #fff3e0; color: #e65100; }}
        .info-count {{ background: #e8f5e9; color: #2e7d32; }}
        .issues-list {{ margin-top: 12px; }}
        .issue {{
            border-left: 4px solid #ccc;
            padding: 12px 16px;
            margin-bottom: 10px;
            background: #fafafa;
            border-radius: 0 6px 6px 0;
        }}
        .issue.severity-error {{ border-left-color: #e53935; background: #fff5f5; }}
        .issue.severity-warning {{ border-left-color: #fb8c00; background: #fffaf0; }}
        .issue.severity-info {{ border-left-color: #43a047; background: #f6fbf6; }}
        .issue-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
        .severity-badge {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 2px 8px;
            border-radius: 4px;
            color: white;
        }}
        .severity-error .severity-badge {{ background: #e53935; }}
        .severity-warning .severity-badge {{ background: #fb8c00; }}
        .severity-info .severity-badge {{ background: #43a047; }}
        .message {{ font-weight: 500; }}
        .issue-location {{
            font-size: 12px;
            color: #888;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 8px;
        }}
        .issue-location .file {{ font-family: monospace; }}
        .snippet {{
            font-size: 12px;
            background: #f0f0f0;
            padding: 8px 12px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: monospace;
            color: #555;
        }}
        .no-issues {{ color: #2e7d32; font-style: italic; padding: 10px 0; }}
        .page-issues {{ margin-top: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="summary">
            <div class="meta">
                扫描目录：{root_dir}<br>
                生成时间：{generated_at}
            </div>
            <div class="summary-stats">
                <div class="stat-card stat-pages">
                    <div class="number">{total_pages}</div>
                    <div class="label">页面总数</div>
                </div>
                <div class="stat-card stat-errors">
                    <div class="number">{total_errors}</div>
                    <div class="label">错误</div>
                </div>
                <div class="stat-card stat-warnings">
                    <div class="number">{total_warnings}</div>
                    <div class="label">警告</div>
                </div>
                <div class="stat-card stat-info">
                    <div class="number">{total_info}</div>
                    <div class="label">提示</div>
                </div>
            </div>
        </div>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="switchTab('by-rule', this)">按规则分类</button>
            <button class="nav-tab" onclick="switchTab('by-page', this)">按页面分类</button>
        </div>

        <div id="by-rule" class="tab-content active">
            <h2>按规则分类</h2>
            {rule_sections}
        </div>

        <div id="by-page" class="tab-content">
            <h2>按页面分类</h2>
            {page_sections}
        </div>
    </div>

    <script>
        function switchTab(tabId, btn) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }}
    </script>
</body>
</html>"""

    def save_json(self, output_path: str, pretty: bool = True) -> str:
        content = self.generate_json(pretty=pretty)
        self._ensure_dir(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def save_html(self, output_path: str) -> str:
        content = self.generate_html()
        self._ensure_dir(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def _ensure_dir(self, file_path: str):
        dir_path = os.path.dirname(os.path.abspath(file_path))
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
