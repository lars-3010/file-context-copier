"""Configuration management for file-context-copier."""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import tomllib
from dataclasses import dataclass, field


@dataclass
class LimitsConfig:
    """File and memory limits configuration."""
    max_file_size_mb: int = 10
    max_total_files: int = 1000
    max_memory_mb: int = 500


@dataclass 
class DefaultsConfig:
    """Default behavior configuration."""
    output_format: str = "markdown"
    exclude_patterns: list[str] = field(default_factory=lambda: [
        ".git/**", "node_modules/**", "__pycache__/**", "*.pyc", ".DS_Store"
    ])
    include_binary: bool = False


@dataclass
class ProjectConfig:
    """Project-specific configuration."""
    name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class FormatConfig:
    """Format-specific configuration."""
    file_separator: str = "\n\n---\n\n"
    code_block_style: str = "```{language}\n{content}\n```"
    file_header: str = "**`{path}`**\n\n"
    pretty_print: bool = True
    include_metadata: bool = True
    include_line_numbers: bool = False
    syntax_highlighting: bool = True
    theme: str = "github"
    include_toc: bool = True


@dataclass
class Config:
    """Main configuration class."""
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)
    languages: Dict[str, str] = field(default_factory=lambda: {
        ".py": "python",
        ".js": "javascript", 
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".html": "html",
        ".css": "css",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".sh": "bash",
        ".c": "c",
        ".cpp": "cpp",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".sql": "sql",
        ".dockerfile": "dockerfile",
        ".toml": "toml",
        ".ipynb": "jupyter-notebook"
    })
    formats: Dict[str, FormatConfig] = field(default_factory=lambda: {
        "markdown": FormatConfig(),
        "json": FormatConfig(pretty_print=True, include_metadata=True),
        "txt": FormatConfig(
            file_separator="\n" + "="*50 + "\n",
            file_header="{path} ({language}, {size} bytes)\n" + "="*50 + "\n"
        ),
        "html": FormatConfig(syntax_highlighting=True, theme="github", include_toc=True)
    })


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self):
        self.global_config_path = Path.home() / ".fcc" / "config.toml"
        self.project_config_path = Path(".fcc.toml")
        self._config: Optional[Config] = None
    
    @property
    def config(self) -> Config:
        """Get the current configuration, loading if necessary."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def load_config(self) -> Config:
        """Load configuration from files and environment variables."""
        # Start with default configuration
        config = Config()
        
        # Load global configuration
        if self.global_config_path.exists():
            try:
                with open(self.global_config_path, "rb") as f:
                    global_data = tomllib.load(f)
                config = self._merge_config(config, global_data)
            except Exception as e:
                logging.warning(f"Failed to load global config: {e}")
        
        # Load project configuration  
        if self.project_config_path.exists():
            try:
                with open(self.project_config_path, "rb") as f:
                    project_data = tomllib.load(f)
                config = self._merge_config(config, project_data)
            except Exception as e:
                logging.warning(f"Failed to load project config: {e}")
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        return config
    
    def _merge_config(self, base: Config, data: Dict[str, Any]) -> Config:
        """Merge configuration data into base configuration."""
        # Update limits
        if "limits" in data:
            for key, value in data["limits"].items():
                if hasattr(base.limits, key):
                    setattr(base.limits, key, value)
        
        # Update defaults
        if "defaults" in data:
            for key, value in data["defaults"].items():
                if hasattr(base.defaults, key):
                    setattr(base.defaults, key, value)
        
        # Update project info
        if "project" in data:
            for key, value in data["project"].items():
                if hasattr(base.project, key):
                    setattr(base.project, key, value)
        
        # Update languages
        if "languages" in data:
            base.languages.update(data["languages"])
        
        # Update format configurations
        if "formats" in data:
            for format_name, format_data in data["formats"].items():
                if format_name not in base.formats:
                    base.formats[format_name] = FormatConfig()
                
                format_config = base.formats[format_name]
                for key, value in format_data.items():
                    if hasattr(format_config, key):
                        setattr(format_config, key, value)
        
        return base
    
    def _apply_env_overrides(self, config: Config) -> Config:
        """Apply environment variable overrides."""
        # Check for common environment overrides
        env_mappings = {
            "FCC_MAX_FILE_SIZE": ("limits", "max_file_size_mb", int),
            "FCC_MAX_TOTAL_FILES": ("limits", "max_total_files", int),
            "FCC_OUTPUT_FORMAT": ("defaults", "output_format", str),
        }
        
        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                try:
                    converted_value = type_func(value)
                    section_obj = getattr(config, section)
                    setattr(section_obj, key, converted_value)
                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid environment variable {env_var}={value}: {e}")
        
        return config
    
    def save_global_config(self, config: Config):
        """Save configuration to global config file."""
        # Create config directory if it doesn't exist
        self.global_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dict
        config_dict = self._config_to_dict(config)
        
        # Write TOML file
        with open(self.global_config_path, "w") as f:
            import tomli_w
            tomli_w.dump(config_dict, f)
    
    def _config_to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert configuration object to dictionary for serialization."""
        return {
            "limits": {
                "max_file_size_mb": config.limits.max_file_size_mb,
                "max_total_files": config.limits.max_total_files,
                "max_memory_mb": config.limits.max_memory_mb
            },
            "defaults": {
                "output_format": config.defaults.output_format,
                "exclude_patterns": config.defaults.exclude_patterns,
                "include_binary": config.defaults.include_binary
            },
            "project": {
                "name": config.project.name,
                "description": config.project.description
            },
            "languages": config.languages,
            "formats": {
                name: {
                    "file_separator": fmt.file_separator,
                    "code_block_style": fmt.code_block_style,
                    "file_header": fmt.file_header,
                    "pretty_print": fmt.pretty_print,
                    "include_metadata": fmt.include_metadata,
                    "include_line_numbers": fmt.include_line_numbers,
                    "syntax_highlighting": fmt.syntax_highlighting,
                    "theme": fmt.theme,
                    "include_toc": fmt.include_toc
                } for name, fmt in config.formats.items()
            }
        }
    
    def get_language(self, file_path: str) -> str:
        """Get language for file based on extension."""
        ext = Path(file_path).suffix.lower()
        return self.config.languages.get(ext, "")
    
    def get_format_config(self, format_name: str) -> FormatConfig:
        """Get format configuration for specified format."""
        return self.config.formats.get(format_name, FormatConfig())


# Global configuration manager instance
config_manager = ConfigManager()