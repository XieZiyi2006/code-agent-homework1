import unittest
from pathlib import Path

from code_agent.planner import Planner


class PlannerPathTests(unittest.TestCase):
    def test_natural_language_is_not_part_of_path(self):
        planner = Planner()
        for request, expected in (
            ("请审查 sample/layer_stack.py", "sample/layer_stack.py"),
            ("解释 sample/layer_stack.py", "sample/layer_stack.py"),
            ("请审查sample/layer_stack.py", "sample/layer_stack.py"),
            (r"解释 sample\layer_stack.py", r"sample\layer_stack.py"),
            ("请审查 missing_file.py", "missing_file.py"),
            ('解释 "sample/my layer.py"', "sample/my layer.py"),
            ('解释 “示例/协议栈.py”', "示例/协议栈.py"),
        ):
            with self.subTest(request=request):
                plan = planner.plan(request, Path.cwd())
                self.assertEqual(plan.calls[0].arguments["path"], expected)

    def test_test_request_defaults_to_tests_directory(self):
        root = Path(__file__).resolve().parents[1]
        plan = Planner().plan("请测试项目", root)
        self.assertEqual(plan.intent, "test")
        self.assertEqual(plan.calls[0].arguments["path"], "tests")


if __name__ == "__main__":
    unittest.main()
