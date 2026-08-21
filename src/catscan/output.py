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
