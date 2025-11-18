"""
Pytest configuration and shared fixtures.
https://github.com/Water-Run/luainstallers/tree/main/luainstaller

:author: WaterRun
:date: 2025-11-18
"""

import sys
from pathlib import Path

import pytest

SOURCE_DIR = Path(__file__).parent.parent / "luainstaller" / "source"
sys.path.insert(0, str(SOURCE_DIR))


@pytest.fixture
def temp_lua_project(tmp_path):
    """
    Create a temporary Lua project directory structure.
    
    Returns a dictionary with paths to various test files.
    """
    project = {
        'root': tmp_path,
        'files': {}
    }
    
    return project


@pytest.fixture
def create_lua_file(tmp_path):
    """
    Factory fixture to create Lua files with given content.
    
    Usage:
        path = create_lua_file('test.lua', 'print("hello")')
    """
    def _create_file(relative_path: str, content: str) -> Path:
        file_path = tmp_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    return _create_file