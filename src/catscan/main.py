import argparse
import io
import json
import os
import readline
import shutil
import sys
import termios
import tty
import zipfile
from pathlib import Path


VERSION = "0.2.2"

RESET = "\033[0m"
BOLD = "\033[1m"

CYAN = "\033[36m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
WHITE = "\033[37m"
GRAY = "\033[90m"


def clear_screen() -> None:
    os.system("clear")


def print_banner() -> None:
    print(f"{BOLD}{CYAN}")
    print("  ██████╗ █████╗ ████████╗███████╗ ██████╗ █████╗ ███╗   ██╗")
    print(" ██╔════╝██╔══██╗╚══██╔══╝██╔════╝██╔════╝██╔══██╗████╗  ██║")
    print(" ██║     ███████║   ██║   ███████╗██║     ███████║██╔██╗ ██║")
    print(" ██║     ██╔══██║   ██║   ╚════██║██║     ██╔══██║██║╚██╗██║")
    print(" ╚██████╗██║  ██║   ██║   ███████╗╚██████╗██║  ██║██║ ╚████║")
    print("  ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝")
    print(f"{RESET}")
    print(f"  {BOLD}{WHITE}CatScan {VERSION}{RESET}")
    print(f"  {GRAY}Scratch project development toolkit{RESET}")
    print()


def print_success(message: str) -> None:
    print(f"{GREEN}✓{RESET} {message}")


def print_error(message: str) -> None:
    print(f"{RED}✗{RESET} {message}")


def print_info(message: str) -> None:
    print(f"{CYAN}•{RESET} {message}")


def print_section(title: str) -> None:
    print()
    print(f"{BOLD}{BLUE}{title}{RESET}")


def strip_ansi(text: str) -> str:
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def get_project_data(sb3_file: Path) -> dict:
    if not sb3_file.exists():
        raise FileNotFoundError(f"File not found: {sb3_file}")

    if not sb3_file.is_file():
        raise ValueError(f"Not a file: {sb3_file}")

    if sb3_file.suffix.lower() != ".sb3":
        raise ValueError("File must be a .sb3 file")

    with zipfile.ZipFile(sb3_file, "r") as archive:
        if "project.json" not in archive.namelist():
            raise ValueError("project.json was not found in the .sb3 file")

        with archive.open("project.json") as project_file:
            return json.load(project_file)


def supports_color(no_color_flag: bool) -> bool:
    if no_color_flag:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    if not sys.stdout.isatty():
        return False
    return True


def disable_colors() -> None:
    global RESET, BOLD, CYAN, BLUE, GREEN, YELLOW, MAGENTA, RED, WHITE, GRAY
    RESET = BOLD = CYAN = BLUE = GREEN = YELLOW = MAGENTA = RED = WHITE = GRAY = ""

def extract_sb3(sb3_file: Path, output_dir: Path) -> None:
    if not sb3_file.exists():
        raise FileNotFoundError(f"File not found: {sb3_file}")

    if sb3_file.suffix.lower() != ".sb3":
        raise ValueError("File must be a .sb3 file")

    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"Output path exists and is not a directory: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(sb3_file, "r") as archive:
        archive.extractall(output_dir)

    print_success(f"Extracted: {sb3_file}")
    print_info(f"Output directory: {output_dir}")


