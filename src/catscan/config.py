import json
import os
import re
import urllib.parse
from pathlib import Path

from .output import print_error

DEFAULT_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEFAULT_MODEL = "gemini-2.5-flash"
OLD_DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"
OLD_DEFAULT_MODEL = "gpt-4o-mini"


def sanitize_error_message(text: str, api_key: str | None = None) -> str:
    if not isinstance(text, str):
        text = str(text)

    if api_key and isinstance(api_key, str) and api_key.strip():
        text = text.replace(api_key.strip(), "[REDACTED_API_KEY]")

    text = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED_API_KEY]", text)
    text = re.sub(r"(key|api_key|token)=([A-Za-z0-9_\-\.]+)", r"\1=[REDACTED_API_KEY]", text, flags=re.IGNORECASE)
    return text


def get_config_path() -> Path:
    config_dir = Path.home() / ".config" / "catscan"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def validate_url(url: str) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False

    parsed = urllib.parse.urlparse(url.strip())

    return (
        parsed.scheme in ("http", "https")
        and bool(parsed.netloc)
        and not any(char.isspace() for char in url)
    )


def load_config() -> dict:
    config = {
        "api_key": "",
        "url": DEFAULT_API_URL,
        "model": DEFAULT_MODEL,
        "timeout": 60,
        "max_tokens": 8192
    }

    env_key = os.environ.get("CATSCAN_AI_KEY") or os.environ.get("GEMINI_API_KEY")
    env_url = os.environ.get("CATSCAN_AI_URL")
    env_model = os.environ.get("CATSCAN_AI_MODEL")
    env_timeout = os.environ.get("CATSCAN_AI_TIMEOUT")
    env_max_tokens = os.environ.get("CATSCAN_AI_MAX_TOKENS")

    if env_key:
        config["api_key"] = env_key

    if env_url:
        if validate_url(env_url):
            config["url"] = env_url
        else:
            print_error("Invalid URL in environment variable CATSCAN_AI_URL.")

    if env_model:
        if isinstance(env_model, str) and env_model.strip():
            config["model"] = env_model.strip()
        else:
            print_error("Invalid model in environment variable CATSCAN_AI_MODEL.")

    if env_timeout:
        try:
            timeout_value = int(env_timeout)
            if 1 <= timeout_value <= 600:
                config["timeout"] = timeout_value
            else:
                print_error("CATSCAN_AI_TIMEOUT must be between 1 and 600 seconds.")
        except ValueError:
            print_error("Invalid CATSCAN_AI_TIMEOUT value.")

    if env_max_tokens:
        try:
            max_tokens_value = int(env_max_tokens)
            if 1 <= max_tokens_value <= 65536:
                config["max_tokens"] = max_tokens_value
            else:
                print_error("CATSCAN_AI_MAX_TOKENS must be between 1 and 65536.")
        except ValueError:
            print_error("Invalid CATSCAN_AI_MAX_TOKENS value.")

    path = get_config_path()

    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                stored = json.load(f)

            if not isinstance(stored, dict):
                print_error(
                    "Config file does not contain a JSON object. Falling back to defaults."
                )
                return config

            if not env_key:
                stored_key = stored.get("api_key")
                if isinstance(stored_key, str):
                    config["api_key"] = stored_key

            if not env_url and "url" in stored:
                url_val = stored["url"]

                if validate_url(url_val):
                    if url_val.strip() == OLD_DEFAULT_API_URL:
                        config["url"] = DEFAULT_API_URL
                    else:
                        config["url"] = url_val.strip()
                else:
                    print_error("Malformed URL found in configuration file.")

            if not env_model and "model" in stored:
                model_val = stored["model"]

                if isinstance(model_val, str) and model_val.strip():
                    if model_val.strip() == OLD_DEFAULT_MODEL:
                        config["model"] = DEFAULT_MODEL
                    else:
                        config["model"] = model_val.strip()
                else:
                    print_error("Malformed model found in configuration file.")

            if not env_timeout and "timeout" in stored:
                timeout_val = stored["timeout"]

                if isinstance(timeout_val, int) and not isinstance(timeout_val, bool):
                    if 1 <= timeout_val <= 600:
                        config["timeout"] = timeout_val
                    else:
                        print_error(
                            "Configured timeout must be between 1 and 600 seconds."
                        )
                else:
                    print_error("Configured timeout must be an integer.")

            if not env_max_tokens and "max_tokens" in stored:
                max_tokens_val = stored["max_tokens"]

                if isinstance(max_tokens_val, int) and not isinstance(max_tokens_val, bool):
                    if 1 <= max_tokens_val <= 65536:
                        config["max_tokens"] = max_tokens_val
                    else:
                        print_error(
                            "Configured max_tokens must be between 1 and 65536."
                        )
                else:
                    print_error("Configured max_tokens must be an integer.")

        except (json.JSONDecodeError, OSError) as e:
            print_error(
                f"Failed to read config file ({e}). Falling back to defaults."
            )

    return config


def save_config(config: dict) -> None:
    path = get_config_path()

    url_to_save = config.get("url", DEFAULT_API_URL)
    model_to_save = config.get("model", DEFAULT_MODEL)
    api_key_to_save = config.get("api_key", "")
    timeout_to_save = config.get("timeout", 60)
    max_tokens_to_save = config.get("max_tokens", 8192)

    if (
        not isinstance(max_tokens_to_save, int)
        or isinstance(max_tokens_to_save, bool)
        or not 1 <= max_tokens_to_save <= 65536
    ):
        print_error(
            "Cannot save invalid max_tokens. Use a value between 1 and 65536."
        )
        return

    if not validate_url(url_to_save):
        print_error("Cannot save invalid API URL.")
        return

    if not isinstance(model_to_save, str) or not model_to_save.strip():
        print_error("Cannot save empty model name.")
        return

    if not isinstance(api_key_to_save, str):
        print_error("Cannot save invalid API key.")
        return

    if (
        not isinstance(timeout_to_save, int)
        or isinstance(timeout_to_save, bool)
        or not 1 <= timeout_to_save <= 600
    ):
        print_error("Cannot save invalid timeout. Use a value between 1 and 600 seconds.")
        return

    data = {
        "api_key": api_key_to_save,
        "url": url_to_save.strip(),
        "model": model_to_save.strip(),
        "timeout": timeout_to_save,
        "max_tokens": max_tokens_to_save
    }

    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600

        fd = os.open(path, flags, mode)

        with open(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        os.chmod(path, 0o600)

    except OSError as e:
        print_error(f"Failed to save configuration: {e}")


