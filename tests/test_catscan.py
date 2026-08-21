import unittest
from unittest.mock import patch, MagicMock
import io
import json
import os
import shutil
import tempfile
import urllib.error
import zipfile
from pathlib import Path

from catscan.main import (
    load_config,
    save_config,
    sanitize_error_message,
    mask_api_key,
    send_ai_request,
    create_safe_backup,
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    OLD_DEFAULT_API_URL,
    OLD_DEFAULT_MODEL,
)


class TestCatScanConfigAndSanitization(unittest.TestCase):
    def test_sanitize_error_message_redacts_key(self):
        secret_key = "AIzaSySecretTestKey12345"
        raw_msg = f"Failed with key {secret_key} and Authorization: Bearer {secret_key}"
        sanitized = sanitize_error_message(raw_msg, secret_key)
        self.assertNotIn(secret_key, sanitized)
        self.assertIn("[REDACTED_API_KEY]", sanitized)

    def test_sanitize_error_message_redacts_query_token(self):
        raw_msg = "Error at https://api.example.com/v1?key=AIzaSySecret9999"
        sanitized = sanitize_error_message(raw_msg, "AIzaSySecret9999")
        self.assertNotIn("AIzaSySecret9999", sanitized)
        self.assertIn("key=[REDACTED_API_KEY]", sanitized)

    def test_mask_api_key(self):
        self.assertEqual(mask_api_key(""), "(not set)")
        self.assertEqual(mask_api_key("1234"), "****")
        self.assertEqual(mask_api_key("123456789012"), "1234****9012")

    def test_rl_prompt_color(self):
        from catscan.main import rl_prompt_color
        self.assertEqual(rl_prompt_color(""), "")
        self.assertEqual(rl_prompt_color("\033[1m"), "\001\033[1m\002")

    def test_load_config_gemini_env_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_path = Path(tmpdir) / "config.json"
            with patch("catscan.main.get_config_path", return_value=dummy_path):
                with patch.dict(os.environ, {"GEMINI_API_KEY": "test_gemini_key"}, clear=True):
                    config = load_config()
                    self.assertEqual(config["api_key"], "test_gemini_key")
                    self.assertEqual(config["url"], DEFAULT_API_URL)
                    self.assertEqual(config["model"], DEFAULT_MODEL)

    def test_load_config_catscan_env_key(self):
        with patch.dict(os.environ, {"CATSCAN_AI_KEY": "test_catscan_key"}, clear=True):
            config = load_config()
            self.assertEqual(config["api_key"], "test_catscan_key")

    def test_load_config_migrates_old_openai_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            old_data = {
                "api_key": "some_key",
                "url": OLD_DEFAULT_API_URL,
                "model": OLD_DEFAULT_MODEL
            }
            config_file.write_text(json.dumps(old_data), encoding="utf-8")
            with patch("catscan.main.get_config_path", return_value=config_file):
                with patch.dict(os.environ, {}, clear=True):
                    config = load_config()
                    self.assertEqual(config["url"], DEFAULT_API_URL)
                    self.assertEqual(config["model"], DEFAULT_MODEL)
                    self.assertEqual(config["api_key"], "some_key")


