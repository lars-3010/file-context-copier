# File Context Copier - Implementation Plan

## Project Overview
A Python CLI tool for interactively selecting project files/folders and copying their content to clipboard as markdown code blocks with proper language detection.

## Tech Stack
- **Python 3.11+** (via Homebrew)
- **UV** for dependency management
- **TUI Framework**: `textual` for interactive file selection
- **Clipboard**: `pyperclip` for cross-platform clipboard operations
- **CLI**: `typer` for command-line interface

## Project Structure
```
file-context-copier/
├── pyproject.toml              # UV project config
├── README.md
├── src/
│   └── file_context_copier/
│       ├── __init__.py
│       ├── main.py             # CLI entry point
│       ├── core/
│       │   ├── __init__.py
│       │   ├── file_scanner.py    # File system traversal
│       │   ├── language_detector.py # Extension → language mapping
│       │   ├── formatter.py       # Markdown formatting
│       │   └── clipboard_manager.py # Clipboard operations
│       └── ui/
│           ├── __init__.py
│           ├── file_selector.py   # TUI for file selection
│           └── progress.py        # Progress indicators
└── tests/
    ├── __init__.py
    └── test_*.py
```

## Core Dependencies
```toml
[project]
dependencies = [
    "textual>=0.50.0",      # Modern TUI framework
    "typer>=0.9.0",         # CLI framework
    "pyperclip>=1.8.0",     # Clipboard operations
    "rich>=13.0.0",         # Enhanced terminal output
    "pathspec>=0.12.0",     # Gitignore-style pattern matching
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

## Core Components

### 1. Language Detector (`language_detector.py`)
```python
class LanguageDetector:
    """Maps file extensions to markdown language identifiers."""
    
    EXTENSION_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.rs': 'rust',
        '.go': 'go',
        '.php': 'php',
        '.rb': 'ruby',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.sh': 'bash',
        '.zsh': 'zsh',
        '.fish': 'fish',
        '.ps1': 'powershell',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'conf',
        '.sql': 'sql',
        '.md': 'markdown',
        '.rst': 'rst',
        '.tex': 'latex',
        '.r': 'r',
        '.R': 'r',
        '.m': 'matlab',
        '.pl': 'perl',
        '.lua': 'lua',
        '.vim': 'vim',
        '.dockerfile': 'dockerfile',
        '.tf': 'hcl',
        '.hcl': 'hcl',
        '.graphql': 'graphql',
        '.proto': 'protobuf',
        '.thrift': 'thrift',
    }
    
    @classmethod
    def detect_language(cls, file_path: Path) -> str:
        """Returns language identifier for markdown code block."""
        # Handle special cases (Dockerfile, Makefile, etc.)
        # Then fall back to extension mapping
        # Default to 'text' for unknown extensions
```

### 2. File Scanner (`file_scanner.py`)
```python
class FileScanner:
    """Scans directory structure and applies filtering rules."""
    
    def __init__(self, exclude_patterns: Optional[List[str]] = None):
        # Default exclusions: .git/, node_modules/, __pycache__/, etc.
        
    def scan_directory(self, root_path: Path) -> List[FileItem]:
        """Returns tree structure of files and directories."""
        
    def is_text_file(self, file_path: Path) -> bool:
        """Determines if file is readable text (not binary)."""
        
    def should_include(self, path: Path) -> bool:
        """Applies exclusion patterns."""

@dataclass
class FileItem:
    path: Path
    is_directory: bool
    size: int
    children: Optional[List['FileItem']] = None