def inspect_sb3(sb3_file: Path) -> None:
    if not sb3_file.exists():
        raise FileNotFoundError(f"File not found: {sb3_file}")

    if sb3_file.suffix.lower() != ".sb3":
        raise ValueError("File must be a .sb3 file")

    with zipfile.ZipFile(sb3_file, "r") as archive:
        if "project.json" not in archive.namelist():
            raise ValueError("project.json was not found in the .sb3 file")

        with archive.open("project.json") as project_file:
            project = json.load(project_file)

    sound_count = 0
    stage_count = 0
    sprite_count = 0
    script_count = 0
    block_count = 0
    variable_count = 0
    list_count = 0
    broadcast_count = 0
    costume_count = 0

    for target in project["targets"]:
        if target["isStage"]:
            stage_count += 1
        else:
            sprite_count += 1

        for block in target["blocks"].values():
            if not isinstance(block, dict):
                continue

            if block.get("topLevel", False):
                script_count += 1

            if not block.get("shadow", False):
                block_count += 1

        variable_count += len(target["variables"])
        list_count += len(target["lists"])
        broadcast_count += len(target["broadcasts"])
        costume_count += len(target["costumes"])
        sound_count += len(target["sounds"])

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

    for target in project["targets"]:
        print(f'  {target["name"]}')

        if target["isStage"]:
            print(f'    Global Variables: {len(target["variables"])}')
        else:
            print(f'    Private Variables: {len(target["variables"])}')

        for variable in target["variables"].values():
            print(f"      Variable: {variable[0]}")

        print(f'    Costumes: {len(target["costumes"])}')

        for costume in target["costumes"]:
            print(f'      Costume: {costume["name"]}')

        print(f'    Sounds: {len(target["sounds"])}')

        for sound in target["sounds"]:
            print(f"      Sound: {sound['name']}")

        target_block_count = sum(
            1
            for block in target["blocks"].values()
            if isinstance(block, dict) and not block.get("shadow", False)
        )

        print(f"    Blocks: {target_block_count}")
        print()

    print("ASSETS")
    print(f"  Costumes: {costume_count}")
    print(f"  Sounds: {sound_count}")


def print_help() -> None:
    print()
    print(f"{BOLD}{CYAN}CatScan Commands{RESET}")
    print()

    commands = [
        ("select <file>", "Select a Scratch project"),
        ("inspect", "Inspect the selected project"),
        ("extract", "Extract the selected .sb3 file"),
        ("script", "Select a target for script inspection"),
        ("script save", "Save target scripts to auto-named file"),
        ("script save <file>", "Save target scripts to specified file"),
        ("clear", "Clear the terminal"),
        ("version", "Show CatScan version"),
        ("help", "Show this help message"),
        ("exit", "Exit CatScan"),
        ("quit", "Exit CatScan"),
    ]

    for command, description in commands:
        print(
            f"  {GREEN}{command:<22}{RESET}"
            f"{GRAY}{description}{RESET}"
        )

    print()


def print_selected(selected_file: Path | None) -> None:
    print()

    if selected_file is None:
        print(f"  {GRAY}No project selected{RESET}")
    else:
        print(
            f"  {GRAY}Selected:{RESET} "
            f"{GREEN}{selected_file.name}{RESET}"
        )

    print()


def require_selected(selected_file: Path | None) -> Path | None:
    if selected_file is None:
        print()
        print_error("You need to select a file first.")
        print()
        print(f"  {GRAY}Use:{RESET}")
        print(f"  {GREEN}select <file.sb3>{RESET}")
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


def get_events(target: dict) -> list[dict]:
    events = []

    for block in target["blocks"].values():
        if not isinstance(block, dict):
            continue

        if block.get("topLevel") and block.get("opcode", "").startswith("event_"):
            events.append(block)

    return events


def get_custom_block_definitions(target: dict) -> list[dict]:
    definitions = []

    for block in target["blocks"].values():
        if not isinstance(block, dict):
            continue

        if block.get("topLevel") and block.get("opcode") == "procedures_definition":
            definitions.append(block)

    return definitions


def resolve_input(target: dict, value) -> str:
    if not isinstance(value, list):
        return str(value)

    if len(value) < 2:
        return str(value)

    val_type = value[0]
    val_data = value[1]

    if val_type == 1 and isinstance(val_data, list):
        if len(val_data) >= 2:
            return str(val_data[1])

    if val_type in (2, 3) and isinstance(val_data, str):
        ref_block = target["blocks"].get(val_data)
        if ref_block and isinstance(ref_block, dict):
            return format_block_inline(target, ref_block)

    if isinstance(val_data, list) and len(val_data) >= 2:
        return str(val_data[1])

    if isinstance(val_data, str):
        ref_block = target["blocks"].get(val_data)
        if ref_block and isinstance(ref_block, dict):
            return format_block_inline(target, ref_block)
        return val_data

    return str(val_data)


