r"""
Dependency analysis engine for Lua scripts.
https://github.com/Water-Run/luainstallers/tree/main/luainstaller

This module provides comprehensive dependency analysis for Lua scripts,
including static require extraction, module path resolution, and dependency
tree construction with cycle detection.

:author: WaterRun
:file: dependency_analyzer.py
:date: 2025-11-18
"""

import re
import subprocess
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from exceptions import (
    CModuleNotSupportedError,
    CircularDependencyError,
    DependencyLimitExceededError,
    DynamicRequireError,
    ModuleNotFoundError,
    ScriptNotFoundError,
)


class LexerState(Enum):
    r"""Enumeration of lexer states for parsing Lua source code."""
    
    NORMAL = auto()             # Normal code
    IN_STRING_SINGLE = auto()   # Inside 'string'
    IN_STRING_DOUBLE = auto()   # Inside "string"
    IN_LONG_STRING = auto()     # Inside [[string]]
    IN_LINE_COMMENT = auto()    # Inside -- comment
    IN_BLOCK_COMMENT = auto()   # Inside --[[ comment ]]


class LuaLexer:
    r"""
    Lightweight Lua lexer focused on extracting static require statements.
    
    This lexer uses a state machine to correctly handle Lua's various string
    and comment formats, ensuring that require statements inside strings or
    comments are not mistakenly extracted.
    """
    
    def __init__(self, source_code: str, file_path: str) -> None:
        r"""
        Initialize the Lua lexer.
        
        :param source_code: The Lua source code to analyze
        :param file_path: Path to the source file (for error reporting)
        """
        self.source = source_code
        self.file_path = file_path
        self.pos = 0
        self.line = 1
        self.state = LexerState.NORMAL
        self.long_bracket_level = 0  # For [=*[ ]=*] matching
    
    def extract_requires(self) -> list[tuple[str, int]]:
        r"""
        Extract all static require statements from the source code.
        
        :return: List of (module_name, line_number) tuples
        :raises DynamicRequireError: If a dynamic require is detected
        """
        requires = []
        
        while self.pos < len(self.source):
            char = self._current_char()
            
            # Update state machine
            self._update_state(char)
            
            # Only process require in NORMAL state
            if self.state == LexerState.NORMAL:
                if self._match_keyword('require'):
                    module_name = self._parse_require()
                    if module_name:
                        requires.append((module_name, self.line))
            
            # Track line numbers
            if char == '\n':
                self.line += 1
            
            self.pos += 1
        
        return requires
    
    def _current_char(self) -> str:
        r"""Get the current character, or empty string if at end."""
        if self.pos >= len(self.source):
            return ''
        return self.source[self.pos]
    
    def _peek_char(self, offset: int = 1) -> str:
        r"""Peek ahead at a character without advancing position."""
        peek_pos = self.pos + offset
        if peek_pos >= len(self.source):
            return ''
        return self.source[peek_pos]
    
    def _match_keyword(self, keyword: str) -> bool:
        r"""
        Check if the current position matches a keyword.
        
        Must be surrounded by non-identifier characters to avoid matching
        'required' when looking for 'require', and should not be part of
        a table/instance member access like obj.require or obj:require.
        """
        # Check forward match
        if not self.source[self.pos:].startswith(keyword):
            return False
        
        # Check previous character: cannot be identifier or member access
        prev_pos = self.pos - 1
        if prev_pos >= 0:
            prev_char = self.source[prev_pos]
            if prev_char.isalnum() or prev_char in ('_', '.', ':'):
                return False
        
        # Check that it's not part of a longer identifier (next char)
        next_pos = self.pos + len(keyword)
        if next_pos < len(self.source):
            next_char = self.source[next_pos]
            if next_char.isalnum() or next_char == '_':
                return False
        
        return True
    
    def _update_state(self, char: str) -> None:
        r"""Update the lexer state machine based on current character."""
        
        if self.state == LexerState.NORMAL:
            # Check for comment start
            if char == '-' and self._peek_char() == '-':
                # Check for block comment
                if self._peek_char(2) == '[':
                    level = self._count_bracket_level(2)
                    if level >= 0:
                        self.state = LexerState.IN_BLOCK_COMMENT
                        self.long_bracket_level = level
                        return
                # Line comment
                self.state = LexerState.IN_LINE_COMMENT
            
            # Check for string start
            elif char == "'":
                self.state = LexerState.IN_STRING_SINGLE
            elif char == '"':
                self.state = LexerState.IN_STRING_DOUBLE
            elif char == '[':
                level = self._count_bracket_level(0)
                if level >= 0:
                    self.state = LexerState.IN_LONG_STRING
                    self.long_bracket_level = level
        
        elif self.state == LexerState.IN_STRING_SINGLE:
            if char == "'" and self._is_not_escaped():
                self.state = LexerState.NORMAL
        
        elif self.state == LexerState.IN_STRING_DOUBLE:
            if char == '"' and self._is_not_escaped():
                self.state = LexerState.NORMAL
        
        elif self.state == LexerState.IN_LONG_STRING:
            if char == ']' and self._check_closing_bracket(self.long_bracket_level):
                self.state = LexerState.NORMAL
        
        elif self.state == LexerState.IN_LINE_COMMENT:
            if char == '\n':
                self.state = LexerState.NORMAL
        
        elif self.state == LexerState.IN_BLOCK_COMMENT:
            if char == ']' and self._check_closing_bracket(self.long_bracket_level):
                self.state = LexerState.NORMAL
    
    def _is_not_escaped(self) -> bool:
        r"""Check if the current character is not escaped by backslash."""
        if self.pos == 0:
            return True
        
        # Count consecutive backslashes before current position
        backslash_count = 0
        check_pos = self.pos - 1
        while check_pos >= 0 and self.source[check_pos] == '\\':
            backslash_count += 1
            check_pos -= 1
        
        # If even number of backslashes, current char is not escaped
        return backslash_count % 2 == 0
    
    def _count_bracket_level(self, start_offset: int) -> int:
        r"""
        Count the level of a long bracket [=*[.
        
        :param start_offset: Offset from current position to start of bracket
        :return: Level (number of =), or -1 if not a valid long bracket
        """
        pos = self.pos + start_offset
        if pos >= len(self.source) or self.source[pos] != '[':
            return -1
        
        pos += 1
        level = 0
        
        while pos < len(self.source) and self.source[pos] == '=':
            level += 1
            pos += 1
        
        if pos < len(self.source) and self.source[pos] == '[':
            return level
        
        return -1
    
    def _check_closing_bracket(self, expected_level: int) -> bool:
        r"""Check if current position starts a closing bracket ]=*] with matching level."""
        if self._current_char() != ']':
            return False
        
        pos = self.pos + 1
        level = 0
        
        while pos < len(self.source) and self.source[pos] == '=':
            level += 1
            pos += 1
        
        if pos < len(self.source) and self.source[pos] == ']' and level == expected_level:
            return True
        
        return False
    
    def _parse_require(self) -> Optional[str]:
        r"""
        Parse a require statement and extract the module name.
        
        :return: Module name if static, None to skip
        :raises DynamicRequireError: If the require is dynamic
        """
        # Save position for error reporting
        start_pos = self.pos
        start_line = self.line
        
        # Skip 'require' keyword
        self.pos += len('require')
        
        # Skip whitespace
        while self.pos < len(self.source) and self._current_char() in ' \t\n\r':
            if self._current_char() == '\n':
                self.line += 1
            self.pos += 1
        
        # Check what comes next
        char = self._current_char()
        
        # Case 1: require('module') or require("module")
        if char == '(':
            self.pos += 1
            # Skip whitespace after (
            while self.pos < len(self.source) and self._current_char() in ' \t\n\r':
                if self._current_char() == '\n':
                    self.line += 1
                self.pos += 1
            
            char = self._current_char()
        
        # Extract string literal
        if char in ('"', "'"):
            return self._extract_string_literal(start_line)
        elif char == '[':
            level = self._count_bracket_level(0)
            if level >= 0:
                return self._extract_long_string_literal(level, start_line)
        
        # If we get here, it's a dynamic require
        # Extract the statement for error reporting
        end_pos = self.pos
        while end_pos < len(self.source) and self.source[end_pos] not in '\n;':
            end_pos += 1
        
        statement = self.source[start_pos:end_pos].strip()
        
        raise DynamicRequireError(
            self.file_path,
            start_line,
            statement
        )
    
    def _extract_string_literal(self, start_line: int) -> str:
        r"""
        Extract a string literal (single or double quoted).
        
        :param start_line: Line number where require started (for error reporting)
        :return: The string content
        :raises DynamicRequireError: If string concatenation is detected
        """
        quote_char = self._current_char()
        self.pos += 1
        
        result = []
        
        while self.pos < len(self.source):
            char = self._current_char()
            
            if char == quote_char and self._is_not_escaped():
                self.pos += 1
                # Check for concatenation
                self._check_no_concatenation(start_line, ''.join(result))
                return ''.join(result)
            
            if char == '\\':
                # Skip escape sequences
                result.append(char)
                self.pos += 1
                if self.pos < len(self.source):
                    result.append(self._current_char())
            else:
                result.append(char)
            
            self.pos += 1
        
        # Unterminated string
        raise DynamicRequireError(
            self.file_path,
            start_line,
            f"Unterminated string in require statement"
        )
    
    def _extract_long_string_literal(self, level: int, start_line: int) -> str:
        r"""
        Extract a long string literal [[...]].
        
        :param level: The bracket level
        :param start_line: Line number where require started
        :return: The string content
        """
        # Skip opening bracket
        self.pos += 2 + level
        
        result = []
        
        while self.pos < len(self.source):
            if self._current_char() == ']' and self._check_closing_bracket(level):
                # Skip closing bracket
                self.pos += 2 + level
                # Check for concatenation
                self._check_no_concatenation(start_line, ''.join(result))
                return ''.join(result)
            
            result.append(self._current_char())
            if self._current_char() == '\n':
                self.line += 1
            self.pos += 1
        
        # Unterminated long string
        raise DynamicRequireError(
            self.file_path,
            start_line,
            f"Unterminated long string in require statement"
        )
    
    def _check_no_concatenation(self, start_line: int, module_name: str) -> None:
        r"""
        Check that there's no string concatenation after the string literal.
        
        :param start_line: Line number where require started
        :param module_name: The extracted module name
        :raises DynamicRequireError: If concatenation is detected
        """
        # Skip whitespace
        saved_pos = self.pos
        while self.pos < len(self.source) and self._current_char() in ' \t\n\r':
            self.pos += 1
        
        # Check for ..
        if self.source[self.pos:self.pos + 2] == '..':
            raise DynamicRequireError(
                self.file_path,
                start_line,
                f"require('{module_name}' .. ...) - String concatenation not supported"
            )
        
        # Restore position
        self.pos = saved_pos


