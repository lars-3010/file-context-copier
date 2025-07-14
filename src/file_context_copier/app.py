"""Main application for file-context-copier."""

import os
import pathlib
from typing import Iterable

import pyperclip
import rich
import textual
import typer
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from rich.markdown import Markdown
from textual.app import App, ComposeResult
from textual.widgets import Button, DirectoryTree, Footer, Header, Static


class SelectableDirectoryTree(DirectoryTree):
    """A directory tree that allows selecting files and directories."""

    def __init__(self, path: str, spec: PathSpec, *args, **kwargs) -> None:
        """Initialise the directory tree."""
        self.spec = spec
        self.selected_nodes = set()
        super().__init__(path, *args, **kwargs)

    def filter_paths(self, paths: Iterable[pathlib.Path]) -> Iterable[pathlib.Path]:
        """Filter paths based on the .gitignore spec."""
        return [path for path in paths if not self.spec.match_file(str(path))]

    def on_tree_node_selected(self, event: DirectoryTree.NodeSelected) -> None:
        """Handle node selection."""
        if event.node.data.path in self.selected_nodes:
            self.selected_nodes.remove(event.node.data.path)
            event.node.label = event.node.data.path.name
        else:
            self.selected_nodes.add(event.node.data.path)
            event.node.label = f"[b green]✓[/b green] {event.node.data.path.name}"
        self.refresh()


