r"""
Custom exception classes for luainstaller.
https://github.com/Water-Run/luainstallers/tree/main/luainstaller

:author: WaterRun
:file: exceptions.py
:date: 2025-11-18
"""

from abc import ABC


class LuaInstallerException(ABC, Exception):
    r"""
    Abstract base class for all luainstaller exceptions.
    
    All custom exceptions in luainstaller should inherit from this class
    to provide a unified exception hierarchy.
    """
    
    def __init__(self, message: str, details: str | None = None) -> None:
        r"""
        Initialize the exception.
        
        :param message: The main error message
        :param details: Additional details about the error
        """
        self.message = message
        self.details = details
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        r"""Format the complete error message."""
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class BinaryNotFoundError(LuaInstallerException):
    r"""
    Raised when the specified Lua binary version is not available.
    
    This occurs when trying to use a binary that doesn't exist in
    the binary directory or is not supported.
    """
    
    def __init__(self, binary_name: str, available_binaries: list[str] | None = None) -> None:
        r"""
        Initialize the BinaryNotFoundError.
        
        :param binary_name: The name of the binary that was not found
        :param available_binaries: List of available binary names
        """
        details = None
        if available_binaries:
            details = f"Available binaries: {', '.join(available_binaries)}"
        super().__init__(
            f"Binary '{binary_name}' not found",
            details
        )
        self.binary_name = binary_name
        self.available_binaries = available_binaries


class ScriptNotFoundError(LuaInstallerException):
    r"""
    Raised when a Lua script file cannot be found.
    
    This occurs when the entry script or a required dependency
    script does not exist at the specified path.
    """
    
    def __init__(self, script_path: str) -> None:
        r"""
        Initialize the ScriptNotFoundError.
        
        :param script_path: The path to the script that was not found
        """
        super().__init__(f"Lua script not found: {script_path}")
        self.script_path = script_path


class DependencyAnalysisError(LuaInstallerException):
    r"""
    Raised when dependency analysis fails.
    
    This can occur due to circular dependencies, malformed require
    statements, or other issues during dependency tree construction.
    """
    
    def __init__(self, script_path: str, reason: str) -> None:
        r"""
        Initialize the DependencyAnalysisError.
        
        :param script_path: The script where analysis failed
        :param reason: Description of why analysis failed
        """
        super().__init__(
            f"Dependency analysis failed for '{script_path}'",
            reason
        )
        self.script_path = script_path
        self.reason = reason


class CircularDependencyError(DependencyAnalysisError):
    r"""
    Raised when a circular dependency is detected.
    
    This occurs when script A requires script B, which in turn
    requires script A (directly or indirectly).
    """
    
    def __init__(self, dependency_chain: list[str]) -> None:
        r"""
        Initialize the CircularDependencyError.
        
        :param dependency_chain: The chain of dependencies forming the cycle
        """
        chain_str = " -> ".join(dependency_chain)
        super().__init__(
            dependency_chain[0],
            f"Circular dependency detected: {chain_str}"
        )
        self.dependency_chain = dependency_chain


class CompilationError(LuaInstallerException):
    r"""
    Raised when compilation with luastatic fails.
    
    This occurs when the underlying luastatic binary returns
    a non-zero exit code or encounters an error.
    """
    
    def __init__(self, command: str, return_code: int, stderr: str | None = None) -> None:
        r"""
        Initialize the CompilationError.
        
        :param command: The compilation command that failed
        :param return_code: The return code from luastatic
        :param stderr: Standard error output from the compilation process
        """
        details = f"Command: {command}\nReturn code: {return_code}"
        if stderr:
            details += f"\nStderr: {stderr}"
        super().__init__(
            "Compilation failed",
            details
        )
        self.command = command
        self.return_code = return_code
        self.stderr = stderr


class InvalidConfigurationError(LuaInstallerException):
    r"""
    Raised when configuration parameters are invalid.
    
    This occurs when user-provided configuration options
    are malformed or incompatible.
    """
    
    def __init__(self, parameter: str, value: str, reason: str) -> None:
        r"""
        Initialize the InvalidConfigurationError.
        
        :param parameter: The configuration parameter that is invalid
        :param value: The invalid value provided
        :param reason: Explanation of why the value is invalid
        """
        super().__init__(
            f"Invalid configuration for parameter '{parameter}': {value}",
            reason
        )
        self.parameter = parameter
        self.value = value
        self.reason = reason


