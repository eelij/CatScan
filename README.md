# CatScan

CatScan is a command-line developer toolkit for analyzing, inspecting, and extracting Scratch projects (`.sb3`).

## Features

- **Interactive Shell**
  - Keeps the selected `.sb3` project in memory between commands.
  - Provides an interactive terminal interface for working with Scratch projects.

- **Project Inspector (`inspect`)**
  - Displays a summary of the project's structure.
  - Shows stages, sprites, scripts, blocks, variables, lists, broadcasts, costumes, and sounds.
  - Displays information about individual targets and their resources.

- **Project Extraction (`extract`)**
  - Extracts the contents of an `.sb3` archive.
  - Extracts `project.json`, costumes, sounds, and other project assets.
  - Supports choosing a custom output directory.

- **Script Viewer (`script`)**
  - Allows you to inspect the scripts of a specific sprite or the Stage.
  - Supports nested loops and conditional blocks.
  - Supports custom blocks and procedure calls.
  - Displays block inputs, fields, and parameters.
  - Uses indentation to make complex Scratch scripts easier to understand.
  - Supports colored terminal output.

- **Script Export (`script save`)**
  - Saves the scripts of a selected target to a text file.
  - Automatically generates an output filename when one is not specified.
  - Supports specifying a custom output file.

- **Command-line support**
  - `inspect` and `extract` can be used directly without entering the interactive shell.
  - Output can be piped into standard Unix tools such as `grep`, `awk`, and `less`.

## Requirements

- Python 3.10 or newer
- Linux or macOS

The interactive target and script selection menus use `termios` and `tty`.

## Installation

Clone the repository:

```bash
git clone https://github.com/eelijo/CatScan.git
cd CatScan