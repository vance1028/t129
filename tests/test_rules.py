import unittest
from a11y_checker.dom_engine import DOMChecker
from a11y_checker.rules.base import RuleRegistry, create_default_registry
from a11y_checker.models import Severity


class TestImageAltRule(unittest.TestCase):
    def setUp(self):
        self.checker = DOMChecker(enabled_rules=["image-alt"])

    def test_missing_alt(self):
        html = '<html><body><img src="test.png"></body></html>'
        result = self.checker.check_html(html, "test.html")
        alt_issues = [i for i in result.issues if i.rule_id == "image-alt"]
        self.assertEqual(len(alt_issues), 1)
        self.assertEqual(alt_issues[0].severity, Severity.ERROR)

    def test_empty_alt(self):
        html = '<html><body><img src="test.png" alt=""></body></html>'
        result = self.checker.check_html(html, "test.html")
        alt_issues = [i for i in result.issues if i.rule_id == "image-alt"]
        self.assertEqual(len(alt_issues), 1)

    def test_valid_alt(self):
        html = '<html><body><img src="test.png" alt="测试图片"></body></html>'
        result = self.checker.check_html(html, "test.html")
        alt_issues = [i for i in result.issues if i.rule_id == "image-alt"]
        self.assertEqual(len(alt_issues), 0)

    def test_decorative_empty_alt(self):
        html = '<html><body><img src="test.png" alt="" role="presentation"></body></html>'
        result = self.checker.check_html(html, "test.html")
        alt_issues = [i for i in result.issues if i.rule_id == "image-alt"]
        self.assertEqual(len(alt_issues), 0)

    def test_multiple_images(self):
        html = '''
        <html><body>
            <img src="a.png" alt="图片A">
            <img src="b.png">
            <img src="c.png" alt="">
        </body></html>
        '''
        result = self.checker.check_html(html, "test.html")
        alt_issues = [i for i in result.issues if i.rule_id == "image-alt"]
        self.assertEqual(len(alt_issues), 2)


class TestFormLabelRule(unittest.TestCase):
    def setUp(self):
        self.checker = DOMChecker(enabled_rules=["form-label"])

    def test_input_without_label(self):
        html = '<html><body><input type="text" name="test"></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "form-label"]
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, Severity.ERROR)

    def test_input_with_label_for(self):
        html = '''
        <html><body>
            <label for="name">姓名</label>
            <input type="text" id="name" name="name">
        </body></html>
        '''
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "form-label"]
        self.assertEqual(len(issues), 0)

    def test_input_wrapped_in_label(self):
        html = '''
        <html><body>
            <label>姓名<input type="text" name="name"></label>
        </body></html>
        '''
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "form-label"]
        self.assertEqual(len(issues), 0)

    def test_input_with_aria_label(self):
        html = '<html><body><input type="text" aria-label="搜索"></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "form-label"]
        self.assertEqual(len(issues), 0)

    def test_hidden_input_ignored(self):
        html = '<html><body><input type="hidden" name="token"></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "form-label"]
        self.assertEqual(len(issues), 0)

    def test_submit_button_ignored(self):
        html = '<html><body><input type="submit" value="提交"></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "form-label"]
        self.assertEqual(len(issues), 0)

    def test_select_without_label(self):
        html = '<html><body><select name="city"><option>北京</option></select></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "form-label"]
        self.assertEqual(len(issues), 1)

    def test_textarea_without_label(self):
        html = '<html><body><textarea name="msg"></textarea></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "form-label"]
        self.assertEqual(len(issues), 1)


class TestHeadingOrderRule(unittest.TestCase):
    def setUp(self):
        self.checker = DOMChecker(enabled_rules=["heading-order"])

    def test_no_headings(self):
        html = '<html><body><p>没有标题</p></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "heading-order"]
        self.assertGreaterEqual(len(issues), 1)

    def test_starts_with_h1(self):
        html = '<html><body><h1>标题</h1><h2>副标题</h2></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "heading-order"]
        self.assertEqual(len(issues), 0)

    def test_starts_with_h2(self):
        html = '<html><body><h2>标题</h2></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "heading-order"]
        self.assertGreaterEqual(len(issues), 1)

    def test_skip_level_h1_to_h3(self):
        html = '<html><body><h1>标题1</h1><h3>标题3</h3></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "heading-order"]
        jump_issues = [i for i in issues if "跳到" in i.message or "跳级" in i.message]
        self.assertGreaterEqual(len(jump_issues), 1)
        self.assertEqual(issues[0].severity, Severity.WARNING)

    def test_correct_order(self):
        html = '''
        <html><body>
            <h1>一级</h1>
            <h2>二级</h2>
            <h2>二级</h2>
            <h3>三级</h3>
            <h2>二级</h2>
        </body></html>
        '''
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "heading-order"]
        self.assertEqual(len(issues), 0)


class TestHtmlLangRule(unittest.TestCase):
    def setUp(self):
        self.checker = DOMChecker(enabled_rules=["html-lang"])

    def test_missing_lang(self):
        html = '<html><body>内容</body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "html-lang"]
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, Severity.ERROR)

    def test_valid_lang(self):
        html = '<html lang="zh-CN"><body>内容</body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "html-lang"]
        self.assertEqual(len(issues), 0)

    def test_lang_en(self):
        html = '<html lang="en"><body>Content</body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "html-lang"]
        self.assertEqual(len(issues), 0)

    def test_empty_lang(self):
        html = '<html lang=""><body>内容</body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "html-lang"]
        self.assertEqual(len(issues), 1)


