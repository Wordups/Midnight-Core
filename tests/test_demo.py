"""The portfolio demo must stay runnable (mock mode, no creds/network)."""
import importlib.util
import os
import pathlib
import sys
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")
os.environ.setdefault("ENVIRONMENT", "dev")

_PATH = pathlib.Path(__file__).parent.parent / "demo" / "rest_api_automation_demo.py"
_spec = importlib.util.spec_from_file_location("rest_demo", _PATH)
demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(demo)


class DemoTests(unittest.TestCase):
    def test_summary_and_labels(self):
        self.assertTrue(demo.build_summary(demo.GAP).startswith("[SOC2-CC6.1]"))
        labels = demo.build_labels(demo.GAP)
        self.assertIn("midnight", labels)
        self.assertIn("severity-high", labels)

    def test_mock_flow_runs_end_to_end(self):
        old = sys.argv
        sys.argv = ["demo"]  # no --live → in-process mock, no network
        try:
            self.assertEqual(demo.main(), 0)
        finally:
            sys.argv = old


if __name__ == "__main__":
    unittest.main()
