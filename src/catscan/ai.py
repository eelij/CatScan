import http.client
import json
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from .scratch_knowledge import build_scratch_knowledge_prompt
from .output import (
    print_ai_response,
    print_error,
    print_info,
    print_section,
)
from .scratch_patterns import build_scratch_patterns_prompt
from .orphan_cleanup import cleanup_orphan_blocks

from .config import (
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    sanitize_error_message,
    validate_url,
)
from .output import (
    print_error,
    print_info,
    print_section,
)

_last_usage: dict | None = None


def get_last_usage() -> dict | None:
    return _last_usage


def resolve_api_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return DEFAULT_API_URL

    u = url.strip().rstrip("/")
    if u in ("https://openrouter.ai", "http://openrouter.ai"):
        return "https://openrouter.ai/api/v1/chat/completions"
    if u in ("https://openrouter.ai/api/v1", "http://openrouter.ai/api/v1"):
        return "https://openrouter.ai/api/v1/chat/completions"
    if not u.endswith("/chat/completions"):
        return f"{u}/chat/completions"
    return u


_GENERAL_RULES = (
    "You are an expert Scratch 3.0 project analyzer and developer. "
    "You are given the project.json structure of a Scratch project (compact JSON; costumes, sounds, and layout data are omitted).\n\n"

    "Decide the user's intent. If they ask a question, want an explanation, or want analysis without changing the project, answer in plain natural language.\n"
    "If they ask to create, add, remove, change, fix, update, improve, refactor, or replace anything in the project, it is a MODIFICATION REQUEST.\n\n"

    "CRITICAL MODIFICATION OUTPUT RULE:\n"
    "For a modification request return ONLY one valid JSON object: no text before or after, no markdown, no code fences, no comments, "
    "and no Scratch code or manual instructions. Put all explanations in the 'explanation' field. "
    "The top-level keys must be exactly: mode, explanation, add_variables, remove_blocks, add_blocks, update_blocks, and mode must be 'modify'.\n\n"
)


_MODIFICATION_SCHEMA_SECTION = (
    "MODIFICATION JSON SCHEMA:\n"
    "{\n"
    '  "mode": "modify",\n'
    '  "explanation": "Brief explanation",\n'
    '  "add_variables": [{"target": "Stage or SpriteName", "name": "variable_name", "value": 0}],\n'
    '  "remove_blocks": [{"target": "Stage or SpriteName", "block_id": "existing_block_id"}],\n'
    '  "add_blocks": [{"target": "Stage or SpriteName", "id": "unique_block_id", "block": {"opcode": "valid_scratch_opcode", "next": null, "parent": null, "inputs": {}, "fields": {}, "shadow": false, "topLevel": false}}],\n'
    '  "update_blocks": [{"target": "Stage or SpriteName", "id": "existing_block_id", "block": {}}]\n'
    "}\n"
    "Empty arrays are fine for operations you do not need.\n\n"

    "HOW CHANGES ARE APPLIED:\n"
    "- update_blocks shallow-merges the keys you give into the existing block. A key you include (inputs, fields, next, parent) replaces that whole key, so write its complete new value.\n"
    "- Prefer update_blocks on an existing script over creating a duplicate script. A new script needs its complete connected chain plus all required shadow/menu blocks.\n"
    "- Automatic orphan cleanup is performed by CatScan after changes are applied. Use remove_blocks only when the user asks to remove a specific block or the change requires it.\n\n"

    "EXAMPLE (append 'change x by 10' after existing block \"abc\", the last block of a script):\n"
    '{"mode":"modify","explanation":"Added change x by 10 after the last block.","add_variables":[],"remove_blocks":[],'
    '"add_blocks":[{"target":"Sprite1","id":"newx1","block":{"opcode":"motion_changexby","next":null,"parent":"abc","inputs":{"DX":[1,[4,"10"]]},"fields":{},"shadow":false,"topLevel":false}}],'
    '"update_blocks":[{"target":"Sprite1","id":"abc","block":{"next":"newx1"}}]}\n\n'
)


