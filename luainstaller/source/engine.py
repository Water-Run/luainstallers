"""
Compilation engine for luainstaller.
https://github.com/Water-Run/luainstallers/tree/main/luainstaller

This module provides the core compilation functionality using luastatic
to build standalone executables from Lua scripts.

:author: WaterRun
:file: engine.py
:date: 2025-11-24
"""

import os
import shutil
import subprocess
from pathlib import Path

from exceptions import (
    CompilationFailedError,
    CompilerNotFoundError,
    LuastaticNotFoundError,
    OutputFileNotFoundError,
    ScriptNotFoundError,
)


def verify_environment() -> None:
    r"""
    Verify that required tools are available in PATH.
    
    :raises LuastaticNotFoundError: If luastatic is not installed
    :raises CompilerNotFoundError: If gcc is not available
    """
    if not shutil.which('luastatic'):
        raise LuastaticNotFoundError()
    
    if not shutil.which('gcc'):
        raise CompilerNotFoundError('gcc')


def compile_lua_script(
    entry_script: str,
    dependencies: list[str],
    output: str | None = None,
    verbose: bool = False,
) -> str:
    r"""
    Compile Lua script with dependencies into standalone executable.
    
    :param entry_script: Path to entry Lua script
    :param dependencies: List of dependency file paths
    :param output: Output executable path (optional)
    :param verbose: Enable verbose output
    :return: Path to generated executable
    :raises ScriptNotFoundError: If entry script doesn't exist
    :raises CompilationFailedError: If compilation fails
    :raises OutputFileNotFoundError: If output file is not generated
    """
    # Verify environment
    verify_environment()
    
    # Validate entry script
    entry_path = Path(entry_script).resolve()
    if not entry_path.exists():
        raise ScriptNotFoundError(str(entry_script))
    
    # Determine output path
    if output:
        output_path = Path(output).resolve()
        output_dir = output_path.parent
        output_name = output_path.name
    else:
        output_dir = Path.cwd()
        output_name = entry_path.stem
        if os.name == 'nt':
            output_name += '.exe'
    
    # Build luastatic command
    command = ['luastatic', str(entry_path)]
    
    # Add dependencies
    for dep in dependencies:
        dep_path = Path(dep).resolve()
        if not dep_path.exists():
            if verbose:
                print(f"Warning: Dependency not found: {dep}")
            continue
        command.append(str(dep_path))
    
    if verbose:
        print(f"Executing: {' '.join(command)}")
        print(f"Working directory: {output_dir}")
    
    # Execute compilation
    result = subprocess.run(
        command,
        cwd=str(output_dir),
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        raise CompilationFailedError(
            ' '.join(command),
            result.returncode,
            result.stderr,
        )
    
    if verbose and result.stdout:
        print(result.stdout)
    
    # Determine expected output filename
    if output:
        expected_output = output_path
    else:
        if os.name == 'nt':
            expected_output = output_dir / f"{entry_path.stem}.exe"
        else:
            expected_output = output_dir / entry_path.stem
    
    # Verify output exists
    if not expected_output.exists():
        raise OutputFileNotFoundError(str(expected_output))
    
    if verbose:
        print(f"Compilation successful: {expected_output}")
    
    return str(expected_output)


def get_environment_status() -> dict[str, bool]:
    r"""
    Get status of compilation environment.
    
    :return: Dictionary with tool availability status
    """
    return {
        'luastatic': bool(shutil.which('luastatic')),
        'gcc': bool(shutil.which('gcc')),
        'lua': bool(shutil.which('lua')),
    }


def print_environment_status() -> None:
    r"""
    Print compilation environment status.
    """
    status = get_environment_status()
    
    print("Compilation Environment Status:")
    print("=" * 50)
    
    symbol = lambda x: "✓" if x else "✗"
    
    print(f"{symbol(status['luastatic'])} luastatic")
    print(f"{symbol(status['gcc'])} gcc")
    print(f"{symbol(status['lua'])} lua")
    
    print("=" * 50)
    
    if not status['luastatic']:
        print("\nInstall luastatic:")
        print("  luarocks install luastatic")
    
    if not status['gcc']:
        print("\nInstall gcc:")
        print("  Ubuntu/Debian: sudo apt install build-essential")
        print("  Fedora/RHEL:   sudo dnf install gcc")
        print("  Windows:       https://github.com/niXman/mingw-builds-binaries")
    
    if not status['lua']:
        print("\nInstall Lua:")
        print("  Ubuntu/Debian: sudo apt install lua5.4")
        print("  Fedora/RHEL:   sudo dnf install lua")
        print("  Windows:       https://www.lua.org/download.html")