```

### 3. File Selector TUI (`file_selector.py`)
```python
class FileSelector(App):
    """Textual-based TUI for interactive file selection."""
    
    CSS_PATH = "file_selector.css"
    
    def __init__(self, root_path: Path):
        super().__init__()
        self.root_path = root_path
        self.selected_items: Set[Path] = set()
        
    def compose(self) -> ComposeResult:
        """Yield child widgets."""
        yield Header()
        yield DirectoryTree(self.root_path)
        yield Footer()
        
    def on_tree_node_selected(self, event) -> None:
        """Handle file/folder selection."""
        
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts:
        - Space: Toggle selection
        - Enter: Confirm and process
        - Ctrl+A: Select all
        - Ctrl+D: Deselect all
        - Escape: Cancel
        """
        
    def get_selected_files(self) -> List[Path]:
        """Returns list of selected file paths."""
```

### 4. Formatter (`formatter.py`)
```python
class MarkdownFormatter:
    """Formats file content as markdown with code blocks."""
    
    def __init__(self, language_detector: LanguageDetector):
        self.language_detector = language_detector
        
    def format_files(self, file_paths: List[Path]) -> str:
        """Formats selected files as markdown string."""
        # Structure:
        # ## File: path/to/file.py
        # ```python
        # file content here
        # ```
        #
        # ## File: path/to/other.js
        # ```javascript
        # other file content
        # ```
        
    def format_single_file(self, file_path: Path) -> str:
        """Formats single file with proper language detection."""
        
    def read_file_safely(self, file_path: Path) -> str:
        """Reads file with encoding detection and error handling."""
```

### 5. CLI Interface (`main.py`)
```python
app = typer.Typer(help="Interactive file context copier")

@app.command()
def select(
    path: Path = typer.Argument(default=".", help="Root directory to scan"),
    exclude: List[str] = typer.Option([], "--exclude", "-x", help="Exclude patterns"),
    include_hidden: bool = typer.Option(False, "--hidden", help="Include hidden files"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to file instead of clipboard"),
    max_file_size: int = typer.Option(1024*1024, "--max-size", help="Max file size in bytes"),
) -> None:
    """Interactive file selection and clipboard copy."""
    
@app.command()
def quick(
    files: List[Path] = typer.Argument(..., help="Files to copy directly"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Quick mode: copy specified files without selection UI."""

@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current config"),
    reset: bool = typer.Option(False, "--reset", help="Reset to defaults"),
) -> None:
    """Manage configuration."""
```

## Installation & Setup

### 1. System Prerequisites
```bash
# Install Python via Homebrew
brew install python@3.11

# Install UV
brew install uv
```

### 2. Project Setup
```bash
# Create project
mkdir file-context-copier
cd file-context-copier

# Initialize UV project
uv init --python 3.11

# Install dependencies
uv add textual typer pyperclip rich pathspec

# Install dev dependencies
uv add --dev pytest black ruff

# Make CLI available
uv pip install -e .
```

### 3. pyproject.toml Configuration
```toml
[project.scripts]
fcc = "file_context_copier.main:app"
```

## Usage Examples

```bash
# Interactive selection from current directory
fcc

# Interactive selection from specific path
fcc ~/projects/my-app

# Quick mode for specific files
fcc quick src/main.py tests/test_main.py

# With custom exclusions
fcc --exclude "*.log" --exclude "build/*"

# Output to file instead of clipboard
fcc --output context.md

# Include hidden files
fcc --hidden
```

## Key Features

### Interactive Selection
- Tree view of directory structure
- Multi-select with checkboxes
- Keyboard shortcuts for efficiency
- Real-time preview of selection size

### Smart Defaults
- Excludes common non-source files (.git, node_modules, __pycache__, etc.)
- Detects binary files automatically
- Language detection for 30+ file types
- File size limits to prevent clipboard overflow

### Output Formats
- Clipboard (default)
- File output
- Structured markdown with headers
- Language-specific code blocks

## Future Enhancements
- Configuration file support
- Project-specific presets
- Custom language mappings
- Integration with popular editors
- Template system for different output formats

## Testing Strategy
- Unit tests for core components
- Integration tests for file operations
- TUI testing with textual testing framework
- Cross-platform clipboard testing