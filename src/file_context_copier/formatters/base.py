"""Base formatter class for output generation."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import os

from ..config import config_manager, FormatConfig


class FileInfo:
    """Information about a processed file."""
    
    def __init__(self, path: str, content: str, language: str = ""):
        self.path = path
        self.content = content
        self.language = language or config_manager.get_language(path)
        self.size = len(content.encode('utf-8'))
        self.line_count = content.count('\n') + 1 if content else 0
        self.relative_path = os.path.relpath(path)


class ProjectInfo:
    """Information about the processed project."""
    
    def __init__(self, files: List[FileInfo], base_path: str = "."):
        self.files = files
        self.base_path = base_path
        self.name = config_manager.config.project.name or Path(base_path).name
        self.description = config_manager.config.project.description
        self.generated_at = datetime.now()
        self.total_files = len(files)
        self.total_size = sum(f.size for f in files)
        self.total_lines = sum(f.line_count for f in files)


class BaseFormatter(ABC):
    """Abstract base class for output formatters."""
    
    def __init__(self):
        self.config = config_manager.get_format_config(self.format_name)
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Name of this formatter."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Default file extension for this format."""
        pass
    
    @abstractmethod
    def format_content(self, project_info: ProjectInfo) -> str:
        """Format project content according to this formatter's rules."""
        pass
    
    def format_file_content(self, files: Dict[str, str], base_path: str = ".") -> str:
        """Format file content dictionary into output string."""
        # Convert dict to FileInfo objects
        file_infos = []
        for path, content in files.items():
            file_infos.append(FileInfo(path, content))
        
        # Create project info
        project_info = ProjectInfo(file_infos, base_path)
        
        # Format content
        return self.format_content(project_info)
    
    def _format_file_header(self, file_info: FileInfo) -> str:
        """Format file header using template."""
        return self.config.file_header.format(
            path=file_info.relative_path,
            language=file_info.language,
            size=file_info.size,
            lines=file_info.line_count
        )
    
    def _format_code_block(self, file_info: FileInfo) -> str:
        """Format code block using template."""
        return self.config.code_block_style.format(
            language=file_info.language,
            content=file_info.content
        )
    
    def _should_include_metadata(self) -> bool:
        """Check if metadata should be included."""
        return getattr(self.config, 'include_metadata', False)
    
    def _should_include_line_numbers(self) -> bool:
        """Check if line numbers should be included."""
        return getattr(self.config, 'include_line_numbers', False)
    
    def _add_line_numbers(self, content: str) -> str:
        """Add line numbers to content."""
        lines = content.split('\n')
        max_width = len(str(len(lines)))
        numbered_lines = []
        
        for i, line in enumerate(lines, 1):
            line_num = str(i).rjust(max_width)
            numbered_lines.append(f"{line_num}: {line}")
        
        return '\n'.join(numbered_lines)
    
    def _format_metadata(self, project_info: ProjectInfo) -> Dict[str, Any]:
        """Generate metadata dictionary."""
        return {
            "project": project_info.name,
            "description": project_info.description,
            "generated_at": project_info.generated_at.isoformat(),
            "base_path": project_info.base_path,
            "total_files": project_info.total_files,
            "total_size": project_info.total_size,
            "total_lines": project_info.total_lines,
            "files": [
                {
                    "path": f.relative_path,
                    "language": f.language,
                    "size": f.size,
                    "lines": f.line_count
                }
                for f in project_info.files
            ]
        }