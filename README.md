# File Context Copier

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![CLI](https://img.shields.io/badge/interface-CLI-orange.svg)

A fast CLI tool for copying project file contents to clipboard or files as formatted markdown. Perfect for sharing code context with AI, colleagues, or documentation.

**✨ Key Features:** Glob patterns • Jupyter notebooks • Docker support • Background service

## Quick Start

```bash
# Install
uv venv && source .venv/bin/activate
uv pip install -e .

# Basic usage - copy current directory to clipboard  
fcc

# Copy specific files/folders
fcc src/ README.md

# Use glob patterns
fcc "**/*.py" "**/*.md"

# Save to file instead of clipboard
fcc src/ --output-file context.md
```

## Installation

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/) package manager

```bash
git clone <your-repo-url>
cd file-context-copier
uv venv && source .venv/bin/activate
uv pip install -e .
```

**Optional dependencies:**
```bash
uv pip install -e '.[clipboard]'  # For clipboard support
uv pip install -e '.[service]'   # For HTTP API server
```

## Usage

### Common Patterns

```bash
# Current directory to clipboard
fcc

# Specific files and folders  
fcc src/ tests/ README.md

# Glob patterns for file selection
fcc "**/*.py" "**/*.md" "src/**/*.ts"

# Different base directory
fcc --base-path ~/my-project src/ tests/

# Additional exclusions beyond .gitignore
fcc . --exclude "*.log,tmp/,**/__pycache__/**"
```

### Output Options

```bash
# Save to single file
fcc src/ --output-file context.md

# Save each selection to separate files
fcc src/ tests/ --output-dir ./output/

# Save as .txt files instead of .md
fcc src/ --output-dir ./output/ --as-txt
```

### Jupyter Notebook Support

Automatically converts `.ipynb` files to clean markdown:
- Preserves cell structure (markdown → markdown, code → code blocks)  
- Detects kernel language (Python, R, Julia, etc.)
- No messy JSON metadata

## Background Service Mode

Run as HTTP API service for remote operation and Docker deployment.

```bash
# Install service dependencies
uv pip install -e '.[service]'

# Start HTTP API server
fcc serve --host 0.0.0.0 --port 8000

# Or run with Docker
docker-compose up -d
```

**API endpoints:**
- `GET /health` - Health check
- `POST /process` - Process files and return content

**Example API usage:**
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"paths": ["src/**/*.py"], "base_path": "/workspace"}'
```

## Essential Commands

```bash
# Help
fcc --help

# Most common usage - current dir to clipboard
fcc  

# Copy specific files
fcc src/ README.md

# Use patterns  
fcc "**/*.py"

# Save to file
fcc src/ -o context.md

# Run as service
fcc serve
```