_FINAL_CHECK_SECTION = (
    "FINAL SELF-CHECK BEFORE RETURNING JSON:\n"
    "1. Complete, valid JSON; mode is 'modify'; all six keys present; target names exist in the project.\n"
    "2. New IDs are unique and exact; every next, parent, SUBSTACK, and input reference resolves; no placeholder IDs.\n"
    "3. Variable names, IDs, and scopes are exact.\n"
    "4. Every new block is reachable from a script or input; no duplicate helpers; removals leave no dangling references.\n"
    "5. Shadow/menu blocks and topLevel/parent/shadow/x/y values are copied from equivalent project blocks; unrelated data is untouched.\n"
    "If the request cannot be safely represented by this schema, return mode 'modify' with empty arrays and explain the limitation in 'explanation'.\n"
)


def build_system_prompt(user_text: str | None = None) -> str:
    return (
        _GENERAL_RULES
        + build_scratch_knowledge_prompt()
        + build_scratch_patterns_prompt(user_text)
        + _MODIFICATION_SCHEMA_SECTION
        + _FINAL_CHECK_SECTION
    )


_PROMPT_TARGET_KEYS = ("name", "isStage", "variables", "lists", "broadcasts", "blocks")
_REQUEST_MARKER = "\n\nUser Request: "
_SNAPSHOT_OMITTED = "[Earlier project snapshot omitted; a newer one follows.]"


def build_project_payload(project_data: dict) -> str:
    """Compact, prompt-only view of a project. Never mutates project_data."""
    targets = []

    for target in project_data.get("targets", []):
        if not isinstance(target, dict):
            continue

        slim = {}
        for key in _PROMPT_TARGET_KEYS:
            value = target.get(key)
            if key in ("name", "isStage") or value:
                if key in target:
                    slim[key] = value
        targets.append(slim)

    payload = {"targets": targets}

    if project_data.get("extensions"):
        payload["extensions"] = project_data["extensions"]

    return json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False
    )


def extract_ai_response_content(res_json: dict) -> str | None:
    global _last_usage
    if not isinstance(res_json, dict):
        return None

    usage = res_json.get("usage")
    if isinstance(usage, dict):
        _last_usage = usage

    choices = res_json.get("choices")
    if isinstance(choices, dict):
        choices = list(choices.values())

    if isinstance(choices, list) and len(choices) > 0:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            msg_obj = first_choice.get("message")
            if not isinstance(msg_obj, dict):
                msg_obj = first_choice.get("delta")

            if isinstance(msg_obj, dict):
                content = msg_obj.get("content")
                if isinstance(content, str) and content.strip():
                    return content
                elif isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, str) and item.strip():
                            text_parts.append(item.strip())
                        elif isinstance(item, dict):
                            txt = item.get("text") or item.get("value")
                            if isinstance(txt, str) and txt.strip():
                                text_parts.append(txt.strip())
                    if text_parts:
                        return "".join(text_parts)
                elif isinstance(content, dict):
                    txt = content.get("text") or content.get("value")
                    if isinstance(txt, str) and txt.strip():
                        return txt.strip()

                for alt_field in ("reasoning_content", "reasoning", "text"):
                    alt_val = msg_obj.get(alt_field)
                    if isinstance(alt_val, str) and alt_val.strip():
                        return alt_val.strip()

            for direct_field in ("text", "content"):
                direct_val = first_choice.get(direct_field)
                if isinstance(direct_val, str) and direct_val.strip():
                    return direct_val.strip()

    for root_field in ("content", "text", "response"):
        root_val = res_json.get(root_field)
        if isinstance(root_val, str) and root_val.strip():
            return root_val.strip()

    return None


