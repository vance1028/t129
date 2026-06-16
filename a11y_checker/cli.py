from __future__ import annotations

import argparse
import sys
import os
from typing import List, Dict, Optional

from .models import Severity
from .scanner import SiteScanner
from .report import ReportGenerator
from .rules.base import create_default_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="a11y-checker",
        description="离线信息无障碍自动化检测工具",
    )

    parser.add_argument("directory", nargs="?", help="要扫描的站点目录")
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="列出所有可用规则",
    )
    parser.add_argument(
        "-o", "--output",
        help="报告输出目录（默认: a11y-report）",
        default="a11y-report",
    )
    parser.add_argument(
        "--html",
        help="HTML报告输出路径",
        default=None,
    )
    parser.add_argument(
        "--json",
        help="JSON报告输出路径",
        default=None,
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：发现严重级别问题时以非零退出码退出",
    )
    parser.add_argument(
        "--strict-severity",
        choices=["error", "warning", "info"],
        default="error",
        help="严格模式下触发非零退出码的最低严重级别（默认: error）",
    )
    parser.add_argument(
        "--enable-rule",
        action="append",
        default=[],
        help="启用指定规则（可多次使用）",
    )
    parser.add_argument(
        "--disable-rule",
        action="append",
        default=[],
        help="禁用指定规则（可多次使用）",
    )
    parser.add_argument(
        "--set-severity",
        action="append",
        default=[],
        help="设置规则的严重级别，格式: rule_id=error|warning|info",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，只输出错误",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_rules:
        return _cmd_list_rules()

    directory = args.directory
    if not directory:
        parser.print_help()
        return 1

    if not os.path.isdir(directory):
        print(f"错误: 目录不存在: {directory}", file=sys.stderr)
        return 2

    return _cmd_scan(args, directory)


def _cmd_list_rules() -> int:
    registry = create_default_registry()
    rules = registry.get_rule_info()

    print("可用规则列表:")
    print()
    for rule in rules:
        status = "启用" if rule["default_enabled"] else "禁用"
        print(f"  {rule['rule_id']:20s} {rule['default_severity']:8s} {status:4s}  {rule['rule_name']}")
        if rule["description"]:
            print(f"      {rule['description']}")
        print()
    print(f"共 {len(rules)} 条规则")
    return 0


def _parse_severity_overrides(overrides: List[str]) -> Dict[str, Severity]:
    result: Dict[str, Severity] = {}
    for item in overrides:
        if "=" not in item:
            print(f"警告: 无效的严重级别设置: {item}，应为 rule_id=severity", file=sys.stderr)
            continue
        rule_id, sev = item.split("=", 1)
        try:
            result[rule_id.strip()] = Severity.from_string(sev.strip())
        except ValueError as e:
            print(f"警告: {e}", file=sys.stderr)
    return result


def _cmd_scan(args, directory: str) -> int:
    directory = os.path.abspath(directory)

    severity_overrides = _parse_severity_overrides(args.set_severity)

    enabled_rules = args.enable_rule if args.enable_rule else None
    disabled_rules = args.disable_rule if args.disable_rule else None

    if not args.quiet:
        print(f"正在扫描: {directory}")

    scanner = SiteScanner(
        root_dir=directory,
        enabled_rules=enabled_rules,
        disabled_rules=disabled_rules,
        severity_overrides=severity_overrides,
    )

    result = scanner.scan()

    if not args.quiet:
        print(f"扫描完成，共 {result.total_pages} 个页面")
        print(f"  错误: {result.total_errors}")
        print(f"  警告: {result.total_warnings}")
        print(f"  提示: {result.total_info}")
        print()

    output_dir = os.path.abspath(args.output)

    html_path = args.html
    if not html_path:
        html_path = os.path.join(output_dir, "report.html")

    json_path = args.json
    if not json_path:
        json_path = os.path.join(output_dir, "report.json")

    generator = ReportGenerator(result)

    html_saved = generator.save_html(html_path)
    json_saved = generator.save_json(json_path)

    if not args.quiet:
        print(f"HTML报告: {html_saved}")
        print(f"JSON报告: {json_saved}")
        print()

    if args.verbose and not args.quiet:
        for page in sorted(result.pages, key=lambda p: p.file_path):
            if page.issues:
                rel_path = os.path.relpath(page.file_path, directory).replace("\\", "/")
                print(f"\n{rel_path}:")
                for issue in page.issues:
                    loc = f"行 {issue.line}" if issue.line else ""
                    print(f"  [{issue.severity.value}] {issue.rule_id}: {issue.message} ({loc})")

    if args.strict:
        threshold = Severity.from_string(args.strict_severity)
        threshold_order = {"info": 0, "warning": 1, "error": 2}
        threshold_val = threshold_order[threshold.value]

        has_issues = False
        for issue in result.all_issues:
            if threshold_order[issue.severity.value] >= threshold_val:
                has_issues = True
                break

        if has_issues:
            if not args.quiet:
                print(f"\n[严格模式] 发现 {threshold.value} 及以上级别的问题，退出码: 1")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
