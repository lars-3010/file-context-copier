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
        ("ctrl+c", "process_selections", "Process"),
    ]

    def __init__(
        self,
        path: str,
        output_file: Optional[str] = None,
        output_dir: Optional[str] = None,
        as_txt: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """Initialise the app."""
        self.path = path
        self.output_file = output_file
        self.output_dir = output_dir
        self.as_txt = as_txt
        self.spec = get_gitignore_spec(path)
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield SelectableDirectoryTree(self.path, self.spec, id="tree-view")
        yield Button("Process Selections", id="copy", variant="primary")
        yield Static(id="status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "copy":
            self.action_process_selections()

    def _get_files_for_path(self, path: pathlib.Path) -> Set[pathlib.Path]:
        """Recursively get all non-ignored files for a given path."""
        files_to_read: Set[pathlib.Path] = set()
        if path.is_file():
            if not self.spec.match_file(str(path)):
                files_to_read.add(path)
        elif path.is_dir():
            for root, dirs, files in os.walk(path, topdown=True):
                dirs[:] = [d for d in dirs if not self.spec.match_file(str(pathlib.Path(root) / d))]
                for file in files:
                    file_path = pathlib.Path(root) / file
                    if not self.spec.match_file(str(file_path)):
                        files_to_read.add(file_path)
        return files_to_read

    def _read_file_content(self, files_to_read: Set[pathlib.Path]) -> dict[str, str]:
        """Safely read content from a set of files, skipping unreadable ones."""
        status = self.query_one("#status", Static)
        content = {}
        status.update(f"Reading {len(files_to_read)} files...")
        for file_path in files_to_read:
            try:
                content[str(file_path)] = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, IOError):
                logging.warning(f"Skipping binary or non-utf8 file: {file_path}")
                status.update(f"[bold yellow]Skipped non-text file: {file_path.name}[/]")
                continue
        return content

    def action_process_selections(self) -> None:
        """Process selections based on the output mode."""
        tree = self.query_one(SelectableDirectoryTree)
        status = self.query_one("#status", Static)
        selected_paths = tree.selected_nodes

        if not selected_paths:
            status.update("[bold red]No files or folders selected.[/]")
            return

        if self.output_dir:
            status.update(f"Writing to directory: {self.output_dir}")
            os.makedirs(self.output_dir, exist_ok=True)
            count = 0
            for path in selected_paths:
                files_for_this_path = self._get_files_for_path(path)
                if not files_for_this_path:
                    continue
                
                content = self._read_file_content(files_for_this_path)
                if not content:
                    continue
                
                formatted_content = format_content(content)
                
                file_extension = ".txt" if self.as_txt else ".md"
                output_filename = f"{path.name}{file_extension}"
                output_filepath = os.path.join(self.output_dir, output_filename)
                
                with open(output_filepath, "w", encoding="utf-8") as f:
                    f.write(formatted_content)
                count += 1
            
            status.update(f"[bold green]{count} context file(s) written to {self.output_dir}[/]")
            return

        all_files_to_read: Set[pathlib.Path] = set()
        status.update("Collecting files from selection...")
        for path in selected_paths:
            all_files_to_read.update(self._get_files_for_path(path))

        if not all_files_to_read:
            status.update("[bold red]No text files found in selection.[/]")
            return

        content = self._read_file_content(all_files_to_read)
        if not content:
             status.update("[bold red]No readable text files found in selection.[/]")
             return

        formatted_content = format_content(content)

        if self.output_file:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(formatted_content)
            status.update(f"[bold green]Content from {len(content)} files written to {self.output_file}[/]")
        else:
            pyperclip.copy(formatted_content)
            status.update(f"[bold green]Content from {len(content)} files copied to clipboard![/]")
