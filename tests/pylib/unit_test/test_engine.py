"""
Unit tests for engine.py

:author: WaterRun
:date: 2025-11-18
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from engine import (
    verify_environment,
    compile_lua_script,
    get_environment_status,
    print_environment_status,
)
from exceptions import (
    CompilationFailedError,
    CompilerNotFoundError,
    LuastaticNotFoundError,
    OutputFileNotFoundError,
    ScriptNotFoundError,
)


# ============================================================================
# verify_environment() Tests
# ============================================================================


class TestVerifyEnvironment:
    """verify_environment 函数测试。"""

    @patch('shutil.which')
    def test_all_tools_available(self, mock_which):
        """测试所有工具都可用的情况。"""
        mock_which.return_value = '/usr/bin/tool'
        
        # 不应抛出异常
        verify_environment()
        
        # 验证检查了正确的工具
        assert mock_which.call_count == 2
        mock_which.assert_any_call('luastatic')
        mock_which.assert_any_call('gcc')

    @patch('shutil.which')
    def test_luastatic_not_found(self, mock_which):
        """测试 luastatic 未安装。"""
        def which_side_effect(name):
            return '/usr/bin/gcc' if name == 'gcc' else None
        
        mock_which.side_effect = which_side_effect
        
        with pytest.raises(LuastaticNotFoundError) as exc_info:
            verify_environment()
        
        assert 'luastatic' in str(exc_info.value).lower()

    @patch('shutil.which')
    def test_gcc_not_found(self, mock_which):
        """测试 gcc 未安装。"""
        def which_side_effect(name):
            return '/usr/bin/luastatic' if name == 'luastatic' else None
        
        mock_which.side_effect = which_side_effect
        
        with pytest.raises(CompilerNotFoundError) as exc_info:
            verify_environment()
        
        error = exc_info.value
        assert error.compiler_name == 'gcc'

    @patch('shutil.which', return_value=None)
    def test_no_tools_available(self, mock_which):
        """测试没有工具可用。"""
        with pytest.raises(LuastaticNotFoundError):
            verify_environment()


# ============================================================================
# compile_lua_script() Tests - Basic Functionality
# ============================================================================


class TestCompileLuaScriptBasic:
    """compile_lua_script 基础功能测试。"""

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_simple_compilation_no_dependencies(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试无依赖的简单编译。"""
        script = create_lua_file('hello.lua', 'print("Hello, World!")')
        
        # 模拟成功的编译
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # 创建预期的输出文件
        if os.name == 'nt':
            output_file = Path.cwd() / 'hello.exe'
        else:
            output_file = Path.cwd() / 'hello'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [])
            
            assert result == str(output_file)
            assert output_file.exists()
            
            # 验证调用了正确的命令
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            command = call_args[0][0]
            
            assert command[0] == 'luastatic'
            assert str(script) in command[1]
            assert call_args[1]['cwd'] == str(Path.cwd())
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_compilation_with_single_dependency(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试带单个依赖的编译。"""
        main = create_lua_file('main.lua', 'require("utils")')
        utils = create_lua_file('utils.lua', 'return {}')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'main.exe'
        else:
            output_file = Path.cwd() / 'main'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(main), [str(utils)])
            
            # 验证命令包含依赖
            call_args = mock_run.call_args
            command = call_args[0][0]
            
            assert str(utils) in ' '.join(command)
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_compilation_with_multiple_dependencies(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试带多个依赖的编译。"""
        main = create_lua_file('main.lua', 'print("main")')
        deps = [
            create_lua_file('dep1.lua', 'return {}'),
            create_lua_file('dep2.lua', 'return {}'),
            create_lua_file('dep3.lua', 'return {}'),
        ]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'main.exe'
        else:
            output_file = Path.cwd() / 'main'
        output_file.touch()
        
        try:
            result = compile_lua_script(
                str(main),
                [str(d) for d in deps]
            )
            
            # 验证所有依赖都在命令中
            call_args = mock_run.call_args
            command = call_args[0][0]
            command_str = ' '.join(command)
            
            for dep in deps:
                assert str(dep) in command_str
        finally:
            if output_file.exists():
                output_file.unlink()

    def test_entry_script_not_found(self):
        """测试入口脚本不存在。"""
        with pytest.raises(ScriptNotFoundError) as exc_info:
            compile_lua_script('nonexistent.lua', [])
        
        assert 'nonexistent.lua' in str(exc_info.value)


# ============================================================================
# compile_lua_script() Tests - Output Path Handling
# ============================================================================


class TestCompileLuaScriptOutputPath:
    """compile_lua_script 输出路径处理测试。"""

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_default_output_current_directory(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试默认输出到当前目录。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [])
            
            assert Path(result).parent == Path.cwd()
            
            # 验证在当前目录执行
            call_args = mock_run.call_args
            assert call_args[1]['cwd'] == str(Path.cwd())
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_custom_output_path(
        self, mock_run, mock_which, create_lua_file, tmp_path
    ):
        """测试自定义输出路径。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        output_path = tmp_path / 'myapp'
        if os.name == 'nt':
            output_path = tmp_path / 'myapp.exe'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        output_path.touch()
        
        result = compile_lua_script(
            str(script),
            [],
            output=str(output_path)
        )
        
        assert result == str(output_path)
        
        # 验证在输出目录执行
        call_args = mock_run.call_args
        assert call_args[1]['cwd'] == str(tmp_path)

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_custom_output_with_extension_unix(
        self, mock_run, mock_which, create_lua_file, tmp_path
    ):
        """测试 Unix 平台自定义输出（无扩展名）。"""
        with patch('os.name', 'posix'):
            script = create_lua_file('test.lua', 'print("test")')
            
            output_path = tmp_path / 'myprogram'
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            output_path.touch()
            
            result = compile_lua_script(
                str(script),
                [],
                output=str(output_path)
            )
            
            assert not result.endswith('.exe')

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_custom_output_with_extension_windows(
        self, mock_run, mock_which, create_lua_file, tmp_path
    ):
        """测试 Windows 平台自定义输出（.exe 扩展名）。"""
        with patch('os.name', 'nt'):
            script = create_lua_file('test.lua', 'print("test")')
            
            output_path = tmp_path / 'myprogram.exe'
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            output_path.touch()
            
            result = compile_lua_script(
                str(script),
                [],
                output=str(output_path)
            )
            
            assert result.endswith('.exe')


# ============================================================================
# compile_lua_script() Tests - Compilation Failures
# ============================================================================


class TestCompileLuaScriptFailures:
    """compile_lua_script 编译失败测试。"""

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_compilation_returns_error_code(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试编译返回错误代码。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Compilation error: undefined symbol 'foo'"
        mock_run.return_value = mock_result
        
        with pytest.raises(CompilationFailedError) as exc_info:
            compile_lua_script(str(script), [])
        
        error = exc_info.value
        assert error.return_code == 1
        assert 'undefined symbol' in error.stderr

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_output_file_not_generated(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试输出文件未生成。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # 不创建输出文件，模拟编译成功但未生成可执行文件的情况
        
        with pytest.raises(OutputFileNotFoundError) as exc_info:
            compile_lua_script(str(script), [])
        
        if os.name == 'nt':
            assert 'test.exe' in exc_info.value.expected_path
        else:
            assert 'test' in exc_info.value.expected_path

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_compilation_with_stderr_warnings(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试编译有警告但成功的情况。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = "Warning: unused variable 'x'"
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            # 应该成功，即使有警告
            result = compile_lua_script(str(script), [])
            assert Path(result).exists()
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which')
    def test_luastatic_not_in_path(self, mock_which, create_lua_file):
        """测试 luastatic 不在 PATH 中。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        def which_side_effect(name):
            return '/usr/bin/gcc' if name == 'gcc' else None
        
        mock_which.side_effect = which_side_effect
        
        with pytest.raises(LuastaticNotFoundError):
            compile_lua_script(str(script), [])

    @patch('shutil.which')
    def test_gcc_not_in_path(self, mock_which, create_lua_file):
        """测试 gcc 不在 PATH 中。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        def which_side_effect(name):
            return '/usr/bin/luastatic' if name == 'luastatic' else None
        
        mock_which.side_effect = which_side_effect
        
        with pytest.raises(CompilerNotFoundError):
            compile_lua_script(str(script), [])


# ============================================================================
# compile_lua_script() Tests - Dependency Handling
# ============================================================================


class TestCompileLuaScriptDependencies:
    """compile_lua_script 依赖处理测试。"""

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_missing_dependency_is_skipped(
        self, mock_run, mock_which, create_lua_file, capsys
    ):
        """测试缺失的依赖被跳过（非详细模式）。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            # 依赖中包含不存在的文件
            result = compile_lua_script(
                str(script),
                ['nonexistent.lua'],
                verbose=False
            )
            
            # 应该成功，跳过缺失的依赖
            assert Path(result).exists()
            
            # 验证命令中不包含缺失的依赖
            call_args = mock_run.call_args
            command = call_args[0][0]
            assert 'nonexistent.lua' not in ' '.join(command)
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_missing_dependency_warning_in_verbose(
        self, mock_run, mock_which, create_lua_file, capsys
    ):
        """测试详细模式下缺失依赖的警告。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(
                str(script),
                ['missing.lua'],
                verbose=True
            )
            
            captured = capsys.readouterr()
            assert 'Warning' in captured.out
            assert 'missing.lua' in captured.out
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_empty_dependency_list(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试空依赖列表。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [])
            
            # 验证命令只包含入口脚本
            call_args = mock_run.call_args
            command = call_args[0][0]
            
            assert len(command) == 2  # luastatic + entry_script
            assert command[0] == 'luastatic'
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_dependency_order_preserved(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试依赖顺序被保留。"""
        script = create_lua_file('test.lua', 'print("test")')
        deps = [
            create_lua_file('a.lua', 'return {}'),
            create_lua_file('b.lua', 'return {}'),
            create_lua_file('c.lua', 'return {}'),
        ]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(
                str(script),
                [str(d) for d in deps]
            )
            
            # 验证依赖顺序
            call_args = mock_run.call_args
            command = call_args[0][0]
            
            # 找到依赖在命令中的位置
            a_idx = next(i for i, arg in enumerate(command) if 'a.lua' in arg)
            b_idx = next(i for i, arg in enumerate(command) if 'b.lua' in arg)
            c_idx = next(i for i, arg in enumerate(command) if 'c.lua' in arg)
            
            assert a_idx < b_idx < c_idx
        finally:
            if output_file.exists():
                output_file.unlink()


# ============================================================================
# compile_lua_script() Tests - Verbose Mode
# ============================================================================


class TestCompileLuaScriptVerbose:
    """compile_lua_script 详细模式测试。"""

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_verbose_output_includes_command(
        self, mock_run, mock_which, create_lua_file, capsys
    ):
        """测试详细模式输出包含命令。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [], verbose=True)
            
            captured = capsys.readouterr()
            assert 'Executing:' in captured.out
            assert 'luastatic' in captured.out
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_verbose_output_includes_working_directory(
        self, mock_run, mock_which, create_lua_file, capsys
    ):
        """测试详细模式输出包含工作目录。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [], verbose=True)
            
            captured = capsys.readouterr()
            assert 'Working directory:' in captured.out
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_verbose_output_includes_success_message(
        self, mock_run, mock_which, create_lua_file, capsys
    ):
        """测试详细模式输出包含成功消息。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [], verbose=True)
            
            captured = capsys.readouterr()
            assert 'Compilation successful:' in captured.out
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_verbose_shows_luastatic_stdout(
        self, mock_run, mock_which, create_lua_file, capsys
    ):
        """测试详细模式显示 luastatic 的标准输出。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Building test.c...\nLinking..."
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [], verbose=True)
            
            captured = capsys.readouterr()
            assert 'Building test.c' in captured.out
            assert 'Linking' in captured.out
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_non_verbose_suppresses_output(
        self, mock_run, mock_which, create_lua_file, capsys
    ):
        """测试非详细模式抑制输出。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Building test.c..."
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [], verbose=False)
            
            captured = capsys.readouterr()
            assert captured.out == ""
        finally:
            if output_file.exists():
                output_file.unlink()


# ============================================================================
# get_environment_status() Tests
# ============================================================================


class TestGetEnvironmentStatus:
    """get_environment_status 函数测试。"""

    @patch('shutil.which')
    def test_all_tools_available(self, mock_which):
        """测试所有工具都可用。"""
        mock_which.return_value = '/usr/bin/tool'
        
        status = get_environment_status()
        
        assert status['luastatic'] is True
        assert status['gcc'] is True
        assert status['lua'] is True

    @patch('shutil.which')
    def test_no_tools_available(self, mock_which):
        """测试没有工具可用。"""
        mock_which.return_value = None
        
        status = get_environment_status()
        
        assert status['luastatic'] is False
        assert status['gcc'] is False
        assert status['lua'] is False

    @patch('shutil.which')
    def test_partial_tools_available(self, mock_which):
        """测试部分工具可用。"""
        def which_side_effect(name):
            if name == 'lua':
                return '/usr/bin/lua'
            return None
        
        mock_which.side_effect = which_side_effect
        
        status = get_environment_status()
        
        assert status['luastatic'] is False
        assert status['gcc'] is False
        assert status['lua'] is True

    def test_returns_correct_keys(self):
        """测试返回正确的键。"""
        status = get_environment_status()
        
        assert 'luastatic' in status
        assert 'gcc' in status
        assert 'lua' in status
        assert len(status) == 3

    def test_all_values_are_boolean(self):
        """测试所有值都是布尔型。"""
        status = get_environment_status()
        
        for key, value in status.items():
            assert isinstance(value, bool)


# ============================================================================
# print_environment_status() Tests
# ============================================================================


class TestPrintEnvironmentStatus:
    """print_environment_status 函数测试。"""

    @patch('engine.get_environment_status')
    def test_prints_header(self, mock_status, capsys):
        """测试打印标题。"""
        mock_status.return_value = {
            'luastatic': True,
            'gcc': True,
            'lua': True,
        }
        
        print_environment_status()
        
        captured = capsys.readouterr()
        assert 'Compilation Environment Status:' in captured.out
        assert '=' * 50 in captured.out

    @patch('engine.get_environment_status')
    def test_shows_all_tools_status(self, mock_status, capsys):
        """测试显示所有工具状态。"""
        mock_status.return_value = {
            'luastatic': True,
            'gcc': False,
            'lua': True,
        }
        
        print_environment_status()
        
        captured = capsys.readouterr()
        assert 'luastatic' in captured.out
        assert 'gcc' in captured.out
        assert 'lua' in captured.out

    @patch('engine.get_environment_status')
    def test_shows_checkmarks_for_available_tools(self, mock_status, capsys):
        """测试为可用工具显示勾选标记。"""
        mock_status.return_value = {
            'luastatic': True,
            'gcc': True,
            'lua': True,
        }
        
        print_environment_status()
        
        captured = capsys.readouterr()
        # 应该有三个勾选标记
        assert captured.out.count('✓') == 3

    @patch('engine.get_environment_status')
    def test_shows_crosses_for_unavailable_tools(self, mock_status, capsys):
        """测试为不可用工具显示叉号。"""
        mock_status.return_value = {
            'luastatic': False,
            'gcc': False,
            'lua': False,
        }
        
        print_environment_status()
        
        captured = capsys.readouterr()
        # 应该有三个叉号
        assert captured.out.count('✗') == 3

    @patch('engine.get_environment_status')
    def test_shows_installation_hint_for_luastatic(self, mock_status, capsys):
        """测试显示 luastatic 安装提示。"""
        mock_status.return_value = {
            'luastatic': False,
            'gcc': True,
            'lua': True,
        }
        
        print_environment_status()
        
        captured = capsys.readouterr()
        assert 'luarocks install luastatic' in captured.out

    @patch('engine.get_environment_status')
    def test_shows_installation_hint_for_gcc(self, mock_status, capsys):
        """测试显示 gcc 安装提示。"""
        mock_status.return_value = {
            'luastatic': True,
            'gcc': False,
            'lua': True,
        }
        
        print_environment_status()
        
        captured = capsys.readouterr()
        assert 'gcc' in captured.out.lower()
        assert any(keyword in captured.out for keyword in ['apt', 'dnf', 'mingw'])

    @patch('engine.get_environment_status')
    def test_shows_installation_hint_for_lua(self, mock_status, capsys):
        """测试显示 Lua 安装提示。"""
        mock_status.return_value = {
            'luastatic': True,
            'gcc': True,
            'lua': False,
        }
        
        print_environment_status()
        
        captured = capsys.readouterr()
        assert 'lua' in captured.out.lower()

    @patch('engine.get_environment_status')
    def test_no_hints_when_all_available(self, mock_status, capsys):
        """测试所有工具可用时不显示提示。"""
        mock_status.return_value = {
            'luastatic': True,
            'gcc': True,
            'lua': True,
        }
        
        print_environment_status()
        
        captured = capsys.readouterr()
        # 不应该有"Install"相关的提示
        assert 'Install' not in captured.out


# ============================================================================
# Edge Cases and Special Scenarios
# ============================================================================


class TestEdgeCases:
    """边缘情况和特殊场景测试。"""

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_script_with_spaces_in_path(
        self, mock_run, mock_which, tmp_path
    ):
        """测试路径中包含空格的脚本。"""
        script_dir = tmp_path / "my scripts"
        script_dir.mkdir()
        script = script_dir / "test.lua"
        script.write_text('print("hello")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'test.exe'
        else:
            output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [])
            
            # 验证命令正确处理了空格
            call_args = mock_run.call_args
            command = call_args[0][0]
            assert str(script) in command
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_script_with_unicode_in_path(
        self, mock_run, mock_which, tmp_path
    ):
        """测试路径中包含 Unicode 字符的脚本。"""
        script_dir = tmp_path / "中文目录"
        script_dir.mkdir()
        script = script_dir / "测试.lua"
        script.write_text('print("你好")', encoding='utf-8')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / '测试.exe'
        else:
            output_file = Path.cwd() / '测试'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [])
            assert Path(result).exists()
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_very_long_dependency_list(
        self, mock_run, mock_which, create_lua_file, tmp_path
    ):
        """测试非常长的依赖列表。"""
        script = create_lua_file('main.lua', 'print("main")')
        
        # 创建100个依赖
        deps = []
        for i in range(100):
            dep = create_lua_file(f'dep{i:03d}.lua', f'return {{id={i}}}')
            deps.append(str(dep))
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'main.exe'
        else:
            output_file = Path.cwd() / 'main'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), deps)
            
            # 验证所有依赖都被添加
            call_args = mock_run.call_args
            command = call_args[0][0]
            assert len(command) >= 101  # entry + 100 deps
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_absolute_and_relative_paths_mixed(
        self, mock_run, mock_which, create_lua_file, tmp_path
    ):
        """测试混合绝对路径和相对路径。"""
        script = create_lua_file('main.lua', 'print("main")')
        abs_dep = create_lua_file('abs.lua', 'return {}')
        
        # 创建相对路径依赖
        rel_dep_path = Path('rel.lua')
        rel_dep_path.write_text('return {}')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        if os.name == 'nt':
            output_file = Path.cwd() / 'main.exe'
        else:
            output_file = Path.cwd() / 'main'
        output_file.touch()
        
        try:
            result = compile_lua_script(
                str(script),
                [str(abs_dep), 'rel.lua']
            )
            
            # 两个依赖都应该在命令中
            call_args = mock_run.call_args
            command = call_args[0][0]
            command_str = ' '.join(command)
            assert 'abs.lua' in command_str
            assert 'rel.lua' in command_str
        finally:
            if output_file.exists():
                output_file.unlink()
            if rel_dep_path.exists():
                rel_dep_path.unlink()


# ============================================================================
# Platform-Specific Tests
# ============================================================================


class TestPlatformSpecific:
    """平台特定功能测试。"""

    @patch('os.name', 'nt')
    @patch('shutil.which', return_value='C:\\tools\\tool.exe')
    @patch('subprocess.run')
    def test_windows_exe_extension(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试 Windows 平台 .exe 扩展名。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        output_file = Path.cwd() / 'test.exe'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [])
            assert result.endswith('.exe')
        finally:
            if output_file.exists():
                output_file.unlink()

    @patch('os.name', 'posix')
    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_unix_no_extension(
        self, mock_run, mock_which, create_lua_file
    ):
        """测试 Unix 平台无扩展名。"""
        script = create_lua_file('test.lua', 'print("test")')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        output_file = Path.cwd() / 'test'
        output_file.touch()
        
        try:
            result = compile_lua_script(str(script), [])
            assert not result.endswith('.exe')
        finally:
            if output_file.exists():
                output_file.unlink()


# ============================================================================
# Integration-like Tests
# ============================================================================


class TestIntegrationScenarios:
    """集成场景测试。"""

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_realistic_project_compilation(
        self, mock_run, mock_which, create_lua_file, tmp_path
    ):
        """测试真实项目的编译场景。"""
        # 创建项目结构
        main = create_lua_file('src/main.lua', '''
            local config = require("config")
            local utils = require("utils.helper")
            print("App started")
        ''')
        
        config = create_lua_file('src/config.lua', 'return {port=8080}')
        helper = create_lua_file('src/utils/helper.lua', 'return {log=print}')
        
        deps = [str(config), str(helper)]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Compiling main.lua..."
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        output_path = tmp_path / 'myapp'
        if os.name == 'nt':
            output_path = tmp_path / 'myapp.exe'
        output_path.touch()
        
        result = compile_lua_script(
            str(main),
            deps,
            output=str(output_path),
            verbose=True
        )
        
        assert Path(result).exists()
        assert Path(result) == output_path

    @patch('shutil.which', return_value='/usr/bin/tool')
    @patch('subprocess.run')
    def test_compilation_workflow_end_to_end(
        self, mock_run, mock_which, create_lua_file, tmp_path
    ):
        """测试端到端的编译工作流。"""
        # 1. 创建脚本
        script = create_lua_file('app.lua', 'print("Hello, World!")')
        
        # 2. 模拟编译过程
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # 3. 设置输出
        output = tmp_path / 'app'
        if os.name == 'nt':
            output = tmp_path / 'app.exe'
        output.touch()
        
        # 4. 执行编译
        result = compile_lua_script(
            str(script),
            [],
            output=str(output)
        )
        
        # 5. 验证结果
        assert Path(result).exists()
        assert Path(result).is_file()
        
        # 6. 验证调用
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][0] == 'luastatic'