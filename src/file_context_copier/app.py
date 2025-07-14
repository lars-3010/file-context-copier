"""Main application for file-context-copier."""

import logging
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

logging.basicConfig(filename="fcc.log", level=logging.DEBUG)


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
        logging.debug(f"Initialising FileContextCopier with path: {path} and output_file: {output_file}")
        self.path = path
        self.output_file = output_file
        self.spec = self._get_gitignore_spec(path)
        super().__init__(*args, **kwargs)

    def _get_gitignore_spec(self, path: str) -> PathSpec:
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

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        logging.debug("Composing app widgets.")
        yield Header()
        yield SelectableDirectoryTree(self.path, self.spec)
        yield Button("Copy to Clipboard", id="copy")
        yield Static(id="status", classes="status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        logging.debug(f"Button pressed: {event.button.id}")
        if event.button.id == "copy":
            self.action_copy_to_clipboard()

    def action_toggle_files(self) -> None:
        """Toggle the display of files."""
        logging.debug("Toggling file display.")
        tree = self.query_one(SelectableDirectoryTree)
        tree.show_files = not tree.show_files

    def action_copy_to_clipboard(self) -> None:
        """Copy the content of selected files to the clipboard."""
        logging.debug("Copy to clipboard action initiated.")
        tree = self.query_one(SelectableDirectoryTree)
        selected_paths = tree.selected_nodes
        logging.debug(f"Selected paths: {selected_paths}")
        if not selected_paths:
            self.query_one("#status").update("No files or folders selected.")
            logging.info("No files or folders selected.")
            return

        content = self._get_content(selected_paths)
        logging.debug(f"Aggregated content keys: {content.keys()}")
        formatted_content = self._format_content(content)
        logging.debug("Content formatted.")

        if self.output_file:
            logging.debug(f"Writing to output file: {self.output_file}")
            try:
                with open(self.output_file, "w") as f:
                    f.write(formatted_content)
                self.query_one("#status").update(f"Content written to {self.output_file}")
                logging.info(f"Content written to {self.output_file}")
            except Exception as e:
                self.query_one("#status").update(f"Error writing to {self.output_file}: {e}")
                logging.error(f"Error writing to {self.output_file}: {e}")
        else:
            logging.debug("Copying to clipboard.")
            pyperclip.copy(formatted_content)
            self.query_one("#status").update("Content copied to clipboard!")
            logging.info("Content copied to clipboard!")

    def _get_content(self, paths: set[pathlib.Path]) -> dict[str, str]:
        """Get the content of the selected files."""
        logging.debug(f"Getting content for paths: {paths}")
        content = {}
        for path in paths:
            logging.debug(f"Processing path: {path}")
            if path.is_file():
                try:
                    file_content = path.read_text()
                    content[str(path)] = file_content
                    logging.debug(f"Read file: {path}")
                except Exception as e:
                    self.query_one("#status").update(f"Error reading {path}: {e}")
                    logging.error(f"Error reading {path}: {e}")
            elif path.is_dir():
                logging.debug(f"Walking directory: {path}")
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = pathlib.Path(root) / file
                        if not self.spec.match_file(str(file_path)):
                            try:
                                file_content = file_path.read_text()
                                content[str(file_path)] = file_content
                                logging.debug(f"Read file in directory: {file_path}")
                            except Exception as e:
                                self.query_one("#status").update(
                                    f"Error reading {file_path}: {e}"
                                )
                                logging.error(f"Error reading {file_path}: {e}")
                        else:
                            logging.debug(f"Ignoring file due to .gitignore: {file_path}")
        return content

    def _format_content(self, content: dict[str, str]) -> str:
        """Format the content as markdown code blocks."""
        logging.debug("Formatting content.")
        formatted_blocks = []
        for path, text in content.items():
            language = self._detect_language(path)
            logging.debug(f"Detected language for {path}: {language}")
            formatted_blocks.append(f'''**{path}**

````{language}
{text}
````''')
        return "\n\n".join(formatted_blocks)

    def _detect_language(self, path: str) -> str:
        """Detect the programming language of a file."""
        ext = os.path.splitext(path)[1]
        language = {
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
        logging.debug(f"Detected language for extension {ext}: {language}")
        return language


app = typer.Typer()


@app.command()
def main(
    path: str = typer.Argument(
        ".", help="The starting directory to display."
    ),
    output_file: str = typer.Option(
        None, "--output-file", "-o", help="Write the output to a file instead of the clipboard."
    ),
) -> None:
    """A Python CLI tool for interactively selecting project files/folders and copying their content to clipboard as markdown code blocks with proper language detection."""
    logging.info(f"CLI tool started with path: {path} and output_file: {output_file}")
    copier_app = FileContextCopier(path, output_file)
    copier_app.run()


if __name__ == "__main__":
    typer.run(main)