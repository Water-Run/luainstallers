# `luainstaller`: Python Library for Out-of-the-Box `.lua` Binary Packaging with Dependency Analysis Engine  

***[English](./README.md)***  

> `luainstaller` is open-sourced on [GitHub](https://github.com/Water-Run/luainstallers/tree/main/luainstaller), licensed under `LGPL`, and is a member of the [luainstallers](https://github.com/Water-Run/luainstallers/tree/main) toolkit collection.  

`luainstaller` is an open-source **Python library** that wraps the precompiled [luastatic](https://github.com/ers35/luastatic/tree/master), featuring a **dependency tree analysis engine** and providing **one-click `.lua` to executable packaging** capability.  

`luainstaller` can be used as:  

- ***A command-line tool***  
- ***A graphical user interface tool***  
- ***A Python library integrated into your own project***  

## Installation  

`luainstaller` is published on [PyPI](), and can be installed via `pip`:  

```bash
pip install luainstaller
```

After installation, run the following command in your terminal:  

```bash
luainstaller
```

You should see the output:  

```plaintext
luainstaller by WaterRun. Version 0.5.
Visit: https://github.com/Water-Run/luainstallers/tree/main/luainstaller :)
```

If you see this, the installation is successful.  

## Getting Started  

The workflow of `luainstaller` is straightforward:  

1. Analyze and build the dependency tree from the entry script (unless automatic analysis is disabled).  
2. Merge manually specified dependency scripts and generate a dependency manifest.  
3. Invoke the configured precompiled `luastatic` binary to build according to the manifest.  

Example:  

```plaintext
test.lua <Entry Script>
 | {Automatic Dependency Analysis}
 ├──> require("utils/log")
 │     └── utils/log.lua
 │           └── require("utils/time")
 │                 └── utils/time.lua       ==>    <Dependency Manifest>
 ├──> require("core/init")                       [   
 │     ├── core/init.lua                         "utils/log.lua",
 │     ├── core/config.lua                       "utils/time.lua",
 │     └── core/db.lua                           "core/init.lua",
 └──(Manually Configured Dependency)              "core/config.lua",
       └── extra/plugin.lua                      "core/db.lua", 
                                                 "extra/plugin.lua"
                                                 ]                                     
↓
{Invoke corresponding version of precompiled luastatic compiler}
win64_546 test.lua utils/log.lua utils/time.lua core/init.lua core/config.lua core/db.lua extra/plugin.lua -o test.exe
```

### Using the Graphical Interface  

The simplest way to use `luainstaller` is through its `GUI`.  
It provides a graphical interface implemented using `Tkinter`. After installation, run:  

```bash
luainstaller-gui
```

...and the interface will start.  

### Using the Command-Line Interface  

`luainstaller` can also be used directly in command-line mode.  

Command structure:  

#### Display Help  

```bash
luainstaller help
```

This prints the usage help.  

#### List Available Precompiled Binaries  

```bash
luainstaller binaries
```

This outputs all available precompiled binaries, composed of `platform-bit_luaVersion`, and indicates the default version (`5.4.8`).  
For example, `win64_515` means it’s for Windows 64-bit platform using `lua 5.1.5`.  

#### View Logs  

```bash
luainstaller logs
```

This prints the operation logs stored by `luainstaller`, in reverse chronological order.  
The logging system uses [SimpSave](https://github.com/Water-Run/SimpSave).  

#### Dependency Analysis  

```bash
luainstaller analyze <entry_script>
```

This performs a dependency analysis and prints the dependency tree.  

#### Perform Compilation  

```bash
luainstaller <entry_script> [-require <dependent .lua scripts>] [-binary <target Lua version>] [-output <output binary path>] [--manual] [--detail]
```

This performs compilation.  

Parameter Explanation:  

- `entry_script`: The entry script that serves as the root for dependency analysis.  
- `require`: One or more required scripts. If a script is already detected by the analyzer, it will be skipped. Use `,` to separate multiple entries.  
- `binary`: Choose a specific precompiled Lua binary version. See `luainstaller binaries` for available options. Defaults to platform-matching `lua 5.4.8`.  
- `output`: The output binary path. Defaults to the same directory as the entry `.lua`, with the same name. On `Windows`, `.exe` is automatically appended.  
- `manual`: Skips dependency analysis and directly compiles the entry script, unless `-require` dependencies are explicitly specified.  
- `detail`: Displays detailed build output.  

*Examples:*  

```bash
luainstaller hello_world.lua
```

Compiles `hello_world.lua` into `hello_world` (Linux) or `hello_world.exe` (Windows), using the same bitness and default `lua 5.4.8`.  

```bash
luainstaller a.lua -require b.lua,c.lua --manual
```

Compiles `a.lua` together with dependencies `b.lua` and `c.lua` into a binary, skipping automatic dependency analysis.  
This behaves identically to directly invoking `luastatic`.  

```bash
luainstaller test.lua -binary lin32_515 -output ../myProgram --detail
```

Packages `test.lua` using `Linux 32-bit` and `lua 5.1.5`, outputs the binary to the parent directory as `myProgram`,  
and shows detailed build information.