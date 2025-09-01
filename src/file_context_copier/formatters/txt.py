"""Plain text formatter for simple output."""

from .base import BaseFormatter, ProjectInfo


class TxtFormatter(BaseFormatter):
    """Plain text formatter for simple, readable output."""
    
    @property
    def format_name(self) -> str:
        return "txt"
    
    @property
    def file_extension(self) -> str:
        return ".txt"
    
    def format_content(self, project_info: ProjectInfo) -> str:
        """Format content as plain text."""
        sections = []
        
        # Project header
        sections.append(f"PROJECT: {project_info.name.upper()}")
        
        if project_info.description:
            sections.append(f"DESCRIPTION: {project_info.description}")
        
        sections.append(f"GENERATED: {project_info.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"FILES: {project_info.total_files}")
        sections.append(f"SIZE: {self._format_size(project_info.total_size)}")
        sections.append(f"LINES: {project_info.total_lines:,}")
        
        # Add separator
        sections.append("")
        
        # File contents
        for i, file_info in enumerate(project_info.files):
            # File header
            file_header = self._format_file_header(file_info)
            sections.append(file_header)
            
            # File content with optional line numbers
            content = file_info.content
            if self._should_include_line_numbers():
                content = self._add_line_numbers(content)
            
            sections.append(content)
            
            # Add separator between files (but not after the last one)
            if i < len(project_info.files) - 1:
                sections.append(self.config.file_separator)
        
        return "\n".join(sections)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"