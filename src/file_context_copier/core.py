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
