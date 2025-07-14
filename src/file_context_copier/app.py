"""CLI entry point for file-context-copier."""

import logging
from typing import Optional

import typer

# We import the Textual App from the tui module
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
) -> None:
    """
    Launches the interactive file context copier.
    """
    if output_file and output_dir:
        print("Error: --output-file and --output-dir cannot be used at the same time.")
        raise typer.Exit(code=1)

    logging.info(f"CLI tool started with path: {path}, output_file: {output_file}, output_dir: {output_dir}")
    # Instantiate the app from tui.py and run it, passing the new option
    copier_app = FileContextCopierApp(path, output_file, output_dir, as_txt)
    copier_app.run()


if __name__ == "__main__":
    app()