def format_block_inline(target: dict, block: dict) -> str:
    opcode = block.get("opcode", "")

    if opcode == "procedures_call":
        proccode = block.get("mutation", {}).get("proccode", "custom_procedure")
        inputs = block.get("inputs", {})
        args = []
        for name, val in inputs.items():
            args.append(resolve_input(target, val))
        if args:
            return f"{proccode}({', '.join(args)})"
        return f"{proccode}()"

    fields = block.get("fields", {})
    field_str = ""
    if fields:
        field_parts = []
        for fname, fval in fields.items():
            if isinstance(fval, list) and fval:
                field_parts.append(str(fval[0]))
        if field_parts:
            field_str = f"[{', '.join(field_parts)}]"

    inputs = block.get("inputs", {})
    input_parts = []
    for iname, ival in inputs.items():
        if iname.startswith("SUBSTACK"):
            continue
        input_parts.append(f"{iname}={resolve_input(target, ival)}")

    inp_str = f"({', '.join(input_parts)})" if input_parts else ""

    return f"{opcode}{field_str}{inp_str}"


def print_block_tree(target: dict, block: dict, indent: int = 0, file=sys.stdout) -> None:
    indent_str = "  " * indent
    opcode = block.get("opcode", "unknown")

    if opcode == "procedures_call":
        mutation = block.get("mutation", {})
        proccode = mutation.get("proccode", "custom_procedure")
        inputs = block.get("inputs", {})
        args = []
        for name, value in inputs.items():
            if name.startswith("SUBSTACK"):
                continue
            args.append(resolve_input(target, value))
        arg_str = f" ({', '.join(args)})" if args else ""
        print(f"{indent_str}{BOLD}{MAGENTA}CALL{RESET} {proccode}{arg_str}", file=file)
    else:
        print(f"{indent_str}{BOLD}{CYAN}{opcode}{RESET}", file=file)

        fields = block.get("fields", {})
        if fields:
            for name, value in fields.items():
                if isinstance(value, list) and value:
                    value = value[0]
                print(f"{indent_str}  {GRAY}field {name}:{RESET} {YELLOW}{value}{RESET}", file=file)

        inputs = block.get("inputs", {})
        if inputs:
            for name, value in inputs.items():
                if name.startswith("SUBSTACK"):
                    continue
                resolved = resolve_input(target, value)
                print(f"{indent_str}  {GRAY}input {name}:{RESET} {GREEN}{resolved}{RESET}", file=file)

    inputs = block.get("inputs", {})
    for name, value in inputs.items():
        if name.startswith("SUBSTACK") and isinstance(value, list) and len(value) >= 2:
            sub_id = value[1]
            if isinstance(sub_id, str):
                print(f"{indent_str}  {BOLD}{YELLOW}{name}:{RESET}", file=file)
                curr_sub_id = sub_id
                while curr_sub_id:
                    sub_block = target["blocks"].get(curr_sub_id)
                    if not isinstance(sub_block, dict):
                        break
                    print_block_tree(target, sub_block, indent + 2, file=file)
                    curr_sub_id = sub_block.get("next")

    next_id = block.get("next")
    if next_id:
        next_block = target["blocks"].get(next_id)
        if isinstance(next_block, dict):
            print_block_tree(target, next_block, indent, file=file)


def print_script(target: dict, event: dict, file=sys.stdout) -> None:
    print_block_tree(target, event, indent=0, file=file)


def print_custom_block_definition(target: dict, definition: dict, file=sys.stdout) -> None:
    blocks = target["blocks"]

    prototype_id = None

    inputs = definition.get("inputs", {})

    for value in inputs.values():
        if isinstance(value, list) and len(value) >= 2:
            if isinstance(value[1], str):
                prototype_id = value[1]
                break

    print(f"{BOLD}{MAGENTA}procedures_definition{RESET}", file=file)

    if prototype_id is None:
        print(file=file)
        return

    prototype = blocks.get(prototype_id)

    if not isinstance(prototype, dict):
        print(file=file)
        return

    mutation = prototype.get("mutation", {})
    proccode = mutation.get("proccode")

    if proccode:
        print(f"  {GRAY}proccode:{RESET} {YELLOW}{proccode}{RESET}", file=file)

    argument_names = mutation.get("argumentnames")

    if argument_names:
        try:
            argument_names = json.loads(argument_names)

            if argument_names:
                print(f"  {GRAY}arguments:{RESET}", file=file)

                for argument in argument_names:
                    print(f"    {GREEN}{argument}{RESET}", file=file)
        except json.JSONDecodeError:
            pass

    print(file=file)

    next_id = definition.get("next")
    if next_id:
        next_block = blocks.get(next_id)
        if isinstance(next_block, dict):
            print_block_tree(target, next_block, indent=1, file=file)


