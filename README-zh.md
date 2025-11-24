# `luainstallers`  

***[English](./README.md)***  

`luainstallers`是一套将 **`.lua`脚本打包为无依赖的, 可执行二进制程序的开箱即用库集**, 包括:  

- [luainstaller](./luainstaller/README-zh.md): **Python库**. 可作为命令行工具使用(包含由`tkinter`实现的图形界面), 也可作为库导入你的`Python`脚本中  
- [lua2bin](./lua2bin/README-zh.md): **Lua库**. 采用面向对象的风格.  

`luainstaller`可选引擎:  

- [srlua](https://github.com/LuaDist/srlua): 一个经典, 简单的引擎. 提供预编译好的二进制, 实现开箱即用  
- [luastatic](https://github.com/ers35/luastatic): 将`.lua`编译为真正的二进制. 需要本机具备`lua`, `luastatic`, `gcc`环境  

> 项目开源于[GitHub](https://github.com/Water-Run/luainstallers), 是对既有旧项目[LuaToEXE](https://github.com/Water-Run/luaToEXE)的全面升级, 使用[LGPL](./License)协议.  