def send_ai_request(
    config: dict,
    messages: list
) -> str:
    max_tokens_value = config.get("max_tokens", 8192)
    if (
        not isinstance(max_tokens_value, int)
        or isinstance(max_tokens_value, bool)
        or not 1 <= max_tokens_value <= 65536
    ):
        raise ValueError(
            "Configured AI max_tokens must be between 1 and 65536."
        )
    
    timeout_value = config.get("timeout", 60)

    if (
        not isinstance(timeout_value, int)
        or isinstance(timeout_value, bool)
        or not 1 <= timeout_value <= 600
    ):
        raise ValueError("Configured AI timeout must be between 1 and 600 seconds.")

    api_key = config.get("api_key")

    if not api_key:
        raise ValueError(
            "AI API key is not configured. Set it using 'ai api' or set CATSCAN_AI_KEY or GEMINI_API_KEY environment variable."
        )

    url = config.get(
        "url",
        DEFAULT_API_URL
    )

    model = config.get(
        "model",
        DEFAULT_MODEL
    )

    if not validate_url(url):
        raise ValueError("Configured AI API URL is invalid.")

    if not isinstance(model, str) or not model.strip():
        raise ValueError("Configured AI model is invalid.")

    target_url = resolve_api_url(url)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens_value
    }

    data = json.dumps(payload).encode("utf-8")

    max_retries = 3
    backoff_delays = [1.0, 2.0, 4.0]

    for attempt in range(max_retries + 1):
        req = urllib.request.Request(
            target_url,
            data=data,
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                req,
                timeout=timeout_value
            ) as response:
                status_code = response.status if hasattr(response, "status") else response.getcode()

                if status_code not in (200, 201):
                    if status_code in (503, 429) and attempt < max_retries:
                        delay = backoff_delays[attempt]
                        print_info(
                            f"AI API returned HTTP {status_code}. Retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})..."
                        )
                        time.sleep(delay)
                        continue

                    raise RuntimeError(
                        f"AI API request failed with HTTP status {status_code}"
                    )

                raw_bytes = response.read()

                content_encoding = (response.headers.get("Content-Encoding") or "").lower()
                if "gzip" in content_encoding:
                    import gzip
                    try:
                        raw_bytes = gzip.decompress(raw_bytes)
                    except Exception:
                        pass
                elif "deflate" in content_encoding:
                    import zlib
                    try:
                        raw_bytes = zlib.decompress(raw_bytes)
                    except Exception:
                        pass

                res_body = raw_bytes.decode("utf-8", errors="replace").lstrip("\ufeff").strip()

                content_type = (response.headers.get("Content-Encoding") or "").lower()
                headers_ct = (response.headers.get("Content-Type") or "").lower()
                is_html = (
                    "text/html" in headers_ct
                    or res_body.lower().startswith("<!doctype")
                    or res_body.lower().startswith("<html")
                )

                if is_html:
                    preview = sanitize_error_message(res_body[:150].replace("\n", " "), api_key)
                    raise RuntimeError(
                        f"AI API (HTTP {status_code}) returned an HTML webpage instead of JSON (Content-Type: '{headers_ct}'). "
                        f"Ensure URL points to an OpenAI-compatible endpoint like '{target_url}'. Raw response preview: '{preview}'"
                    )

            try:
                res_json = json.loads(res_body)
            except json.JSONDecodeError as err:
                preview = sanitize_error_message(res_body[:200], api_key)
                raise RuntimeError(
                    f"AI API (HTTP {status_code}) returned malformed JSON response: {err}. Raw response preview: '{preview}'"
                )

            extracted_content = extract_ai_response_content(res_json)
            if extracted_content is not None:
                return extracted_content

            if isinstance(res_json, dict) and "error" in res_json:
                err_data = res_json["error"]
                if isinstance(err_data, dict) and isinstance(err_data.get("message"), str):
                    err_msg = err_data["message"].strip()
                elif isinstance(err_data, str):
                    err_msg = err_data.strip()
                else:
                    err_msg = str(err_data)
                safe_err = sanitize_error_message(f"AI API (HTTP {status_code}) returned error: {err_msg}", api_key)
                raise RuntimeError(safe_err)

            structure_preview = sanitize_error_message(json.dumps(res_json, ensure_ascii=False)[:300], api_key)
            raise RuntimeError(
                f"AI API (HTTP {status_code}) response missing expected 'content' in choices. Response structure: {structure_preview}"
            )

        except urllib.error.HTTPError as e:
            status_code = e.code
            reason = e.reason

            server_message = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")
                err_json = json.loads(err_body)

                if isinstance(err_json, dict):
                    error_data = err_json.get("error")

                    if isinstance(error_data, dict):
                        msg = error_data.get("message")
                        if isinstance(msg, str) and msg.strip():
                            server_message = msg.strip()
                    elif isinstance(error_data, str) and error_data.strip():
                        server_message = error_data.strip()
            except Exception:
                pass

            if status_code in (503, 429) and attempt < max_retries:
                delay = backoff_delays[attempt]
                print_info(
                    f"AI API returned HTTP {status_code} ({reason}). Retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(delay)
                continue

            error_msg = f"HTTP Error {status_code}: {reason}"
            if server_message:
                error_msg += f" - {server_message}"

            error_msg = sanitize_error_message(error_msg, api_key)
            raise RuntimeError(error_msg)

        except (urllib.error.URLError, TimeoutError, socket.timeout, http.client.RemoteDisconnected, ConnectionError) as e:
            is_timeout = isinstance(e, (TimeoutError, socket.timeout)) or (
                isinstance(e, urllib.error.URLError) and isinstance(e.reason, socket.timeout)
            )

            if attempt < max_retries:
                delay = backoff_delays[attempt]
                err_label = "request timed out" if is_timeout else "connection failed"
                print_info(
                    f"AI API {err_label}. Retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(delay)
                continue

            if is_timeout:
                raise RuntimeError("AI API request timed out after maximum retries.")

            raw_reason = str(getattr(e, "reason", e))
            safe_reason = sanitize_error_message(raw_reason, api_key)
            raise RuntimeError(f"Connection failed: {safe_reason}")


def parse_ai_response(
    response_text: str
) -> tuple[str, dict | None]:
    clean_text = response_text.strip()

    fence_start = clean_text.find("```")

    while fence_start != -1:
        fence_end = clean_text.find(
            "```",
            fence_start + 3
        )

        if fence_end == -1:
            break

        fenced_content = clean_text[
            fence_start + 3:fence_end
        ].strip()

        if fenced_content.lower().startswith("json"):
            fenced_content = fenced_content[4:].strip()

        try:
            parsed = json.loads(
                fenced_content
            )

            if (
                isinstance(parsed, dict)
                and parsed.get("mode") == "modify"
            ):
                return "modify", parsed

        except json.JSONDecodeError:
            pass

        fence_start = clean_text.find(
            "```",
            fence_end + 3
        )

    if clean_text.startswith("{") and clean_text.endswith("}"):
        try:
            parsed = json.loads(
                clean_text
            )

            if (
                isinstance(parsed, dict)
                and parsed.get("mode") == "modify"
            ):
                return "modify", parsed

        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()

    for index, char in enumerate(clean_text):
        if char != "{":
            continue

        try:
            parsed, _ = decoder.raw_decode(
                clean_text[index:]
            )

            if (
                isinstance(parsed, dict)
                and parsed.get("mode") == "modify"
            ):
                return "modify", parsed

        except json.JSONDecodeError:
            continue

    return "chat", None


MAX_CONVERSATION_MESSAGES = 12
conversation_history: list[dict] = []


_last_sent_payload: str | None = None


def clear_conversation_history() -> None:
    global _last_sent_payload
    conversation_history.clear()
    _last_sent_payload = None


def _drop_old_snapshots() -> None:
    for message in conversation_history:
        content = message.get("content")
        if (
            message.get("role") == "user"
            and isinstance(content, str)
            and content.startswith("Project data:")
            and _REQUEST_MARKER in content
        ):
            request = content.split(_REQUEST_MARKER, 1)[1]
            message["content"] = (
                _SNAPSHOT_OMITTED + _REQUEST_MARKER + request
            )


def _append_user_message(content: str) -> None:
    conversation_history.append({"role": "user", "content": content})
    if len(conversation_history) > MAX_CONVERSATION_MESSAGES:
        conversation_history[:] = conversation_history[-MAX_CONVERSATION_MESSAGES:]


def _append_assistant_message(content: str) -> None:
    conversation_history.append({"role": "assistant", "content": content})
    if len(conversation_history) > MAX_CONVERSATION_MESSAGES:
        conversation_history[:] = conversation_history[-MAX_CONVERSATION_MESSAGES:]


def ai_command_flow(
    sb3_file: Path,
    prompt_text: str,
    config: dict
) -> None:
    from catscan.main import (
        apply_project_changes,
        get_project_data,
        save_project_atomic,
        validate_ai_modification_response,
        validate_scratch_project_structure,
    )

    global _last_sent_payload

    system_prompt = build_system_prompt(prompt_text)

    project_data = get_project_data(
        sb3_file
    )

    payload = build_project_payload(
        project_data
    )

    has_snapshot = any(
        isinstance(m.get("content"), str)
        and m["content"].startswith("Project data:")
        for m in conversation_history
    )

    if not has_snapshot or payload != _last_sent_payload:
        _drop_old_snapshots()
        user_prompt = (
            "Project data:\n"
            + payload
            + _REQUEST_MARKER
            + prompt_text
        )
        snapshot_sent = True
    else:
        user_prompt = prompt_text
        snapshot_sent = False

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)

    print_info(
        "Sending request to AI model..."
    )

    try:
        _append_user_message(user_prompt)
        messages.append(
            {"role": "user", "content": user_prompt}
        )

        response_text = send_ai_request(
            config,
            messages
        )

    except Exception as e:
        if conversation_history and conversation_history[-1].get("content") == user_prompt:
            conversation_history.pop()

        safe_msg = sanitize_error_message(str(e), config.get("api_key"))
        print_error(
            f"AI API request failed: {safe_msg}"
        )
        return

    _append_assistant_message(response_text)

    if snapshot_sent:
        _last_sent_payload = payload

    mode, modifications = parse_ai_response(
        response_text
    )

    if mode == "chat" or modifications is None:
        print_section("AI Response")
        print_ai_response(response_text)
        print()
        return

    print_section(
        "AI Proposed Project Modifications"
    )

    explanation = modifications.get(
        "explanation",
        "No explanation provided."
    )

    print(
        f"Explanation: {explanation}"
    )

    print()

    val_errors = validate_ai_modification_response(
    modifications,
    project_data
)

    if val_errors:
        print_error(
            "AI modification proposal failed structural validation:"
        )

        for err in val_errors:
            print(f"  - {err}")

        print()
        force_confirm = input(
            "Execute anyway? [y/N]: "
        ).strip().lower()

        if force_confirm not in ("y", "yes"):
            print_error(
                "Modification aborted. Original .sb3 file remains untouched."
            )
            return

        print_info(
            "Validation override enabled. Final project validation is still enforced."
        )

    updated_project, stats = apply_project_changes(
        project_data,
        modifications
    )

    cleanup_stats = cleanup_orphan_blocks(updated_project)

    post_errors = validate_scratch_project_structure(
        updated_project
    )

    if post_errors:
        print_error(
            "Post-modification project validation failed:"
        )

        for err in post_errors:
            print(f"  - {err}")

        print_error(
            "Modification aborted. Original .sb3 file remains untouched."
        )

        return

    print(
        "Proposed Changes Summary:"
    )

    print(
        f"  Variables added: {stats['variables_added']}"
    )

    print(
        f"  Blocks added:    {stats['blocks_added']}"
    )

    print(
        f"  Blocks updated:  {stats['blocks_updated']}"
    )

    print(
        f"  Blocks removed:  {stats['blocks_removed']}"
    )

    if cleanup_stats["blocks_removed"] > 0:
        print(
            f"  Automatically cleaned orphan blocks: {cleanup_stats['blocks_removed']}"
        )

    print()

    confirm = input(
        "Apply these modifications to the .sb3 file? [y/N]: "
    ).strip().lower()

    if confirm not in ("y", "yes"):
        print_info(
            "Modifications cancelled by user."
        )
        return

    try:
        save_project_atomic(
            sb3_file,
            updated_project
        )

    except Exception as e:
        print_error(
            f"Failed to save modified project: {e}"
        )