def render_all_target_scripts(target: dict) -> str:
    events = get_events(target)
    custom_blocks = get_custom_block_definitions(target)

    scripts = []
    for event in events:
        scripts.append(("script", event))
    for definition in custom_blocks:
        scripts.append(("custom", definition))

    buffer = io.StringIO()

    if not scripts:
        print_error("No scripts found in this target.")
        return ""

    for index, (item_type, item) in enumerate(scripts):
        if item_type == "script":
            print(f"{BOLD}Script {index + 1}{RESET}", file=buffer)
            print_script(target, item, file=buffer)
        else:
            custom_index = custom_blocks.index(item) + 1
            print(f"{BOLD}Custom Block {custom_index}{RESET}", file=buffer)
            print_custom_block_definition(target, item, file=buffer)

        print(file=buffer)

    return buffer.getvalue()


def save_scripts_to_file(sb3_file: Path, target: dict, out_file_str: str | None) -> None:
    if out_file_str:
        out_path = Path(out_file_str).expanduser().resolve()
    else:
        out_path = Path.cwd() / f"{sb3_file.stem}_scripts.txt"

    content_colored = render_all_target_scripts(target)
    if not content_colored:
        return

    content_clean = strip_ansi(content_colored)

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content_clean, encoding="utf-8")
        print_success(f"Script output saved to: {out_path}")
    except Exception as e:
        print_error(f"Could not write file {out_path}: {e}")


def print_all_scripts(sb3_file: Path) -> None:
    project = get_project_data(sb3_file)
    targets = project["targets"]

    if not targets:
        print_error("No targets found in this project.")
        return

    for target in targets:
        print(f"{BOLD}{CYAN}{target['name']}{RESET}")
        print()

        content = render_all_target_scripts(target)

        if content:
            print(content, end="")

        print()

