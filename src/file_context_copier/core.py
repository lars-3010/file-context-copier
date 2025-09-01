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


def _process_single_file(file_path: pathlib.Path, spec: PathSpec) -> tuple[str, str] | None:
    """Process a single file, handling Jupyter notebooks and gitignore rules."""
    if spec.match_file(str(file_path)):
        return None
    
    try:
        if str(file_path).endswith('.ipynb'):
            content = parse_jupyter_notebook(str(file_path))
        else:
            content = file_path.read_text(encoding="utf-8")
        return str(file_path), content
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None


def get_content(paths: Set[pathlib.Path], spec: PathSpec) -> dict[str, str]:
    """Get the content of the selected files, respecting the gitignore spec."""
    content = {}
    
    for path in paths:
        if path.is_file():
            result = _process_single_file(path, spec)
            if result:
                content[result[0]] = result[1]
        elif path.is_dir():
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = pathlib.Path(root) / file
                    result = _process_single_file(file_path, spec)
                    if result:
                        content[result[0]] = result[1]
    
    return content


def parse_jupyter_notebook(notebook_path: str) -> str:
    """Parse a Jupyter notebook and convert to simple markdown format."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
    except Exception as e:
        return f"Error parsing notebook: {e}"
    
    cells = notebook.get('cells', [])
    if not cells:
        return "# Empty Notebook"
    
    # Simple kernel detection
    kernel_lang = notebook.get('metadata', {}).get('kernelspec', {}).get('language', 'python')
    
    converted_cells = []
    for cell in cells:
        source = cell.get('source', [])
        content = ''.join(source).strip() if isinstance(source, list) else str(source).strip()
        
        if not content:
            continue
            
        cell_type = cell.get('cell_type', 'code')
        if cell_type == 'markdown':
            converted_cells.append(content)
        else:  # code, raw, or unknown - treat as code
            converted_cells.append(f"```{kernel_lang}\n{content}\n```")
    
    return '\n\n'.join(converted_cells)


def process_paths_to_content(paths_list, base_path: str = ".", exclude_patterns: str = None) -> dict[str, str]:
    """
    Shared processing function for both CLI and API use.
    
    Args:
        paths_list: List of path patterns/strings
        base_path: Base directory to operate from
        exclude_patterns: Comma-separated additional exclude patterns
        
    Returns:
        Dictionary of file paths to content
    """
    from glob import glob
    
    # Expand paths (copied from app.py expand_paths function)
    expanded_paths: Set[pathlib.Path] = set()
    
    for pattern in paths_list:
        if os.path.isabs(pattern):
            if os.path.exists(pattern):
                expanded_paths.add(pathlib.Path(pattern))
            else:
                matches = glob(pattern, recursive=True)
                for match in matches:
                    expanded_paths.add(pathlib.Path(match))
        else:
            full_pattern = os.path.join(base_path, pattern) if base_path != "." else pattern
            if os.path.exists(full_pattern):
                expanded_paths.add(pathlib.Path(full_pattern))
            else:
                matches = glob(full_pattern, recursive=True)
                for match in matches:
                    expanded_paths.add(pathlib.Path(match))
    
    # Get gitignore spec
    spec = get_gitignore_spec(base_path)
    
    # Add additional exclude patterns if provided
    if exclude_patterns:
        additional_patterns = [p.strip() for p in exclude_patterns.split(",")]
        additional_spec = PathSpec.from_lines(GitWildMatchPattern, additional_patterns)
        all_patterns = spec.patterns + additional_spec.patterns
        spec = PathSpec(all_patterns)
    
    # Get content
    return get_content(expanded_paths, spec)


def detect_language(path: str) -> str:
    """Detect the programming language based on file extension."""
    ext = os.path.splitext(path)[1].lower()
    # Common languages only - covers 95% of use cases
    languages = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".html": "html", ".css": "css", ".md": "markdown", 
        ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        ".sh": "bash", ".c": "c", ".cpp": "cpp", ".java": "java",
        ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
        ".sql": "sql", ".dockerfile": "dockerfile", ".toml": "toml",
        ".ipynb": "jupyter-notebook"
    }
    return languages.get(ext, "")


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
