import unittest
from pathlib import Path
from typing import Dict, List

from code_agent.agent import Agent
from code_agent.providers import Provider


class RecordingProvider(Provider):
    def __init__(self) -> None:
        self.calls: List[List[Dict[str, str]]] = []

    def complete(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        return "模型回答"


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.agent = Agent(self.root)

    def test_review_loop_calls_tools_and_remembers(self):
        result = self.agent.run("请审查 sample/layer_stack.py")
        self.assertIn("代码审查", result.answer)
        self.assertIn("TOOL_CALL: inspect_python", "\n".join(result.trace))
        self.assertGreaterEqual(len(self.agent.memory.messages()), 2)

    def test_explain_loop(self):
        result = self.agent.run("解释 sample/layer_stack.py")
        self.assertIn("代码解释", result.answer)
        self.assertIn("Layer", result.answer)

    def test_missing_file_is_reported_after_retry(self):
        result = self.agent.run("请审查 missing_file.py")
        self.assertIn("未完全成功", result.answer)
        self.assertGreaterEqual(sum("TOOL_CALL" in item for item in result.trace), 2)

    def test_previous_memory_is_sent_to_provider(self):
        provider = RecordingProvider()
        agent = Agent(self.root, provider=provider)
        agent.memory.add("user", "上一轮问题")
        agent.memory.add("assistant", "上一轮回答")

        result = agent.run("解释 sample/layer_stack.py")

        self.assertEqual(result.answer, "模型回答")
        prompt = "\n".join(message["content"] for message in provider.calls[0])
        self.assertIn("上一轮问题", prompt)
        self.assertNotIn("user: 解释 sample/layer_stack.py", prompt)


if __name__ == "__main__":
    unittest.main()

