# `luainstallers`  

***[中文](./README-zh.md)***  

`luainstallers` is an **out-of-the-box toolkit for packaging `.lua` scripts into standalone, dependency-free native executables**, consisting of:  

- [luainstaller](./luainstaller/README.md): **Python library** — usable both as a command-line tool (with a `tkinter`-based graphical interface) and as a library importable into your own `Python` scripts.  
- [lua2bin](./lua2bin/README.md): **Lua library**.  

`luainstallers` is a comprehensive upgrade of the older project [LuaToEXE](https://github.com/Water-Run/luaToEXE).  
By integrating the precompiled [luastatic](https://github.com/ers35/luastatic/tree/master) core in place of [srlua](https://github.com/LuaDist/srlua), it produces **true native executables** that support **multi-platform builds** and **binary module compilation**.  
Additionally, it implements a **dependency tree analysis engine**, providing **automatic dependency resolution**, including libraries installed via `luarocks`.  

> The project is open-sourced on [GitHub](https://github.com/Water-Run/luainstallers/tree/main) under the [LGPL](./License) license.  