# ============================================================================
# Module Resolution
# ============================================================================


class ModuleResolver:
    r"""
    Resolves Lua module names to absolute file paths.
    
    This resolver handles:
    - Dot-separated module names (foo.bar.baz)
    - Relative paths (./module, ../module)
    - LuaRocks package paths
    - Standard Lua search patterns
    """
    
    # C module extensions that are not supported
    C_EXTENSIONS = {'.so', '.dll', '.dylib'}
    
    def __init__(self, base_path: Path) -> None:
        r"""
        Initialize the module resolver.
        
        :param base_path: Base directory for relative module resolution
        """
        self.base_path = base_path.resolve()
        self.search_paths = self._build_search_paths()
    
    def _detect_luarocks(self) -> list[Path]:
        r"""
        Detect LuaRocks installation and return module paths.
        
        :return: List of LuaRocks module paths
        """
        paths = []
        
        try:
            # Try to get Lua module path from luarocks
            result = subprocess.run(
                ['luarocks', 'path', '--lr-path'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse the output. On Windows LuaRocks usually uses ';',
                # on POSIX systems ':' is common.
                import os
                
                raw = result.stdout.strip()
                
                # In some LuaRocks versions the output may contain environment
                # variable assignments, e.g. LUA_PATH='...'; handle that crudely.
                if '=' in raw and os.linesep in raw:
                    # If it's a shell snippet, try to extract last line content
                    raw = raw.split(os.linesep)[-1].strip().strip("'").strip('"')
                
                sep = ';' if os.name == 'nt' else ':'
                lua_paths = raw.split(sep)
                
                for lua_path in lua_paths:
                    lua_path = lua_path.strip().strip("'").strip('"')
                    
                    # Remove common pattern suffixes only if they are at the end
                    if lua_path.endswith('?.lua'):
                        lua_path = lua_path[: -len('?.lua')]
                    elif lua_path.endswith('?/init.lua'):
                        lua_path = lua_path[: -len('?/init.lua')]
                    
                    lua_path = lua_path.strip()
                    if lua_path:
                        path_obj = Path(lua_path)
                        if path_obj.exists():
                            paths.append(path_obj.resolve())
        
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # LuaRocks not available or command failed
            pass
        
        return paths
    
    def _build_search_paths(self) -> list[Path]:
        r"""
        Build the complete list of module search paths.
        
        :return: List of paths to search for modules
        """
        paths = [
            self.base_path,  # Current script directory
        ]
        
        # Add common local module directories
        local_dirs = [
            self.base_path / 'lua_modules',
            self.base_path / 'lib',
            self.base_path / 'src',
        ]
        
        for local_dir in local_dirs:
            if local_dir.exists():
                paths.append(local_dir.resolve())
        
        # Add LuaRocks paths
        luarocks_paths = self._detect_luarocks()
        paths.extend(luarocks_paths)
        
        return paths
    
    def resolve(self, module_name: str, from_script: str) -> Path:
        r"""
        Resolve a module name to an absolute file path.
        
        :param module_name: The module name (e.g., 'foo.bar' or './local')
        :param from_script: Path of the script requiring this module
        :return: Absolute path to the module file
        :raises ModuleNotFoundError: If module cannot be found
        :raises CModuleNotSupportedError: If module is a C module
        """
        from_script_path = Path(from_script).resolve()
        
        # Handle relative paths
        if module_name.startswith('./') or module_name.startswith('../'):
            return self._resolve_relative(module_name, from_script_path)
        
        # Convert dot-separated name to path
        module_path = module_name.replace('.', '/')
        
        # Search in all search paths for Lua modules first
        for search_path in self.search_paths:
            lua_candidates = [
                search_path / f"{module_path}.lua",
                search_path / module_path / "init.lua",
            ]
            
            for candidate in lua_candidates:
                if candidate.exists():
                    return candidate.resolve()
            
            # After Lua candidates, check for C modules with known extensions
            for ext in self.C_EXTENSIONS:
                c_candidate = search_path / f"{module_path}{ext}"
                if c_candidate.exists():
                    raise CModuleNotSupportedError(
                        module_name,
                        str(c_candidate)
                    )
        
        # Module not found
        raise ModuleNotFoundError(
            module_name,
            from_script,
            [str(p) for p in self.search_paths]
        )
        
    def _resolve_relative(self, module_name: str, from_script_path: Path) -> Path:
        r"""
        Resolve a relative module path.
        
        :param module_name: Relative module name (e.g., './local' or '../parent')
        :param from_script_path: Absolute path of the requiring script
        :return: Absolute path to the module file
        :raises ModuleNotFoundError: If module cannot be found
        :raises CModuleNotSupportedError: If module is a C module
        """
        # Base directory is the parent of the requiring script
        base_dir = from_script_path.parent
        
        # Construct the path directly; Path will normalize ./ and ../
        target_path = (base_dir / module_name).resolve()
        
        # Try Lua module candidates
        candidates: list[Path] = []
        if target_path.suffix == '.lua':
            # User may have written require("./foo.lua")
            candidates.append(target_path)
        else:
            candidates.extend([
                Path(str(target_path) + '.lua'),
                target_path / 'init.lua',
            ])
        
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        
        # Try relative C modules (if present)
        for ext in self.C_EXTENSIONS:
            c_candidate = Path(str(target_path) + ext)
            if c_candidate.exists():
                raise CModuleNotSupportedError(
                    module_name,
                    str(c_candidate)
                )
        
        # Not found
        raise ModuleNotFoundError(
            module_name,
            str(from_script_path),
            [str(base_dir)]
        )

# ============================================================================
# Dependency Analysis
# ============================================================================


class DependencyAnalyzer:
    r"""
    Analyzes Lua script dependencies and builds dependency tree.
    
    This analyzer performs:
    - Recursive dependency extraction
    - Circular dependency detection
    - Dependency count limitation
    - Topological sorting of dependencies
    """
    
    def __init__(self, entry_script: str, max_dependencies: int = 36) -> None:
        r"""
        Initialize the dependency analyzer.
        
        :param entry_script: Path to the entry Lua script
        :param max_dependencies: Maximum number of dependencies allowed (default: 36)
        """
        self.entry_script = Path(entry_script).resolve()
        self.max_dependencies = max_dependencies
        
        if not self.entry_script.exists():
            raise ScriptNotFoundError(str(entry_script))
        
        self.resolver = ModuleResolver(self.entry_script.parent)
        
        self.visited: set[Path] = set()
        self.visiting: set[Path] = set()
        self.stack: list[Path] = []
        self.dependency_tree: dict[Path, list[Path]] = {}
    
    def analyze(self) -> list[str]:
        r"""
        Perform complete dependency analysis.
        
        :return: List of dependency file paths (absolute, topologically sorted)
        :raises CircularDependencyError: If circular dependency detected
        :raises DependencyLimitExceededError: If dependency count exceeds limit
        :raises DynamicRequireError: If dynamic require detected
        :raises ModuleNotFoundError: If a required module cannot be found
        :raises CModuleNotSupportedError: If a C module is encountered
        """
        self._analyze_recursive(self.entry_script)
        
        # Check total dependency limit
        total_count = len(self.visited) - 1  # Exclude entry script
        if total_count > self.max_dependencies:
            raise DependencyLimitExceededError(total_count, self.max_dependencies)
        
        # Generate topologically sorted manifest
        return self._generate_manifest()
    
    def _analyze_recursive(self, script_path: Path) -> None:
        r"""
        Recursively analyze a single script and its dependencies.
        
        :param script_path: Absolute path to the script
        :raises CircularDependencyError: If circular dependency detected
        """
        # Circular dependency detection using explicit stack
        if script_path in self.stack:
            idx = self.stack.index(script_path)
            chain = [str(p) for p in self.stack[idx:]] + [str(script_path)]
            raise CircularDependencyError(chain)
        
        # Already analyzed
        if script_path in self.visited:
            return
        
        # Verify script exists
        if not script_path.exists():
            raise ScriptNotFoundError(str(script_path))
        
        # Read source code
        try:
            source_code = script_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with other encodings
            try:
                source_code = script_path.read_text(encoding='gbk')
            except UnicodeDecodeError:
                source_code = script_path.read_text(encoding='latin-1')
        
        # Extract require statements
        lexer = LuaLexer(source_code, str(script_path))
        requires = lexer.extract_requires()
        
        # Mark as currently visiting
        self.visiting.add(script_path)
        self.stack.append(script_path)
        
        # Resolve and recursively analyze dependencies (deduplicated)
        dependencies: list[Path] = []
        seen: set[Path] = set()
        
        for module_name, line_number in requires:
            dep_path = self.resolver.resolve(module_name, str(script_path))
            if dep_path not in seen:
                seen.add(dep_path)
                dependencies.append(dep_path)
                self._analyze_recursive(dep_path)
        
        # Record dependency tree
        self.dependency_tree[script_path] = dependencies
        
        # Mark as completed
        self.stack.pop()
        self.visiting.remove(script_path)
        self.visited.add(script_path)

    def _generate_manifest(self) -> list[str]:
        r"""
        Generate topologically sorted dependency manifest.
        
        Dependencies are ordered such that each module appears before
        any module that depends on it.
        
        :return: List of dependency file paths (excluding entry script)
        """
        sorted_deps: list[str] = []
        visited: set[Path] = set()
        
        def visit(node: Path) -> None:
            if node in visited:
                return
            visited.add(node)
            
            # Visit dependencies first (post-order traversal)
            for dep in self.dependency_tree.get(node, []):
                visit(dep)
            
            sorted_deps.append(str(node))
        
        # Start from entry script
        visit(self.entry_script)
        
        # Remove entry script from manifest (it's handled separately)
        if str(self.entry_script) in sorted_deps:
            sorted_deps.remove(str(self.entry_script))
        
        return sorted_deps
    
    def print_tree(self, indent: int = 0, current: Optional[Path] = None) -> None:
        r"""
        Print the dependency tree in a readable format.
        
        Useful for the 'luainstaller analyze' command.
        
        :param indent: Current indentation level
        :param current: Current node (defaults to entry script)
        """
        if current is None:
            current = self.entry_script
            print(f"Dependency tree for {current.name}:")
        
        dependencies = self.dependency_tree.get(current, [])
        
        for i, dep in enumerate(dependencies):
            is_last = (i == len(dependencies) - 1)
            prefix = "└── " if is_last else "├── "
            print("  " * indent + prefix + dep.name)
            
            # Recursively print dependencies
            next_indent = indent + 1
            self.print_tree(next_indent, dep)


# ============================================================================
# Public API
# ============================================================================


def analyze_dependencies(
    entry_script: str,
    manual_mode: bool = False,
    max_dependencies: int = 36
) -> list[str]:
    r"""
    Analyze Lua script dependencies.
    
    This is the main entry point for dependency analysis. It performs
    static analysis of require statements and builds a complete dependency
    tree with cycle detection and topological sorting.
    
    :param entry_script: Path to the entry Lua script
    :param manual_mode: If True, skip automatic analysis and return empty list
    :param max_dependencies: Maximum number of dependencies allowed (default: 36)
    :return: List of dependency file paths (absolute, topologically sorted)
    :raises CircularDependencyError: If circular dependency detected
    :raises DependencyLimitExceededError: If dependency count exceeds limit
    :raises DynamicRequireError: If dynamic require detected
    :raises ModuleNotFoundError: If a required module cannot be found
    :raises CModuleNotSupportedError: If a C module is encountered
    :raises ScriptNotFoundError: If entry script not found
    
    Example:
        >>> deps = analyze_dependencies('main.lua')
        >>> print(deps)
        ['/path/to/utils.lua', '/path/to/config.lua', '/path/to/core.lua']
    """
    if manual_mode:
        return []
    
    analyzer = DependencyAnalyzer(entry_script, max_dependencies)
    return analyzer.analyze()


def print_dependency_tree(entry_script: str, max_dependencies: int = 36) -> None:
    r"""
    Print the dependency tree for a Lua script.
    
    This is a convenience function for the CLI 'analyze' command.
    
    :param entry_script: Path to the entry Lua script
    :param max_dependencies: Maximum number of dependencies allowed (default: 36)
    :raises: Same exceptions as analyze_dependencies
    
    Example:
        >>> print_dependency_tree('main.lua')
        Dependency tree for main.lua:
        ├── utils.lua
        ├── config.lua
        └── core.lua
            ├── database.lua
            └── network.lua
    """
    analyzer = DependencyAnalyzer(entry_script, max_dependencies)
    analyzer.analyze()
    analyzer.print_tree()