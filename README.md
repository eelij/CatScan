# CatScan

> **CatScan** is a command-line developer toolkit for analyzing, inspecting, and extracting Scratch (`.sb3`) projects with clear formatting and terminal visualizers.

---

## ⚡ Features

### 🖥️ Interactive Shell

* **Persistent Context:** Keeps the selected `.sb3` file active in memory across commands.
* **Streamlined Workflow:** Interactive prompt with project status indicators and custom navigation.

### 🔍 Project Inspector (`inspect`)

* **Project Overview:** High-level metrics for stages, sprites, scripts, blocks, variables, lists, and broadcasts.
* **Target Analysis:** Breakdown of costumes, sounds, and local vs. global variables per target.

### 📦 Project Extraction (`extract`)

* **Asset Unpacker:** Extracts `project.json`, costumes, sounds, and graphics.
* **Flexible Destination:** Output directly to current directory or specify custom destination paths.

### 📜 Script Viewer (`script`)

* **Structured Code Output:** Indented, colored trees for complex scripts.
* **Control Flow Support:** Renders nested loops, conditional branches (`if`/`else`), and custom procedure calls.
* **Value Resolution:** Displays inline fields, variables, and input arguments directly.

### 💾 Script Exporter (`script save`)

* **Text Export:** Dumps formatted AST-like script representation to plain text files.
* **Automatic Naming:** Generates structured filenames by default or accepts custom paths.

---

## 📋 Requirements

* **Python:** `3.10` or higher
* **OS:** Linux or macOS (*interactive selector relies on `termios` and `tty*`)

---

## 🚀 Installation

```bash
# Clone repository
git clone https://github.com/eelij/CatScan.git
cd CatScan

# Install package
python3 -m pip install .

# Verify installation
catscan --version

```

---

## 💡 Usage

### CLI Commands

```bash
# Inspect a project
catscan inspect project.sb3

# Extract assets to default folder
catscan extract project.sb3

# Extract assets to a specific directory
catscan extract project.sb3 ./output_dir

# View scripts interactively
catscan script project.sb3

# Save target scripts to a text file
catscan script save project.sb3
catscan script save project.sb3 output_scripts.txt

```

### Interactive Shell Session

```bash
$ catscan shell

catscan> select project.sb3
catscan(project.sb3)> inspect
catscan(project.sb3)> script
catscan(project.sb3)> script save
catscan(project.sb3)> extract
catscan(project.sb3)> help

```

---

## 🛠️ Unix Pipeline Examples

CatScan produces clean text output designed to integrate with standard CLI tools:

```bash
# Filter block metrics
catscan inspect project.sb3 | grep "Blocks"

# Search for procedure definitions (disable ANSI color codes for clean parsing)
catscan script project.sb3 --no-color | grep "proccode:"

# Page through large script outputs
catscan script project.sb3 | less -R

```

---

## 📖 Command Reference

| Command | Usage | Description |
| --- | --- | --- |
| `shell` | `catscan shell` | Launches the interactive shell environment. |
| `inspect` | `catscan inspect <file.sb3>` | Displays metadata and structure overview. |
| `extract` | `catscan extract <file.sb3> [dir]` | Extracts project assets and JSON file. |
| `script` | `catscan script <file.sb3>` | Opens the interactive visual script inspector. |
| `script save` | `catscan script save <file.sb3> [out]` | Writes target scripts out to a file. |
| `--version` | `catscan --version` | Displays current installed version. |
| `--help` | `catscan --help` | Shows CLI usage and argument instructions. |

---

## 📄 License

This project is licensed under the **MIT License**.

Copyright (c) 2026 **eelij**