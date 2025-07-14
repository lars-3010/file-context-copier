# file-context-copier

A Python CLI tool for interactively selecting project files/folders and copying their content to clipboard as markdown code blocks with proper language detection.

## Features

- **Interactive TUI:** A Textual-based terminal user interface for easy file and folder selection.
- **Directory Tree:** A navigable directory tree with checkboxes for selection.
- **Content Aggregation:** Gathers content from selected files and folders.
- **Markdown Formatting:** Formats the aggregated content into Markdown code blocks with automatic language detection.
- **Clipboard Integration:** Copies the formatted content to the clipboard.
- **.gitignore Support:** Automatically ignores files and folders listed in your `.gitignore` file.

## Planned CLI Usage

```bash
fcc [PATH] [--output-file FILENAME]
```

- `[PATH]`: The starting directory to display (defaults to the current directory).
- `--output-file`: Write the output to a file instead of the clipboard.