class PlatformNotSupportedError(LuaInstallerException):
    r"""
    Raised when the current platform is not supported.
    
    This occurs when trying to compile on a platform for which
    no compatible binary is available.
    """
    
    def __init__(self, platform: str, architecture: str) -> None:
        r"""
        Initialize the PlatformNotSupportedError.
        
        :param platform: The platform name (e.g., 'linux', 'windows')
        :param architecture: The architecture (e.g., '64', '32')
        """
        super().__init__(
            f"Platform not supported: {platform} {architecture}-bit",
            "Please compile luastatic manually for your platform or use a supported platform"
        )
        self.platform = platform
        self.architecture = architecture


class LuaRocksError(LuaInstallerException):
    r"""
    Raised when there are issues with LuaRocks dependencies.
    
    This occurs when a required LuaRocks module cannot be found
    or there are problems resolving LuaRocks packages.
    """
    
    def __init__(self, module_name: str, reason: str) -> None:
        r"""
        Initialize the LuaRocksError.
        
        :param module_name: The name of the LuaRocks module
        :param reason: Description of the issue
        """
        super().__init__(
            f"LuaRocks module '{module_name}' error",
            reason
        )
        self.module_name = module_name
        self.reason = reason
     
        
class DynamicRequireError(DependencyAnalysisError):
    r"""
    Raised when a dynamic require statement is detected.
    
    Dynamic requires cannot be statically analyzed and must be
    converted to static form or manually specified.
    """
    
    def __init__(self, script_path: str, line_number: int, statement: str) -> None:
        r"""
        Initialize the DynamicRequireError.
        
        :param script_path: The script containing the dynamic require
        :param line_number: Line number where the dynamic require was found
        :param statement: The actual require statement
        """
        super().__init__(
            script_path,
            f"Dynamic require detected at line {line_number}: {statement}\n"
            f"Only static require statements can be analyzed. "
            f"Use require('module_name') with a literal string."
        )
        self.line_number = line_number
        self.statement = statement


class DependencyLimitExceededError(DependencyAnalysisError):
    r"""
    Raised when the total number of dependencies exceeds the limit.
    
    To prevent infinite loops or excessive compilation times,
    there is a hard limit of 99 total dependencies.
    """
    
    def __init__(self, current_count: int, limit: int = 99) -> None:
        r"""
        Initialize the DependencyLimitExceededError.
        
        :param current_count: The current dependency count
        :param limit: The maximum allowed dependencies
        """
        super().__init__(
            "<multiple>",
            f"Total dependency count ({current_count}) exceeds limit ({limit}). "
            f"This may indicate circular dependencies or an overly complex project."
        )
        self.current_count = current_count
        self.limit = limit


class ModuleNotFoundError(DependencyAnalysisError):
    r"""
    Raised when a required module cannot be resolved to a file path.
    
    This occurs when the module is not found in any search path.
    """
    
    def __init__(self, module_name: str, script_path: str, searched_paths: list[str]) -> None:
        r"""
        Initialize the ModuleNotFoundError.
        
        :param module_name: The module name that couldn't be found
        :param script_path: The script that requires this module
        :param searched_paths: List of paths where the module was searched
        """
        paths_str = "\n  - ".join(searched_paths)
        super().__init__(
            script_path,
            f"Cannot resolve module '{module_name}'.\n"
            f"Searched in:\n  - {paths_str}\n"
            f"Check if the module name is correct or if it needs to be installed via LuaRocks."
        )
        self.module_name = module_name
        self.searched_paths = searched_paths


class CModuleNotSupportedError(DependencyAnalysisError):
    r"""
    Raised when a C module (.so, .dll) is encountered.
    
    C modules require special compilation handling and are not
    currently supported by the automatic dependency analyzer.
    """
    
    def __init__(self, module_name: str, module_path: str) -> None:
        r"""
        Initialize the CModuleNotSupportedError.
        
        :param module_name: The name of the C module
        :param module_path: The path to the C module file
        """
        super().__init__(
            module_path,
            f"C module '{module_name}' detected at '{module_path}'.\n"
            f"C modules (.so, .dll, .dylib) are not supported by automatic dependency analysis.\n"
            f"You may need to compile them manually or use --manual mode."
        )
        self.module_name = module_name
        self.module_path = module_path