class TestCatScanBackupAndFileOps(unittest.TestCase):
    def test_create_safe_backup_uses_shutil(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "project.sb3"
            sb3_path.write_bytes(b"scratch data")
            backup1 = create_safe_backup(sb3_path)
            self.assertTrue(backup1.exists())
            self.assertEqual(backup1.read_bytes(), b"scratch data")
            self.assertEqual(backup1.name, "project.sb3.bak")

            backup2 = create_safe_backup(sb3_path)
            self.assertTrue(backup2.exists())
            self.assertEqual(backup2.name, "project.sb3.bak.1")

    def test_save_project_atomic_succeeds(self):
        from catscan.main import save_project_atomic, get_project_data
        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "project.sb3"
            initial_project = {
                "targets": [
                    {
                        "isStage": True,
                        "name": "Stage",
                        "variables": {},
                        "blocks": {},
                        "costumes": [],
                        "sounds": []
                    }
                ]
            }
            with zipfile.ZipFile(sb3_path, "w") as z:
                z.writestr("project.json", json.dumps(initial_project))

            updated_project = {
                "targets": [
                    {
                        "isStage": True,
                        "name": "Stage",
                        "variables": {"var1": ["my_var", 0]},
                        "blocks": {},
                        "costumes": [],
                        "sounds": []
                    }
                ]
            }
            save_project_atomic(sb3_path, updated_project)
            read_back = get_project_data(sb3_path)
            self.assertEqual(read_back["targets"][0]["variables"], {"var1": ["my_var", 0]})
            self.assertTrue((Path(tmpdir) / "project.sb3.bak").exists())


class TestGeminiApiRetries(unittest.TestCase):
    @patch("time.sleep", return_value=None)
    @patch("urllib.request.urlopen")
    def test_send_ai_request_503_retry_and_exhaustion(self, mock_urlopen, mock_sleep):
        err_stream = io.BytesIO(json.dumps({"error": {"message": "Service Unavailable"}}).encode("utf-8"))
        http_err = urllib.error.HTTPError("http://example.com", 503, "Service Unavailable", {}, err_stream)
        mock_urlopen.side_effect = http_err

        config = {
            "api_key": "secret_gemini_key_123",
            "url": DEFAULT_API_URL,
            "model": DEFAULT_MODEL,
        }
        messages = [{"role": "user", "content": "Hello"}]

        with self.assertRaises(RuntimeError) as cm:
            send_ai_request(config, messages)

        self.assertIn("HTTP Error 503: Service Unavailable", str(cm.exception))
        self.assertNotIn("secret_gemini_key_123", str(cm.exception))
        self.assertEqual(mock_urlopen.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("time.sleep", return_value=None)
    @patch("urllib.request.urlopen")
    def test_send_ai_request_503_retry_success(self, mock_urlopen, mock_sleep):
        err_stream = io.BytesIO(json.dumps({"error": {"message": "Temporary Unavailable"}}).encode("utf-8"))
        http_err = urllib.error.HTTPError("http://example.com", 503, "Service Unavailable", {}, err_stream)

        success_response = MagicMock()
        success_response.status = 200
        success_body = json.dumps({
            "choices": [{"message": {"content": "Success response"}}]
        }).encode("utf-8")
        success_response.read.return_value = success_body
        success_response.__enter__.return_value = success_response

        mock_urlopen.side_effect = [http_err, http_err, success_response]

        config = {
            "api_key": "valid_key",
            "url": DEFAULT_API_URL,
            "model": DEFAULT_MODEL,
        }
        result = send_ai_request(config, [{"role": "user", "content": "Hi"}])
        self.assertEqual(result, "Success response")
        self.assertEqual(mock_urlopen.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep", return_value=None)
    @patch("urllib.request.urlopen")
    def test_send_ai_request_429_rate_limit_retry(self, mock_urlopen, mock_sleep):
        err_stream = io.BytesIO(json.dumps({"error": {"message": "Rate limit exceeded"}}).encode("utf-8"))
        http_err = urllib.error.HTTPError("http://example.com", 429, "Too Many Requests", {}, err_stream)
        mock_urlopen.side_effect = http_err

        config = {
            "api_key": "key_429",
            "url": DEFAULT_API_URL,
            "model": DEFAULT_MODEL,
        }
        with self.assertRaises(RuntimeError) as cm:
            send_ai_request(config, [{"role": "user", "content": "Hi"}])

        self.assertIn("HTTP Error 429: Too Many Requests", str(cm.exception))
        self.assertEqual(mock_urlopen.call_count, 4)

    @patch("urllib.request.urlopen")
    def test_send_ai_request_401_no_retry_and_sanitized(self, mock_urlopen):
        err_stream = io.BytesIO(json.dumps({"error": {"message": "Invalid API key provided: secret_key_abc"}}).encode("utf-8"))
        http_err = urllib.error.HTTPError("http://example.com", 401, "Unauthorized", {}, err_stream)
        mock_urlopen.side_effect = http_err

        config = {
            "api_key": "secret_key_abc",
            "url": DEFAULT_API_URL,
            "model": DEFAULT_MODEL,
        }
        with self.assertRaises(RuntimeError) as cm:
            send_ai_request(config, [{"role": "user", "content": "Hi"}])

        self.assertIn("HTTP Error 401: Unauthorized", str(cm.exception))
        self.assertNotIn("secret_key_abc", str(cm.exception))
        self.assertIn("[REDACTED_API_KEY]", str(cm.exception))
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("urllib.request.urlopen")
    def test_send_ai_request_openrouter_response_parsing(self, mock_urlopen):
        openrouter_response = MagicMock()
        openrouter_response.status = 200
        openrouter_response.headers = {}
        openrouter_body = json.dumps({
            "id": "gen-1740000000-openrouter",
            "provider": "DeepInfra",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "OpenRouter response content"
                    }
                }
            ]
        }).encode("utf-8")
        openrouter_response.read.return_value = openrouter_body
        openrouter_response.__enter__.return_value = openrouter_response
        mock_urlopen.return_value = openrouter_response

        config = {
            "api_key": "sk-or-v1-secret12345",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": "deepseek/deepseek-r1",
        }
        result = send_ai_request(config, [{"role": "user", "content": "Hello"}])
        self.assertEqual(result, "OpenRouter response content")

    @patch("urllib.request.urlopen")
    def test_send_ai_request_gzip_content_encoding(self, mock_urlopen):
        import gzip
        gzip_response = MagicMock()
        gzip_response.status = 200
        gzip_response.headers = {"Content-Encoding": "gzip"}
        raw_json = json.dumps({
            "choices": [{"message": {"content": "Decompressed gzip content"}}]
        }).encode("utf-8")
        gzip_response.read.return_value = gzip.compress(raw_json)
        gzip_response.__enter__.return_value = gzip_response
        mock_urlopen.return_value = gzip_response

        config = {
            "api_key": "key_gzip",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": "gpt-4o",
        }
        result = send_ai_request(config, [{"role": "user", "content": "Hi"}])
        self.assertEqual(result, "Decompressed gzip content")

    @patch("urllib.request.urlopen")
    def test_send_ai_request_invalid_response_structure_error(self, mock_urlopen):
        invalid_response = MagicMock()
        invalid_response.status = 200
        invalid_response.headers = {}
        invalid_body = json.dumps({
            "unexpected": "data",
            "key_param": "sk-or-v1-secret12345"
        }).encode("utf-8")
        invalid_response.read.return_value = invalid_body
        invalid_response.__enter__.return_value = invalid_response
        mock_urlopen.return_value = invalid_response

        config = {
            "api_key": "sk-or-v1-secret12345",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": "gpt-4o",
        }
        with self.assertRaises(RuntimeError) as cm:
            send_ai_request(config, [{"role": "user", "content": "Hi"}])

        self.assertIn("HTTP 200", str(cm.exception))
        self.assertIn("missing expected 'content'", str(cm.exception))
        self.assertNotIn("sk-or-v1-secret12345", str(cm.exception))
        self.assertIn("[REDACTED_API_KEY]", str(cm.exception))

    def test_resolve_api_url(self):
        from catscan.main import resolve_api_url
        self.assertEqual(resolve_api_url("https://openrouter.ai"), "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(resolve_api_url("https://openrouter.ai/"), "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(resolve_api_url("https://openrouter.ai/api/v1"), "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(resolve_api_url("https://openrouter.ai/api/v1/chat/completions"), "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(resolve_api_url("https://generativelanguage.googleapis.com/v1beta/openai"), "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")

    @patch("urllib.request.urlopen")
    def test_send_ai_request_html_response_error(self, mock_urlopen):
        html_response = MagicMock()
        html_response.status = 200
        html_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        html_body = b"<!DOCTYPE html><html><body>OpenRouter Landing Page sk-or-v1-secret999</body></html>"
        html_response.read.return_value = html_body
        html_response.__enter__.return_value = html_response
        mock_urlopen.return_value = html_response

        config = {
            "api_key": "sk-or-v1-secret999",
            "url": "https://openrouter.ai",
            "model": "gpt-4o",
        }
        with self.assertRaises(RuntimeError) as cm:
            send_ai_request(config, [{"role": "user", "content": "Hi"}])

        self.assertIn("HTML webpage instead of JSON", str(cm.exception))
        self.assertIn("https://openrouter.ai/api/v1/chat/completions", str(cm.exception))
        self.assertNotIn("sk-or-v1-secret999", str(cm.exception))
        self.assertIn("[REDACTED_API_KEY]", str(cm.exception))


class TestScratchBlockSerialization(unittest.TestCase):
    def test_apple_sprite_blocks_serialization_and_visibility(self):
        from catscan.main import normalize_project_blocks, save_project_atomic, get_project_data

        apple_blocks = {
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": False
            },
            "b2": {
                "opcode": "motion_movesteps",
                "next": "b3",
                "parent": None,
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": True
            },
            "b3": {
                "opcode": "control_repeat",
                "next": "b7",
                "parent": None,
                "inputs": {
                    "TIMES": [1, [6, "10"]],
                    "SUBSTACK": [2, "b4"]
                },
                "fields": {},
                "shadow": False,
                "topLevel": True
            },
            "b4": {
                "opcode": "motion_turnright",
                "next": "b5",
                "parent": None,
                "inputs": {"DEGREES": [1, [10, "15"]]},
                "fields": {},
                "shadow": False,
                "topLevel": True
            },
            "b5": {
                "opcode": "looks_sayforsecs",
                "next": "b6",
                "parent": None,
                "inputs": {
                    "MESSAGE": [1, [10, "Hello!"]],
                    "SECS": [1, [4, "2"]]
                },
                "fields": {},
                "shadow": False,
                "topLevel": True
            },
            "b6": {
                "opcode": "looks_hide",
                "next": None,
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True
            },
            "b7": {
                "opcode": "control_wait",
                "next": "b8",
                "parent": None,
                "inputs": {"DURATION": [1, [5, "1"]]},
                "fields": {},
                "shadow": False,
                "topLevel": True
            },
            "b8": {
                "opcode": "looks_show",
                "next": None,
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True
            }
        }

        project_data = {
            "targets": [
                {
                    "isStage": False,
                    "name": "Apple",
                    "variables": {},
                    "blocks": apple_blocks,
                    "costumes": [],
                    "sounds": []
                }
            ]
        }

        normalized = normalize_project_blocks(project_data)
        target = normalized["targets"][0]
        blocks = target["blocks"]

        self.assertEqual(len(blocks), 8)

        b1 = blocks["b1"]
        self.assertTrue(b1["topLevel"])
        self.assertIsNone(b1["parent"])
        self.assertIsInstance(b1.get("x"), (int, float))
        self.assertIsInstance(b1.get("y"), (int, float))
        self.assertGreaterEqual(b1["x"], 0)
        self.assertGreaterEqual(b1["y"], 0)

        self.assertFalse(blocks["b2"]["topLevel"])
        self.assertEqual(blocks["b2"]["parent"], "b1")

        self.assertFalse(blocks["b3"]["topLevel"])
        self.assertEqual(blocks["b3"]["parent"], "b2")

        self.assertFalse(blocks["b4"]["topLevel"])
        self.assertEqual(blocks["b4"]["parent"], "b3")

        self.assertFalse(blocks["b5"]["topLevel"])
        self.assertEqual(blocks["b5"]["parent"], "b4")

        self.assertFalse(blocks["b6"]["topLevel"])
        self.assertEqual(blocks["b6"]["parent"], "b5")

        self.assertFalse(blocks["b7"]["topLevel"])
        self.assertEqual(blocks["b7"]["parent"], "b3")

        self.assertFalse(blocks["b8"]["topLevel"])
        self.assertEqual(blocks["b8"]["parent"], "b7")

        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "apple_test.sb3"
            with zipfile.ZipFile(sb3_path, "w") as z:
                z.writestr("project.json", json.dumps(project_data))

            save_project_atomic(sb3_path, project_data)
            saved = get_project_data(sb3_path)
            saved_apple = saved["targets"][0]["blocks"]

            self.assertEqual(len(saved_apple), 8)
            self.assertTrue(saved_apple["b1"]["topLevel"])
            self.assertIsInstance(saved_apple["b1"]["x"], (int, float))
            self.assertIsInstance(saved_apple["b1"]["y"], (int, float))
            self.assertEqual(saved_apple["b2"]["parent"], "b1")
            self.assertFalse(saved_apple["b2"]["topLevel"])


if __name__ == "__main__":
    unittest.main()
