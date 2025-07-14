import pathlib
from unittest.mock import MagicMock

import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from file_context_copier.app import FileContextCopier


@pytest.fixture
def app(tmp_path: pathlib.Path) -> FileContextCopier:
    """Return a FileContextCopier instance."""
    return FileContextCopier(str(tmp_path))


@pytest.fixture
def spec() -> PathSpec:
    """Return a PathSpec instance."""
    return PathSpec.from_lines(GitWildMatchPattern, [])


def test_get_content(app: FileContextCopier, tmp_path: pathlib.Path) -> None:
    """Test the _get_content method."""
    (tmp_path / "file1.txt").write_text("content1")
    (tmp_path / "file2.txt").write_text("content2")
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file3.txt").write_text("content3")

    paths = {
        tmp_path / "file1.txt",
        tmp_path / "dir1",
    }

    content = app._get_content(paths)

    assert content == {
        str(tmp_path / "file1.txt"): "content1",
        str(tmp_path / "dir1" / "file3.txt"): "content3",
    }


def test_format_content(app: FileContextCopier) -> None:
    """Test the _format_content method."""
    content = {
        "file1.py": "print('hello')",
        "file2.html": "<h1>hello</h1>",
    }

    formatted_content = app._format_content(content)

    assert formatted_content == (
        """**file1.py**

````python
print('hello')
````"""
        """\n\n**file2.html**\n\n````html\n<h1>hello</h1>\n````"""
    )

