"""Enhanced Markdown formatter."""

from .base import BaseFormatter, ProjectInfo


class MarkdownFormatter(BaseFormatter):
    """Enhanced Markdown formatter with metadata and project info."""
    
    @property
    def format_name(self) -> str:
        return "markdown"
    
    @property
    def file_extension(self) -> str:
        return ".md"
    
    def format_content(self, project_info: ProjectInfo) -> str:
        """Format content as enhanced markdown."""
        sections = []
        
        # Project header
        sections.append(f"# {project_info.name}")
        
        if project_info.description:
            sections.append(project_info.description)
        
        # Metadata section
        if self._should_include_metadata():
            sections.append(self._format_metadata_section(project_info))
        
        # Files section
        sections.append(f"## Files Processed: {project_info.total_files}")
        
        # File contents
        file_sections = []
        for file_info in project_info.files:
            file_content = []
            
            # File header
            file_content.append(self._format_file_header(file_info))
            
            # File content with optional line numbers
            content = file_info.content
            if self._should_include_line_numbers():
                content = self._add_line_numbers(content)
            
            # Format based on file type
            if file_info.language == "jupyter-notebook":
                # Jupyter notebooks are already formatted as markdown
                file_content.append(content)
            elif file_info.language == "markdown":
                # Markdown files - preserve as-is but indicate they're markdown
                file_content.append(f"```markdown\n{content}\n```")
            else:
                # Regular code files
                file_content.append(self._format_code_block(file_info))
            
            file_sections.append("\n".join(file_content))
        
        # Join all file sections
        sections.append(self.config.file_separator.join(file_sections))
        
        return "\n\n".join(sections)
    
    def _format_metadata_section(self, project_info: ProjectInfo) -> str:
        """Format metadata as markdown section."""
        metadata = []
        metadata.append("## Project Information")
        metadata.append(f"- **Generated:** {project_info.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        metadata.append(f"- **Total Files:** {project_info.total_files}")
        metadata.append(f"- **Total Size:** {self._format_size(project_info.total_size)}")
        metadata.append(f"- **Total Lines:** {project_info.total_lines:,}")
        
        # Language breakdown
        language_counts = {}
        for file_info in project_info.files:
            lang = file_info.language or "unknown"
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        if language_counts:
            metadata.append("- **Languages:**")
            for lang, count in sorted(language_counts.items()):
                metadata.append(f"  - {lang}: {count} file{'s' if count != 1 else ''}")
        
        return "\n".join(metadata)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"