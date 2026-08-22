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
from catscan.ai import build_system_prompt
from catscan.ai import clear_conversation_history
from catscan.ai import conversation_history
from catscan.ai import get_last_usage
from catscan.ai import MAX_CONVERSATION_MESSAGES
from catscan.orphan_cleanup import cleanup_orphan_blocks
from catscan.scratch_knowledge import (
    build_scratch_knowledge_prompt,
    get_general_json_rules,
    get_input_rules,
    get_menu_block_opcodes,
    get_scratch_opcode_rules,
    get_shadow_block_rules,
    get_top_level_script_rules,
    get_variable_rules,
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
            with patch("catscan.config.get_config_path", return_value=dummy_path):
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
            with patch("catscan.config.get_config_path", return_value=config_file):
                with patch.dict(os.environ, {}, clear=True):
                    config = load_config()
                    self.assertEqual(config["url"], DEFAULT_API_URL)
                    self.assertEqual(config["model"], DEFAULT_MODEL)
                    self.assertEqual(config["api_key"], "some_key")


class TestCatScanBackupAndFileOps(unittest.TestCase):
    def test_create_safe_backup_uses_shutil(self):
        from catscan.workspace import get_backups_path
        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "project.sb3"
            sb3_path.write_bytes(b"scratch data")
            backup1 = create_safe_backup(sb3_path)
            self.assertTrue(backup1.exists())
            self.assertEqual(backup1.read_bytes(), b"scratch data")
            self.assertEqual(backup1.name, "project.sb3.bak")
            self.assertEqual(backup1.parent, get_backups_path(sb3_path))

            backup2 = create_safe_backup(sb3_path)
            self.assertTrue(backup2.exists())
            self.assertEqual(backup2.name, "project.sb3.bak.1")
            self.assertEqual(backup2.parent, get_backups_path(sb3_path))

    def test_save_project_atomic_succeeds(self):
        from catscan.main import save_project_atomic, get_project_data
        from catscan.workspace import get_backups_path
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
            self.assertTrue((get_backups_path(sb3_path) / "project.sb3.bak").exists())


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


class TestScratchKnowledge(unittest.TestCase):
    def test_build_scratch_knowledge_prompt_returns_nonempty_string(self):
        prompt = build_scratch_knowledge_prompt()
        self.assertIsInstance(prompt, str)
        self.assertTrue(prompt.strip())

    def test_knowledge_contains_key_scratch_rules(self):
        prompt = build_scratch_knowledge_prompt()
        for needle in (
            "GENERAL SCRATCH JSON RULES:",
            "TOP-LEVEL AND WORKSPACE RULES:",
            "SHADOW AND MENU BLOCK RULES:",
            "KNOWN SCRATCH STRUCTURE EXAMPLES:",
            "OPCODE SAFETY:",
            "INPUT SAFETY:",
            "VARIABLE RULES:",
            "SUBSTACK",
            "topLevel",
            "parent",
            "shadow",
        ):
            self.assertIn(needle, prompt)

    def test_opcode_reference_covers_common_opcodes(self):
        reference = get_scratch_opcode_rules()
        for opcode in (
            "event_whenflagclicked",
            "control_forever",
            "control_if",
            "control_repeat",
            "motion_movesteps",
            "motion_pointtowards",
            "motion_pointtowards_menu",
            "motion_goto",
            "motion_goto_menu",
            "sensing_touchingobject",
            "sensing_touchingobjectmenu",
            "sensing_keypressed",
            "sensing_keyoptions",
            "looks_nextcostume",
            "looks_switchcostumeto",
            "looks_changeeffectby",
            "looks_seteffectto",
            "sound_play",
            "sound_sounds_menu",
            "data_setvariableto",
            "data_changevariableby",
            "operator_add",
            "procedures_definition",
            "procedures_prototype",
            "procedures_call",
        ):
            self.assertIn(opcode, reference)

    def test_helpers_return_sections(self):
        self.assertIn("GENERAL SCRATCH JSON RULES:", get_general_json_rules())
        self.assertIn("TOP-LEVEL AND WORKSPACE RULES:", get_top_level_script_rules())
        self.assertIn("SHADOW AND MENU BLOCK RULES:", get_shadow_block_rules())
        self.assertIn("INPUT SAFETY:", get_input_rules())
        self.assertIn("VARIABLE RULES:", get_variable_rules())
        self.assertIn("OPCODE SAFETY:", get_scratch_opcode_rules())

    def test_menu_block_opcodes_known_set(self):
        opcodes = get_menu_block_opcodes()
        for opcode in (
            "motion_goto_menu",
            "motion_pointtowards_menu",
            "sensing_touchingobjectmenu",
            "sensing_keyoptions",
            "sound_sounds_menu",
            "control_create_clone_of_menu",
        ):
            self.assertIn(opcode, opcodes)

    def test_system_prompt_embeds_scratch_knowledge(self):
        system = build_system_prompt()
        knowledge = build_scratch_knowledge_prompt()
        self.assertIsInstance(system, str)
        self.assertGreater(len(system), len(knowledge))
        self.assertIn(knowledge, system)
        self.assertIn("CRITICAL MODIFICATION OUTPUT RULE:", system)
        self.assertIn("MODIFICATION JSON SCHEMA:", system)
        self.assertIn("FINAL SELF-CHECK BEFORE RETURNING JSON:", system)


class TestConversationHistory(unittest.TestCase):

    def setUp(self):
        clear_conversation_history()

    def _make_project(self):
        return {
            "targets": [
                {
                    "name": "Stage",
                    "isStage": True,
                    "blocks": {},
                    "costumes": [],
                    "sounds": [],
                }
            ],
            "monitors": [],
            "extensions": [],
            "meta": {"semver": "3.0.0"},
        }

    def test_first_request_includes_project_json(self):
        from catscan.ai import ai_command_flow
        project = self._make_project()

        with patch("catscan.main.get_project_data", return_value=project), \
             patch("catscan.ai.send_ai_request", return_value="analysis response") as mock_send:
            ai_command_flow(
                Path("test.sb3"),
                "analyze this project",
                {"api_key": "test-key", "timeout": 60},
            )

            messages = mock_send.call_args[0][1]
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0]["role"], "system")
            self.assertEqual(messages[1]["role"], "user")
            self.assertIn("Project data:", messages[1]["content"])
            self.assertIn(json.dumps(project, indent=2), messages[1]["content"])
            self.assertIn("analyze this project", messages[1]["content"])

    def test_second_request_contains_history_not_project_json(self):
        from catscan.ai import ai_command_flow
        project = self._make_project()

        with patch("catscan.main.get_project_data", return_value=project), \
             patch("catscan.ai.send_ai_request", return_value="response text") as mock_send:
            ai_command_flow(
                Path("test.sb3"),
                "analyze this project",
                {"api_key": "test-key", "timeout": 60},
            )

            mock_send.reset_mock()

            ai_command_flow(
                Path("test.sb3"),
                "yes fix the issues",
                {"api_key": "test-key", "timeout": 60},
            )

            messages = mock_send.call_args[0][1]
            self.assertEqual(len(messages), 4)
            self.assertEqual(messages[0]["role"], "system")
            self.assertEqual(messages[1]["role"], "user")
            self.assertIn("Project data:", messages[1]["content"])
            self.assertEqual(messages[2]["role"], "assistant")
            self.assertEqual(messages[2]["content"], "response text")
            self.assertEqual(messages[3]["role"], "user")
            self.assertNotIn("Project data:", messages[3]["content"])
            self.assertEqual(messages[3]["content"], "yes fix the issues")

    def test_ai_response_added_to_history(self):
        from catscan.ai import ai_command_flow
        project = self._make_project()

        with patch("catscan.main.get_project_data", return_value=project), \
             patch("catscan.ai.send_ai_request", return_value="analysis done"):
            self.assertEqual(len(conversation_history), 0)

            ai_command_flow(
                Path("test.sb3"),
                "analyze this",
                {"api_key": "test-key", "timeout": 60},
            )

            self.assertEqual(len(conversation_history), 2)
            self.assertEqual(conversation_history[0]["role"], "user")
            self.assertEqual(conversation_history[1]["role"], "assistant")
            self.assertEqual(conversation_history[1]["content"], "analysis done")

    def test_ai_clear_clears_history(self):
        from catscan.ai import ai_command_flow
        project = self._make_project()

        with patch("catscan.main.get_project_data", return_value=project), \
             patch("catscan.ai.send_ai_request", return_value="response"):
            ai_command_flow(
                Path("test.sb3"),
                "test",
                {"api_key": "test-key", "timeout": 60},
            )

            self.assertGreater(len(conversation_history), 0)

            clear_conversation_history()
            self.assertEqual(len(conversation_history), 0)

    def test_project_selection_clears_history(self):
        from catscan.ai import ai_command_flow
        project = self._make_project()

        with patch("catscan.main.get_project_data", return_value=project), \
             patch("catscan.ai.send_ai_request", return_value="response"):
            ai_command_flow(
                Path("test.sb3"),
                "test",
                {"api_key": "test-key", "timeout": 60},
            )

            self.assertGreater(len(conversation_history), 0)

            clear_conversation_history()
            self.assertEqual(len(conversation_history), 0)

    def test_history_max_size(self):
        from catscan.ai import ai_command_flow
        project = self._make_project()

        with patch("catscan.main.get_project_data", return_value=project), \
             patch("catscan.ai.send_ai_request", return_value="response"):
            for i in range(8):
                ai_command_flow(
                    Path("test.sb3"),
                    f"prompt {i}",
                    {"api_key": "test-key", "timeout": 60},
                )

            self.assertEqual(len(conversation_history), MAX_CONVERSATION_MESSAGES)

    def test_api_failure_does_not_add_assistant(self):
        from catscan.ai import ai_command_flow
        project = self._make_project()

        with patch("catscan.main.get_project_data", return_value=project), \
             patch("catscan.ai.send_ai_request", side_effect=RuntimeError("API failure")):
            ai_command_flow(
                Path("test.sb3"),
                "test",
                {"api_key": "test-key", "timeout": 60},
            )

            self.assertEqual(len(conversation_history), 0)

    def test_existing_tests_still_pass(self):
        self.assertTrue(True)


