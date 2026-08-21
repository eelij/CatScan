import argparse
import copy
import getpass
import io
import json
import os
import re
import secrets
import shutil
import string
import sys
import termios
import tty
import zipfile
import atexit
from pathlib import Path

from catscan import output
from catscan.ai import ai_command_flow, resolve_api_url, send_ai_request
from catscan.config import (
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    OLD_DEFAULT_API_URL,
    OLD_DEFAULT_MODEL,
    load_config,
    sanitize_error_message,
    save_config,
    validate_url,
)
from catscan.output import (
    disable_colors,
    print_error,
    print_info,
    print_section,
    print_success,
)

try:
    import readline
    history_file = Path.home() / ".config" / "catscan" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    if history_file.exists():
        try:
            readline.read_history_file(str(history_file))
        except Exception:
            pass

    def _save_readline_history():
        try:
            history_file.parent.mkdir(parents=True, exist_ok=True)
            readline.write_history_file(str(history_file))
        except Exception:
            pass

    atexit.register(_save_readline_history)
except ImportError:
    pass

VERSION = "1.2.0"


def mask_api_key(key: str) -> str:
    if not key:
        return "(not set)"

    if len(key) <= 8:
        return "*" * len(key)

    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def rl_prompt_color(color_code: str) -> str:
    if not color_code:
        return ""
    return f"\001{color_code}\002"


def clear_screen() -> None:
    os.system("clear")


def print_banner() -> None:
    print(f"{output.BOLD}{output.CYAN}")
    print("  ██████╗ █████╗ ████████╗███████╗ ██████╗ █████╗ ███╗   ██╗")
    print(" ██╔════╝██╔══██╗╚══██╔══╝██╔════╝██╔════╝██╔══██╗████╗  ██║")
    print(" ██║     ███████║   ██║   ███████╗██║     ███████║██╔██╗ ██║")
    print(" ██║     ██╔══██║   ██║   ╚════██║██║     ██╔══██║██║╚██╗██║")
    print(" ╚██████╗██║  ██║   ██║   ███████╗╚██████╗██║  ██║██║ ╚████║")
    print("  ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝")
    print(f"{output.RESET}")
    print(f"  {output.BOLD}{output.WHITE}CatScan {VERSION}{output.RESET}")
    print(f"  {output.GRAY}Scratch project development toolkit{output.RESET}")
    print()


def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def validate_target_structure(target: dict) -> bool:
    if not isinstance(target, dict):
        return False

    if "name" in target and not isinstance(target["name"], str):
        return False

    for key, expected_type in [
        ("blocks", dict),
        ("variables", dict),
        ("lists", dict),
        ("broadcasts", dict),
        ("costumes", list),
        ("sounds", list)
    ]:
        if key in target and not isinstance(target[key], expected_type):
            return False

    return True


def normalize_project_blocks(project_data: dict) -> dict:
    if not isinstance(project_data, dict):
        return project_data

    targets = project_data.get("targets")
    if not isinstance(targets, list):
        return project_data

    for target in targets:
        if not isinstance(target, dict):
            continue

        blocks = target.get("blocks")
        if not isinstance(blocks, dict) or not blocks:
            continue

        child_parents = {}

        for block_id, block in blocks.items():
            if not isinstance(block, dict):
                continue

            next_id = block.get("next")
            if isinstance(next_id, str) and next_id in blocks and next_id != block_id:
                child_parents[next_id] = block_id

            inputs = block.get("inputs")
            if isinstance(inputs, dict):
                for input_val in inputs.values():
                    if not isinstance(input_val, list) or len(input_val) < 2:
                        continue

                    val_type = input_val[0]
                    val_data = input_val[1]

                    if val_type in (2, 3):
                        if isinstance(val_data, str) and val_data in blocks and val_data != block_id:
                            child_parents[val_data] = block_id
                        elif (
                            isinstance(val_data, list)
                            and len(val_data) >= 2
                            and isinstance(val_data[1], str)
                            and val_data[1] in blocks
                            and val_data[1] != block_id
                        ):
                            child_parents[val_data[1]] = block_id

                    if len(input_val) >= 3:
                        shadow_data = input_val[2]
                        if isinstance(shadow_data, str) and shadow_data in blocks and shadow_data != block_id:
                            child_parents[shadow_data] = block_id
                        elif (
                            isinstance(shadow_data, list)
                            and len(shadow_data) >= 2
                            and isinstance(shadow_data[1], str)
                            and shadow_data[1] in blocks
                            and shadow_data[1] != block_id
                        ):
                            child_parents[shadow_data[1]] = block_id

        top_level_index = 0
        for block_id, block in blocks.items():
            if not isinstance(block, dict):
                continue

            if block_id in child_parents:
                block["topLevel"] = False
                block["parent"] = child_parents[block_id]
                block.pop("x", None)
                block.pop("y", None)
            else:
                block["topLevel"] = True
                block["parent"] = None

                x = block.get("x")
                y = block.get("y")

                is_valid_x = (
                    x is not None
                    and not isinstance(x, bool)
                    and isinstance(x, (int, float))
                    and -2000 <= x <= 3000
                )
                is_valid_y = (
                    y is not None
                    and not isinstance(y, bool)
                    and isinstance(y, (int, float))
                    and -2000 <= y <= 3000
                )

                if not is_valid_x:
                    block["x"] = 36
                if not is_valid_y:
                    block["y"] = 72 + (top_level_index * 200)

                top_level_index += 1

    return project_data


def get_project_data(sb3_file: Path) -> dict:
    if not sb3_file.exists():
        raise FileNotFoundError(f"File not found: {sb3_file}")

    if not sb3_file.is_file():
        raise ValueError(f"Not a file: {sb3_file}")

    if sb3_file.suffix.lower() != ".sb3":
        raise ValueError("File must be a .sb3 file")

    try:
        with zipfile.ZipFile(sb3_file, "r") as archive:
            if "project.json" not in archive.namelist():
                raise ValueError("project.json was not found in the .sb3 file")

            with archive.open("project.json") as project_file:
                project = json.load(project_file)

            if not isinstance(project, dict):
                raise ValueError(
                    "project.json is malformed (not a JSON object)"
                )

            targets = project.get("targets")

            if not isinstance(targets, list):
                raise ValueError(
                    "project.json missing or invalid 'targets' array"
                )

            for target in targets:
                if not validate_target_structure(target):
                    raise ValueError(
                        "project.json contains malformed target structure"
                    )

            return normalize_project_blocks(project)

    except zipfile.BadZipFile as e:
        raise ValueError(f"Invalid or corrupted .sb3 ZIP archive: {e}")


def supports_color(no_color_flag: bool) -> bool:
    if no_color_flag:
        return False

    if os.environ.get("NO_COLOR") is not None:
        return False

    if not sys.stdout.isatty():
        return False

    return True


