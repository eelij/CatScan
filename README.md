# CatScan

> **CatScan** is a command-line developer toolkit for analyzing, inspecting, extracting, and AI-modifying Scratch (`.sb3`) projects with clear formatting and terminal visualizers.

---

## ⚡ Features

### 🖥️ Interactive Shell

* **Persistent Context:** Keeps the selected `.sb3` file active across commands.
* **Interactive Workflow:** Provides a terminal-based command interface with project status and configuration management.
* **Command History:** Stores shell history in the user's CatScan configuration directory.

### 🔍 Project Inspector

* **Project Overview:** Displays stages, sprites, scripts, blocks, variables, lists, and broadcasts.
* **Target Analysis:** Shows costumes, sounds, and local vs. global variables for each target.
* **Scratch Structure Validation:** Validates block references, parent/next relationships, inputs, and project structure.

### 📦 Project Extraction

* **Asset Unpacker:** Extracts `project.json`, costumes, sounds, and other project assets.
* **Path Safety:** Protects against unsafe ZIP paths during extraction.

### 📜 Script Viewer

* **Structured Output:** Displays Scratch scripts as readable, indented trees.
* **Control Flow Support:** Handles loops, conditionals, sub-stacks, and custom procedure definitions.
* **Value Resolution:** Resolves fields, variables, reporters, and block inputs where possible.
* **Target Selection:** Lets you select a specific Stage or Sprite interactively.

### 💾 Script Exporter

* **Text Export:** Saves formatted script output to plain text files.
* **Automatic Naming:** Generates an output filename automatically when none is specified.
* **Custom Paths:** Supports specifying your own output file.

### 🤖 AI Project Development

CatScan can connect to OpenAI-compatible AI APIs and use the selected Scratch project as context.

* **Project-Aware AI:** Sends the complete `project.json` structure to the AI.
* **AI Analysis:** Ask questions about the project, its scripts, blocks, and structure.
* **AI Modifications:** Request changes such as adding gameplay logic, changing costumes, modifying scripts, or adding Scratch blocks.
* **Structured Modifications:** AI modification responses are parsed as structured JSON instead of directly executing generated Scratch code.
* **Modification Validation:** Proposed changes are validated before they are applied.
* **Safe Backups:** A backup of the original `.sb3` project is created before modifications are saved.
* **Atomic Saving:** Project changes are written to a temporary archive and validated before replacing the original project.
* **Configurable Model:** Supports changing the AI endpoint and model.
* **Configurable Output Limit:** Supports configuring the maximum AI output token count.
* **Configurable Timeout:** Supports configuring the AI request timeout.
* **Retry Handling:** Retries temporary API failures such as HTTP `429` and `503`.

### 🔐 AI Configuration

CatScan stores AI configuration in:

```text
~/.config/catscan/config.json
```

API keys are stored with restrictive file permissions.

Supported settings include:

* API key
* API URL
* Model
* Request timeout
* Maximum output tokens

---

## 📋 Requirements

* **Python:** `3.10` or higher
* **OS:** Linux or macOS
* **Terminal:** Interactive target selection uses `termios` and `tty`

---

## 🚀 Installation

```bash
git clone https://github.com/eelij/CatScan.git
cd CatScan

python3 -m pip install .

catscan --version
```

---

## 💡 Usage

### Interactive Shell

Start CatScan:

```bash
catscan
```

Select a project:

```text
catscan > select project.sb3
```

Inspect it:

```text
catscan > inspect
```

View scripts:

```text
catscan > script
```

Extract the project:

```text
catscan > extract
```

---

## 🤖 AI Usage

Configure your API key:

```text
catscan > ai api
```

Set an API endpoint:

```text
catscan > ai url https://openrouter.ai/api/v1/chat/completions
```

Set a model:

```text
catscan > ai model qwen/qwen3-coder
```

Set the request timeout:

```text
catscan > ai timeout 120
```

Set the maximum AI output tokens:

```text
catscan > ai max-tokens 8192
```

View the current configuration:

```text
catscan > ai config
```

Ask the AI about the selected project:

```text
catscan > ai explain how the Rocketship script works
```

Request a project modification:

```text
catscan > ai add a feature that makes the Rocketship change costume while flying
```

CatScan will validate the proposed modification before asking whether it should be applied.

---

## 🧠 AI Modification Workflow

AI modifications follow a controlled pipeline:

```text
Scratch .sb3
    ↓
Read project.json
    ↓
Build AI context
    ↓
AI generates structured modification JSON
    ↓
Validate modification
    ↓
Apply changes to a copy of the project
    ↓
Validate resulting Scratch structure
    ↓
Create backup
    ↓
Replace original .sb3 atomically
```

The original project is left untouched when validation fails or the user declines the modification.

---

## 📜 Script Commands

View scripts for a selected target:

```text
catscan > script
```

Save the selected target's scripts:

```text
catscan > script save
```

Save to a custom file:

```text
catscan > script save output_scripts.txt
```

---

## 🔍 Project Commands

Inspect a project:

```text
catscan > inspect
```

Extract a project:

```text
catscan > extract
```

Select another project:

```text
catscan > select another_project.sb3
```

---

## 📖 Command Reference

| Command                  | Description                               |
| ------------------------ | ----------------------------------------- |
| `select <file>`          | Select a Scratch `.sb3` project           |
| `inspect`                | Inspect project structure and metadata    |
| `extract`                | Extract project assets and `project.json` |
| `script`                 | Open the interactive script viewer        |
| `script save`            | Save target scripts to a text file        |
| `script save <file>`     | Save scripts to a specified file          |
| `ai api`                 | Set the AI API key securely               |
| `ai url <url>`           | Set the AI API endpoint                   |
| `ai model <model>`       | Set the AI model                          |
| `ai timeout <seconds>`   | Set the AI request timeout                |
| `ai max-tokens <amount>` | Set the maximum AI output tokens          |
| `ai config`              | Display AI configuration                  |
| `ai <prompt>`            | Ask the AI about the selected project     |
| `clear`                  | Clear the terminal                        |
| `version`                | Show CatScan version                      |
| `help`                   | Show available commands                   |
| `exit`                   | Exit CatScan                              |
| `quit`                   | Exit CatScan                              |

---

## 🛠️ Unix Pipeline Examples

CatScan produces terminal output that can be combined with standard Unix tools.

```bash
catscan | grep "Blocks"

catscan | grep "Variables"

catscan | less
```

---

## 🧪 Development

Clone the repository:

```bash
git clone https://github.com/eelij/CatScan.git
cd CatScan
```

Install the package:

```bash
python3 -m pip install -e .
```

Run the test suite:

```bash
python3 -m unittest discover -s tests -v
```

---

## 📁 Project Structure

```text
CatScan/
├── src/
│   └── catscan/
│       ├── __init__.py
│       └── main.py
├── tests/
│   └── test_catscan.py
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

---

## 📄 License

This project is licensed under the **MIT License**.

Copyright (c) 2026 **eelij**
