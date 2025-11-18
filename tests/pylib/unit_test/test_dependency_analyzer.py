"""
Unit tests for dependency_analyzer.py

:author: WaterRun
:date: 2025-11-18
"""

from pathlib import Path

import pytest

from dependency_analyzer import (
    LuaLexer,
    ModuleResolver,
    DependencyAnalyzer,
    analyze_dependencies,
)
from exceptions import (
    DynamicRequireError,
    CircularDependencyError,
    ModuleNotFoundError,
    DependencyLimitExceededError,
    ScriptNotFoundError,
    CModuleNotSupportedError,
)


# ============================================================================
# LuaLexer Tests
# ============================================================================


class TestLuaLexer:
    """LuaLexer 的行为测试。"""

    def test_simple_require(self):
        source = '''
        local utils = require('utils')
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'utils'

    def test_multiple_requires(self):
        source = '''
        local utils = require('utils')
        local config = require("config")
        local core = require [[core]]
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 3
        assert requires[0][0] == 'utils'
        assert requires[1][0] == 'config'
        assert requires[2][0] == 'core'

    def test_dotted_module_name(self):
        source = '''
        local db = require('database.mysql.connection')
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'database.mysql.connection'

    def test_relative_paths(self):
        source = '''
        local local_mod = require('./local_module')
        local parent_mod = require("../parent_module")
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 2
        assert requires[0][0] == './local_module'
        assert requires[1][0] == '../parent_module'

    def test_require_without_parentheses(self):
        source = '''
        local utils = require 'utils'
        local config = require "config"
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 2
        assert requires[0][0] == 'utils'
        assert requires[1][0] == 'config'

    def test_require_with_spaces_and_newlines(self):
        source = '''
        local a = require
            (
            "moda"
            )
        local b = require
        'modb'
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert [name for name, _ in requires] == ['moda', 'modb']

    def test_ignore_require_in_string(self):
        source = '''
        local str = "require('fake')"
        local real = require('real')
        local str2 = 'another require("fake2")'
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'real'

    def test_ignore_require_in_line_comment(self):
        source = '''
        -- local fake = require('fake')
        local real = require('real')  -- require('also_fake')
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'real'

    def test_ignore_require_in_block_comment(self):
        source = '''
        --[[
        local fake = require('fake')
        ]]
        local real = require('real')
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'real'

    def test_ignore_require_in_nested_block_comment(self):
        source = '''
        --[==[
        local fake = require('fake')
        ]==]
        local real = require('real')
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'real'

    def test_long_string_require(self):
        source = '''
        local mod = require [[my_module]]
        local mod2 = require [==[another.module]==]
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 2
        assert requires[0][0] == 'my_module'
        assert requires[1][0] == 'another.module'

    def test_escaped_quotes_in_string(self):
        source = r'''
        local mod = require('module\'name')
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert 'module' in requires[0][0]

    def test_ignore_required_as_identifier(self):
        source = '''
        local is_required = true
        local mod = require('real')
        function is_required_func() end
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'real'

    def test_ignore_member_require_calls(self):
        """obj.require / obj:require 不应被识别为 require 关键字。"""
        source = '''
        obj.require("fake1")
        obj:require('fake2')
        local real = require("real")
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'real'

    def test_dynamic_require_variable(self):
        source = '''
        local module_name = "dynamic"
        local mod = require(module_name)
        '''
        lexer = LuaLexer(source, 'test.lua')

        with pytest.raises(DynamicRequireError) as exc_info:
            lexer.extract_requires()

        assert 'dynamic require' in str(exc_info.value).lower()
        assert 'module_name' in str(exc_info.value)

    def test_dynamic_require_concatenation(self):
        source = '''
        local mod = require('prefix.' .. 'suffix')
        '''
        lexer = LuaLexer(source, 'test.lua')

        with pytest.raises(DynamicRequireError) as exc_info:
            lexer.extract_requires()

        assert 'concatenation' in str(exc_info.value).lower()

    def test_dynamic_require_function_call(self):
        source = '''
        local mod = require(get_module_name())
        '''
        lexer = LuaLexer(source, 'test.lua')

        with pytest.raises(DynamicRequireError) as exc_info:
            lexer.extract_requires()

        assert 'get_module_name' in str(exc_info.value)

    def test_line_numbers_monotonic(self):
        """
        不强行依赖具体行号，只验证行号递增、非 0。
        """
        source = '''
        -- comment
        local mod1 = require('first')

        -- another
        local mod2 = require('second')
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 2
        (name1, line1), (name2, line2) = requires
        assert name1 == 'first'
        assert name2 == 'second'
        assert line1 > 0 and line2 > 0
        assert line1 < line2  # later require must have bigger line

    def test_multiline_require(self):
        source = '''
        local mod = require(
            'my_module'
        )
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'my_module'

    def test_multiple_requires_same_line(self):
        source = '''
        local a, b = require('mod1'), require('mod2')
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 2
        assert requires[0][0] == 'mod1'
        assert requires[1][0] == 'mod2'

    def test_empty_file(self):
        source = ''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert requires == []

    def test_file_without_requires(self):
        source = '''
        local function hello()
            print("Hello, world!")
        end
        hello()
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert requires == []

    def test_require_at_end_of_file_no_newline(self):
        source = "local m = require('mod')"
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == 'mod'

    def test_utf8_and_non_ascii(self):
        source = '''
        -- 这是中文注释，包含 require("fake")
        local 标识符 = require("真实模块")
        print("你好")
        '''
        lexer = LuaLexer(source, 'test.lua')
        requires = lexer.extract_requires()

        assert len(requires) == 1
        assert requires[0][0] == '真实模块'


