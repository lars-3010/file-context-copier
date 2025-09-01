"""CLI entry point for file-context-copier."""

import os
from typing import List, Optional

import typer

from .core import format_content, process_paths_to_content

# The Typer app instance
app = typer.Typer(
    help="A tool to copy file/folder contents to clipboard as markdown."
)



@app.command()
def main(
    paths: List[str] = typer.Argument(
        default=None,
        help="Files/folders to include. Supports glob patterns. If not provided, processes current directory."
    ),
    base_path: str = typer.Option(
        ".", "--base-path", "-p",
        help="Base directory to operate in."
    ),
    output_file: Optional[str] = typer.Option(
        None,
        "--output-file",
        "-o",
        help="Write all output to a single file instead of the clipboard.",
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Write output to a new directory, with one file per selected item.",
    ),
    as_txt: bool = typer.Option(
        False,
        "--as-txt",
        help="Save output files as .txt instead of .md when using --output-dir.",
    ),
    exclude_patterns: Optional[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Additional exclude patterns (comma-separated), beyond .gitignore."
    ),
) -> None:
    """
    Copy file/folder contents to clipboard as markdown or save to files.
    
    Examples:
      fcc                           # Process current directory  
      fcc src/ tests/               # Process specific folders
      fcc "**/*.py" "*.md"          # Use glob patterns
      fcc . --exclude "*.log,temp/" # Exclude additional patterns
    """
    if output_file and output_dir:
        print("Error: --output-file and --output-dir cannot be used at the same time.")
        raise typer.Exit(code=1)

    # Default to current directory if no paths provided
    if not paths:
        paths = ["."]

    # Use shared processing function
    content = process_paths_to_content(paths, base_path, exclude_patterns)
    
    if not content:
        print(f"Error: No files or directories found matching the provided patterns: {paths}")
        raise typer.Exit(code=1)

    if output_dir:
        # Process each path separately for output_dir mode  
        print(f"Writing to directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        count = 0
        
        for path_pattern in paths:
            # Process each pattern separately for output_dir mode
            single_content = process_paths_to_content([path_pattern], base_path, exclude_patterns)
            if not single_content:
                continue
                
            formatted_content = format_content(single_content)
            
            file_extension = ".txt" if as_txt else ".md"
            # Use pattern as filename (clean it up)
            safe_name = path_pattern.replace("/", "_").replace("*", "star").replace(".", "dot")
            output_filename = f"{safe_name}{file_extension}"
            output_filepath = os.path.join(output_dir, output_filename)
            
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(formatted_content)
            count += 1
        
        print(f"✓ {count} context file(s) written to {output_dir}")
        return

    formatted_content = format_content(content)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        print(f"✓ Content from {len(content)} files written to {output_file}")
    else:
        # Optional clipboard functionality
        try:
            import pyperclip
            pyperclip.copy(formatted_content)
            print(f"✓ Content from {len(content)} files copied to clipboard!")
        except ImportError:
            print("Error: pyperclip not available for clipboard operations.")
            print("Install with: uv pip install pyperclip")
            print("Or use --output-file option instead.")
            raise typer.Exit(code=1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    log_level: str = typer.Option("info", "--log-level", help="Log level (debug, info, warning, error)")
) -> None:
    """Start HTTP API service for background operation."""
    try:
        from .service import start_service
        start_service(host=host, port=port, log_level=log_level)
    except ImportError:
        print("Error: Service dependencies not installed.")
        print("Install with: uv pip install -e '.[service]'")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
