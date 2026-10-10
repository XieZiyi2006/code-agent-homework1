import unittest
from pathlib import Path

from code_agent.tools import build_default_registry


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.registry = build_default_registry(self.root)

    def test_inspect_sample(self):
        result = self.registry.run("inspect_python", {"path": "sample/layer_stack.py"})
        self.assertTrue(result.ok)
        self.assertIn("Layer", result.data["classes"])
        self.assertIsNone(result.data["syntax_error"])

    def test_read_sample(self):
        result = self.registry.run("read_file", {"path": "sample/layer_stack.py"})
        self.assertTrue(result.ok)
        self.assertIn("class Layer", result.data["content"])

    def test_read_empty_utf8_file(self):
        empty_file = self.root / "empty_test_file.txt"
        try:
            empty_file.write_text("", encoding="utf-8")
            result = self.registry.run("read_file", {"path": empty_file.name})
            self.assertTrue(result.ok)
            self.assertEqual(result.data["content"], "")
        finally:
            empty_file.unlink(missing_ok=True)

    def test_path_escape_is_rejected(self):
        result = self.registry.run("read_file", {"path": "..\\outside.txt"})
        self.assertFalse(result.ok)

    def test_search(self):
        result = self.registry.run("search_files", {"query": "error_notify"})
        self.assertTrue(result.ok)
        self.assertGreater(result.data["count"], 0)

    def test_run_tests_rejects_python_file(self):
        result = self.registry.run("run_tests", {"path": "sample/layer_stack.py"})
        self.assertFalse(result.ok)
        self.assertIn("测试目录", result.data["error"])


if __name__ == "__main__":
    unittest.main()