def extract_sb3(sb3_file: Path, output_dir: Path) -> None:
    if not sb3_file.exists():
        raise FileNotFoundError(f"File not found: {sb3_file}")

    if not sb3_file.is_file():
        raise ValueError(f"Not a file: {sb3_file}")

    if sb3_file.suffix.lower() != ".sb3":
        raise ValueError("File must be a .sb3 file")

    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(
            f"Output path exists and is not a directory: {output_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_output_dir = output_dir.resolve()

    with zipfile.ZipFile(sb3_file, "r") as archive:
        for member in archive.infolist():
            member_path = Path(member.filename)
            target_path = (resolved_output_dir / member_path).resolve()

            try:
                target_path.relative_to(resolved_output_dir)
            except ValueError:
                raise ValueError(
                    f"Unsafe ZIP member path detected: {member.filename}"
                )

        archive.extractall(resolved_output_dir)

    print_success(f"Extracted: {sb3_file}")
    print_info(f"Output directory: {resolved_output_dir}")


def inspect_sb3(sb3_file: Path) -> None:
    project = get_project_data(sb3_file)

    sound_count = 0
    stage_count = 0
    sprite_count = 0
    script_count = 0
    block_count = 0
    variable_count = 0
    list_count = 0
    broadcast_count = 0
    costume_count = 0

    for target in project.get("targets", []):
        if not isinstance(target, dict):
            continue

        if target.get("isStage", False):
            stage_count += 1
        else:
            sprite_count += 1

        blocks = target.get("blocks", {})

        if isinstance(blocks, dict):
            for block in blocks.values():
                if not isinstance(block, dict):
                    continue

                if block.get("topLevel", False):
                    script_count += 1

                if not block.get("shadow", False):
                    block_count += 1

        vars_dict = target.get("variables", {})

        if isinstance(vars_dict, dict):
            variable_count += len(vars_dict)

        lists_dict = target.get("lists", {})

        if isinstance(lists_dict, dict):
            list_count += len(lists_dict)

        broadcasts_dict = target.get("broadcasts", {})

        if isinstance(broadcasts_dict, dict):
            broadcast_count += len(broadcasts_dict)

        costumes_list = target.get("costumes", [])

        if isinstance(costumes_list, list):
            costume_count += len(costumes_list)

        sounds_list = target.get("sounds", [])

        if isinstance(sounds_list, list):
            sound_count += len(sounds_list)

    lines = "-" * len(sb3_file.name)

    print(f"{sb3_file.name}\n{lines}")
    print("PROJECT")
    print(f"  Stages: {stage_count}")
    print(f"  Sprites: {sprite_count}")
    print(f"  Scripts: {script_count}")
    print(f"  Blocks: {block_count}")
    print(f"  Variables: {variable_count}")
    print(f"  Lists: {list_count}")
    print(f"  Broadcasts: {broadcast_count}")

    print("TARGETS")

    for target in project.get("targets", []):
        if not isinstance(target, dict):
            continue

        print(f'  {target.get("name", "Unnamed")}')

        vars_dict = (
            target.get("variables", {})
            if isinstance(target.get("variables"), dict)
            else {}
        )

        costumes_list = (
            target.get("costumes", [])
            if isinstance(target.get("costumes"), list)
            else []
        )

        sounds_list = (
            target.get("sounds", [])
            if isinstance(target.get("sounds"), list)
            else []
        )

        if target.get("isStage", False):
            print(f"    Global Variables: {len(vars_dict)}")
        else:
            print(f"    Private Variables: {len(vars_dict)}")

        for variable in vars_dict.values():
            if isinstance(variable, list) and variable:
                print(f"      Variable: {variable[0]}")

        print(f"    Costumes: {len(costumes_list)}")

        for costume in costumes_list:
            if isinstance(costume, dict):
                print(f'      Costume: {costume.get("name", "")}')

        print(f"    Sounds: {len(sounds_list)}")

        for sound in sounds_list:
            if isinstance(sound, dict):
                print(f'      Sound: {sound.get("name", "")}')

        blocks = target.get("blocks", {})
        target_block_count = 0

        if isinstance(blocks, dict):
            target_block_count = sum(
                1
                for block in blocks.values()
                if isinstance(block, dict)
                and not block.get("shadow", False)
            )

        print(f"    Blocks: {target_block_count}")
        print()

    print("ASSETS")
    print(f"  Costumes: {costume_count}")
    print(f"  Sounds: {sound_count}")


def print_help() -> None:
    print()
    print(f"{output.BOLD}{output.CYAN}CatScan Commands{output.RESET}")
    print()

    commands = [
        ("select <file>", "Select a Scratch project"),
        ("inspect", "Inspect the selected project"),
        ("extract", "Extract the selected .sb3 file"),
        ("script", "Select a target for script inspection"),
        ("script save", "Save target scripts to auto-named file"),
        ("script save <file>", "Save target scripts to specified file"),
        ("ai api", "Interactively set your AI API key securely"),
        ("ai api <api_key>", "Set your AI API key"),
        ("ai url <url>", "Set AI Endpoint URL"),
        ("ai model <model>", "Set AI Model name"),
        ("ai max-tokens <amount>", "Set maximum AI output tokens"),
        ("ai timeout <seconds>", "Set AI request timeout"),
        ("ai config", "Display current AI configuration"),
        ("ai <prompt>", "Ask AI about the selected project or request modifications"),
        ("clear", "Clear the terminal"),
        ("version", "Show CatScan version"),
        ("help", "Show this help message"),
        ("exit", "Exit CatScan"),
        ("quit", "Exit CatScan")
    ]

    for command, description in commands:
        print(
            f"  {output.GREEN}{command:<22}{output.RESET}"
            f"{output.GRAY}{description}{output.RESET}"
        )

    print()


def print_selected(selected_file: Path | None) -> None:
    print()

    if selected_file is None:
        print(f"  {output.GRAY}No project selected{output.RESET}")
    else:
        print(
            f"  {output.GRAY}Selected:{output.RESET} "
            f"{output.GREEN}{selected_file.name}{output.RESET}"
        )

    print()


def require_selected(selected_file: Path | None) -> Path | None:
    if selected_file is None:
        print()
        print_error("You need to select a file first.")
        print()
        print(f"  {output.GRAY}Use:{output.RESET}")
        print(f"  {output.GREEN}select <file.sb3>{output.RESET}")
        print()
        return None

    return selected_file


def select_file(path_text: str) -> Path:
    path = Path(path_text).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    if path.suffix.lower() != ".sb3":
        raise ValueError("File must be a .sb3 file")

    return path.resolve()


def get_top_level_blocks(target: dict) -> list[dict]:
    top_blocks = []

    blocks = target.get("blocks", {})

    if not isinstance(blocks, dict):
        return top_blocks

    for block in blocks.values():
        if not isinstance(block, dict):
            continue

        if block.get("topLevel", False):
            top_blocks.append(block)

    return top_blocks


def get_events(target: dict) -> list[dict]:
    events = []

    for block in get_top_level_blocks(target):
        if str(block.get("opcode", "")).startswith("event_"):
            events.append(block)

    return events


def get_custom_block_definitions(target: dict) -> list[dict]:
    definitions = []

    for block in get_top_level_blocks(target):
        if block.get("opcode") == "procedures_definition":
            definitions.append(block)

    return definitions


def get_other_top_level_blocks(target: dict) -> list[dict]:
    others = []

    for block in get_top_level_blocks(target):
        opcode = str(block.get("opcode", ""))

        if not opcode.startswith("event_") and opcode != "procedures_definition":
            others.append(block)

    return others


def resolve_input(
    target: dict,
    value,
    visited: set | None = None
) -> str:
    if visited is None:
        visited = set()

    if not isinstance(value, list) or len(value) < 2:
        return str(value)

    val_type = value[0]
    val_data = value[1]

    if val_type == 1:
        if isinstance(val_data, list) and len(val_data) >= 2:
            return str(val_data[1])

        if isinstance(val_data, str):
            blocks = target.get("blocks", {})

            if isinstance(blocks, dict) and val_data in blocks:
                ref_block = blocks.get(val_data)

                if isinstance(ref_block, dict):
                    return format_block_inline(
                        target,
                        ref_block,
                        visited
                    )

            return val_data

    if val_type in (2, 3) and isinstance(val_data, str):
        blocks = target.get("blocks", {})

        if isinstance(blocks, dict) and val_data in blocks:
            ref_block = blocks.get(val_data)

            if isinstance(ref_block, dict):
                return format_block_inline(
                    target,
                    ref_block,
                    visited
                )

        return val_data

    if isinstance(val_data, list) and len(val_data) >= 2:
        return str(val_data[1])

    if isinstance(val_data, str):
        blocks = target.get("blocks", {})

        if isinstance(blocks, dict) and val_data in blocks:
            ref_block = blocks.get(val_data)

            if isinstance(ref_block, dict):
                return format_block_inline(
                    target,
                    ref_block,
                    visited
                )

        return val_data

    return str(val_data)


def format_block_inline(
    target: dict,
    block: dict,
    visited: set | None = None
) -> str:
    if visited is None:
        visited = set()

    block_id = id(block)

    if block_id in visited:
        return "[Cyclic Block Reference]"

    visited.add(block_id)

    try:
        opcode = block.get("opcode", "")

        if opcode == "procedures_call":
            mutation = block.get("mutation", {})

            proccode = (
                mutation.get("proccode", "custom_procedure")
                if isinstance(mutation, dict)
                else "custom_procedure"
            )

            inputs = block.get("inputs", {})
            args = []

            if isinstance(inputs, dict):
                for value in inputs.values():
                    args.append(
                        resolve_input(
                            target,
                            value,
                            visited.copy()
                        )
                    )

            if args:
                return f"{proccode}({', '.join(args)})"

            return f"{proccode}()"

        fields = block.get("fields", {})
        field_str = ""

        if isinstance(fields, dict) and fields:
            field_parts = []

            for fval in fields.values():
                if isinstance(fval, list) and fval:
                    field_parts.append(str(fval[0]))

            if field_parts:
                field_str = f"[{', '.join(field_parts)}]"

        inputs = block.get("inputs", {})
        input_parts = []

        if isinstance(inputs, dict):
            for iname, ival in inputs.items():
                if str(iname).startswith("SUBSTACK"):
                    continue

                input_parts.append(
                    f"{iname}={resolve_input(target, ival, visited.copy())}"
                )

        inp_str = f"({', '.join(input_parts)})" if input_parts else ""

        return f"{opcode}{field_str}{inp_str}"

    finally:
        visited.remove(block_id)


def print_block_tree(
    target: dict,
    block: dict,
    indent: int = 0,
    file=sys.stdout,
    visited: set | None = None
) -> None:
    if visited is None:
        visited = set()

    block_id = id(block)

    if block_id in visited:
        indent_str = "  " * indent
        print(
            f"{indent_str}{output.RED}[Cyclic Reference Detected]{output.RESET}",
            file=file
        )
        return

    visited.add(block_id)

    try:
        indent_str = "  " * indent
        opcode = block.get("opcode", "unknown")

        if opcode == "procedures_call":
            mutation = block.get("mutation", {})

            proccode = (
                mutation.get("proccode", "custom_procedure")
                if isinstance(mutation, dict)
                else "custom_procedure"
            )

            inputs = block.get("inputs", {})
            args = []

            if isinstance(inputs, dict):
                for name, value in inputs.items():
                    if str(name).startswith("SUBSTACK"):
                        continue

                    args.append(
                        resolve_input(
                            target,
                            value,
                            visited.copy()
                        )
                    )

            arg_str = f" ({', '.join(args)})" if args else ""

            print(
                f"{indent_str}{output.BOLD}{output.MAGENTA}CALL{output.RESET} "
                f"{proccode}{arg_str}",
                file=file
            )

        else:
            print(
                f"{indent_str}{output.BOLD}{output.CYAN}{opcode}{output.RESET}",
                file=file
            )

            fields = block.get("fields", {})

            if isinstance(fields, dict) and fields:
                for name, value in fields.items():
                    if isinstance(value, list) and value:
                        value = value[0]

                    print(
                        f"{indent_str}  "
                        f"{output.GRAY}field {name}:{output.RESET} "
                        f"{output.YELLOW}{value}{output.RESET}",
                        file=file
                    )

            inputs = block.get("inputs", {})

            if isinstance(inputs, dict) and inputs:
                for name, value in inputs.items():
                    if str(name).startswith("SUBSTACK"):
                        continue

                    resolved = resolve_input(
                        target,
                        value,
                        visited.copy()
                    )

                    print(
                        f"{indent_str}  "
                        f"{output.GRAY}input {name}:{output.RESET} "
                        f"{output.GREEN}{resolved}{output.RESET}",
                        file=file
                    )

        inputs = block.get("inputs", {})
        blocks = target.get("blocks", {})

        if isinstance(inputs, dict) and isinstance(blocks, dict):
            for name, value in inputs.items():
                if not str(name).startswith("SUBSTACK"):
                    continue

                if not isinstance(value, list) or len(value) < 2:
                    continue

                sub_id = value[1]

                if not isinstance(sub_id, str):
                    continue

                print(
                    f"{indent_str}  "
                    f"{output.BOLD}{output.YELLOW}{name}:{output.RESET}",
                    file=file
                )

                curr_sub_id = sub_id
                sub_visited = visited.copy()

                while curr_sub_id:
                    sub_block = blocks.get(curr_sub_id)

                    if not isinstance(sub_block, dict):
                        break

                    print_block_tree(
                        target,
                        sub_block,
                        indent + 2,
                        file=file,
                        visited=sub_visited
                    )

                    curr_sub_id = sub_block.get("next")

        next_id = block.get("next")

        if next_id and isinstance(blocks, dict):
            next_block = blocks.get(next_id)

            if isinstance(next_block, dict):
                print_block_tree(
                    target,
                    next_block,
                    indent,
                    file=file,
                    visited=visited
                )

    finally:
        visited.remove(block_id)


def print_script(
    target: dict,
    event: dict,
    file=sys.stdout
) -> None:
    print_block_tree(
        target,
        event,
        indent=0,
        file=file
    )


def print_custom_block_definition(
    target: dict,
    definition: dict,
    file=sys.stdout
) -> None:
    blocks = target.get("blocks", {})

    if not isinstance(blocks, dict):
        return

    prototype_id = None
    inputs = definition.get("inputs", {})

    if isinstance(inputs, dict):
        for value in inputs.values():
            if isinstance(value, list) and len(value) >= 2:
                if isinstance(value[1], str):
                    prototype_id = value[1]
                    break

    print(
        f"{output.BOLD}{output.MAGENTA}procedures_definition{output.RESET}",
        file=file
    )

    if prototype_id is None:
        print(file=file)
        return

    prototype = blocks.get(prototype_id)

    if not isinstance(prototype, dict):
        print(file=file)
        return

    mutation = prototype.get("mutation", {})

    proccode = (
        mutation.get("proccode")
        if isinstance(mutation, dict)
        else None
    )

    if proccode:
        print(
            f"  {output.GRAY}proccode:{output.RESET} "
            f"{output.YELLOW}{proccode}{output.RESET}",
            file=file
        )

    argument_names = (
        mutation.get("argumentnames")
        if isinstance(mutation, dict)
        else None
    )

    if argument_names:
        try:
            if isinstance(argument_names, str):
                argument_names = json.loads(argument_names)

            if isinstance(argument_names, list) and argument_names:
                print(
                    f"  {output.GRAY}arguments:{output.RESET}",
                    file=file
                )

                for argument in argument_names:
                    print(
                        f"    {output.GREEN}{argument}{output.RESET}",
                        file=file
                    )

        except json.JSONDecodeError:
            pass

    print(file=file)

    next_id = definition.get("next")

    if next_id:
        next_block = blocks.get(next_id)

        if isinstance(next_block, dict):
            print_block_tree(
                target,
                next_block,
                indent=1,
                file=file
            )


def render_all_target_scripts(
    target: dict,
    quiet: bool = False
) -> str:
    events = get_events(target)
    custom_blocks = get_custom_block_definitions(target)
    others = get_other_top_level_blocks(target)

    scripts = []

    for event in events:
        scripts.append(("script", event))

    for definition in custom_blocks:
        scripts.append(("custom", definition))

    for other in others:
        scripts.append(("other", other))

    buffer = io.StringIO()

    if not scripts:
        if not quiet:
            print_error("No scripts found in this target.")

        return ""

    for index, (item_type, item) in enumerate(scripts):
        if item_type == "script":
            print(
                f"{output.BOLD}Script {index + 1}{output.RESET}",
                file=buffer
            )

            print_script(
                target,
                item,
                file=buffer
            )

        elif item_type == "custom":
            custom_index = custom_blocks.index(item) + 1

            print(
                f"{output.BOLD}Custom Block {custom_index}{output.RESET}",
                file=buffer
            )

            print_custom_block_definition(
                target,
                item,
                file=buffer
            )

        else:
            other_index = others.index(item) + 1

            print(
                f"{output.BOLD}Orphan/Other Script {other_index}{output.RESET}",
                file=buffer
            )

            print_script(
                target,
                item,
                file=buffer
            )

        print(file=buffer)

    return buffer.getvalue()


def save_scripts_to_file(
    sb3_file: Path,
    target: dict,
    out_file_str: str | None
) -> None:
    if out_file_str:
        out_path = Path(out_file_str).expanduser().resolve()
    else:
        out_path = Path.cwd() / f"{sb3_file.stem}_scripts.txt"

    content_colored = render_all_target_scripts(
        target,
        quiet=False
    )

    if not content_colored:
        return

    content_clean = strip_ansi(content_colored)

    try:
        out_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        out_path.write_text(
            content_clean,
            encoding="utf-8"
        )

        print_success(
            f"Script output saved to: {out_path}"
        )

    except OSError as e:
        print_error(
            f"Could not write file {out_path}: {e}"
        )


def print_all_scripts(sb3_file: Path) -> None:
    project = get_project_data(sb3_file)
    targets = project.get("targets", [])

    if not targets:
        print_error("No targets found in this project.")
        return

    for target in targets:
        if not isinstance(target, dict):
            continue

        print(
            f"{output.BOLD}{output.CYAN}"
            f"{target.get('name', 'Unnamed')}"
            f"{output.RESET}"
        )

        print()

        content = render_all_target_scripts(
            target,
            quiet=True
        )

        if content:
            print(content, end="")
        else:
            print(
                f"  {output.GRAY}(No scripts){output.RESET}\n"
            )

        print()


def select_target_flow(sb3_file: Path) -> dict | None:
    project = get_project_data(sb3_file)

    targets = [
        t
        for t in project.get("targets", [])
        if isinstance(t, dict)
    ]

    if not targets:
        print_error("No targets found in this project.")
        return None

    selected = 0

    try:
        old_settings = termios.tcgetattr(sys.stdin)
    except termios.error:
        print_error("Interactive target selection requires a terminal.")
        return None

    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:
            clear_screen()

            print(
                f"{output.BOLD}{output.CYAN}Select Target{output.RESET}"
            )

            print(
                f"{output.GRAY}{sb3_file.name}{output.RESET}"
            )

            print()

            for index, target in enumerate(targets):
                name = target.get("name", "Unnamed")

                if index == selected:
                    print(
                        f"  {output.CYAN}❯ "
                        f"{output.BOLD}{name}{output.RESET}"
                    )
                else:
                    print(f"    {name}")

            print()

            print(
                f"{output.GRAY}Use ↑ ↓ to move, "
                f"Enter to select, Q to cancel{output.RESET}"
            )

            key = sys.stdin.read(1)

            if key == "\x1b":
                key += sys.stdin.read(2)

                if key == "\x1b[A":
                    selected = (
                        selected - 1
                    ) % len(targets)

                elif key == "\x1b[B":
                    selected = (
                        selected + 1
                    ) % len(targets)

            elif key in ("\r", "\n"):
                clear_screen()
                return targets[selected]

            elif key.lower() == "q":
                clear_screen()
                print_info("Selection cancelled.")
                return None

    finally:
        termios.tcsetattr(
            sys.stdin,
            termios.TCSADRAIN,
            old_settings
        )


def save_scripts_flow(
    sb3_file: Path,
    out_file_str: str | None
) -> None:
    project = get_project_data(sb3_file)

    targets = [
        t
        for t in project.get("targets", [])
        if isinstance(t, dict)
    ]

    if not targets:
        print_error("No targets found in this project.")
        return

    target = select_target_flow(sb3_file)

    if target is None:
        return

    clear_screen()

    print()
    save_scripts_to_file(
        sb3_file,
        target,
        out_file_str
    )
    print()



def generate_scratch_id(target: dict) -> str:
    chars = string.ascii_letters + string.digits + "!#%()*+,-./:;=?@[]^_`{|}~"

    existing_ids = set()

    blocks = target.get("blocks", {})

    if isinstance(blocks, dict):
        existing_ids.update(blocks.keys())

    variables = target.get("variables", {})

    if isinstance(variables, dict):
        existing_ids.update(variables.keys())

    lists = target.get("lists", {})

    if isinstance(lists, dict):
        existing_ids.update(lists.keys())

    broadcasts = target.get("broadcasts", {})

    if isinstance(broadcasts, dict):
        existing_ids.update(broadcasts.keys())

    while True:
        new_id = "".join(
            secrets.choice(chars)
            for _ in range(20)
        )

        if new_id not in existing_ids:
            return new_id


def is_block_reference(
    val: str,
    target: dict,
    new_block_ids: set
) -> bool:
    if not isinstance(val, str):
        return False

    blocks = target.get("blocks", {})

    if isinstance(blocks, dict) and val in blocks:
        return True

    return val in new_block_ids


def validate_input_structure(
    val,
    target: dict,
    new_block_ids: set,
    removed_ids: set
) -> bool:
    if not isinstance(val, list) or len(val) < 2:
        return False

    val_type = val[0]
    val_ref = val[1]

    if not isinstance(val_type, int):
        return False

    if val_type == 1:
        if isinstance(val_ref, list):
            return len(val_ref) >= 2

        return isinstance(val_ref, str)

    if val_type in (2, 3):
        if isinstance(val_ref, str):
            if val_ref in removed_ids:
                return False

            return is_block_reference(
                val_ref,
                target,
                new_block_ids
            )

        if isinstance(val_ref, list):
            return len(val_ref) >= 2

        return False

    if val_type in (
        4, 5, 6, 7, 8, 9,
        10, 11, 12, 13
    ):
        return True

    return False


def validate_scratch_project_structure(
    project: dict
) -> list[str]:
    errors = []

    if not isinstance(project, dict):
        return ["Project data is not a dictionary."]

    targets = project.get("targets")

    if not isinstance(targets, list):
        return ["Project missing 'targets' list."]

    target_names = set()

    for target in targets:
        if not isinstance(target, dict):
            errors.append("A target is not a dictionary.")
            continue

        tname = target.get("name", "Unnamed")

        if tname in target_names:
            errors.append(
                f"Duplicate target name '{tname}'."
            )

        target_names.add(tname)

        blocks = target.get("blocks")

        if not isinstance(blocks, dict):
            errors.append(
                f"Target '{tname}' blocks field is not a dictionary."
            )
            continue

        for block_id, block in blocks.items():
            if not isinstance(block_id, str):
                errors.append(
                    f"Target '{tname}' contains a non-string block ID."
                )

            if not isinstance(block, dict):
                errors.append(
                    f"Target '{tname}' block '{block_id}' "
                    f"is not a dictionary."
                )
                continue

            opcode = block.get("opcode")

            if not opcode or not isinstance(opcode, str):
                errors.append(
                    f"Target '{tname}' block '{block_id}' "
                    f"missing valid opcode."
                )

            next_id = block.get("next")

            if next_id is not None:
                if (
                    not isinstance(next_id, str)
                    or next_id not in blocks
                ):
                    errors.append(
                        f"Target '{tname}' block '{block_id}' "
                        f"has dangling 'next' reference '{next_id}'."
                    )

            parent_id = block.get("parent")

            if parent_id is not None:
                if (
                    not isinstance(parent_id, str)
                    or parent_id not in blocks
                ):
                    errors.append(
                        f"Target '{tname}' block '{block_id}' "
                        f"has dangling 'parent' reference '{parent_id}'."
                    )

            inputs = block.get("inputs")

            if inputs is not None and not isinstance(inputs, dict):
                errors.append(
                    f"Target '{tname}' block '{block_id}' "
                    f"inputs field is not a dictionary."
                )
                continue

            if not isinstance(inputs, dict):
                continue

            for input_name, input_val in inputs.items():
                if (
                    not isinstance(input_val, list)
                    or len(input_val) < 2
                ):
                    errors.append(
                        f"Target '{tname}' block '{block_id}' "
                        f"input '{input_name}' is malformed."
                    )
                    continue

                val_type = input_val[0]
                val_data = input_val[1]

                if str(input_name).startswith("SUBSTACK"):
                    if (
                        isinstance(val_data, str)
                        and val_data not in blocks
                    ):
                        errors.append(
                            f"Target '{tname}' block '{block_id}' "
                            f"SUBSTACK reference '{val_data}' "
                            f"does not exist."
                        )

                elif val_type in (2, 3):
                    if (
                        isinstance(val_data, str)
                        and val_data not in blocks
                    ):
                        errors.append(
                            f"Target '{tname}' block '{block_id}' "
                            f"input '{input_name}' references "
                            f"non-existent block '{val_data}'."
                        )

    return errors


def validate_ai_modification_response(
    modifications: dict,
    project: dict
) -> list[str]:
    errors = []

    if not isinstance(modifications, dict):
        return ["AI response is not a valid JSON object."]

    if modifications.get("mode") != "modify":
        errors.append("Modification response must have mode='modify'.")

    targets = project.get("targets", [])

    target_map = {
        t.get("name"): t
        for t in targets
        if isinstance(t, dict)
        and isinstance(t.get("name"), str)
    }

    add_vars = modifications.get("add_variables", [])

    if not isinstance(add_vars, list):
        errors.append("'add_variables' must be a list.")
        add_vars = []

    for v in add_vars:
        if not isinstance(v, dict):
            errors.append(
                "Invalid variable addition specification."
            )
            continue

        tname = v.get("target")
        vname = v.get("name")

        if tname not in target_map:
            errors.append(
                f"Invalid target '{tname}' for variable creation."
            )

        if (
            not isinstance(vname, str)
            or not vname.strip()
        ):
            errors.append(
                "Variable name must be a non-empty string."
            )

    add_blocks = modifications.get("add_blocks", [])

    if not isinstance(add_blocks, list):
        errors.append("'add_blocks' must be a list.")
        add_blocks = []

    new_block_ids_by_target = {}

    for b in add_blocks:
        if not isinstance(b, dict):
            errors.append(
                "Invalid block addition item."
            )
            continue

        tname = b.get("target")
        bid = b.get("id")
        bdata = b.get("block")

        if tname not in target_map:
            errors.append(
                f"Invalid target '{tname}' in add_blocks."
            )
            continue

        if (
            not isinstance(bid, str)
            or not bid
        ):
            errors.append(
                "Added block missing valid string 'id'."
            )
            continue

        existing_blocks = target_map[tname].get(
            "blocks",
            {}
        )

        if (
            isinstance(existing_blocks, dict)
            and bid in existing_blocks
        ):
            errors.append(
                f"Added block '{bid}' already exists."
            )

        target_new_ids = new_block_ids_by_target.setdefault(
            tname,
            set()
        )

        if bid in target_new_ids:
            errors.append(
                f"Duplicate added block ID '{bid}' "
                f"in target '{tname}'."
            )

        target_new_ids.add(bid)

        if not isinstance(bdata, dict):
            errors.append(
                f"Added block '{bid}' data must be an object."
            )
            continue

        opcode = bdata.get("opcode")

        if (
            not isinstance(opcode, str)
            or not opcode
        ):
            errors.append(
                f"Added block '{bid}' missing valid opcode."
            )

    remove_blocks = modifications.get(
        "remove_blocks",
        []
    )

    if not isinstance(remove_blocks, list):
        errors.append("'remove_blocks' must be a list.")
        remove_blocks = []

    removals_by_target = {}

    for r in remove_blocks:
        if not isinstance(r, dict):
            errors.append(
                "Invalid block removal item."
            )
            continue

        tname = r.get("target")
        bid = r.get("block_id")

        if tname not in target_map:
            errors.append(
                f"Invalid target '{tname}' in remove_blocks."
            )
            continue

        if (
            not isinstance(bid, str)
            or not bid
        ):
            errors.append(
                "Removal block_id must be a non-empty string."
            )
            continue

        existing_blocks = target_map[tname].get(
            "blocks",
            {}
        )

        if (
            not isinstance(existing_blocks, dict)
            or bid not in existing_blocks
        ):
            errors.append(
                f"Block '{bid}' does not exist in "
                f"target '{tname}'."
            )

        target_removals = removals_by_target.setdefault(
            tname,
            set()
        )

        if bid in target_removals:
            errors.append(
                f"Block '{bid}' is listed for removal "
                f"more than once."
            )

        target_removals.add(bid)

    update_blocks = modifications.get(
        "update_blocks",
        []
    )

    if not isinstance(update_blocks, list):
        errors.append("'update_blocks' must be a list.")
        update_blocks = []

    updates_by_target = {}

    for u in update_blocks:
        if not isinstance(u, dict):
            errors.append(
                "Invalid block update item."
            )
            continue

        tname = u.get("target")
        bid = u.get("id")
        bdata = u.get("block")

        if tname not in target_map:
            errors.append(
                f"Invalid target '{tname}' in update_blocks."
            )
            continue

        existing_blocks = target_map[tname].get(
            "blocks",
            {}
        )

        if (
            not isinstance(bid, str)
            or not bid
        ):
            errors.append(
                "Updated block missing valid string 'id'."
            )
            continue

        if (
            not isinstance(existing_blocks, dict)
            or bid not in existing_blocks
        ):
            errors.append(
                f"Block '{bid}' does not exist in "
                f"target '{tname}'."
            )

        if not isinstance(bdata, dict):
            errors.append(
                f"Updated block '{bid}' data must be an object."
            )
            continue

        target_updates = updates_by_target.setdefault(
            tname,
            set()
        )

        if bid in target_updates:
            errors.append(
                f"Block '{bid}' is listed for update "
                f"more than once."
            )

        target_updates.add(bid)

    for tname, target in target_map.items():
        existing_blocks = target.get(
            "blocks",
            {}
        )

        if not isinstance(existing_blocks, dict):
            existing_blocks = {}

        new_ids = new_block_ids_by_target.get(
            tname,
            set()
        )

        removed_ids = removals_by_target.get(
            tname,
            set()
        )

        remaining_ids = (
            set(existing_blocks.keys())
            | new_ids
        ) - removed_ids

        for b in add_blocks:
            if (
                not isinstance(b, dict)
                or b.get("target") != tname
            ):
                continue

            bid = b.get("id")
            bdata = b.get("block", {})

            if not isinstance(bdata, dict):
                continue

            next_id = bdata.get("next")

            if (
                next_id is not None
                and (
                    not isinstance(next_id, str)
                    or next_id not in remaining_ids
                )
            ):
                errors.append(
                    f"Block '{bid}' next reference "
                    f"'{next_id}' does not exist."
                )

            parent_id = bdata.get("parent")

            if (
                parent_id is not None
                and (
                    not isinstance(parent_id, str)
                    or parent_id not in remaining_ids
                )
            ):
                errors.append(
                    f"Block '{bid}' parent reference "
                    f"'{parent_id}' does not exist."
                )

            inputs = bdata.get("inputs", {})

            if not isinstance(inputs, dict):
                errors.append(
                    f"Block '{bid}' inputs must be an object."
                )
                continue

            for iname, ival in inputs.items():
                if not validate_input_structure(
                    ival,
                    target,
                    new_ids,
                    removed_ids
                ):
                    errors.append(
                        f"Block '{bid}' has invalid "
                        f"input structure for '{iname}'."
                    )
                    continue

                if (
                    isinstance(ival, list)
                    and len(ival) >= 2
                ):
                    val_type = ival[0]
                    val_ref = ival[1]

                    if (
                        val_type in (2, 3)
                        and isinstance(val_ref, str)
                        and val_ref not in remaining_ids
                    ):
                        errors.append(
                            f"Block '{bid}' input "
                            f"'{iname}' references "
                            f"non-existent block '{val_ref}'."
                        )

        for u in update_blocks:
            if (
                not isinstance(u, dict)
                or u.get("target") != tname
            ):
                continue

            bid = u.get("id")
            bdata = u.get("block", {})

            if not isinstance(bdata, dict):
                continue

            if bid in removed_ids:
                errors.append(
                    f"Block '{bid}' cannot be both "
                    f"removed and updated."
                )
                continue

            next_id = bdata.get("next")

            if (
                next_id is not None
                and (
                    not isinstance(next_id, str)
                    or next_id not in remaining_ids
                )
            ):
                errors.append(
                    f"Updated block '{bid}' next reference "
                    f"'{next_id}' does not exist."
                )

            parent_id = bdata.get("parent")

            if (
                parent_id is not None
                and (
                    not isinstance(parent_id, str)
                    or parent_id not in remaining_ids
                )
            ):
                errors.append(
                    f"Updated block '{bid}' parent reference "
                    f"'{parent_id}' does not exist."
                )

            inputs = bdata.get("inputs", {})

            if not isinstance(inputs, dict):
                errors.append(
                    f"Updated block '{bid}' inputs "
                    f"must be an object."
                )
                continue

            for iname, ival in inputs.items():
                if not validate_input_structure(
                    ival,
                    target,
                    new_ids,
                    removed_ids
                ):
                    errors.append(
                        f"Updated block '{bid}' has invalid "
                        f"input structure for '{iname}'."
                    )

    for tname, removed_ids in removals_by_target.items():
        target = target_map[tname]
        blocks = target.get("blocks", {})

        if not isinstance(blocks, dict):
            continue

        for block_id, block in blocks.items():
            if block_id in removed_ids:
                continue

            if not isinstance(block, dict):
                continue

            if block.get("next") in removed_ids:
                errors.append(
                    f"Removing block(s) would leave block "
                    f"'{block_id}' with a dangling next reference."
                )

            if block.get("parent") in removed_ids:
                errors.append(
                    f"Removing block(s) would leave block "
                    f"'{block_id}' with a dangling parent reference."
                )

            inputs = block.get("inputs", {})

            if not isinstance(inputs, dict):
                continue

            for input_name, input_val in inputs.items():
                if (
                    isinstance(input_val, list)
                    and len(input_val) >= 2
                    and input_val[0] in (2, 3)
                    and isinstance(input_val[1], str)
                    and input_val[1] in removed_ids
                ):
                    errors.append(
                        f"Removing block(s) would leave "
                        f"block '{block_id}' input "
                        f"'{input_name}' dangling."
                    )

                if (
                    str(input_name).startswith("SUBSTACK")
                    and isinstance(input_val, list)
                    and len(input_val) >= 2
                    and isinstance(input_val[1], str)
                    and input_val[1] in removed_ids
                ):
                    errors.append(
                        f"Removing block(s) would leave "
                        f"block '{block_id}' SUBSTACK "
                        f"'{input_name}' dangling."
                    )

    return errors


def apply_project_changes(
    project_data: dict,
    modifications: dict
) -> tuple[dict, dict]:
    updated = copy.deepcopy(project_data)

    stats = {
        "variables_added": 0,
        "blocks_added": 0,
        "blocks_updated": 0,
        "blocks_removed": 0
    }

    targets = updated.get("targets", [])

    target_map = {
        t.get("name"): t
        for t in targets
        if isinstance(t, dict)
        and "name" in t
    }

    for var_def in modifications.get(
        "add_variables",
        []
    ):
        if not isinstance(var_def, dict):
            continue

        tname = var_def.get("target")
        vname = var_def.get("name")
        vval = var_def.get("value", 0)

        if (
            tname not in target_map
            or not isinstance(vname, str)
            or not vname.strip()
        ):
            continue

        target = target_map[tname]

        vars_dict = target.setdefault(
            "variables",
            {}
        )

        if not isinstance(vars_dict, dict):
            vars_dict = {}
            target["variables"] = vars_dict

        already_exists = any(
            isinstance(v, list)
            and len(v) > 0
            and v[0] == vname
            for v in vars_dict.values()
        )

        if not already_exists:
            var_id = generate_scratch_id(target)
            vars_dict[var_id] = [
                vname,
                vval
            ]

            stats["variables_added"] += 1

    for rem_def in modifications.get(
        "remove_blocks",
        []
    ):
        if not isinstance(rem_def, dict):
            continue

        tname = rem_def.get("target")
        bid = rem_def.get("block_id")

        if tname not in target_map or not bid:
            continue

        target = target_map[tname]

        blocks = target.get(
            "blocks",
            {}
        )

        if not isinstance(blocks, dict):
            continue

        if bid not in blocks:
            continue

        block_to_remove = blocks.get(bid)

        if isinstance(block_to_remove, dict):
            next_id = block_to_remove.get("next")

            previous_blocks = [
                block
                for block in blocks.values()
                if isinstance(block, dict)
                and block.get("next") == bid
            ]

            for previous in previous_blocks:
                previous["next"] = next_id

            for block in blocks.values():
                if not isinstance(block, dict):
                    continue

                if block.get("parent") == bid:
                    block["parent"] = None

                inputs = block.get("inputs", {})

                if not isinstance(inputs, dict):
                    continue

                for input_name, input_val in list(
                    inputs.items()
                ):
                    if (
                        isinstance(input_val, list)
                        and len(input_val) >= 2
                        and input_val[0] in (2, 3)
                        and input_val[1] == bid
                    ):
                        inputs[input_name] = [
                            1,
                            [
                                10,
                                ""
                            ]
                        ]

                    elif (
                        str(input_name).startswith("SUBSTACK")
                        and isinstance(input_val, list)
                        and len(input_val) >= 2
                        and input_val[1] == bid
                    ):
                        inputs[input_name] = [
                            2,
                            None
                        ]

        del blocks[bid]

        stats["blocks_removed"] += 1

    for add_def in modifications.get(
        "add_blocks",
        []
    ):
        if not isinstance(add_def, dict):
            continue

        tname = add_def.get("target")
        bid = add_def.get("id")
        bdata = add_def.get("block")

        if (
            tname not in target_map
            or not isinstance(bid, str)
            or not bid
            or not isinstance(bdata, dict)
        ):
            continue

        target = target_map[tname]

        blocks = target.setdefault(
            "blocks",
            {}
        )

        if not isinstance(blocks, dict):
            blocks = {}
            target["blocks"] = blocks

        if bid in blocks:
            continue

        blocks[bid] = copy.deepcopy(bdata)

        stats["blocks_added"] += 1

    for up_def in modifications.get(
        "update_blocks",
        []
    ):
        if not isinstance(up_def, dict):
            continue

        tname = up_def.get("target")
        bid = up_def.get("id")
        bdata = up_def.get("block")

        if (
            tname not in target_map
            or not isinstance(bid, str)
            or not isinstance(bdata, dict)
        ):
            continue

        target = target_map[tname]

        blocks = target.get(
            "blocks",
            {}
        )

        if (
            isinstance(blocks, dict)
            and bid in blocks
            and isinstance(blocks[bid], dict)
        ):
            blocks[bid].update(
                copy.deepcopy(bdata)
            )

            stats["blocks_updated"] += 1

    updated = normalize_project_blocks(updated)
    return updated, stats


def create_safe_backup(sb3_file: Path) -> Path:
    backup_file = sb3_file.with_suffix(
        ".sb3.bak"
    )

    if backup_file.exists():
        counter = 1

        while True:
            candidate = sb3_file.with_suffix(
                f".sb3.bak.{counter}"
            )

            if not candidate.exists():
                backup_file = candidate
                break

            counter += 1

    shutil.copy2(
        sb3_file,
        backup_file
    )

    return backup_file


def save_project_atomic(
    sb3_file: Path,
    new_project_data: dict
) -> None:
    new_project_data = normalize_project_blocks(new_project_data)
    temp_file = sb3_file.with_suffix(".tmp.sb3")

    try:
        with zipfile.ZipFile(
            sb3_file,
            "r"
        ) as orig_zip:
            with zipfile.ZipFile(
                temp_file,
                "w",
                compression=zipfile.ZIP_DEFLATED
            ) as new_zip:

                for item in orig_zip.infolist():
                    if item.filename != "project.json":
                        new_zip.writestr(
                            item,
                            orig_zip.read(item.filename)
                        )

                project_bytes = json.dumps(
                    new_project_data,
                    indent=2,
                    ensure_ascii=False
                ).encode("utf-8")

                new_zip.writestr(
                    "project.json",
                    project_bytes
                )

        temp_project = get_project_data(
            temp_file
        )

        val_errors = validate_scratch_project_structure(
            temp_project
        )

        if val_errors:
            raise ValueError(
                "Final saved project package validation failed: "
                + "; ".join(val_errors)
            )

        backup_file = create_safe_backup(
            sb3_file
        )

        os.replace(
            temp_file,
            sb3_file
        )

        print_success(
            f"Project updated safely: {sb3_file.name}"
        )

        print_info(
            f"Backup preserved at: {backup_file.name}"
        )

    except Exception as e:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass

        raise RuntimeError(
            f"Atomic save failed: {e}"
        )


def handle_ai_api_interactive(
    config: dict
) -> None:
    print_info(
        "Interactive API Key Configuration"
    )

    print_info(
        "Input will not be echoed to the terminal."
    )

    try:
        key = getpass.getpass(
            "Enter AI API Key: "
        ).strip()

        if not key:
            print_error(
                "API key cannot be empty."
            )
            return

        config["api_key"] = key

        save_config(config)

        print_success(
            f"API key updated to: {mask_api_key(key)}"
        )

    except Exception as e:
        safe_msg = sanitize_error_message(str(e), config.get("api_key"))
        print_error(
            f"Could not read API key interactively: {safe_msg}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "CatScan - Linux CLI tool for inspecting, "
            "extracting, and AI-modifying Scratch .sb3 projects."
        ),
        add_help=False
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="Path to Scratch .sb3 file"
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    args = parser.parse_args()

    if not supports_color(
        args.no_color
    ):
        disable_colors()

    config = load_config()

    selected_file = None

    if args.file:
        try:
            selected_file = select_file(
                args.file
            )

        except Exception as e:
            print_error(
                str(e)
            )
            sys.exit(1)

    clear_screen()

    print_banner()

    print_selected(
        selected_file
    )

    while True:
        try:
            prompt_str = (
                f"{rl_prompt_color(output.BOLD + output.CYAN)}"
                f"catscan"
                f"{rl_prompt_color(output.RESET)} > "
            )

            user_input = input(
                prompt_str
            ).strip()

        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)

        if not user_input:
            continue

        parts = user_input.split()

        cmd = parts[0].lower()

        if cmd in ("exit", "quit"):
            sys.exit(0)

        elif cmd == "clear":
            clear_screen()
            print_banner()
            print_selected(
                selected_file
            )

        elif cmd == "version":
            print(
                f"CatScan {VERSION}"
            )

        elif cmd == "help":
            print_help()

        elif cmd == "select":
            if len(parts) < 2:
                print_error(
                    "Usage: select <file.sb3>"
                )
            else:
                try:
                    selected_file = select_file(
                        " ".join(parts[1:])
                    )

                    print_success(
                        f"Selected project: "
                        f"{selected_file.name}"
                    )

                except Exception as e:
                    print_error(
                        str(e)
                    )

        elif cmd == "inspect":
            req_file = require_selected(
                selected_file
            )

            if req_file:
                try:
                    inspect_sb3(
                        req_file
                    )

                except Exception as e:
                    print_error(
                        str(e)
                    )

        elif cmd == "extract":
            req_file = require_selected(
                selected_file
            )

            if req_file:
                out_dir = (
                    req_file.parent
                    / f"{req_file.stem}_extracted"
                )

                try:
                    extract_sb3(
                        req_file,
                        out_dir
                    )

                except Exception as e:
                    print_error(
                        str(e)
                    )

        elif cmd == "script":
            req_file = require_selected(
                selected_file
            )

            if req_file:
                if (
                    len(parts) >= 2
                    and parts[1].lower() == "save"
                ):
                    out_file_str = (
                        " ".join(parts[2:])
                        if len(parts) > 2
                        else None
                    )

                    save_scripts_flow(
                        req_file,
                        out_file_str
                    )

                else:
                    target = select_target_flow(
                        req_file
                    )

                    if target:
                        print_section(
                            "Scripts for target: "
                            f"{target.get('name', 'Unnamed')}"
                        )

                        content = render_all_target_scripts(
                            target
                        )

                        if content:
                            print(
                                content
                            )

        elif cmd == "ai":
            if len(parts) == 1:
                print_error(
                    "Usage: ai <prompt> | "
                    "ai api | "
                    "ai url <url> | "
                    "ai model <model> | "
                    "ai timeout <seconds> | "
                    "ai max-tokens <amount> | "
                    "ai config"
                )
                continue

            subcmd = parts[1].lower()

            if subcmd == "api":
                if len(parts) == 2:
                    handle_ai_api_interactive(
                        config
                    )

                else:
                    key = " ".join(
                        parts[2:]
                    ).strip()

                    if not key:
                        print_error(
                            "API key cannot be empty."
                        )
                        continue

                    config["api_key"] = key

                    save_config(
                        config
                    )

                    print_success(
                        "API key updated."
                    )

                    print_info(
                        "Interactive input "
                        "('ai api') is safer than "
                        "terminal commands."
                    )

            elif subcmd == "url":
                if len(parts) < 3:
                    print_error(
                        "Usage: ai url <url>"
                    )

                else:
                    new_url = " ".join(
                        parts[2:]
                    ).strip()

                    if validate_url(new_url):
                        config["url"] = new_url

                        save_config(
                            config
                        )

                        print_success(
                            f"AI API URL set to: "
                            f"{new_url}"
                        )

                    else:
                        print_error(
                            "Invalid API URL format. "
                            "URL must start with "
                            "http:// or https://"
                        )

            elif subcmd == "model":
                if len(parts) < 3:
                    print_error(
                        "Usage: ai model <model>"
                    )

                else:
                    new_model = " ".join(
                        parts[2:]
                    ).strip()

                    if new_model:
                        config["model"] = new_model

                        save_config(
                            config
                        )

                        print_success(
                            f"AI Model set to: "
                            f"{new_model}"
                        )

                    else:
                        print_error(
                            "Model name cannot be empty."
                        )

            elif subcmd == "config":
                print_section(
                    "AI Configuration"
                )

                print(
                    "  API Key: "
                    f"{mask_api_key(config.get('api_key', ''))}"
                )

                print(
                    "  URL:     "
                    f"{config.get('url', DEFAULT_API_URL)}"
                )

                print(
                    "  Model:   "
                    f"{config.get('model', DEFAULT_MODEL)}"
                )
                print(
                    "  Timeout: "
                    f"{config.get('timeout', 60)} seconds"
                )
                print(
                    "  Max Tokens: "
                    f"{config.get('max_tokens', 8192)}"
                )

                print()
            elif subcmd == "timeout":
                if len(parts) < 3:
                    print_error("Usage: ai timeout <seconds>")
                else:
                    try:
                        new_timeout = int(parts[2])

                        if not 1 <= new_timeout <= 600:
                            print_error(
                                "Timeout must be between 1 and 600 seconds."
                            )
                            continue

                        config["timeout"] = new_timeout
                        save_config(config)

                        print_success(
                            f"AI timeout set to: {new_timeout} seconds"
                        )

                    except ValueError:
                        print_error(
                            "Timeout must be a whole number of seconds."
                        )
            elif subcmd == "max-tokens":
                if len(parts) < 3:
                    print_error("Usage: ai max-tokens <amount>")
                else:
                    try:
                        new_max_tokens = int(parts[2])

                        if not 1 <= new_max_tokens <= 65536:
                            print_error(
                                "max-tokens must be between 1 and 65536."
                            )
                            continue

                        config["max_tokens"] = new_max_tokens
                        save_config(config)

                        print_success(
                            f"AI max tokens set to: {new_max_tokens}"
                        )

                    except ValueError:
                        print_error(
                            "max-tokens must be a whole number."
                        )

            else:
                req_file = require_selected(
                    selected_file
                )

                if req_file:
                    ai_prompt = " ".join(
                        parts[1:]
                    ).strip()

                    ai_command_flow(
                        req_file,
                        ai_prompt,
                        config
                    )

        else:
            print_error(
                f"Unknown command: {cmd}. "
                "Type 'help' for available commands."
            )


if __name__ == "__main__":
    main()