def save_scripts_flow(sb3_file: Path, out_file_str: str | None) -> None:
    project = get_project_data(sb3_file)
    targets = project["targets"]

    if not targets:
        print_error("No targets found in this project.")
        return

    selected = 0
    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:
            clear_screen()

            print(f"{BOLD}{CYAN}Select Target for Saving{RESET}")
            print(f"{GRAY}{sb3_file.name}{RESET}")
            print()

            for index, target in enumerate(targets):
                if index == selected:
                    print(
                        f"  {CYAN}❯ {BOLD}{target['name']}{RESET}"
                    )
                else:
                    print(f"    {target['name']}")

            print()
            print(
                f"{GRAY}Use ↑ ↓ to move, "
                f"Enter to select, Q to cancel{RESET}"
            )

            key = sys.stdin.read(1)

            if key == "\x1b":
                key += sys.stdin.read(2)

                if key == "\x1b[A":
                    selected = (selected - 1) % len(targets)

                elif key == "\x1b[B":
                    selected = (selected + 1) % len(targets)

            elif key in ("\r", "\n"):
                target = targets[selected]

                clear_screen()

                print()
                save_scripts_to_file(sb3_file, target, out_file_str)
                print()

                return

            elif key.lower() == "q":
                clear_screen()
                print_info("Target selection cancelled.")
                print()
                return

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def select_script(target: dict) -> None:
    events = get_events(target)
    custom_blocks = get_custom_block_definitions(target)

    scripts = []

    for event in events:
        scripts.append(("script", event))

    for definition in custom_blocks:
        scripts.append(("custom", definition))

    if not scripts:
        print_error("No scripts found in this target.")
        return

    selected = 0
    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:
            clear_screen()

            print(f"{BOLD}{CYAN}Select Script{RESET}")
            print()

            menu_items = [("all", None)] + scripts

            for index, (script_type, script) in enumerate(menu_items):
                if script_type == "all":
                    label = "All scripts"
                elif script_type == "script":
                    label = f"Script {scripts.index((script_type, script)) + 1}"
                else:
                    # Haetaan custom blockin nimi (proccode)
                    proccode = None
                    inputs = script.get("inputs", {})
                    for value in inputs.values():
                        if isinstance(value, list) and len(value) >= 2 and isinstance(value[1], str):
                            proto = target["blocks"].get(value[1])
                            if isinstance(proto, dict):
                                proccode = proto.get("mutation", {}).get("proccode")
                            break
                    
                    if proccode:
                        label = f"define {proccode}"
                    else:
                        label = f"Custom Block {custom_blocks.index(script) + 1}"

                if index == selected:
                    print(
                        f"  {CYAN}❯ {BOLD}{label}{RESET}"
                    )
                else:
                    print(f"    {label}")

            print()
            print(
                f"{GRAY}Use ↑ ↓ to move, "
                f"Enter to select, Q to cancel{RESET}"
            )

            key = sys.stdin.read(1)

            if key == "\x1b":
                key += sys.stdin.read(2)

                if key == "\x1b[A":
                    selected = (selected - 1) % len(menu_items)

                elif key == "\x1b[B":
                    selected = (selected + 1) % len(menu_items)

            elif key in ("\r", "\n"):
                script_type, script = menu_items[selected]

                clear_screen()

                if script_type == "all":
                    for index, (item_type, item) in enumerate(scripts):
                        if item_type == "script":
                            print(f"{BOLD}Script {index + 1}{RESET}")
                            print_script(target, item)
                        else:
                            print_custom_block_definition(target, item)

                        print()

                elif script_type == "script":
                    print_script(target, script)

                elif script_type == "custom":
                    print_custom_block_definition(target, script)

                print()
                print(f"{GRAY}Press Enter to return...{RESET}")

                while True:
                    key = sys.stdin.read(1)

                    if key in ("\r", "\n"):
                        break

                return

            elif key.lower() == "q":
                clear_screen()
                print_info("Script selection cancelled.")
                print()
                return

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def select_target(sb3_file: Path) -> None:
    project = get_project_data(sb3_file)
    targets = project["targets"]

    if not targets:
        print_error("No targets found in this project.")
        return

    selected = 0
    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:
            clear_screen()

            print(f"{BOLD}{CYAN}Select Target{RESET}")
            print(f"{GRAY}{sb3_file.name}{RESET}")
            print()

            for index, target in enumerate(targets):
                if index == selected:
                    print(
                        f"  {CYAN}❯ {BOLD}{target['name']}{RESET}"
                    )
                else:
                    print(f"    {target['name']}")

            print()
            print(
                f"{GRAY}Use ↑ ↓ to move, "
                f"Enter to select, Q to cancel{RESET}"
            )

            key = sys.stdin.read(1)

            if key == "\x1b":
                key += sys.stdin.read(2)

                if key == "\x1b[A":
                    selected = (selected - 1) % len(targets)

                elif key == "\x1b[B":
                    selected = (selected + 1) % len(targets)

            elif key in ("\r", "\n"):
                target = targets[selected]

                clear_screen()

                print()
                print_success(f"Selected target: {target['name']}")
                print()

                select_script(target)

                return

            elif key.lower() == "q":
                clear_screen()
                print_info("Target selection cancelled.")
                print()
                return

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def execute_command(
    command: str,
    arguments: list[str],
    selected_file: Path | None
) -> Path | None:
    command = command.lower()

    if command == "help":
        print_help()
        return selected_file

    if command == "version":
        print()
        print(f"{BOLD}{CYAN}CatScan {VERSION}{RESET}")
        print()
        return selected_file

    if command in ("exit", "quit"):
        raise SystemExit

    if command == "clear":
        clear_screen()
        print_banner()
        print_selected(selected_file)
        return selected_file

    if command == "select":
        if len(arguments) != 1:
            print_error("Usage: select <file.sb3>")
            return selected_file

        try:
            selected_file = select_file(arguments[0])
            print()
            print_success(f"Selected: {selected_file.name}")
            print()
        except (FileNotFoundError, ValueError) as error:
            print()
            print_error(str(error))
            print()

        return selected_file

    if command == "inspect":
        if arguments:
            print_error("Usage: inspect")
            return selected_file

        file = require_selected(selected_file)

        if file is not None:
            try:
                inspect_sb3(file)
            except (FileNotFoundError, ValueError, zipfile.BadZipFile) as error:
                print_error(str(error))

        return selected_file

    if command == "extract":
        if len(arguments) > 1:
            print_error("Usage: extract [output]")
            return selected_file

        file = require_selected(selected_file)

        if file is not None:
            if arguments:
                output_dir = Path(arguments[0]).expanduser()
            else:
                output_dir = Path.cwd() / file.stem

            try:
                extract_sb3(file, output_dir)
            except (FileNotFoundError, ValueError, zipfile.BadZipFile) as error:
                print_error(str(error))

        return selected_file

    if command == "script":
        if arguments and arguments[0].lower() == "save":
            if len(arguments) > 2:
                print_error("Usage: script save [file]")
                return selected_file

            file = require_selected(selected_file)

            if file is not None:
                out_file = arguments[1] if len(arguments) == 2 else None
                try:
                    save_scripts_flow(file, out_file)
                except (
                    FileNotFoundError,
                    ValueError,
                    zipfile.BadZipFile
                ) as error:
                    print_error(str(error))

            return selected_file

        if arguments:
            print_error("Usage: script OR script save [file]")
            return selected_file

        file = require_selected(selected_file)

        if file is not None:
            try:
                select_target(file)
            except (
                FileNotFoundError,
                ValueError,
                zipfile.BadZipFile
            ) as error:
                print_error(str(error))

        return selected_file

    print()
    print_error(f"Unknown command: {command}")
    print(f"  {GRAY}Type 'help' to see available commands.{RESET}")
    print()

    return selected_file


