# Plan for file-context-copier

This document outlines the development plan for the `file-context-copier` CLI tool.

## 1. Project Setup & Structure (Done)

- [x] Create `src/file_context_copier` directory.
- [x] Move `main.py` to `src/file_context_copier/app.py`.
- [x] Create `src/file_context_copier/__init__.py`.
- [x] Create `tests` directory.
- [x] Update `pyproject.toml` to reflect the new structure and add `[tool.setuptools]`.

## 2. Core Functionality

- **File & Folder Selection (TUI):**
  - [x] Implement a `DirectoryTree` widget using `textual`.
  - [x] The widget should display files and folders recursively.
  - [x] Use `textual`'s built-in checkbox functionality for selection.
  - [x] Allow navigation with arrow keys.
  - [x] Implement `.gitignore` parsing using the `pathspec` library to exclude specified files.

- **Content Aggregation:**
  - [x] Create a function to get the content of selected files.
  - [x] For selected folders, walk through them and get the content of all files.
  - [x] Handle potential file reading errors gracefully.

- **Clipboard Output:**
  - [x] Create a function to format the content.
  - [x] Use `rich` to create Markdown code blocks.
  - [x] Detect the programming language of each file for syntax highlighting.
  - [x] Use `pyperclip` to copy the final string to the clipboard.

## 3. UI/UX

- **Main Application:**
  - [x] Create a `textual` `App` class.
  - [x] Add the `DirectoryTree` widget to the app's view.
  - [x] Add a "Copy to Clipboard" button.
  - [x] Add a status bar to show progress and confirmations.

- **Interactivity:**
  - [x] Bind the "Copy to Clipboard" button to the content aggregation and clipboard functions.
  - [x] Show a loading indicator while files are being processed.
  - [x] Display a success message after content is copied.
  - [x] Show error dialogs for file access or other issues.

## 4. Command-Line Interface

- **CLI with `typer`:**
  - [x] Create a `typer` CLI entry point in `app.py`.
  - [x] Add a `[PATH]` argument for the starting directory (defaulting to `.`).
  - [x] Add an `--output-file` option to save the output to a file.
  - [x] Add `--version` and `--help` options.

## 5. Code Quality & Maintainability

- **Linting & Formatting:**
  - [x] Configure `ruff` and `black` in `pyproject.toml`.
  - [x] Run the linters and formatters regularly.

- **Testing with `pytest`:**
  - [x] Write unit tests for the content aggregation logic.
  - [x] Mock the file system to avoid side effects.
  - [x] Write tests for the clipboard output formatting.

## 6. Next Steps

- [x] Start by implementing the `DirectoryTree` widget.
- [x] Then, implement the content aggregation logic.
- [x] Wire up the UI and CLI.
- [x] Write tests.
