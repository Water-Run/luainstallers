# `luainstallers`  

***[中文](./README-zh.md)***  

`luainstallers` is a toolkit for packaging **`.lua` scripts into standalone, dependency-free executable binaries**, consisting of:  

- [luainstaller](./luainstaller/README.md): **Python library**. Can be used as a command-line tool (with a GUI implemented using `tkinter`), or imported as a library into your `Python` scripts  
- [lua2bin](./lua2bin/README.md): **Lua library**. Adopts an object-oriented style.  

Using [luastatic] as the packaging engine requires the local machine to have `lua`, `luastatic`, and `gcc` environments:  

- lua: [Lua official website](https://www.lua.org/), including the package manager `luarocks`  
- luastatic: `luarocks install luastatic`  
- gcc: usually comes with `linux`, on `windows` refer to: [MinGW](https://github.com/niXman/mingw-builds-binaries)

> The project is open-sourced on [GitHub](https://github.com/Water-Run/luainstallers) and is a comprehensive upgrade of the existing legacy project [LuaToEXE](https://github.com/Water-Run/luaToEXE), using the [LGPL](./License) license.