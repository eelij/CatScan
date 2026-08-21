# CatScan

CatScan is a command-line development toolkit for analyzing, inspecting, and extracting Scratch projects (`.sb3`).

CatScan is designed for exploring the structure and scripts of Scratch projects directly from the terminal.

## Features

- **Interactive Shell**
  - Keeps the selected `.sb3` project in memory between commands.
  - Allows you to inspect and work with the same project without repeatedly specifying the file.

- **Project Inspector (`inspect`)**
  - Displays a summary of the project's structure.
  - Stages
  - Sprites
  - Scripts
  - Blocks
  - Variables
  - Lists
  - Broadcasts
  - Costumes
  - Sounds
  - Target-specific information

- **Project Extraction (`extract`)**
  - Extracts the contents of an `.sb3` project into a directory.
  - Includes files such as:
    - `project.json`
    - Costumes
    - Sounds
    - Other project assets

- **Script Inspector (`script`)**
  - Displays Scratch scripts directly in the terminal.
  - Allows you to select a target and a specific script interactively.
  - Supports nested structures.
  - Supports conditional statements.
  - Supports loops.
  - Supports custom blocks.
  - Supports `procedures_call`.
  - Displays blocks, fields, and parameters with clear indentation.
  - Output works with standard Unix tools such as `grep`, `awk`, and `sed`.

- **Script Saving (`script save`)**
  - Saves scripts to a text file.
  - Automatically generates a filename or allows you to specify one.

- **ANSI Colors**
  - Uses color-coded terminal output for improved readability.
  - Colors can be disabled with `--no-color`.
  - Designed to work well with Unix pipelines.

## Requirements

- Python 3.10 or newer
- Linux or macOS

Interactive menus use Python's `termios` and `tty` modules.

## Installation

Clone the repository:

```bash
git clone https://github.com/epulix77/CatScan.git
cd CatScan
