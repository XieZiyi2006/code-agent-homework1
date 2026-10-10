import io
import unittest
from contextlib import redirect_stdout

from sample.layer_stack import build_stack


class LayerStackTests(unittest.TestCase):
    def test_send_encapsulates_at_every_layer(self):
        app, _, _ = build_stack()
        output = io.StringIO()

        with redirect_stdout(output):
            app.send("Hello Network")

        text = output.getvalue()
        self.assertIn("[APP_PDU]Hello Network", text)
        self.assertIn("[TCP_HDR][APP_PDU]Hello Network", text)
        self.assertIn("[IP_HDR][TCP_HDR][APP_PDU]Hello Network", text)


if __name__ == "__main__":
    unittest.main()
