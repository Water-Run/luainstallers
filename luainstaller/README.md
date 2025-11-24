# `luainstaller`: Python Library for Packaging `.lua` into Binaries with Dependency Analysis  

***[中文](./README-zh.md)***  

> `luainstaller` is open-sourced on [GitHub](https://github.com/Water-Run/luainstallers/tree/main/luainstaller) under the `LGPL` license and is a member of the [luainstallers](https://github.com/Water-Run/luainstallers/tree/main) toolkit  

`luainstaller` is an open-source **Python library** that encapsulates the capability to **package `.lua` files into executables**. It includes:  

- Optional packaging engines: out-of-the-box when using `srlua` as the packaging engine  
- A dependency analysis engine that automatically analyzes dependencies, including packages from `luarocks`  

`luainstaller` can be used:  

- ***As a command-line tool***  
- ***As a graphical tool***  
- ***As a library imported into your projects***  

## Installation  

`luainstaller` is published on [pypi]() and can be installed using `pip`:  

```bash
pip install luainstaller
```

After installation, run in the terminal:  

```bash
luainstaller
```

If you see the output:  

```plaintext
luainstaller by WaterRun. Version 1.0.
Visit: https://github.com/Water-Run/luainstallers/tree/main/luainstaller :-)
```

The installation was successful.  

## Getting Started  

The workflow of `luainstaller` is straightforward:  

1. Scan the entry script, recursively build dependency analysis (if automatic dependency analysis is not disabled)  
2. Merge manually configured dependency scripts to generate a dependency list  
3. Call the packaging engine based on the dependency list to compile and output to the specified directory  

As illustrated:  

```plaintext
test.lua <entry script>
 | {automatic dependency analysis}
 ├──> require("utils/log")
 │     └── utils/log.lua
 │           └── require("utils/time")
 │                 └── utils/time.lua       ==>    <dependency manifest>
 ├──> require("core/init")                       [   
 │     ├── core/init.lua                         "utils/log.lua",
 │     ├── core/config.lua                       "utils/time.lua",
 │     └── core/db.lua                           "core/init.lua",
 └──(manually configured dependencies)           "core/config.lua",
       └── extra/plugin.lua                      "core/db.lua", 
                                                 "extra/plugin.lua"
                                                 ]                                     
                                          ↓
                       {invoke precompiled luastatic compile command for the corresponding version}
win64_546 test.lua utils/log.lua utils/time.lua core/init.lua core/config.lua core/db.lua extra/plugin.lua -o test.exe
```

### About Automatic Dependency Analysis  

The automatic dependency analysis engine of `luainstaller` matches the following forms of `require` statements:  

```lua
require '{pkg_name}'
require "{pkg_name}"
require('pkg_name')
require("pkg_name")
require([[pkg_name]])
```

Other forms will cause errors, including dynamic dependencies.  

> In such cases, automatic dependency analysis should be disabled and manually add the required dependencies instead  

### About Optional Engines  

`luainstaller` supports optional packaging engines.  

- By default, it uses [srlua](https://github.com/LuaDist/srlua), a classic, simple packaging engine. Precompiled versions are bundled for out-of-the-box use.  

- Optionally, the [luastatic](https://github.com/ers35/luastatic) engine can be used, which compiles into true native binaries.  

> Using the `luastatic` engine requires environment configuration to ensure the following are in the environment variables:  
>> lua: [Lua official website](https://www.lua.org/), including the package manager `luarocks`  
>> luastatic: `luarocks install luastatic`  
>> gcc: usually comes with `linux`, on `windows` refer to: [MinGW](https://github.com/niXman/mingw-builds-binaries)

### Using as a Graphical Tool  

The simplest way to use it is through the `GUI`.  
`luainstaller` provides a graphical interface implemented with `Tkinter`. After installation, enter in the terminal:  

```bash
luainstaller-gui
```

to launch it.  

> The GUI interface only includes basic functionality  

### Using as a Command-Line Tool  

`luainstaller` can also be used directly as a command-line tool. Simply enter in the terminal:  

```bash
luainstaller
```

> Or `luainstaller-cli`, both are equivalent  

#### Command Set  

##### Get Help  

```bash
luainstaller help
```

##### Get Logs  

```bash
luainstaller logs [-limit limit_number] [-asc]
```

##### Dependency Analysis  

```bash
luainstaller analyze entry_script [-max max_dependencies]
```

##### Execute Compilation  

```bash
luainstaller build entry_script [-require <dependency .lua scripts>] [-max max_dependencies] [-output <output_binary_path>] [--luastatic] [--manual] [--detail]
```

## Using as a Library  

`luainstaller` can also be imported into your scripts as a library:  

```python
import luainstaller
```

And provides functional APIs.  

## API Reference  

### `get_logs()`

Get logs  

```python
def get_logs(limit: int | None = None,
             _range: range | None = None,
             desc: bool = True) -> list[dict[str, Any]]:
    r"""
    Returns luainstaller logs.
    :param limit: Return count limit, None means no limit
    :param _range: Return range limit, None means no limit
    :param desc: Whether to return in descending order
    :return list[dict[str, Any]]: List of log dictionaries
    """
```

Example:

```python
import luainstaller

log_1: dict = luainstaller.get_logs() # Get all logs in descending order
log_2: dict = luainstaller.get_logs(limit = 100, _range = range(128, 256), desc=False) # Get at most 100 logs in the range 128 to 256 in ascending order
```

### `analyze()`

Execute dependency analysis (corresponds to CLI `luainstaller analyze`)

```python
def analyze(entry: str,
            max_deps: int = 36) -> list[str]:
    r"""
    Execute dependency analysis on entry script.

    :param entry: Entry script path
    :param max_deps: Maximum recursive dependencies, default 36
    :return list[str]: List of analyzed dependency script paths
    """
```

Example:

```python
import luainstaller

deps_1: list = luainstaller.analyze("main.lua") # Dependency analysis, analyze at most 36 dependencies by default
deps_2: list = luainstaller.analyze("main.lua", max_deps=112) # Execute dependency analysis, change maximum dependency analysis count to 112
```

### `build()`

Execute compilation (corresponds to CLI `luainstaller build`)

```python
def build(entry: str,
          requires: list[str] | None = None,
          max_deps: int = 36,
          output: str | None = None,
          use_luastatic: bool = False,
          manual: bool = False,
          detail: bool = False,
          binary: str | None = None) -> str:
    r"""
    Execute script compilation.

    :param entry: Entry script
    :param requires: Manually specify dependency list; if empty, rely on automatic analysis only
    :param max_deps: Maximum dependency tree analysis count
    :param output: Output binary path, None uses default rules
    :param use_luastatic: Whether to use luastatic as packaging engine
    :param manual: Disable automatic dependency analysis
    :param detail: Whether to output detailed information
    :param binary: Specify precompiled luastatic binary (e.g., 'win64_546')
    :return str: Path to the generated executable file
    """
```

Example:

```python
import luainstaller

# Simplest build method, automatically analyze dependencies and generate an executable with the same name as the script
luainstaller.build("hello.lua")

# Manual mode: disable automatic dependency analysis, compile using only dependencies specified in requires
luainstaller.build("a.lua", requires=["b.lua", "c.lua"], manual=True)

# Advanced build example:
# - Enable luastatic engine
# - Specify using precompiled binary lin32_515 (linux 32bit + lua 5.1.5)
# - Set maximum dependency analysis count to 100
# - Output binary to "bin/myProgram"
# - Enable detailed output
luainstaller.build(
    "test.lua",
    max_deps=100,
    output="bin/myProgram",
    use_luastatic=True,
    detail=True,
    binary="lin32_515"
)
```