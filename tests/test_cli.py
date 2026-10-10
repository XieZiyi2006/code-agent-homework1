import unittest
from unittest.mock import patch

from code_agent.cli import _make_agent, build_parser
from code_agent.providers import OpenAICompatibleProvider


class CliTests(unittest.TestCase):
    def test_api_key_enables_remote_provider_by_default(self):
        with patch.dict("os.environ", {"CODE_AGENT_API_KEY": "test-key"}, clear=True):
            args = build_parser().parse_args([])
            agent = _make_agent(args)

        self.assertIsInstance(agent.provider, OpenAICompatibleProvider)

    def test_offline_disables_remote_provider(self):
        with patch.dict("os.environ", {"CODE_AGENT_API_KEY": "test-key"}, clear=True):
            args = build_parser().parse_args(["--offline"])
            agent = _make_agent(args)

        self.assertIsNone(agent.provider)

    def test_model_defaults_to_environment_value(self):
        with patch.dict("os.environ", {"CODE_AGENT_MODEL": "deepseek-flash"}, clear=True):
            args = build_parser().parse_args([])

        self.assertEqual(args.model, "deepseek-flash")

    def test_deepseek_url_selects_deepseek_model(self):
        with patch.dict(
            "os.environ",
            {"CODE_AGENT_BASE_URL": "https://api.deepseek.com"},
            clear=True,
        ):
            args = build_parser().parse_args([])

        self.assertEqual(args.model, "deepseek-chat")


if __name__ == "__main__":
    unittest.main()