class TestLinkTextRule(unittest.TestCase):
    def setUp(self):
        self.checker = DOMChecker(enabled_rules=["link-text"])

    def test_vague_click_here(self):
        html = '<html><body><a href="page.html">点击这里</a></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "link-text"]
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, Severity.WARNING)

    def test_vague_more(self):
        html = '<html><body><a href="page.html">更多</a></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "link-text"]
        self.assertEqual(len(issues), 1)

    def test_good_link_text(self):
        html = '<html><body><a href="about.html">关于我们</a></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "link-text"]
        self.assertEqual(len(issues), 0)

    def test_anchor_link_ignored(self):
        html = '<html><body><a href="#section">点击这里</a></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "link-text"]
        self.assertEqual(len(issues), 0)

    def test_empty_link_with_alt_image(self):
        html = '<html><body><a href="page.html"><img src="icon.png" alt="下载"></a></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "link-text"]
        self.assertEqual(len(issues), 0)

    def test_empty_link_no_text(self):
        html = '<html><body><a href="page.html"><img src="icon.png"></a></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "link-text"]
        self.assertEqual(len(issues), 1)


class TestColorContrastRule(unittest.TestCase):
    def setUp(self):
        self.checker = DOMChecker(enabled_rules=["color-contrast"])

    def test_low_contrast_inline(self):
        html = '''
        <html lang="zh">
        <body>
            <p style="color: #ccc; background: #fff;">低对比度文字</p>
        </body>
        </html>
        '''
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "color-contrast"]
        self.assertGreaterEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, Severity.ERROR)

    def test_good_contrast_inline(self):
        html = '''
        <html lang="zh">
        <body>
            <p style="color: #000; background: #fff;">正常对比度文字</p>
        </body>
        </html>
        '''
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "color-contrast"]
        self.assertEqual(len(issues), 0)

    def test_contrast_in_style_tag(self):
        html = '''
        <html lang="zh">
        <head>
            <style>
                .bad { color: #aaa; background: #fff; }
            </style>
        </head>
        <body>
            <p class="bad">低对比度文字</p>
        </body>
        </html>
        '''
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "color-contrast"]
        self.assertGreaterEqual(len(issues), 1)

    def test_large_text_lower_threshold(self):
        html = '''
        <html lang="zh">
        <body>
            <h1 style="color: #777; background: #fff;">大标题</h1>
        </body>
        </html>
        '''
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "color-contrast"]
        for issue in issues:
            self.assertIn("contrast_ratio", issue.context)
            self.assertIn("threshold", issue.context)


class TestAriaRule(unittest.TestCase):
    def setUp(self):
        self.checker = DOMChecker(enabled_rules=["aria"])

    def test_invalid_role(self):
        html = '<html><body><div role="invalidrole">内容</div></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "aria"]
        self.assertGreaterEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, Severity.WARNING)

    def test_redundant_role_button(self):
        html = '<html><body><button role="button">按钮</button></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "aria" and "冗余" in i.message]
        self.assertGreaterEqual(len(issues), 1)

    def test_redundant_role_link(self):
        html = '<html><body><a href="#" role="link">链接</a></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "aria" and "冗余" in i.message]
        self.assertGreaterEqual(len(issues), 1)

    def test_valid_role(self):
        html = '<html><body><div role="navigation">导航</div></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "aria" and "role" in i.message.lower()]
        self.assertEqual(len(issues), 0)

    def test_unknown_aria_attribute(self):
        html = '<html><body><div aria-unknown="value">内容</div></body></html>'
        result = self.checker.check_html(html, "test.html")
        issues = [i for i in result.issues if i.rule_id == "aria" and "未知" in i.message]
        self.assertGreaterEqual(len(issues), 1)


class TestRuleConsistency(unittest.TestCase):
    def test_same_input_same_output(self):
        html = '''
        <html>
        <body>
            <img src="test.png">
            <h2>标题</h2>
            <a href="page.html">点击这里</a>
            <input type="text" name="test">
        </body>
        </html>
        '''
        checker = DOMChecker()
        result1 = checker.check_html(html, "test.html")
        result2 = checker.check_html(html, "test.html")
        result3 = checker.check_html(html, "test.html")

        issue_ids_1 = sorted([(i.rule_id, i.message) for i in result1.issues])
        issue_ids_2 = sorted([(i.rule_id, i.message) for i in result2.issues])
        issue_ids_3 = sorted([(i.rule_id, i.message) for i in result3.issues])

        self.assertEqual(issue_ids_1, issue_ids_2)
        self.assertEqual(issue_ids_2, issue_ids_3)


class TestRuleRegistry(unittest.TestCase):
    def test_default_registry_has_all_rules(self):
        registry = create_default_registry()
        rules = registry.list_rules()
        expected = {
            "image-alt", "form-label", "heading-order", "html-lang",
            "link-text", "color-contrast", "aria", "dead-link",
        }
        self.assertEqual(set(rules), expected)

    def test_disable_rule(self):
        registry = create_default_registry()
        instances = registry.create_instances(disabled_rules=["image-alt"])
        alt_rule = next((r for r in instances if r.rule_id == "image-alt"), None)
        self.assertIsNotNone(alt_rule)
        self.assertFalse(alt_rule.enabled)

    def test_enable_only_specific_rules(self):
        registry = create_default_registry()
        instances = registry.create_instances(enabled_rules=["image-alt", "html-lang"])
        enabled_ids = [r.rule_id for r in instances if r.enabled]
        self.assertEqual(set(enabled_ids), {"image-alt", "html-lang"})

    def test_severity_override(self):
        registry = create_default_registry()
        instances = registry.create_instances(
            severity_overrides={"image-alt": Severity.WARNING}
        )
        alt_rule = next((r for r in instances if r.rule_id == "image-alt"), None)
        self.assertIsNotNone(alt_rule)
        self.assertEqual(alt_rule.severity, Severity.WARNING)


if __name__ == "__main__":
    unittest.main()
