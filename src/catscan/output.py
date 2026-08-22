import re

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


def print_success(message: str) -> None:
    print(f"{GREEN}✓{RESET} {message}")


def print_error(message: str) -> None:
    print(f"{RED}✗{RESET} {message}")


def print_info(message: str) -> None:
    print(f"{CYAN}•{RESET} {message}")


def print_section(title: str) -> None:
    print()
    print(f"{BOLD}{BLUE}{title}{RESET}")


def format_ai_response(text: str) -> str:
    if not isinstance(text, str):
        return str(text)

    text = re.sub(
        r"\$\s*([^\$]*?)\\circ\s*\$",
        lambda match: f"{match.group(1).strip()}°",
        text
    )

    text = re.sub(
        r"\$\s*([^\$]+?)\s*\$",
        lambda match: match.group(1),
        text
    )

    text = re.sub(
        r"\*\*(.+?)\*\*",
        lambda match: f"{BOLD}{match.group(1)}{RESET}",
        text
    )

    text = re.sub(
        r"(?<!\*)\*([^*\n]+)\*(?!\*)",
        lambda match: match.group(1),
        text
    )

    text = re.sub(
        r"`([^`\n]+)`",
        lambda match: match.group(1),
        text
    )

    text = re.sub(
        r"^#{1,6}\s+",
        "",
        text,
        flags=re.MULTILINE
    )

    text = text.replace("\\_", "_")
    text = text.replace("\\*", "*")
    text = text.replace("\\#", "#")
    text = text.replace("\\-", "-")
    text = text.replace("\\+", "+")
    text = text.replace("\\=", "=")

    return text


def print_ai_response(text: str) -> None:
    print(format_ai_response(text))


def disable_colors() -> None:
    global RESET, BOLD, CYAN, BLUE, GREEN, YELLOW, MAGENTA, RED, WHITE, GRAY

    RESET = ""
    BOLD = ""
    CYAN = ""
    BLUE = ""
    GREEN = ""
    YELLOW = ""
    MAGENTA = ""
    RED = ""
    WHITE = ""
    GRAY = ""