# ============================================================================
# ModuleResolver Tests
# ============================================================================


class TestModuleResolver:
    """ModuleResolver 的查找逻辑测试。"""

    def test_resolve_simple_module(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("utils")')
        utils_file = create_lua_file('utils.lua', 'return {}')

        resolver = ModuleResolver(main_file.parent)
        resolved = resolver.resolve('utils', str(main_file))

        assert resolved == utils_file

    def test_resolve_dotted_module(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("lib.utils")')
        utils_file = create_lua_file('lib/utils.lua', 'return {}')

        resolver = ModuleResolver(main_file.parent)
        resolved = resolver.resolve('lib.utils', str(main_file))

        assert resolved == utils_file

    def test_resolve_init_module(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("mylib")')
        init_file = create_lua_file('mylib/init.lua', 'return {}')

        resolver = ModuleResolver(main_file.parent)
        resolved = resolver.resolve('mylib', str(main_file))

        assert resolved == init_file

    def test_resolve_relative_same_dir(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("./utils")')
        utils_file = create_lua_file('utils.lua', 'return {}')

        resolver = ModuleResolver(main_file.parent)
        resolved = resolver.resolve('./utils', str(main_file))

        assert resolved == utils_file

    def test_resolve_relative_parent_dir(self, create_lua_file):
        main_file = create_lua_file('src/main.lua', 'require("../config")')
        config_file = create_lua_file('config.lua', 'return {}')

        resolver = ModuleResolver(main_file.parent)
        resolved = resolver.resolve('../config', str(main_file))

        assert resolved == config_file

    def test_resolve_in_lua_modules_dir(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("external")')
        external_file = create_lua_file('lua_modules/external.lua', 'return {}')

        resolver = ModuleResolver(main_file.parent)
        resolved = resolver.resolve('external', str(main_file))

        assert resolved == external_file

    def test_resolve_in_lib_dir(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("helper")')
        helper_file = create_lua_file('lib/helper.lua', 'return {}')

        resolver = ModuleResolver(main_file.parent)
        resolved = resolver.resolve('helper', str(main_file))

        assert resolved == helper_file

    def test_module_not_found_error(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("nonexistent")')

        resolver = ModuleResolver(main_file.parent)

        with pytest.raises(ModuleNotFoundError) as exc_info:
            resolver.resolve('nonexistent', str(main_file))

        msg = str(exc_info.value)
        assert 'nonexistent' in msg
        assert 'main.lua' in msg

    def test_c_module_not_supported(self, create_lua_file):
        """
        C 模块必须位于 search_paths 之中（当前实现中为 base_path 及其特定子目录）。
        """
        main_file = create_lua_file('main.lua', 'require("cmodule")')
        c_module = main_file.parent / 'cmodule.so'
        c_module.write_bytes(b'fake so file')

        resolver = ModuleResolver(main_file.parent)

        with pytest.raises(CModuleNotSupportedError) as exc_info:
            resolver.resolve('cmodule', str(main_file))

        assert 'cmodule' in str(exc_info.value)

    def test_resolver_base_path_is_entry_dir(self, create_lua_file):
        """
        验证 resolver.base_path 就是入口脚本所在目录。
        """
        main_file = create_lua_file('src/main.lua', 'require("a")')
        create_lua_file('src/a.lua', 'return {}')

        analyzer = DependencyAnalyzer(str(main_file))
        assert analyzer.resolver.base_path == main_file.parent


# ============================================================================
# DependencyAnalyzer Tests - Simple Cases
# ============================================================================


class TestDependencyAnalyzerSimple:
    """DependencyAnalyzer 的简单场景测试。"""

    def test_no_dependencies(self, create_lua_file):
        main_file = create_lua_file('main.lua', '''
        print("Hello, world!")
        ''')

        deps = analyze_dependencies(str(main_file))

        assert deps == []

    def test_single_dependency(self, create_lua_file):
        main_file = create_lua_file('main.lua', '''
        local utils = require('utils')
        utils.greet()
        ''')
        utils_file = create_lua_file('utils.lua', '''
        return {
            greet = function() print("Hello") end
        }
        ''')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 1
        assert Path(deps[0]) == utils_file

    def test_two_independent_dependencies(self, create_lua_file):
        main_file = create_lua_file('main.lua', '''
        local utils = require('utils')
        local config = require('config')
        ''')
        utils_file = create_lua_file('utils.lua', 'return {}')
        config_file = create_lua_file('config.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 2
        assert set(Path(d) for d in deps) == {utils_file, config_file}

    def test_manual_mode_skips_analysis(self, create_lua_file):
        main_file = create_lua_file('main.lua', '''
        local utils = require('utils')
        ''')
        create_lua_file('utils.lua', 'return {}')

        deps = analyze_dependencies(str(main_file), manual_mode=True)

        assert deps == []

    def test_script_not_found_error(self):
        with pytest.raises(ScriptNotFoundError):
            analyze_dependencies('nonexistent.lua')

    def test_entry_script_not_counted_as_dep(self, create_lua_file):
        """
        验证返回的依赖列表不包含入口脚本本身。
        """
        main_file = create_lua_file('main.lua', 'require("mod")')
        mod_file = create_lua_file('mod.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert Path(main_file) not in map(Path, deps)
        assert Path(mod_file) in map(Path, deps)


# ============================================================================
# DependencyAnalyzer Tests - Nested Dependencies
# ============================================================================


class TestDependencyAnalyzerNested:
    """嵌套依赖场景测试。"""

    def test_two_level_dependency(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("b")')
        b_file = create_lua_file('b.lua', 'require("c")')
        c_file = create_lua_file('c.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 2
        # C comes before B (topological order)
        assert Path(deps[0]) == c_file
        assert Path(deps[1]) == b_file

    def test_three_level_dependency(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("b")')
        b_file = create_lua_file('b.lua', 'require("c")')
        c_file = create_lua_file('c.lua', 'require("d")')
        d_file = create_lua_file('d.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 3
        # D -> C -> B
        assert Path(deps[0]) == d_file
        assert Path(deps[1]) == c_file
        assert Path(deps[2]) == b_file

    def test_diamond_dependency(self, create_lua_file):
        """
        菱形依赖：A -> B,C -> D
        D 只应出现一次，且在 B、C 之前。
        """
        main_file = create_lua_file('main.lua', '''
        require("b")
        require("c")
        ''')
        b_file = create_lua_file('b.lua', 'require("d")')
        c_file = create_lua_file('c.lua', 'require("d")')
        d_file = create_lua_file('d.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 3
        dep_paths = [Path(d) for d in deps]
        assert dep_paths.count(d_file) == 1

        d_index = dep_paths.index(d_file)
        b_index = dep_paths.index(b_file)
        c_index = dep_paths.index(c_file)
        assert d_index < b_index
        assert d_index < c_index

    def test_complex_dependency_tree(self, create_lua_file):
        r"""
        复杂树：
              main
             /  |  \ 
            a   b   c
           / \  |
          d   e f
               |
               g
        """
        main_file = create_lua_file('main.lua', '''
        require("a")
        require("b")
        require("c")
        ''')
        a_file = create_lua_file('a.lua', '''
        require("d")
        require("e")
        ''')
        b_file = create_lua_file('b.lua', 'require("f")')
        c_file = create_lua_file('c.lua', 'return {}')
        d_file = create_lua_file('d.lua', 'return {}')
        e_file = create_lua_file('e.lua', 'return {}')
        f_file = create_lua_file('f.lua', 'require("g")')
        g_file = create_lua_file('g.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 7
        dep_paths = [Path(d) for d in deps]

        assert dep_paths.index(g_file) < dep_paths.index(f_file)
        assert dep_paths.index(f_file) < dep_paths.index(b_file)
        assert dep_paths.index(d_file) < dep_paths.index(a_file)
        assert dep_paths.index(e_file) < dep_paths.index(a_file)
        # c 只有自己，不关心顺序，只要在列表中
        assert c_file in dep_paths


# ============================================================================
# DependencyAnalyzer Tests - Circular Dependencies
# ============================================================================


class TestDependencyAnalyzerCircular:
    """循环依赖检测测试。"""

    def test_direct_circular_dependency(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("b")')
        create_lua_file('b.lua', 'require("main")')

        with pytest.raises(CircularDependencyError) as exc_info:
            analyze_dependencies(str(main_file))

        error_msg = str(exc_info.value)
        assert 'main.lua' in error_msg
        assert 'b.lua' in error_msg

    def test_indirect_circular_dependency(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("b")')
        create_lua_file('b.lua', 'require("c")')
        create_lua_file('c.lua', 'require("main")')

        with pytest.raises(CircularDependencyError) as exc_info:
            analyze_dependencies(str(main_file))

        error_msg = str(exc_info.value)
        assert 'main.lua' in error_msg
        assert 'b.lua' in error_msg
        assert 'c.lua' in error_msg

    def test_self_dependency(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("main")')

        with pytest.raises(CircularDependencyError) as exc_info:
            analyze_dependencies(str(main_file))

        error_msg = str(exc_info.value)
        assert 'main.lua' in error_msg


# ============================================================================
# DependencyAnalyzer Tests - Limits and Edge Cases
# ============================================================================


class TestDependencyAnalyzerLimits:
    """依赖个数限制及其它边缘情况测试。"""

    def test_dependency_limit_exceeded(self, create_lua_file):
        """
        构造 5 个依赖的链条，但限制为 3，应该报错。
        """
        main_file = create_lua_file('main.lua', 'require("m1")')
        for i in range(1, 6):
            next_req = f'require("m{i+1}")' if i < 5 else 'return {}'
            create_lua_file(f'm{i}.lua', next_req)

        with pytest.raises(DependencyLimitExceededError) as exc_info:
            analyze_dependencies(str(main_file), max_dependencies=3)

        msg = str(exc_info.value)
        assert '3' in msg  # Max limit
        assert '5' in msg  # Actual count

    def test_exactly_at_dependency_limit(self, create_lua_file):
        main_file = create_lua_file('main.lua', '''
        require("m1")
        require("m2")
        require("m3")
        ''')
        create_lua_file('m1.lua', 'return {}')
        create_lua_file('m2.lua', 'return {}')
        create_lua_file('m3.lua', 'return {}')

        deps = analyze_dependencies(str(main_file), max_dependencies=3)
        assert len(deps) == 3

    def test_default_max_dependencies(self, create_lua_file):
        """
        当前实现默认 max_dependencies 为 36。
        """
        main_file = create_lua_file('main.lua', 'require("m1")')
        create_lua_file('m1.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))
        assert len(deps) == 1

    def test_shared_dependencies_counted_once(self, create_lua_file):
        """
        A 和 B 都依赖 C，总数应该是 3（A, B, C），而不是 4。
        """
        main_file = create_lua_file('main.lua', '''
        require("a")
        require("b")
        ''')
        create_lua_file('a.lua', 'require("c")')
        create_lua_file('b.lua', 'require("c")')
        create_lua_file('c.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 3

    def test_zero_max_dependencies_disallows_anything(self, create_lua_file):
        """
        max_dependencies=0 时，只要出现一个依赖就应报错。
        """
        main_file = create_lua_file('main.lua', 'require("a")')
        create_lua_file('a.lua', 'return {}')

        with pytest.raises(DependencyLimitExceededError):
            analyze_dependencies(str(main_file), max_dependencies=0)

    def test_one_max_dependencies_allows_single_dep(self, create_lua_file):
        main_file = create_lua_file('main.lua', 'require("a")')
        a_file = create_lua_file('a.lua', 'return {}')

        deps = analyze_dependencies(str(main_file), max_dependencies=1)
        assert len(deps) == 1
        assert Path(deps[0]) == a_file


# ============================================================================
# Integration Tests - Real-world Scenarios
# ============================================================================


class TestDependencyAnalyzerIntegration:
    """偏真实项目结构的集成测试。"""

    def test_realistic_project_structure(self, create_lua_file):
        """
        典型项目布局，注意 config.lua 要在 src 下，
        否则与当前 ModuleResolver 的 search_paths 不符。
        """
        main_file = create_lua_file('src/main.lua', '''
        local config = require("config")
        local app = require("app.core")
        app.run(config)
        ''')

        # 根据当前实现，entry_script.parent = src 目录
        # 因此 config.lua 需要放在 src/config.lua
        create_lua_file('src/config.lua', '''
        return {
            port = 8080,
            host = "localhost"
        }
        ''')

        create_lua_file('src/app/core.lua', '''
        local utils = require("app.utils")
        local db = require("app.database")

        return {
            run = function(config)
                utils.log("Starting server...")
                db.connect(config)
            end
        }
        ''')

        create_lua_file('src/app/utils.lua', '''
        return {
            log = function(msg) print(msg) end
        }
        ''')

        create_lua_file('src/app/database.lua', '''
        local utils = require("app.utils")

        return {
            connect = function(config)
                utils.log("Connecting to database...")
            end
        }
        ''')

        deps = analyze_dependencies(str(main_file))

        # 期望依赖：config, utils, database, core
        assert len(deps) == 4
        dep_stems = [Path(d).stem for d in deps]
        for name in ('config', 'utils', 'database', 'core'):
            assert name in dep_stems

        utils_idx = dep_stems.index('utils')
        core_idx = dep_stems.index('core')
        database_idx = dep_stems.index('database')
        assert utils_idx < core_idx
        assert utils_idx < database_idx

    def test_mixed_require_styles(self, create_lua_file):
        main_file = create_lua_file('main.lua', '''
        local a = require('a')
        local b = require("b")
        local c = require [[c]]
        local d = require 'd'
        local e = require "e"
        ''')
        for name in ['a', 'b', 'c', 'd', 'e']:
            create_lua_file(f'{name}.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 5

    def test_unicode_in_files(self, create_lua_file):
        main_file = create_lua_file('main.lua', '''
        -- 这是中文注释
        local utils = require('utils')
        print("你好，世界！")
        ''')

        create_lua_file('utils.lua', '''
        -- UTF-8 文件
        return {
            greeting = "こんにちは"
        }
        ''')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 1

    def test_require_from_subdirectory_entry(self, create_lua_file):
        """
        entry 在子目录下，依赖应该相对于该目录解析。
        """
        main_file = create_lua_file('src/main.lua', 'require("mod")')
        mod_file = create_lua_file('src/mod.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))

        assert len(deps) == 1
        assert Path(deps[0]) == mod_file

    def test_require_relative_from_nested_module(self, create_lua_file):
        """
        嵌套模块中使用相对路径 require。
        """
        main_file = create_lua_file('src/main.lua', 'require("pkg.a")')
        a_file = create_lua_file('src/pkg/a.lua', 'require("../b")')
        b_file = create_lua_file('src/b.lua', 'return {}')

        deps = analyze_dependencies(str(main_file))
        dep_paths = [Path(d) for d in deps]

        assert len(dep_paths) == 2
        assert b_file in dep_paths
        assert a_file in dep_paths
        # b should come before a
        assert dep_paths.index(b_file) < dep_paths.index(a_file)


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.slow
class TestDependencyAnalyzerPerformance:
    """性能相关测试（默认加 slow 标记，可选择性运行）。"""

    def test_deep_dependency_chain(self, create_lua_file):
        """
        构造 20 层深度的依赖链。
        """
        main_file = create_lua_file('main.lua', 'require("m1")')

        for i in range(1, 21):
            if i < 20:
                content = f'require("m{i+1}")'
            else:
                content = 'return {}'
            create_lua_file(f'm{i}.lua', content)

        deps = analyze_dependencies(str(main_file), max_dependencies=20)

        assert len(deps) == 20
        # 验证排序：m20.lua 在最前，m1.lua 在最后
        stems = [Path(d).stem for d in deps]
        assert stems[0] == 'm20'
        assert stems[-1] == 'm1'

    
        """
        构造 15 个并列依赖的场景。
        """
        requires = '\n'.join(f'require("m{i}")' for i in range(1, 16))
        main_file = create_lua_file('main.lua', requires)

        for i in range(1, 16):
            create_lua_file(f'm{i}.lua', f'return {{id={i}}}')

        deps = analyze_dependencies(str(main_file), max_dependencies=15)

        assert len(deps) == 15
        stems = sorted((Path(d).stem for d in deps), key=lambda s: int(s[1:]))
        assert stems == [f'm{i}' for i in range(1, 16)]