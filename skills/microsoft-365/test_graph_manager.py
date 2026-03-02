import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parent / "graph_manager.py"
spec = importlib.util.spec_from_file_location("graph_manager", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
GraphManager = mod.GraphManager


class TestGraphManager(unittest.TestCase):
    def test_mock_mode_without_config(self):
        gm = GraphManager()
        self.assertTrue(gm.mock_mode)

    def test_channel_parser_short_form(self):
        team, channel = GraphManager._parse_channel("team123/channel456")
        self.assertEqual(team, "team123")
        self.assertEqual(channel, "channel456")

    def test_channel_parser_graph_form(self):
        team, channel = GraphManager._parse_channel("teams/team123/channels/channel456")
        self.assertEqual(team, "team123")
        self.assertEqual(channel, "channel456")

    def test_send_teams_message_mock(self):
        gm = GraphManager()
        res = gm.send_teams_message("team123/channel456", "hello")
        self.assertTrue(res["mocked"])
        self.assertEqual(res["method"], "POST")

    def test_inbox_uses_user_root_for_app_mode(self):
        gm = GraphManager()
        gm.mock_mode = False
        gm.config.auth_mode = "application"
        gm.config.mailbox_user = "bot@example.com"

        captured = {}

        def fake_graph_request(method, path, payload=None, params=None, retries=3):
            captured["method"] = method
            captured["path"] = path
            return {"value": []}

        gm._graph_request = fake_graph_request
        gm.read_outlook_inbox(limit=5)
        self.assertEqual(captured["method"], "GET")
        self.assertTrue(captured["path"].startswith("/users/bot@example.com/messages"))

    def test_excel_range_path(self):
        gm = GraphManager()
        gm.mock_mode = False
        gm.config.auth_mode = "delegated"

        captured = {}

        def fake_graph_request(method, path, payload=None, params=None, retries=3):
            captured["path"] = path
            return {"values": [["ok"]]}

        gm._graph_request = fake_graph_request
        gm.read_excel_range("file123", "A1:B2", worksheet="Sheet1")
        self.assertIn("/me/drive/items/file123/workbook/worksheets('Sheet1')/range", captured["path"])


if __name__ == "__main__":
    unittest.main()
