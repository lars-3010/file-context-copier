"""Core logic for file handling and content formatting."""

import json
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
                    if str(path).endswith('.ipynb'):
                        notebook_content = parse_jupyter_notebook(str(path))
                        content[str(path)] = notebook_content
                        logging.debug(f"Parsed Jupyter notebook: {path}")
                    else:
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
                            if str(file_path).endswith('.ipynb'):
                                notebook_content = parse_jupyter_notebook(str(file_path))
                                content[str(file_path)] = notebook_content
                                logging.debug(f"Parsed Jupyter notebook in directory: {file_path}")
                            else:
                                file_content = file_path.read_text(encoding="utf-8")
                                content[str(file_path)] = file_content
                                logging.debug(f"Read file in directory: {file_path}")
                        except Exception as e:
                            logging.error(f"Error reading {file_path}: {e}")
                    else:
                        logging.debug(f"Ignoring file due to .gitignore: {file_path}")
    return content


def parse_jupyter_notebook(notebook_path: str) -> str:
    """
    Parse a Jupyter notebook and convert it to markdown format.
    
    Args:
        notebook_path: Path to the .ipynb file
        
    Returns:
        Formatted markdown string with all cells converted
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to parse Jupyter notebook {notebook_path}: {e}")
        return f"Error: Could not parse Jupyter notebook - {e}"
    
    cells = notebook.get('cells', [])
    if not cells:
        return "# Empty Notebook\n\nThis Jupyter notebook contains no cells."
    
    # Extract kernel language for code cells
    kernel_language = "python"  # Default
    try:
        kernel_spec = notebook.get('metadata', {}).get('kernelspec', {})
        kernel_language = kernel_spec.get('language', 'python')
    except (KeyError, AttributeError):
        pass
    
    converted_cells = []
    cell_counter = 0
    
    for cell in cells:
        cell_type = cell.get('cell_type', 'unknown')
        source = cell.get('source', [])
        
        # Join source lines (Jupyter stores as array of strings)
        if isinstance(source, list):
            content = ''.join(source).rstrip()
        else:
            content = str(source).rstrip()
        
        if not content.strip():  # Skip empty cells
            continue
            
        cell_counter += 1
        
        if cell_type == 'markdown':
            # Direct markdown output with a subtle separator
            converted_cells.append(f"{content}")
            
        elif cell_type == 'code':
            # Code block with detected language
            converted_cells.append(f"```{kernel_language}\n{content}\n```")
            
        elif cell_type == 'raw':
            # Raw cells as code blocks without language
            converted_cells.append(f"```\n{content}\n```")
            
        else:
            # Unknown cell type - treat as raw
            logging.warning(f"Unknown cell type '{cell_type}' in {notebook_path}")
            converted_cells.append(f"```\n{content}\n```")
    
    # Join all cells with double line breaks for proper markdown spacing
    result = '\n\n'.join(converted_cells)
    
    logging.info(f"Converted {cell_counter} cells from Jupyter notebook {notebook_path}")
    return result


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
        ".ipynb": "jupyter-notebook"
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
        
        # Special handling for Jupyter notebooks
        if language == "jupyter-notebook":
            # For notebooks, we already have formatted markdown from parse_jupyter_notebook
            formatted_blocks.append(
                f"**`{relative_path}`**\n\n{text}"  # No extra code block wrapper
            )
        else:
            # Existing logic for regular files
            formatted_blocks.append(
                f"**`{relative_path}`**\n\n"
                f"```{language}\n"
                f"{text}\n"
                f"```"
            )
    return "\n\n---\n\n".join(formatted_blocks)
