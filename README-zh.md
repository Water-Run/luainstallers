# `luainstallers`  

***[English](./README.md)***  

`luainstallers`是一套将 **`.lua`脚本打包为无依赖的, 可执行二进制程序的库集**, 包括:  

- [luainstaller](./luainstaller/README-zh.md): **Python库**. 可作为命令行工具使用(包含由`tkinter`实现的图形界面), 也可作为库导入你的`Python`脚本中  
- [lua2bin](./lua2bin/README-zh.md): **Lua库**. 采用面向对象的风格.  

使用[luastatic]作为打包引擎, 需要本机具备`lua`, `luastatic`, `gcc`环境:  

- lua: [Lua官网](https://www.lua.org/), 包括包管理器`luarocks`  
- luastatic: `luarocks install luastatic`  
- gcc: `linux`上一般自带, `windows`上参考: [MinGW](https://github.com/niXman/mingw-builds-binaries)

> 项目开源于[GitHub](https://github.com/Water-Run/luainstallers), 是对既有旧项目[LuaToEXE](https://github.com/Water-Run/luaToEXE)的全面升级, 使用[LGPL](./License)协议.  