def shell() -> None:
    clear_screen()
    print_banner()
    print_selected(None)

    selected_file = None

    while True:
        try:
            if selected_file is None:
                prompt = f"{BOLD}{CYAN}catscan{RESET}> "
            else:
                prompt = (
                    f"{BOLD}{CYAN}catscan"
                    f"{GRAY}({selected_file.name})"
                    f"{RESET}> "
                )

            user_input = input(prompt).strip()

            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0]
            arguments = parts[1:]

            selected_file = execute_command(
                command,
                arguments,
                selected_file
            )

        except KeyboardInterrupt:
            print()
            continue

        except EOFError:
            print()
            break

        except SystemExit:
            break

def add_color_flag(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="catscan",
        description="Scratch project development toolkit"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"CatScan {VERSION}"
    )

    add_color_flag(parser)

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "shell",
        help="Start the CatScan interactive shell"
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a Scratch project"
    )


    inspect_parser.add_argument("file", help="Path to .sb3 file")
    add_color_flag(inspect_parser)

    script_parser = subparsers.add_parser(
        "script",
        help="Inspect scripts in a Scratch project"
    )

    script_parser.add_argument("file", help="Path to .sb3 file")
    script_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Open interactive target and script selection"
    )
    add_color_flag(script_parser)

    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract a .sb3 file"
    )
    extract_parser.add_argument("file", help="Path to .sb3 file")
    extract_parser.add_argument("output", nargs="?", default=None)
    add_color_flag(extract_parser)

    args = parser.parse_args()

    if not supports_color(getattr(args, "no_color", False)):
        disable_colors()

    if args.command == "inspect":
        try:
            inspect_sb3(Path(args.file))
        except (FileNotFoundError, ValueError, zipfile.BadZipFile) as error:
            print_error(str(error))
            sys.exit(1)
    elif args.command == "extract":
        out = Path(args.output) if args.output else Path.cwd() / Path(args.file).stem
        try:
            extract_sb3(Path(args.file), out)
        except (FileNotFoundError, ValueError, zipfile.BadZipFile) as error:
            print_error(str(error))
            sys.exit(1)
    elif args.command == "shell":
        shell()
    elif args.command == "script":
        try:
            file = Path(args.file)

            if args.interactive:
                select_target(file)
            else:
                print_all_scripts(file)

        except (FileNotFoundError, ValueError, zipfile.BadZipFile) as error:
            print_error(str(error))
            sys.exit(1)
    else:
        shell()





if __name__ == "__main__":
    main()