class FileContextCopier(App):
    """A textual app to copy file context."""

    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, path: str, output_file: str | None = None, *args, **kwargs) -> None:
        """Initialise the app."""
        self.path = path
        self.output_file = output_file
        self.spec = self._get_gitignore_spec(path)
        super().__init__(*args, **kwargs)

    def _get_gitignore_spec(self, path: str) -> PathSpec:
        """Get the .gitignore spec for the given path."""
        gitignore_path = os.path.join(path, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path) as f:
                return PathSpec.from_lines(GitWildMatchPattern, f.readlines())
        return PathSpec.from_lines(GitWildMatchPattern, [])

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield SelectableDirectoryTree(self.path, self.spec)
        yield Button("Copy to Clipboard", id="copy")
        yield Static(id="status", classes="status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "copy":
            self.action_copy_to_clipboard()

    def action_toggle_files(self) -> None:
        """Toggle the display of files."""
        tree = self.query_one(SelectableDirectoryTree)
        tree.show_files = not tree.show_files

    def action_copy_to_clipboard(self) -> None:
        """Copy the content of selected files to the clipboard."""
        tree = self.query_one(SelectableDirectoryTree)
        selected_paths = tree.selected_nodes
        if not selected_paths:
            self.query_one("#status").update("No files or folders selected.")
            return

        content = self._get_content(selected_paths)
        formatted_content = self._format_content(content)

        if self.output_file:
            try:
                with open(self.output_file, "w") as f:
                    f.write(formatted_content)
                self.query_one("#status").update(f"Content written to {self.output_file}")
            except Exception as e:
                self.query_one("#status").update(f"Error writing to {self.output_file}: {e}")
        else:
            pyperclip.copy(formatted_content)
            self.query_one("#status").update("Content copied to clipboard!")

    def _get_content(self, paths: set[pathlib.Path]) -> dict[str, str]:
        """Get the content of the selected files."""
        content = {}
        for path in paths:
            if path.is_file():
                try:
                    content[str(path)] = path.read_text()
                except Exception as e:
                    self.query_one("#status").update(f"Error reading {path}: {e}")
            elif path.is_dir():
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = pathlib.Path(root) / file
                        if not self.spec.match_file(str(file_path)):
                            try:
                                content[str(file_path)] = file_path.read_text()
                            except Exception as e:
                                self.query_one("#status").update(
                                    f"Error reading {file_path}: {e}"
                                )
        return content

    def _format_content(self, content: dict[str, str]) -> str:
        """Format the content as markdown code blocks."""
        formatted_blocks = []
        for path, text in content.items():
            language = self._detect_language(path)
            formatted_blocks.append(f'''**{path}**

````{language}
{text}
````''')
        return "\n\n".join(formatted_blocks)

    def _detect_language(self, path: str) -> str:
        """Detect the programming language of a file."""
        ext = os.path.splitext(path)[1]
        return {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".html": "html",
            ".css": "css",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".sh": "shell",
            ".bash": "bash",
            ".zsh": "zsh",
            ".fish": "fish",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".kts": "kotlin",
            ".scala": "scala",
            ".rb": "ruby",
            ".php": "php",
            ".pl": "perl",
            ".pm": "perl",
            ".t": "perl",
            ".r": "r",
            ".R": "r",
            ".Rmd": "r",
            ".Rnw": "r",
            ".Rpres": "r",
            ".Rproj": "r",
            ".ps1": "powershell",
            ".psm1": "powershell",
            ".psd1": "powershell",
            ".ps1xml": "powershell",
            ".psc1": "powershell",
            ".psrc": "powershell",
            ".sql": "sql",
            ".lua": "lua",
            ".groovy": "groovy",
            ".gvy": "groovy",
            ".gy": "groovy",
            ".gradle": "groovy",
            ".kts": "kotlin",
            ".clj": "clojure",
            ".cljs": "clojure",
            ".cljc": "clojure",
            ".edn": "clojure",
            ".lisp": "lisp",
            ".lsp": "lisp",
            ".cl": "lisp",
            ".el": "lisp",
            ".scm": "scheme",
            ".ss": "scheme",
            ".rkt": "racket",
            ".rktl": "racket",
            ".scrbl": "racket",
            ".hs": "haskell",
            ".lhs": "haskell",
            ".purs": "purescript",
            ".elm": "elm",
            ".erl": "erlang",
            ".hrl": "erlang",
            ".ex": "elixir",
            ".exs": "elixir",
            ".eex": "elixir",
            ".leex": "elixir",
            ".heex": "elixir",
            ".dart": "dart",
            ".f": "fortran",
            ".f90": "fortran",
            ".f95": "fortran",
            ".f03": "fortran",
            ".f08": "fortran",
            ".for": "fortran",
            ".ftn": "fortran",
            ".s": "assembly",
            ".asm": "assembly",
            ".d": "d",
            ".di": "d",
            ".pas": "pascal",
            ".pp": "pascal",
            ".inc": "pascal",
            ".p": "pascal",
            ".lpr": "pascal",
            ".dpr": "pascal",
            ".dpk": "pascal",
            ".dfm": "pascal",
            ".pascal": "pascal",
            ".vb": "vbnet",
            ".vbs": "vbnet",
            ".bas": "vbnet",
            ".frm": "vbnet",
            ".cls": "vbnet",
            ".ctl": "vbnet",
            ".dob": "vbnet",
            ".dsr": "vbnet",
            ".vbp": "vbnet",
            ".vbproj": "vbnet",
            ".sln": "vbnet",
            ".cs": "csharp",
            ".csx": "csharp",
            ".csproj": "csharp",
            ".sln": "csharp",
            ".fs": "fsharp",
            ".fsi": "fsharp",
            ".fsx": "fsharp",
            ".fsproj": "fsharp",
            ".sln": "fsharp",
            ".ml": "ocaml",
            ".mli": "ocaml",
            ".mll": "ocaml",
            ".mly": "ocaml",
            ".fs": "fsharp",
            ".fsi": "fsharp",
            ".fsx": "fsharp",
            ".fsproj": "fsharp",
            ".sln": "fsharp",
            ".v": "verilog",
            ".vh": "verilog",
            ".sv": "verilog",
            ".svh": "verilog",
            ".vhd": "vhdl",
            ".vhdl": "vhdl",
            ".tcl": "tcl",
            ".tk": "tcl",
            ".itcl": "tcl",
            ".itk": "tcl",
            ".tm": "tcl",
            ".tex": "latex",
            ".sty": "latex",
            ".cls": "latex",
            ".bib": "bibtex",
            ".bst": "bibtex",
            ".pro": "prolog",
            ".pl": "prolog",
            ".P": "prolog",
            ".ada": "ada",
            ".adb": "ada",
            ".ads": "ada",
            ".gpr": "ada",
            ".cob": "cobol",
            ".cbl": "cobol",
            ".cpy": "cobol",
            ".jcl": "jcl"
        }.get(ext, "")


def main(
    path: str = typer.Argument(
        ".", help="The starting directory to display."
    ),
    output_file: str = typer.Option(
        None, "--output-file", "-o", help="Write the output to a file instead of the clipboard."
    ),
) -> None:
    """A Python CLI tool for interactively selecting project files/folders and copying their content to clipboard as markdown code blocks with proper language detection."""
    app = FileContextCopier(path, output_file)
    app.run()


if __name__ == "__main__":
    typer.run(main)