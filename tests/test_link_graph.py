import unittest
import tempfile
import os

from a11y_checker.link_graph import LinkGraph
from a11y_checker.scanner import SiteScanner
from a11y_checker.dom_engine import DOMChecker
from a11y_checker.models import Severity


class TestLinkGraph(unittest.TestCase):
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

    def test_build_from_directory(self):
        self._write_file("index.html", "<html></html>")
        self._write_file("about.html", "<html></html>")
        self._write_file("sub/page.html", "<html></html>")

        graph = LinkGraph(self.temp_dir)
        graph.build_from_directory()

        self.assertIn("index.html", graph.all_files)
        self.assertIn("about.html", graph.all_files)
        self.assertIn("sub/page.html", graph.all_files)

    def test_valid_internal_link(self):
        self._write_file("index.html", "<html></html>")
        self._write_file("about.html", "<html></html>")

        graph = LinkGraph(self.temp_dir)
        graph.build_from_directory()

        is_dead, reason = graph.check_link(
            os.path.join(self.temp_dir, "index.html"),
            "about.html"
        )
        self.assertFalse(is_dead)

    def test_dead_internal_link(self):
        self._write_file("index.html", "<html></html>")

        graph = LinkGraph(self.temp_dir)
        graph.build_from_directory()

        is_dead, reason = graph.check_link(
            os.path.join(self.temp_dir, "index.html"),
            "nonexistent.html"
        )
        self.assertTrue(is_dead)
        self.assertIn("不存在", reason)

    def test_anchor_exists(self):
        self._write_file("index.html", '<html><body><div id="section1"></div></body></html>')

        graph = LinkGraph(self.temp_dir)
        graph.build_from_directory()
        graph.add_page(
            os.path.join(self.temp_dir, "index.html"),
            [],
            ["section1"],
        )

        is_dead, reason = graph.check_link(
            os.path.join(self.temp_dir, "index.html"),
            "#section1"
        )
        self.assertFalse(is_dead)

    def test_anchor_not_exists(self):
        self._write_file("index.html", "<html></html>")

        graph = LinkGraph(self.temp_dir)
        graph.build_from_directory()
        graph.add_page(
            os.path.join(self.temp_dir, "index.html"),
            [],
            [],
        )

        is_dead, reason = graph.check_link(
            os.path.join(self.temp_dir, "index.html"),
            "#missing"
        )
        self.assertTrue(is_dead)

    def test_external_link_not_checked(self):
        graph = LinkGraph(self.temp_dir)
        graph.build_from_directory()

        page_path = os.path.join(self.temp_dir, "test.html")
        is_dead, reason = graph.check_link(page_path, "http://example.com")
        self.assertFalse(is_dead)

    def test_subdirectory_link(self):
        self._write_file("index.html", "<html></html>")
        self._write_file("sub/page.html", "<html></html>")

        graph = LinkGraph(self.temp_dir)
        graph.build_from_directory()

        is_dead, _ = graph.check_link(
            os.path.join(self.temp_dir, "sub/page.html"),
            "../index.html"
        )
        self.assertFalse(is_dead)

    def test_root_relative_link(self):
        self._write_file("index.html", "<html></html>")
        self._write_file("sub/page.html", "<html></html>")

        graph = LinkGraph(self.temp_dir)
        graph.build_from_directory()

        is_dead, _ = graph.check_link(
            os.path.join(self.temp_dir, "sub/page.html"),
            "/index.html"
        )
        self.assertFalse(is_dead)


class TestDeadLinkRule(unittest.TestCase):
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

    def test_dead_link_detected(self):
        self._write_file("index.html", '''
        <html lang="zh">
        <body>
            <a href="exists.html">存在的页面</a>
            <a href="missing.html">不存在的页面</a>
        </body>
        </html>
        ''')
        self._write_file("exists.html", "<html></html>")

        scanner = SiteScanner(self.temp_dir)
        result = scanner.scan()

        index_result = next(
            (p for p in result.pages if p.file_path.endswith("index.html")),
            None
        )
        self.assertIsNotNone(index_result)

        dead_link_issues = [i for i in index_result.issues if i.rule_id == "dead-link"]
        self.assertEqual(len(dead_link_issues), 1)
        self.assertIn("missing.html", dead_link_issues[0].message)

    def test_valid_link_no_false_positive(self):
        self._write_file("index.html", '''
        <html lang="zh">
        <body>
            <a href="about.html">关于</a>
            <a href="http://example.com">外部</a>
        </body>
        </html>
        ''')
        self._write_file("about.html", "<html></html>")

        scanner = SiteScanner(self.temp_dir)
        result = scanner.scan()

        index_result = next(
            (p for p in result.pages if p.file_path.endswith("index.html")),
            None
        )
        self.assertIsNotNone(index_result)

        dead_link_issues = [i for i in index_result.issues if i.rule_id == "dead-link"]
        self.assertEqual(len(dead_link_issues), 0)

    def test_missing_anchor_detected(self):
        self._write_file("index.html", '''
        <html lang="zh">
        <body>
            <div id="exists"></div>
            <a href="#exists">存在的锚点</a>
            <a href="#missing">不存在的锚点</a>
        </body>
        </html>
        ''')

        scanner = SiteScanner(self.temp_dir)
        result = scanner.scan()

        index_result = next(
            (p for p in result.pages if p.file_path.endswith("index.html")),
            None
        )
        self.assertIsNotNone(index_result)

        dead_link_issues = [i for i in index_result.issues if i.rule_id == "dead-link"]
        self.assertEqual(len(dead_link_issues), 1)
        self.assertIn("锚点", dead_link_issues[0].message)


class TestSiteScanner(unittest.TestCase):
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

    def test_scan_finds_all_html(self):
        self._write_file("index.html", "<html></html>")
        self._write_file("about.html", "<html></html>")
        self._write_file("sub/page.html", "<html></html>")
        self._write_file("css/style.css", "body {}")
        self._write_file("images/logo.png", "")

        scanner = SiteScanner(self.temp_dir)
        result = scanner.scan()

        self.assertEqual(result.total_pages, 3)
        paths = [os.path.relpath(p.file_path, self.temp_dir).replace("\\", "/") for p in result.pages]
        self.assertIn("index.html", paths)
        self.assertIn("about.html", paths)
        self.assertIn("sub/page.html", paths)

    def test_scan_consistency(self):
        self._write_file("index.html", '''
        <html>
        <body>
            <img src="test.png">
            <h2>标题</h2>
        </body>
        </html>
        ''')

        scanner = SiteScanner(self.temp_dir)
        result1 = scanner.scan()
        result2 = scanner.scan()

        self.assertEqual(result1.total_pages, result2.total_pages)
        self.assertEqual(result1.total_errors, result2.total_errors)
        self.assertEqual(result1.total_warnings, result2.total_warnings)


if __name__ == "__main__":
    unittest.main()
