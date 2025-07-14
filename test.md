**`src/file_context_copier/app.py`**

```python
"""CLI entry point for file-context-copier."""

import logging

import typer

# We now import the Textual App from the tui module
from .tui import FileContextCopierApp

# The Typer app instance remains the main entry point
app = typer.Typer(
    help="A tool to copy file/folder contents to clipboard as markdown."
)


@app.command()
def main(
    path: str = typer.Argument(
        ".", help="The starting directory to display."
    ),
    output_file: str = typer.Option(
        None,
        "--output-file",
        "-o",
        help="Write the output to a file instead of the clipboard.",
    ),
) -> None:
    """
    Launches the interactive file context copier.
    """
    logging.info(f"CLI tool started with path: {path} and output_file: {output_file}")
    # Instantiate the app from tui.py and run it
    copier_app = FileContextCopierApp(path, output_file)
    copier_app.run()


if __name__ == "__main__":
    app()

```

---

**`src/file_context_copier/core.py`**

```python
"""Core logic for file handling and content formatting."""

import logging
import os
import pathlib
from typing import Set

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


def get_gitignore_spec(path: str) -> PathSpec:
    """Get the .gitignore spec for the given path."""
    logging.debug(f"Getting .gitignore spec for path: {path}")
    gitignore_path = os.path.join(path, ".gitignore")
    if os.path.exists(gitignore_path):
        logging.debug(f".gitignore found at: {gitignore_path}")
        with open(gitignore_path) as f:
            spec = PathSpec.from_lines(GitWildMatchPattern, f.readlines())
            logging.debug(f"Loaded .gitignore spec: {spec.patterns}")
            return spec
    logging.debug("No .gitignore found.")
    return PathSpec.from_lines(GitWildMatchPattern, [])


def get_content(paths: Set[pathlib.Path], spec: PathSpec) -> dict[str, str]:
    """Get the content of the selected files, respecting the gitignore spec."""
    logging.debug(f"Getting content for paths: {paths}")
    content = {}
    for path in paths:
        logging.debug(f"Processing path: {path}")
        if path.is_file():
            try:
                # Ensure we don't include ignored files even if explicitly selected
                if not spec.match_file(str(path)):
                    file_content = path.read_text(encoding="utf-8")
                    content[str(path)] = file_content
                    logging.debug(f"Read file: {path}")
            except Exception as e:
                logging.error(f"Error reading {path}: {e}")
        elif path.is_dir():
            logging.debug(f"Walking directory: {path}")
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = pathlib.Path(root) / file
                    if not spec.match_file(str(file_path)):
                        try:
                            file_content = file_path.read_text(encoding="utf-8")
                            content[str(file_path)] = file_content
                            logging.debug(f"Read file in directory: {file_path}")
                        except Exception as e:
                            logging.error(f"Error reading {file_path}: {e}")
                    else:
                        logging.debug(f"Ignoring file due to .gitignore: {file_path}")
    return content


def detect_language(path: str) -> str:
    """Detect the programming language of a file based on its extension."""
    ext = os.path.splitext(path)[1].lower()
    # A comprehensive map of extensions to markdown language identifiers
    language_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "tsx", ".jsx": "jsx", ".html": "html", ".css": "css",
        ".scss": "scss", ".md": "markdown", ".json": "json", ".yaml": "yaml",
        ".yml": "yaml", ".sh": "shell", ".bash": "bash", ".zsh": "zsh",
        ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".java": "java",
        ".go": "go", ".rs": "rust", ".swift": "swift", ".kt": "kotlin",
        ".rb": "ruby", ".php": "php", ".pl": "perl", ".sql": "sql",
        ".lua": "lua", ".groovy": "groovy", ".cs": "csharp", ".fs": "fsharp",
        ".r": "r", ".dockerfile": "dockerfile", ".toml": "toml", ".ini": "ini",
        ".xml": "xml", ".log": "log", ".tex": "latex", ".v": "verilog",
        ".sv": "systemverilog", ".vhdl": "vhdl", ".dart": "dart",
    }
    language = language_map.get(ext, "")
    logging.debug(f"Detected language for extension {ext}: {language}")
    return language


def format_content(content: dict[str, str]) -> str:
    """Format the content as markdown code blocks."""
    logging.debug("Formatting content.")
    formatted_blocks = []
    for path, text in content.items():
        language = detect_language(path)
        # Use relative path for cleaner output
        relative_path = os.path.relpath(path)
        formatted_blocks.append(
            f"**`{relative_path}`**\n\n"
            f"```{language}\n"
            f"{text}\n"
            f"```"
        )
    return "\n\n---\n\n".join(formatted_blocks)

