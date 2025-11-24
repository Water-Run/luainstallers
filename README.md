# `luainstallers`  

***[中文](./README-zh.md)***  

`luainstallers` is a ready-to-use toolkit for packaging **`.lua` scripts into standalone, dependency-free executable binaries**, including:  

- [luainstaller](./luainstaller/README.md): **Python library**. Can be used as a command-line tool (with a GUI implemented using `tkinter`), or imported as a library into your `Python` scripts  
- [lua2bin](./lua2bin/README.md): **Lua library**. Adopts an object-oriented style.  

`luainstaller` optional engines:  

- [srlua](https://github.com/LuaDist/srlua): A classic, simple engine. Provides precompiled binaries for out-of-the-box use  
- [luastatic](https://github.com/ers35/luastatic): Compiles `.lua` into true native binaries. Requires local `lua`, `luastatic`, and `gcc` environment  

> The project is open-sourced on [GitHub](https://github.com/Water-Run/luainstallers) and is a comprehensive upgrade of the existing legacy project [LuaToEXE](https://github.com/Water-Run/luaToEXE), using the [LGPL](./License) license.