# `lua2bin`  

***[English](./README.md)***  

> `lua2bin`开源于[GitHub](), 遵循`LGPL`协议, 是[luainstallers]()工具集的成员  

`lua2bin`是一个开源的**lua库**, 封装了预编译的[luastatic](https://github.com/ers35/luastatic/tree/master), 实现了依赖树分析引擎, 提供了**一键式的将`.lua`打包为可执行文件的能力**.  

`lua2bin`发布在[luarocks]()上, 使用`luarocks install lua2bin`即可安装. 提供了面向对象的接口, 非常简洁易懂.  

*示例代码:*  

```lua
lua2bin = require('lua2bin')

myProgram = lua2bin.instance(
    'myProgram.lua'
)

myProgram:compile()
```

```lua
lua2bin = require('lua2bin')

myProgram = lua2bin.instance(
    'myProgram.lua'
)

myProgram.analyze = false;
myProgram:require('require_1.lua')
myProgram.set(lua2bin.TYPES.WIN32_50)

myProgram:build(
    'MyPath.exe'
)
```

## `API`参考  
