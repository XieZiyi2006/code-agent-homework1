import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from code_agent.providers import OpenAICompatibleProvider, ProviderError


class ProviderTests(unittest.TestCase):
    def test_empty_content_is_rejected(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"choices":[{"message":{"content":""}}]}'
        )
        provider = OpenAICompatibleProvider(api_key="test-key", retries=0)

        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(ProviderError, "empty content"):
                provider.complete([{"role": "user", "content": "hello"}])

    def test_request_limits_generated_tokens(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"choices":[{"message":{"content":"ok"}}]}'
        )
        provider = OpenAICompatibleProvider(api_key="test-key", max_tokens=123)

        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            result = provider.complete([{"role": "user", "content": "hello"}])

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(result, "ok")
        self.assertEqual(payload["max_tokens"], 123)

    def test_http_error_includes_response_details(self):
        response = io.BytesIO(b'{"error":{"message":"invalid model"}}')
        error = urllib.error.HTTPError(
            "https://api.example.com/chat/completions",
            400,
            "Bad Request",
            None,
            response,
        )
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://api.example.com",
            retries=2,
        )

        with patch("urllib.request.urlopen", side_effect=error) as urlopen:
            with self.assertRaisesRegex(ProviderError, "invalid model"):
                provider.complete([{"role": "user", "content": "hello"}])

        self.assertEqual(urlopen.call_count, 1)


if __name__ == "__main__":
    unittest.main()
