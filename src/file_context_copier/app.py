"""Advanced CLI with format-first interface and configuration management."""

import os
from pathlib import Path
from typing import List, Optional

import typer

from .config import config_manager
from .core import process_paths_to_content
from .formatters import get_formatter, FORMATTERS

# The Typer app instance
app = typer.Typer(
    help="Advanced file context copier with configurable output formats."
)

# Configuration management subapp
config_app = typer.Typer(help="Configuration management commands.")
app.add_typer(config_app, name="config")


@app.command()
def markdown(
    paths: List[str] = typer.Argument(
        default=None,
        help="Files/folders to include. Supports glob patterns. If not provided, processes current directory."
    ),
    output: Optional[str] = typer.Option(
        None, "-o", "--output",
        help="Output file path. If not provided, copies to clipboard."
    ),
    base_path: str = typer.Option(
        ".", "--base-path", "-p",
        help="Base directory to operate in."
    ),
    exclude: Optional[str] = typer.Option(
        None, "-e", "--exclude",
        help="Additional exclude patterns (comma-separated)."
    ),
    output_dir: Optional[str] = typer.Option(
        None, "-d", "--output-dir",
        help="Write each selection to separate files in directory."
    ),
) -> None:
    """Generate markdown format output (enhanced with metadata)."""
    _process_format("markdown", paths, output, base_path, exclude, output_dir)


@app.command()
def txt(
    paths: List[str] = typer.Argument(
        default=None,
        help="Files/folders to include. Supports glob patterns."
    ),
    output: Optional[str] = typer.Option(
        None, "-o", "--output",
        help="Output file path. If not provided, copies to clipboard."
    ),
    base_path: str = typer.Option(
        ".", "--base-path", "-p",
        help="Base directory to operate in."
    ),
    exclude: Optional[str] = typer.Option(
        None, "-e", "--exclude",
        help="Additional exclude patterns (comma-separated)."
    ),
    output_dir: Optional[str] = typer.Option(
        None, "-d", "--output-dir",
        help="Write each selection to separate files in directory."
    ),
) -> None:
    """Generate plain text format output."""
    _process_format("txt", paths, output, base_path, exclude, output_dir)


def _process_format(
    format_name: str,
    paths: Optional[List[str]],
    output: Optional[str],
    base_path: str,
    exclude: Optional[str],
    output_dir: Optional[str]
) -> None:
    """Internal function to process files with specified format."""
    # Default to current directory if no paths provided
    if not paths:
        paths = ["."]

    # Get file content
    content = process_paths_to_content(paths, base_path, exclude)
    
    if not content:
        print(f"Error: No files found matching patterns: {paths}")
        raise typer.Exit(code=1)

    # Get formatter
    formatter = get_formatter(format_name)
    
    if output_dir:
        # Process each path separately for output_dir mode  
        print(f"Writing to directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        count = 0
        
        for path_pattern in paths:
            # Process each pattern separately
            single_content = process_paths_to_content([path_pattern], base_path, exclude)
            if not single_content:
                continue
                
            formatted_content = formatter.format_file_content(single_content, base_path)
            
            # Use pattern as filename (clean it up)
            safe_name = path_pattern.replace("/", "_").replace("*", "star").replace(".", "dot")
            output_filename = f"{safe_name}{formatter.file_extension}"
            output_filepath = os.path.join(output_dir, output_filename)
            
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(formatted_content)
            count += 1
        
        print(f"✓ {count} context file(s) written to {output_dir}")
        return

    # Format content
    formatted_content = formatter.format_file_content(content, base_path)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        print(f"✓ Content from {len(content)} files written to {output}")
    else:
        # Clipboard functionality (both formats support clipboard)
        try:
            import pyperclip
            pyperclip.copy(formatted_content)
            print(f"✓ Content from {len(content)} files copied to clipboard!")
        except ImportError:
            print("Error: pyperclip not available for clipboard operations.")
            print("Install with: uv pip install pyperclip")
            print("Or use --output option instead.")
            raise typer.Exit(code=1)


@config_app.command("get")
def config_get(
    key: str = typer.Argument(help="Configuration key to get (e.g., 'defaults.output_format')")
) -> None:
    """Get a configuration value."""
    config = config_manager.config
    try:
        # Navigate nested config structure
        value = config
        for part in key.split('.'):
            value = getattr(value, part)
        print(f"{key}: {value}")
    except AttributeError:
        print(f"Error: Configuration key '{key}' not found.")
        raise typer.Exit(code=1)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(help="Configuration key to set"),
    value: str = typer.Argument(help="Value to set")
) -> None:
    """Set a configuration value."""
    config = config_manager.config
    
    # Navigate to parent and set value
    parts = key.split('.')
    target = config
    for part in parts[:-1]:
        target = getattr(target, part)
    
    # Convert value to appropriate type
    attr_name = parts[-1]
    current_value = getattr(target, attr_name)
    
    if isinstance(current_value, bool):
        converted_value = value.lower() in ("true", "1", "yes", "on")
    elif isinstance(current_value, int):
        converted_value = int(value)
    elif isinstance(current_value, list):
        converted_value = [item.strip() for item in value.split(',')]
    else:
        converted_value = value
    
    setattr(target, attr_name, converted_value)
    config_manager.save_global_config(config)
    print(f"✓ Set {key} = {converted_value}")


@config_app.command("edit")
def config_edit() -> None:
    """Open configuration file in default editor."""
    config_file = config_manager.global_config_path
    
    # Create config file if it doesn't exist
    if not config_file.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_manager.save_global_config(config_manager.config)
    
    # Open in editor
    editor = os.getenv("EDITOR", "nano")
    os.system(f"{editor} {config_file}")
    print(f"✓ Configuration file: {config_file}")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    config = config_manager.config
    print("Current Configuration:")
    print(f"  Limits:")
    print(f"    Max file size: {config.limits.max_file_size_mb} MB")
    print(f"    Max total files: {config.limits.max_total_files}")
    print(f"    Max memory: {config.limits.max_memory_mb} MB")
    print(f"  Defaults:")
    print(f"    Output format: {config.defaults.output_format}")
    print(f"    Exclude patterns: {config.defaults.exclude_patterns}")
    print(f"  Project:")
    print(f"    Name: {config.project.name or 'Not set'}")
    print(f"    Description: {config.project.description or 'Not set'}")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    log_level: str = typer.Option("info", "--log-level", help="Log level")
) -> None:
    """Start HTTP API service for background operation."""
    try:
        from .service import start_service
        start_service(host=host, port=port, log_level=log_level)
    except ImportError:
        print("Error: Service dependencies not installed.")
        print("Install with: uv pip install -e '.[service]'")
        raise typer.Exit(code=1)


@app.command()
def formats() -> None:
    """List available output formats."""
    print("Available output formats:")
    for name, formatter_class in FORMATTERS.items():
        formatter = formatter_class()
        print(f"  {name:<10} -> {formatter.file_extension:<6} ({formatter.__class__.__doc__ or 'No description'})")


if __name__ == "__main__":
    app()
