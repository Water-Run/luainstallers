# `luainstaller`: Python Library for Out-of-the-Box `.lua` Binary Packaging with Dependency Analysis Engine  

***[中文](./README-zh.md)***  

> `luainstaller` is open-sourced on [GitHub](https://github.com/Water-Run/luainstallers/tree/main/luainstaller) under the `LGPL` license and is a member of the [luainstallers](https://github.com/Water-Run/luainstallers/tree/main) toolkit.  

`luainstaller` is an open-source **Python library** that wraps a precompiled [luastatic](https://github.com/ers35/luastatic/tree/master) core and implements a dependency analysis engine, providing **one-click packaging of `.lua` scripts into executables**.  

`luainstaller` can be used in three ways:  

- ***As a command-line tool***  
- ***As a graphical tool***  
- ***As a library imported into your project***  

## Installation  

`luainstaller` is published on [PyPI](), and can be installed with `pip`:  

```bash
pip install luainstaller
```

After installation, run the following in your terminal:  

```bash
luainstaller
```

You should see:  

```plaintext
luainstaller by WaterRun. Version 1.0.
Visit: https://github.com/Water-Run/luainstallers/tree/main/luainstaller :-)
```

This means the installation was successful.  

## Getting Started  

The `luainstaller` workflow is straightforward:  

1. Scan the entry script, recursively build the dependency tree (if automatic dependency analysis is not disabled)  
2. Merge manually configured dependency scripts to produce the final dependency list  
3. Invoke the configured binary `luastatic` with the dependency list to compile  

Illustration:  

```plaintext
test.lua <entry script>
 | {automatic dependency analysis}
 ├──> require("utils/log")
 │     └── utils/log.lua
 │           └── require("utils/time")
 │                 └── utils/time.lua       ==>    <dependency list>
 ├──> require("core/init")                       [   
 │     ├── core/init.lua                         "utils/log.lua",
 │     ├── core/config.lua                       "utils/time.lua",
 │     └── core/db.lua                           "core/init.lua",
 └──(manually configured dependency)              "core/config.lua",
       └── extra/plugin.lua                      "core/db.lua", 
                                                 "extra/plugin.lua"
                                                 ]                                     
                                          ↓
                       {invoke corresponding precompiled luastatic command}
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

Other forms, including dynamic dependencies, will result in an error.  

> In such cases, you should disable automatic dependency analysis and instead add the required dependencies manually.  

### Using the Graphical Interface  

The easiest way to use `luainstaller` is via its `GUI`.  
`luainstaller` provides a Tkinter-based graphical interface. After installation, run:  

```bash
luainstaller-gui
```

This will start the GUI.  

> The GUI only exposes basic functionality.  

### Using the Command-Line Tool  

`luainstaller` can also be used directly as a command-line tool. Simply run:  

```bash
luainstaller
```

to start.  

> Or use `luainstaller-cli`; both are equivalent.  

#### Command Set  

##### Show Help  

```bash
luainstaller help
```

This prints usage help.  

##### List Available Precompiled Binaries  

```bash
luainstaller binaries [-match pattern]
```

This prints available precompiled binaries, named as `platform-and-arch_lua-version`, and indicates the default version (`5.4.8`).  
For example, `winarm64_515` means it targets Windows ARM 64-bit with `Lua 5.1.5`.  
By default, only binaries matching the current platform are listed.  

Arguments:  

- `match`: regular expression used to filter names  

#### View Logs  

```bash
luainstaller logs [-limit number] [-order {desc | asc}]
```

This prints operation logs stored by `luainstaller`, in reverse chronological order by default, limited to 100 entries.  
The logging system is powered by [SimpSave](https://github.com/Water-Run/SimpSave).  

Arguments:  

- `limit`: maximum number of entries to print; positive integer  
- `order`: time order, `asc` (ascending) or `desc` (descending)  

#### Dependency Analysis  

```bash
luainstaller analyze <entry_script> [-max max_deps]
```

This performs dependency analysis and prints the resulting list.  
By default, at most 36 dependencies are analyzed.  

Arguments:  

- `max`: maximum size of the dependency tree; positive integer  

#### Perform Compilation  

```bash
luainstaller <entry_script> [-require <dep.lua list>] [-max max_deps] [-binary <lua_binary_id>] [-output <output_path>] [--manual] [--detail]
```

This runs the compilation.  

Arguments:  

- `<entry_script>`: the entry script, and starting point for dependency analysis  
- `require`: dependency scripts; if already discovered by the analysis engine they will be skipped. Multiple values are separated by `,`  
- `max`: maximum dependency tree size; positive integer. Default is 36  
- `binary`: select a specific precompiled binary version, as listed by `luainstaller binaries`. Defaults to `Lua 5.4.8` matching the current platform  
- `output`: output executable path. Defaults to an executable with the same basename as the `.lua` file in the current directory; on Windows the `.exe` suffix is added automatically  
- `manual`: disable dependency analysis and compile only the entry script, unless `-require` is explicitly specified  
- `detail`: enable verbose output  

*Examples:*  

```bash
luainstaller hello_world.lua
```

Compiles `hello_world.lua` into an executable `hello_world` (Linux) or `hello_world.exe` (Windows) in the same directory, using `Lua 5.4.8` with the same bitness as the host system.  

```bash
luainstaller a.lua -require b.lua, c.lua --manual
```

Packages `a.lua` together with dependencies `b.lua` and `c.lua` into a single binary, with automatic dependency analysis disabled; this behavior is fully equivalent to invoking `luastatic` directly.  

```bash
luainstaller test.lua -binary lin32_515 -max 100 -output ../myProgram --detail
```

Packages `test.lua` using `Linux 32-bit` and `Lua 5.1.5`, analyzes up to 100 dependencies, outputs to `../myProgram`, and prints detailed compilation logs.  
