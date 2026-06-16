import unittest
import tempfile
import os
import json

from a11y_checker.report import ReportGenerator
from a11y_checker.models import ScanResult, PageResult, Issue, Severity
from a11y_checker.cli import main


class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        result = ScanResult(root_dir="/test")
        result.total_pages = 2

        page1 = PageResult(file_path="/test/index.html")
        page1.issues.append(Issue(
            rule_id="image-alt",
            rule_name="图片缺少alt文本",
            severity=Severity.ERROR,
            message="图片缺少alt属性",
            file_path="/test/index.html",
            line=10,
            element="img",
        ))
        page1.issues.append(Issue(
            rule_id="heading-order",
            rule_name="标题层级乱跳",
            severity=Severity.WARNING,
            message="标题从h1跳到h3",
            file_path="/test/index.html",
            line=20,
            element="h3",
        ))
        result.pages.append(page1)

        page2 = PageResult(file_path="/test/about.html")
        page2.issues.append(Issue(
            rule_id="image-alt",
            rule_name="图片缺少alt文本",
            severity=Severity.ERROR,
            message="图片缺少alt属性",
            file_path="/test/about.html",
            line=5,
            element="img",
        ))
        result.pages.append(page2)

        self.result = result
        self.generator = ReportGenerator(result)

    def test_generate_json(self):
        json_str = self.generator.generate_json()
        data = json.loads(json_str)

        self.assertEqual(data["total_pages"], 2)
        self.assertEqual(data["total_errors"], 2)
        self.assertEqual(data["total_warnings"], 1)
        self.assertEqual(len(data["pages"]), 2)
        self.assertIn("generated_at", data)

    def test_generate_json_compact(self):
        json_str = self.generator.generate_json(pretty=False)
        data = json.loads(json_str)
        self.assertEqual(data["total_pages"], 2)

    def test_generate_html(self):
        html = self.generator.generate_html()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("信息无障碍检测报告", html)
        self.assertIn("图片缺少alt", html)
        self.assertIn("标题层级乱跳", html)
        self.assertIn("index.html", html)
        self.assertIn("about.html", html)

    def test_save_html_and_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = os.path.join(tmpdir, "report.html")
            json_path = os.path.join(tmpdir, "report.json")

            saved_html = self.generator.save_html(html_path)
            saved_json = self.generator.save_json(json_path)

            self.assertEqual(saved_html, html_path)
            self.assertEqual(saved_json, json_path)
            self.assertTrue(os.path.exists(html_path))
            self.assertTrue(os.path.exists(json_path))

            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("信息无障碍检测报告", content)

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["total_pages"], 2)

    def test_empty_result(self):
        empty_result = ScanResult(root_dir="/test")
        generator = ReportGenerator(empty_result)

        html = generator.generate_html()
        self.assertIn("信息无障碍检测报告", html)

        json_str = generator.generate_json()
        data = json.loads(json_str)
        self.assertEqual(data["total_pages"], 0)
        self.assertEqual(data["total_errors"], 0)


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_file(self, rel_path, content):
        full_path = os.path.join(self.temp_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    def test_list_rules(self):
        exit_code = main(["--list-rules"])
        self.assertEqual(exit_code, 0)

    def test_scan_clean_page_strict_pass(self):
        self._write_file("good.html", '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <body>
            <h1>标题</h1>
            <img src="test.png" alt="测试图片">
            <a href="good.html">好页面链接</a>
            <label for="name">姓名</label>
            <input type="text" id="name" name="name">
        </body>
        </html>
        ''')

        exit_code = main([
            self.temp_dir,
            "--strict",
            "--quiet",
            "--output", os.path.join(self.temp_dir, "output"),
        ])
        self.assertEqual(exit_code, 0)

    def test_scan_bad_page_strict_fail(self):
        self._write_file("bad.html", '''
        <html>
        <body>
            <img src="test.png">
        </body>
        </html>
        ''')

        exit_code = main([
            self.temp_dir,
            "--strict",
            "--quiet",
            "--output", os.path.join(self.temp_dir, "output"),
        ])
        self.assertEqual(exit_code, 1)

    def test_scan_with_disabled_rule(self):
        self._write_file("bad.html", '''
        <html>
        <body>
            <img src="test.png">
        </body>
        </html>
        ''')

        exit_code = main([
            self.temp_dir,
            "--strict",
            "--disable-rule", "image-alt",
            "--disable-rule", "html-lang",
            "--disable-rule", "heading-order",
            "--quiet",
            "--output", os.path.join(self.temp_dir, "output"),
        ])
        self.assertEqual(exit_code, 0)

    def test_scan_generates_reports(self):
        self._write_file("index.html", "<html lang='zh'><body><h1>Test</h1></body></html>")
        output_dir = os.path.join(self.temp_dir, "report")

        exit_code = main([
            self.temp_dir,
            "--output", output_dir,
            "--quiet",
        ])

        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(os.path.join(output_dir, "report.html")))
        self.assertTrue(os.path.exists(os.path.join(output_dir, "report.json")))

    def test_invalid_directory(self):
        exit_code = main([
            "/nonexistent/path",
            "--quiet",
        ])
        self.assertEqual(exit_code, 2)

    def test_no_arguments_shows_help(self):
        exit_code = main([])
        self.assertEqual(exit_code, 1)

    def test_strict_warning_threshold(self):
        self._write_file("test.html", '''
        <html lang="zh">
        <body>
            <h1>标题</h1>
            <a href="page.html">点击这里</a>
        </body>
        </html>
        ''')
        self._write_file("page.html", "<html lang='zh'><body><h1>Page</h1></body></html>")

        exit_code = main([
            self.temp_dir,
            "--strict",
            "--strict-severity", "warning",
            "--quiet",
            "--output", os.path.join(self.temp_dir, "output"),
        ])
        self.assertEqual(exit_code, 1)


class TestDeterminism(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_file(self, rel_path, content):
        full_path = os.path.join(self.temp_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    def test_multiple_runs_consistent(self):
        self._write_file("index.html", '''
        <html>
        <head>
            <style>
                .bad { color: #ccc; }
            </style>
        </head>
        <body>
            <h3>标题</h3>
            <img src="test.png">
            <img src="test2.png" alt="">
            <a href="missing.html">点击这里</a>
            <a href="#nonexist">跳转</a>
            <input type="text" name="test">
            <p class="bad">低对比度</p>
            <div role="button" aria-invalidattr="x">test</div>
        </body>
        </html>
        ''')
        self._write_file("about.html", '''
        <html lang="en">
        <body>
            <h1>About</h1>
            <img src="photo.jpg" alt="Photo">
        </body>
        </html>
        ''')

        from a11y_checker.scanner import SiteScanner

        scanner = SiteScanner(self.temp_dir)
        result1 = scanner.scan()
        result2 = scanner.scan()
        result3 = scanner.scan()

        self.assertEqual(result1.total_pages, result2.total_pages)
        self.assertEqual(result1.total_errors, result2.total_errors)
        self.assertEqual(result1.total_warnings, result2.total_warnings)
        self.assertEqual(result1.total_info, result2.total_info)

        self.assertEqual(result2.total_pages, result3.total_pages)
        self.assertEqual(result2.total_errors, result3.total_errors)
        self.assertEqual(result2.total_warnings, result3.total_warnings)

        issues1 = sorted([(i.rule_id, i.message, i.file_path) for i in result1.all_issues])
        issues2 = sorted([(i.rule_id, i.message, i.file_path) for i in result2.all_issues])
        self.assertEqual(issues1, issues2)


if __name__ == "__main__":
    unittest.main()
