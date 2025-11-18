# `luainstallers`  

***[English](./README.md)***  

`luainstallers`是一套将**`.lua`脚本打包为无依赖的, 可执行二进制程序的开箱即用库集**, 包括:  

- [luainstaller](./luainstaller/README-zh.md): **Python库**. 可作为命令行工具使用(包含由`tkinter`实现的图形界面), 也可作为库导入你的`Python`脚本中  
- [lua2bin](./lua2bin/README-zh.md): **Lua库**.  

`luainstallers`是对旧项目[LuaToEXE](https://github.com/Water-Run/luaToEXE)的全面升级: 通过封装预编译的[luastatic](https://github.com/ers35/luastatic/tree/master)代替[srlua](https://github.com/LuaDist/srlua), 使打包后的可执行文件是真正的原生可执行文件, 并支持多平台, 也可执行编译扩展; 并实现了依赖分析引擎, 具备自动获取依赖依赖, 包括来自`luarocks`安装的库.  

> 项目开源于[GitHub](https://github.com/Water-Run/luainstallers), 使用[LGPL](./License)协议.  
