# CatScan

CatScan is a command-line tool for inspecting, validating, extracting, and modifying Scratch `.sb3` projects.

It is designed primarily for developers and power users who need to inspect Scratch project internals, work with `project.json`, extract project data, run scripts against projects, or use an AI-assisted workflow to propose and apply structured modifications.

## Features

* Inspect Scratch `.sb3` project structure
* Inspect sprites, the stage, blocks, variables, lists, broadcasts, costumes, and sounds
* Extract project data
* Validate Scratch project structure
* Run custom scripts against projects
* Save generated script output
* AI-assisted Scratch project modification
* Structured AI modifications instead of unrestricted file rewriting
* Scratch-specific AI knowledge and validation
* Orphan block cleanup
* Automatic backup before replacing the original project
* Temporary-file validation before saving
* Atomic project replacement
* Configurable AI API endpoint, model, timeout, and token limit

## Installation

Clone the repository:

```bash
git clone https://github.com/eelij/CatScan.git
cd CatScan
```

Install the project and its dependencies according to the project's Python packaging configuration.

CatScan is intended to be used from the command line.

## Usage

The main command is:

```bash
catscan
```

Run:

```bash
catscan --help
```

to see the currently available commands and options.

### Project inspection

CatScan can inspect the internal structure of a Scratch project without requiring Scratch itself.

Typical inspection includes:

* targets (sprites and stage)
* scripts and blocks
* variables
* lists
* broadcasts
* costumes
* sounds
* project metadata

Example:

```bash
catscan inspect project.sb3
```

The exact available inspection options can be viewed with:

```bash
catscan inspect --help
```

## Selecting Project Data

CatScan provides selection functionality for working with specific parts of a project.

For example:

```bash
catscan select project.sb3
```

Use:

```bash
catscan select --help
```

for the currently supported selection options.

## Extracting Data

Project data can be extracted from an `.sb3` file:

```bash
catscan extract project.sb3
```

See:

```bash
catscan extract --help
```

for available options.

## Running Scripts

CatScan can execute scripts against Scratch project data.

```bash
catscan script project.sb3
```

Generated script output can also be saved.

```bash
catscan script save project.sb3
```

Use the command help for the exact arguments supported by the current version.

## AI-Assisted Modification

CatScan includes an AI-assisted workflow for modifying Scratch projects.

The AI workflow is designed around structured modifications rather than allowing the model to freely rewrite the entire Scratch project.

At a high level, the process is:

```text
Scratch project
      │
      ▼
Project inspection
      │
      ▼
AI receives project context
      │
      ▼
AI proposes structured modification
      │
      ▼
Modification validation
      │
      ├── invalid → user confirmation
      │
      ▼
Modification applied
      │
      ▼
Orphan block cleanup
      │
      ▼
Full project validation
      │
      ├── invalid → project is not saved
      │
      ▼
Temporary .sb3 created and validated
      │
      ▼
User approval
      │
      ▼
Backup created
      │
      ▼
Original project replaced atomically
```

This provides several layers of protection against malformed Scratch projects.

### AI Configuration

The AI configuration supports options such as:

* API endpoint
* model
* request timeout
* maximum output tokens
* configuration management
* clearing stored configuration

The available commands can be inspected with:

```bash
catscan ai --help
```

CatScan can also maintain AI conversation context during an interactive modification session.

### Validation

AI-generated modifications are validated before they are applied.

If an initial modification fails structural validation, CatScan can ask the user whether the modification should be executed anyway.

Regardless of that choice, the resulting project is subjected to final project validation before it can be saved.

This means that bypassing the initial modification check does **not** bypass the final project validation.

## Scratch Project Safety

CatScan treats Scratch `.sb3` files as structured ZIP packages containing project data and assets.

The project structure is handled using Scratch-specific knowledge rather than treating `project.json` as arbitrary JSON.

The internal knowledge covers concepts including:

* blocks
* inputs
* shadow blocks
* variables
* lists
* broadcasts
* procedures
* menus
* operators
* reporters
* scripts
* Scratch block input types
* Scratch-specific serialization structures

This information is used to help the AI produce modifications that are compatible with Scratch's project format.

## Orphan Block Cleanup

AI modifications can leave behind blocks that are no longer reachable from a valid script structure.

CatScan includes orphan block cleanup as part of the AI modification pipeline.

This helps prevent unused block structures from accumulating in the resulting project.

## Backups and Atomic Saving

CatScan does not immediately overwrite the original project while constructing an AI modification.

Instead, the modified project is first written to a temporary `.sb3` file.

The temporary project is validated before the original file is replaced.

Before replacement, CatScan creates a backup of the original project.

The final replacement uses an atomic file replacement operation where supported by the underlying filesystem.

This reduces the risk of leaving the user with a partially written or malformed `.sb3` file if saving fails.

## Configuration Security

Stored API configuration is written with restrictive file permissions where supported by the operating system.

API credentials should still be treated as sensitive information and should not be committed to Git or shared publicly.

## Project Structure

The implementation is split into several modules:

```text
src/
└── catscan/
    ├── __init__.py
    ├── main.py
    ├── ai.py
    ├── config.py
    ├── output.py
    ├── scratch_knowledge.py
    ├── scratch_patterns.py
    └── orphan_cleanup.py
```

### `main.py`

Command-line interface and command dispatch.

### `ai.py`

AI interaction and the structured project-modification pipeline.

### `config.py`

AI and application configuration handling.

### `output.py`

Terminal output and user-facing formatting.

### `scratch_knowledge.py`

Scratch-specific structural knowledge used when working with Scratch projects and AI-generated modifications.

### `scratch_patterns.py`

Scratch structure and pattern definitions used by the project-processing logic.

### `orphan_cleanup.py`

Detection and cleanup of orphaned Scratch blocks.

## Development

The source code is located under:

```text
src/catscan/
```

When developing CatScan, changes affecting Scratch project manipulation should be tested against real `.sb3` projects.

In particular, changes to the AI modification pipeline should be tested for:

1. valid input projects
2. valid modifications
3. invalid modifications
4. orphan blocks
5. failed final validation
6. backup creation
7. temporary-file handling
8. successful atomic replacement

## Scratch Compatibility

CatScan works with the serialized structure used by Scratch `.sb3` projects.

Because Scratch projects contain a number of implicit structural rules, arbitrary changes to `project.json` can easily produce projects that Scratch cannot correctly load or execute.

For this reason, CatScan's modification workflow performs structural validation instead of assuming that syntactically valid JSON is sufficient.

## Disclaimer

AI-generated modifications can still be incorrect.

Always keep backups of important Scratch projects and review AI-generated changes before relying on them in production or educational projects.

CatScan's validation reduces the risk of malformed projects, but validation cannot guarantee that an AI-generated modification does exactly what the user intended.

## License

See the repository license for the current licensing terms.

## Repository

GitHub:

https://github.com/eelij/CatScan