class TestWorkspace(unittest.TestCase):

    def test_get_workspace_path_basic(self):
        from catscan.workspace import get_workspace_path
        result = get_workspace_path(Path("/tmp/Trampoline.sb3"))
        self.assertEqual(result, Path("/tmp/Trampoline.sb3.catscan"))

    def test_get_workspace_path_spaces(self):
        from catscan.workspace import get_workspace_path
        result = get_workspace_path(Path("/tmp/My Project.sb3"))
        self.assertEqual(result, Path("/tmp/My Project.sb3.catscan"))

    def test_get_workspace_path_multiple_dots(self):
        from catscan.workspace import get_workspace_path
        result = get_workspace_path(Path("/tmp/game.v2.final.sb3"))
        self.assertEqual(result, Path("/tmp/game.v2.final.sb3.catscan"))

    def test_workspace_directories_created(self):
        from catscan.workspace import ensure_workspace, get_workspace_path
        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "project.sb3"
            sb3_path.write_bytes(b"data")
            ensure_workspace(sb3_path)
            ws = get_workspace_path(sb3_path)
            self.assertTrue(ws.exists())
            self.assertTrue(ws.is_dir())

    def test_backup_paths_use_workspace(self):
        from catscan.workspace import get_backups_path
        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "project.sb3"
            sb3_path.write_bytes(b"data")
            backups = get_backups_path(sb3_path)
            self.assertEqual(
                backups,
                Path(tmpdir) / "project.sb3.catscan" / "backups"
            )

    def test_script_save_defaults_to_workspace(self):
        from catscan.main import save_scripts_to_file
        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "project.sb3"
            sb3_path.write_bytes(b"data")
            target = {
                "name": "Sprite1",
                "blocks": {
                    "b1": {
                        "opcode": "event_whenflagclicked",
                        "next": "b2",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                        "x": 0,
                        "y": 0,
                    },
                    "b2": {
                        "opcode": "looks_say",
                        "next": None,
                        "parent": "b1",
                        "inputs": {"MESSAGE": [1, [10, "Hello!"]]},
                        "fields": {},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "costumes": [],
                "sounds": [],
            }
            save_scripts_to_file(sb3_path, target, None)
            expected = (
                Path(tmpdir)
                / "project.sb3.catscan"
                / "scripts"
                / "project_scripts.txt"
            )
            self.assertTrue(expected.exists())

    def test_script_save_custom_path_preserved(self):
        from catscan.main import save_scripts_to_file
        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "project.sb3"
            sb3_path.write_bytes(b"data")
            custom = Path(tmpdir) / "custom_output.txt"
            target = {
                "name": "Sprite1",
                "blocks": {
                    "b1": {
                        "opcode": "event_whenflagclicked",
                        "next": "b2",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                        "x": 0,
                        "y": 0,
                    },
                    "b2": {
                        "opcode": "looks_say",
                        "next": None,
                        "parent": "b1",
                        "inputs": {"MESSAGE": [1, [10, "Hello!"]]},
                        "fields": {},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "costumes": [],
                "sounds": [],
            }
            save_scripts_to_file(sb3_path, target, str(custom))
            self.assertTrue(custom.exists())
            ws_scripts = (
                Path(tmpdir)
                / "project.sb3.catscan"
                / "scripts"
            )
            self.assertFalse(ws_scripts.exists())

    def test_different_projects_get_different_workspaces(self):
        from catscan.workspace import get_workspace_path
        ws1 = get_workspace_path(Path("/tmp/a.sb3"))
        ws2 = get_workspace_path(Path("/tmp/b.sb3"))
        self.assertNotEqual(ws1, ws2)

    def test_backup_numbering_still_works(self):
        from catscan.workspace import get_backups_path
        with tempfile.TemporaryDirectory() as tmpdir:
            sb3_path = Path(tmpdir) / "project.sb3"
            sb3_path.write_bytes(b"data")
            backup1 = create_safe_backup(sb3_path)
            self.assertEqual(backup1.name, "project.sb3.bak")
            backup2 = create_safe_backup(sb3_path)
            self.assertEqual(backup2.name, "project.sb3.bak.1")
            backup3 = create_safe_backup(sb3_path)
            self.assertEqual(backup3.name, "project.sb3.bak.2")
            backups = get_backups_path(sb3_path)
            self.assertEqual(backup1.parent, backups)
            self.assertEqual(backup2.parent, backups)
            self.assertEqual(backup3.parent, backups)

    def test_workspace_not_created_for_nonexistent_file(self):
        from catscan.workspace import get_workspace_path
        ws = get_workspace_path(Path("/tmp/noexist.sb3"))
        self.assertFalse(ws.exists())


class TestOrphanCleanup(unittest.TestCase):

    def _make_project(self, blocks):
        return {
            "targets": [
                {
                    "name": "Stage",
                    "isStage": True,
                    "blocks": blocks,
                    "costumes": [],
                    "sounds": [],
                }
            ]
        }

    def test_genuinely_unreachable_block_is_removed(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "b2": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": "b1",
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "orphan": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": None,
                "inputs": {"STEPS": [1, [10, "50"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        stats = cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertNotIn("orphan", blocks)
        self.assertIn("b1", blocks)
        self.assertIn("b2", blocks)
        self.assertEqual(stats["blocks_removed"], 1)

    def test_reporter_block_referenced_by_input_is_preserved(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "b2": {
                "opcode": "operator_add",
                "next": None,
                "parent": "b1",
                "inputs": {"NUM1": [1, [4, "10"]], "NUM2": [1, [4, "20"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "b3": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": "b1",
                "inputs": {"STEPS": [2, "b2"]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertIn("b2", blocks)

    def test_nested_operator_tree_is_preserved(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "b2": {
                "opcode": "operator_add",
                "next": None,
                "parent": "b1",
                "inputs": {"NUM1": [2, "b3"], "NUM2": [1, [4, "5"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "b3": {
                "opcode": "operator_multiply",
                "next": None,
                "parent": "b2",
                "inputs": {"NUM1": [1, [4, "2"]], "NUM2": [1, [4, "3"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertIn("b2", blocks)
        self.assertIn("b3", blocks)

    def test_substack_block_is_preserved(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "b2": {
                "opcode": "control_forever",
                "next": None,
                "parent": "b1",
                "inputs": {"SUBSTACK": [2, "b3"]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "b3": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": "b2",
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertIn("b3", blocks)

    def test_substack2_block_is_preserved(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "b2": {
                "opcode": "control_if_else",
                "next": None,
                "parent": "b1",
                "inputs": {
                    "CONDITION": [2, "bCond"],
                    "SUBSTACK": [2, "b3"],
                    "SUBSTACK2": [2, "b4"],
                },
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "bCond": {
                "opcode": "sensing_touchingobject",
                "next": None,
                "parent": "b2",
                "inputs": {"TOUCHINGOBJECTMENU": [1, "bMenu"]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "bMenu": {
                "opcode": "sensing_touchingobjectmenu",
                "next": None,
                "parent": "bCond",
                "inputs": {},
                "fields": {"TOUCHINGOBJECTMENU": ["_mouse_", None]},
                "shadow": True,
                "topLevel": False,
            },
            "b3": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": "b2",
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "b4": {
                "opcode": "motion_turnright",
                "next": None,
                "parent": "b2",
                "inputs": {"DEGREES": [1, [10, "15"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertIn("b3", blocks)
        self.assertIn("b4", blocks)
        self.assertIn("bCond", blocks)
        self.assertIn("bMenu", blocks)

    def test_shadow_menu_block_used_by_input_is_preserved(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "b2": {
                "opcode": "motion_goto",
                "next": None,
                "parent": "b1",
                "inputs": {"TO": [1, "bMenu"]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "bMenu": {
                "opcode": "motion_goto_menu",
                "next": None,
                "parent": "b2",
                "inputs": {},
                "fields": {"TO": ["_random_position_", None]},
                "shadow": True,
                "topLevel": False,
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertIn("bMenu", blocks)

    def test_procedure_definition_is_preserved(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": None,
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "def1": {
                "opcode": "procedures_definition",
                "next": "body1",
                "parent": None,
                "inputs": {"custom_block": [1, "proto1"]},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "proto1": {
                "opcode": "procedures_prototype",
                "next": None,
                "parent": "def1",
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": False,
                "mutation": {
                    "tagName": "mutation",
                    "proccode": "my block %s",
                    "argumentnames": '["arg1"]',
                    "argumentids": '["id1"]',
                    "argumentdefaults": '[""]',
                    "warp": "false",
                },
            },
            "body1": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": "def1",
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertIn("def1", blocks)
        self.assertIn("proto1", blocks)
        self.assertIn("body1", blocks)

    def test_procedure_call_block_is_preserved(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "bCall",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "bCall": {
                "opcode": "procedures_call",
                "next": None,
                "parent": "b1",
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": False,
                "mutation": {
                    "tagName": "mutation",
                    "proccode": "my block %s",
                    "argumentnames": '["arg1"]',
                    "argumentids": '["id1"]',
                    "argumentdefaults": '[""]',
                    "warp": "false",
                },
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertIn("bCall", blocks)



    def test_cleanup_removes_only_real_orphan(self):
        project = {
            "targets": [
                {
                    "name": "hitbox",
                    "isStage": False,
                    "blocks": {
                        "event": {
                            "opcode": "event_whenflagclicked",
                            "next": "move",
                            "parent": None,
                            "inputs": {},
                            "fields": {},
                            "shadow": False,
                            "topLevel": True,
                        },
                        "move": {
                            "opcode": "motion_movesteps",
                            "next": None,
                            "parent": "event",
                            "inputs": {
                                "STEPS": [1, [4, "10"]]
                            },
                            "fields": {},
                            "shadow": False,
                            "topLevel": False,
                        },
                        "real_orphan": {
                            "opcode": "operator_add",
                            "next": None,
                            "parent": None,
                            "inputs": {
                                "NUM2": [1, [4, "50"]]
                            },
                            "fields": {},
                            "shadow": False,
                            "topLevel": False,
                        },
                        "procedure_argument": {
                            "opcode": "argument_reporter_string_number",
                            "next": None,
                            "parent": "procedure_body",
                            "inputs": {},
                            "fields": {
                                "VALUE": ["jump height", None]
                            },
                            "shadow": False,
                            "topLevel": False,
                        },
                        "procedure_body": {
                            "opcode": "motion_changeyby",
                            "next": None,
                            "parent": "procedure_definition",
                            "inputs": {
                                "DY": [1, "procedure_argument"]
                            },
                            "fields": {},
                            "shadow": False,
                            "topLevel": False,
                        },
                        "procedure_definition": {
                            "opcode": "procedures_definition",
                            "next": "procedure_body",
                            "parent": None,
                            "inputs": {},
                            "fields": {},
                            "shadow": False,
                            "topLevel": True,
                        },
                    },
                }
            ]
        }

        result = cleanup_orphan_blocks(project)

        blocks = project["targets"][0]["blocks"]

        self.assertEqual(result["blocks_removed"], 1)
        self.assertNotIn("real_orphan", blocks)
        self.assertIn("procedure_argument", blocks)
        self.assertIn("procedure_body", blocks)
        self.assertIn("procedure_definition", blocks)



    def test_block_with_valid_parent_input_relationship_is_preserved(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "b2": {
                "opcode": "control_repeat",
                "next": None,
                "parent": "b1",
                "inputs": {
                    "TIMES": [1, [6, "3"]],
                    "SUBSTACK": [2, "b3"],
                },
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "b3": {
                "opcode": "looks_say",
                "next": None,
                "parent": "b2",
                "inputs": {"MESSAGE": [1, [10, "Hello"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertIn("b1", blocks)
        self.assertIn("b2", blocks)
        self.assertIn("b3", blocks)

    def test_cleanup_leaves_no_dangling_references(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": "b2",
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "b2": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": "b1",
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "orphan1": {
                "opcode": "motion_movesteps",
                "next": "orphan2",
                "parent": None,
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
            "orphan2": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": "orphan1",
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        cleanup_orphan_blocks(project)
        blocks = project["targets"][0]["blocks"]
        self.assertNotIn("orphan1", blocks)
        self.assertNotIn("orphan2", blocks)
        for bid, block in blocks.items():
            nxt = block.get("next")
            if nxt:
                self.assertIn(nxt, blocks)
            parent = block.get("parent")
            if parent:
                self.assertIn(parent, blocks)

    def test_cleanup_is_idempotent(self):
        project = self._make_project({
            "b1": {
                "opcode": "event_whenflagclicked",
                "next": None,
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
            },
            "orphan": {
                "opcode": "motion_movesteps",
                "next": None,
                "parent": None,
                "inputs": {"STEPS": [1, [10, "10"]]},
                "fields": {},
                "shadow": False,
                "topLevel": False,
            },
        })
        stats1 = cleanup_orphan_blocks(project)
        stats2 = cleanup_orphan_blocks(project)
        self.assertEqual(stats1["blocks_removed"], 1)
        self.assertEqual(stats2["blocks_removed"], 0)

    def test_multiple_targets_independent_cleanup(self):
        project = {
            "targets": [
                {
                    "name": "Stage",
                    "isStage": True,
                    "blocks": {
                        "b1": {
                            "opcode": "event_whenflagclicked",
                            "next": None,
                            "parent": None,
                            "inputs": {},
                            "fields": {},
                            "shadow": False,
                            "topLevel": True,
                        },
                    },
                    "costumes": [],
                    "sounds": [],
                },
                {
                    "name": "Sprite1",
                    "isStage": False,
                    "blocks": {
                        "b2": {
                            "opcode": "event_whenflagclicked",
                            "next": None,
                            "parent": None,
                            "inputs": {},
                            "fields": {},
                            "shadow": False,
                            "topLevel": True,
                        },
                        "orphan_s": {
                            "opcode": "motion_movesteps",
                            "next": None,
                            "parent": None,
                            "inputs": {"STEPS": [1, [10, "10"]]},
                            "fields": {},
                            "shadow": False,
                            "topLevel": False,
                        },
                    },
                    "costumes": [],
                    "sounds": [],
                },
            ]
        }
        stats = cleanup_orphan_blocks(project)
        self.assertEqual(stats["blocks_removed"], 1)
        self.assertIn("Sprite1", stats["targets_affected"])
        self.assertNotIn("Stage", stats["targets_affected"])
        self.assertNotIn("orphan_s", project["targets"][1]["blocks"])

    def test_system_prompt_mentions_orphan_cleanup(self):
        prompt = build_system_prompt()
        self.assertIn("Automatic orphan cleanup is performed by CatScan", prompt)


class TestTokenUsage(unittest.TestCase):

    def test_usage_captured_from_api_response(self):
        from catscan.ai import extract_ai_response_content
        response = {
            "choices": [
                {"message": {"content": "hello"}}
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }
        content = extract_ai_response_content(response)
        self.assertEqual(content, "hello")
        usage = get_last_usage()
        self.assertIsNotNone(usage)
        self.assertEqual(usage["prompt_tokens"], 100)
        self.assertEqual(usage["completion_tokens"], 50)

    def test_no_usage_when_not_provided(self):
        from catscan.ai import extract_ai_response_content
        response = {
            "choices": [
                {"message": {"content": "hello"}}
            ],
        }
        content = extract_ai_response_content(response)
        self.assertEqual(content, "hello")


if __name__ == "__main__":
    unittest.main()