```

---

**`src/file_context_copier/__init__.py`**

```python

```

---

**`src/file_context_copier/tui.py`**

```python
"""Textual User Interface components for file-context-copier."""

import logging
import os
import pathlib
from typing import Iterable, Optional, Set

import pyperclip
from pathspec import PathSpec
from textual.app import App, ComposeResult
from textual.widgets import Button, DirectoryTree, Footer, Header, Static

# Import the core logic functions
from .core import format_content, get_gitignore_spec


class SelectableDirectoryTree(DirectoryTree):
    """A directory tree that allows selecting files and directories."""

    def __init__(self, path: str, spec: PathSpec, *args, **kwargs) -> None:
        """Initialise the directory tree."""
        self.spec = spec
        self.selected_nodes: Set[pathlib.Path] = set()
        super().__init__(path, *args, **kwargs)

    def filter_paths(self, paths: Iterable[pathlib.Path]) -> Iterable[pathlib.Path]:
        """Filter paths based on the .gitignore spec."""
        return [path for path in paths if not self.spec.match_file(str(path))]

    def on_tree_node_selected(self, event: DirectoryTree.NodeSelected) -> None:
        """Handle node selection with a checkbox-like behavior."""
        node_path = event.node.data.path
        if node_path in self.selected_nodes:
            self.selected_nodes.remove(node_path)
            event.node.label = node_path.name
        else:
            self.selected_nodes.add(node_path)
            event.node.label = f"[b green]✓[/b green] {node_path.name}"
        self.refresh()


class FileContextCopierApp(App):
    """The main Textual application to select and copy file context."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #tree-view {
        height: 80%;
        border: round white;
    }
    #status {
        height: 1;
        padding: 0 1;
        background: $primary;
        color: $text;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "copy_to_clipboard", "Copy"),
    ]

    def __init__(
        self,
        path: str,
        output_file: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialise the app."""
        self.path = path
        self.output_file = output_file
        self.spec = get_gitignore_spec(path)
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        logging.debug("Composing app widgets.")
        yield Header()
        yield SelectableDirectoryTree(self.path, self.spec, id="tree-view")
        yield Button("Copy to Clipboard", id="copy", variant="primary")
        yield Static(id="status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "copy":
            self.action_copy_to_clipboard()

    def action_copy_to_clipboard(self) -> None:
        """Gather all files, format their content, and copy to the clipboard."""
        logging.debug("Copy to clipboard action initiated.")
        tree = self.query_one(SelectableDirectoryTree)
        status = self.query_one("#status", Static)
        selected_paths = tree.selected_nodes

        if not selected_paths:
            status.update("[bold red]No files or folders selected.[/]")
            logging.info("No files or folders selected.")
            return

        status.update("Collecting files...")
        
        # --- Start of new, more robust file collection logic ---
        all_files_to_read: Set[pathlib.Path] = set()
        for path in selected_paths:
            if path.is_file():
                if not self.spec.match_file(str(path)):
                    all_files_to_read.add(path)
            elif path.is_dir():
                # Walk through the directory and add all non-ignored files
                for root, dirs, files in os.walk(path):
                    # Prune ignored directories to avoid walking them
                    dirs[:] = [d for d in dirs if not self.spec.match_file(str(pathlib.Path(root) / d))]
                    for file in files:
                        file_path = pathlib.Path(root) / file
                        if not self.spec.match_file(str(file_path)):
                            all_files_to_read.add(file_path)
        # --- End of new logic ---

        if not all_files_to_read:
            status.update("[bold red]No files found in selection (or all are ignored).[/]")
            return

        status.update(f"Reading {len(all_files_to_read)} files...")
        content = {}
        for file_path in all_files_to_read:
            try:
                content[str(file_path)] = file_path.read_text(encoding="utf-8")
            except Exception as e:
                logging.error(f"Error reading {file_path}: {e}")
                status.update(f"[bold red]Error reading {file_path.name}[/]")
                # Skip this file and continue
                continue
        
        logging.debug(f"Aggregated content for {len(content)} files.")
        formatted_content = format_content(content)
        logging.debug("Content formatted.")

        if self.output_file:
            try:
                with open(self.output_file, "w", encoding="utf-8") as f:
                    f.write(formatted_content)
                status.update(f"[bold green]Content written to {self.output_file}[/]")
                logging.info(f"Content written to {self.output_file}")
            except Exception as e:
                status.update(f"[bold red]Error writing to file: {e}[/]")
                logging.error(f"Error writing to {self.output_file}: {e}")
        else:
            pyperclip.copy(formatted_content)
            status.update(f"[bold green]Content for {len(content)} files copied to clipboard![/]")
            logging.info("Content copied to clipboard!")

```