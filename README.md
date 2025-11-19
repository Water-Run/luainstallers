# `luainstallers`  

***[English](./README.md)***  

`luainstallers` is an out-of-the-box toolkit for packaging **`.lua` scripts into standalone, dependency-free native executables**, consisting of:  

- [luainstaller](./luainstaller/README-zh.md): a **Python library** that can be used as a command-line tool (with a `tkinter`-based graphical interface), or imported as a library into your own `Python` scripts  
- [lua2bin](./lua2bin/README-zh.md): a **Lua library** with an object-oriented style.  

`luainstallers` is a comprehensive upgrade of the existing legacy project [LuaToEXE](https://github.com/Water-Run/luaToEXE): by wrapping a precompiled [luastatic](https://github.com/ers35/luastatic/tree/master) in place of [srlua](https://github.com/LuaDist/srlua), it turns the packaged executables into true native binaries, supports multiple platforms, and can also compile binary modules. It also implements a dependency analysis engine with automatic dependency discovery (including libraries installed via `luarocks`).  

> The project is open-sourced on [GitHub](https://github.com/Water-Run/luainstallers) under the [LGPL](./License) license.  
